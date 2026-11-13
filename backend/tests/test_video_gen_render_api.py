"""The Render job of the สอนกลอง tab under /api/drums/render and its results, with real ffmpeg
and the fake samples (video-gen seam 1 › render to `done`, sound on the picture, `too_long`,
`busy`, `lesson_busy`, cancel, `ffmpeg_failed`, the results, a picture background)."""

import io
import subprocess
import threading
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageFont

from backend import disk, ffmpeg, paths
from backend.app import app
from backend.paths import ProjectPaths
from backend.video_gen import captions, frames, kit, lessons, render

from .fakes import FINISHED, png, poll_until, put_background, restart

LESSONS = "/api/drums/lessons"
RENDER = "/api/drums/render"
SNARE = kit.STRIKE["snare"].center


class FakePiped:
    """The job's `run_piped`: the real one, but frame `pause_at` waits for `released` or the
    cancel, `audio` keeps each run's `audio.wav`, and `change` may rewrite the command first."""

    def __init__(self):
        self.pause_at: int | None = None
        self.reached, self.released = threading.Event(), threading.Event()
        self.audio: list[bytes] = []
        self.change = lambda command: command

    def __call__(self, command, cwd, cancel, drawn, on_frame) -> None:
        self.audio.append((Path(cwd) / render.AUDIO).read_bytes())

        def paused():
            for n, frame in enumerate(drawn):
                if n == self.pause_at:
                    self.reached.set()
                    while not (self.released.is_set() or cancel.is_set()):
                        cancel.wait(0.01)
                yield frame

        ffmpeg.run_piped(self.change(command), cwd, cancel, paused(), on_frame)


@pytest.fixture
def project(fake_root, monkeypatch) -> ProjectPaths:
    monkeypatch.setattr(paths, "ROOT", fake_root)
    return ProjectPaths(fake_root)


@pytest.fixture
def piped(monkeypatch) -> FakePiped:
    fake = FakePiped()
    title_font = lambda _project: ImageFont.load_default(captions.TITLE_SIZE)  # noqa: E731 – the fake root's Kanit is a name only
    monkeypatch.setattr(render, "render_jobs", render.DrumRenderJobs(run_piped=fake, title_font=title_font))
    return fake


@pytest.fixture
def client(project, piped) -> TestClient:
    return TestClient(app, base_url="http://127.0.0.1")


def short_lesson(client, notes: list[dict] | None = None, **changes) -> dict:
    """BPM 240, one bar, one chapter: a 1 s count-in, a 1 s bar, the 1.5 s tail."""
    lesson = client.post(LESSONS, json={"title": "FILL"}).json()
    body = {k: v for k, v in lesson.items() if k not in ("id", "version", "updated_at", "length_s")}
    body |= {
        "bpm": 240,
        "groove": {"bars": 1, "notes": notes if notes is not None else [{"piece": "snare", "step": 0, "hand": "R", "hit": "normal"}]},
        "chapters": [{"label": "", "text": "", "focus": [], "repeats": 1, "speed": 100}],
    } | changes
    response = client.put(f"{LESSONS}/{lesson['id']}", json=body)
    assert response.status_code == 200, response.json()
    return response.json()


def start(client, lesson_id: str):
    return client.post(RENDER, json={"lesson_id": lesson_id})


def rendered(client, lesson_id: str) -> dict:
    response = start(client, lesson_id)
    assert response.status_code == 202, response.json()
    return poll_until(client, RENDER, lambda job: job["state"] in FINISHED, timeout_s=60)


def renders_dir(project: ProjectPaths, lesson_id: str) -> Path:
    return project.lessons_dir / lesson_id / "renders"


def ffmpeg_out(*args: str) -> bytes:
    return subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", *args], check=True, capture_output=True).stdout


# --- render to done ---


def test_a_render_is_a_1080x1920_30fps_h264_aac_mp4_as_long_as_the_lesson_with_its_srt_and_json(client, project):
    lesson = short_lesson(client)
    job = rendered(client, lesson["id"])

    assert (job["state"], job["percent"], job["lesson_id"]) == ("done", 100, lesson["id"])
    folder = renders_dir(project, lesson["id"])
    assert sorted(p.suffix for p in folder.iterdir()) == [".json", ".mp4", ".srt"]
    info = ffmpeg.input_info(folder / f"{job['result']}.mp4")
    assert "1080x1920" in info and "30 fps" in info and "Video: h264" in info and "Audio: aac" in info
    assert ffmpeg.probe(folder / f"{job['result']}.mp4").duration_s == pytest.approx(lesson["length_s"], abs=0.1)
    assert not project.drums_render_dir.exists()


def test_the_snare_s_sound_starts_within_a_frame_of_its_red_ring(client, project):
    lesson = short_lesson(client)  # the snare on the first step after a 1 s count-in
    job = rendered(client, lesson["id"])
    mp4 = renders_dir(project, lesson["id"]) / f"{job['result']}.mp4"

    rate = 48_000
    sound = np.frombuffer(ffmpeg_out("-i", str(mp4), "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"), dtype=np.int16)
    after_count_in = np.abs(sound[int(0.9 * rate) : int(1.3 * rate)].astype(np.int32))
    sound_at = (int(0.9 * rate) + int(np.argmax(after_count_in > after_count_in.max() // 2))) / rate
    # Beside the stick's head, whose letter libass draws over the strike point; still in the red flash.
    x, y = SNARE[0] - 16, SNARE[1]
    # 2×2: yuv420p can't crop to one pixel. Each frame is 12 bytes; its first pixel is the strike point.
    pixels = ffmpeg_out("-i", str(mp4), "-vf", f"crop=2:2:{x}:{y}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-")
    red = [n for n in range(len(pixels) // 12) if pixels[12 * n] > 180 and pixels[12 * n + 1] < 110 and pixels[12 * n + 2] < 110]
    assert abs(red[0] / frames.FPS - sound_at) <= 1 / frames.FPS


def corner_of_first_frame(mp4: Path) -> tuple[int, int, int]:
    """The top-left pixel of frame 0, from a 2×2 crop (yuv420p can't crop to one pixel)."""
    pixels = ffmpeg_out("-i", str(mp4), "-vf", "crop=2:2:0:0", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-")
    return pixels[0], pixels[1], pixels[2]


def test_a_lesson_with_a_picture_renders_it_blurred_under_55_percent_black(client, project):
    plain = short_lesson(client)
    pictured = short_lesson(client)
    # Red left, blue right: blurred, the two run into each other along the middle.
    halves = Image.new("RGB", (frames.WIDTH, frames.HEIGHT), "#0000FF")
    halves.paste("#FF0000", (0, 0, frames.WIDTH // 2, frames.HEIGHT))
    out = io.BytesIO()
    halves.save(out, "PNG")
    assert put_background(client, pictured["id"], out.getvalue()).status_code == 200

    plain_job, pictured_job = rendered(client, plain["id"]), rendered(client, pictured["id"])

    colors = corner_of_first_frame(renders_dir(project, plain["id"]) / f"{plain_job['result']}.mp4")
    mp4 = renders_dir(project, pictured["id"]) / f"{pictured_job['result']}.mp4"
    corner = corner_of_first_frame(mp4)
    assert corner != colors
    # Pure red under 55 % black is (115, 0, 0); h264 moves a few steps either way.
    assert abs(corner[0] - 115) <= 8 and max(corner[1], corner[2]) <= 8
    # On the seam (left of the kit's middle, in the background only) both colours show.
    middle = ffmpeg_out("-i", str(mp4), "-vf", f"crop=2:2:{frames.WIDTH // 2}:{frames.HEIGHT - 40}", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-")
    assert middle[0] > 20 and middle[2] > 20


def test_a_render_keeps_the_picture_it_started_with_and_the_picture_can_t_change_meanwhile(client, project, piped):
    lesson = short_lesson(client)
    put_background(client, lesson["id"], png(540, 960, "#FF0000"))
    piped.pause_at = 10
    assert start(client, lesson["id"]).status_code == 202
    assert piped.reached.wait(10)

    replaced = put_background(client, lesson["id"], png(540, 960, "#00FF00"))
    removed = client.delete(f"{LESSONS}/{lesson['id']}/background")
    checked = client.post(f"{LESSONS}/{lesson['id']}/background/check", json={"size": 1000})
    # The API can't change it meanwhile (409 above), so the file itself changes: this render
    # still has its copy in `.render/` (spec › Render job step 6).
    green = io.BytesIO()
    Image.new("RGB", (frames.WIDTH, frames.HEIGHT), "#00FF00").save(green, "JPEG")
    (project.lessons_dir / lesson["id"] / lessons.BACKGROUND).write_bytes(green.getvalue())
    piped.released.set()
    job = poll_until(client, RENDER, lambda job: job["state"] in FINISHED, timeout_s=60)

    for refused in (replaced, removed, checked):
        assert (refused.status_code, refused.json()["code"]) == (409, "lesson_busy")
    corner = corner_of_first_frame(renders_dir(project, lesson["id"]) / f"{job['result']}.mp4")
    assert corner[0] > 80 and corner[1] < 30  # the red's (115, 0, 0), not the green's (0, 115, 0)


def test_the_same_lesson_rendered_twice_mixes_the_same_audio_wav(client, piped):
    lesson = short_lesson(client)
    rendered(client, lesson["id"])
    rendered(client, lesson["id"])

    assert len(piped.audio) == 2 and piped.audio[0] == piped.audio[1]


# --- refused ---


def test_a_render_without_the_drum_samples_is_not_ready(client, project):
    lesson = short_lesson(client)
    project.drum_kit_marker.unlink()

    response = start(client, lesson["id"])
    assert response.status_code == 503
    assert response.json()["code"] == "not_ready" and response.json()["rows"] == ["drum_kit"]


def test_a_lesson_over_ninety_seconds_is_too_long(client):
    lesson = short_lesson(client, bpm=40, chapters=[{"label": "", "text": "", "focus": [], "repeats": 8, "speed": 50}])
    assert lesson["length_s"] > 90

    response = start(client, lesson["id"])
    assert (response.status_code, response.json()["code"]) == (422, "too_long")


def test_a_render_with_too_little_disk_is_disk_full(client, monkeypatch):
    lesson = short_lesson(client)
    monkeypatch.setattr(disk, "free_bytes", lambda _root: disk.MIN_FREE_BYTES + 3 * 1024 * 1024)  # under 3.5 s × 2 MB

    response = start(client, lesson["id"])
    assert (response.status_code, response.json()["code"]) == (507, "disk_full")


def test_an_unknown_lesson_is_not_found_and_a_body_without_one_invalid(client):
    assert start(client, "aaaaaaaaaaaa").status_code == 404
    assert client.post(RENDER, json={}).json()["code"] == "invalid_request"


# --- while it runs ---


def test_a_second_render_is_busy_naming_the_lesson_that_renders(client, piped):
    first, second = short_lesson(client), short_lesson(client)
    piped.pause_at = 10
    assert start(client, first["id"]).status_code == 202
    assert piped.reached.wait(10)

    response = start(client, second["id"])
    assert response.status_code == 409
    assert response.json()["code"] == "busy" and response.json()["lesson_id"] == first["id"]
    assert client.get(LESSONS).status_code == 200
    piped.released.set()
    poll_until(client, RENDER, lambda job: job["state"] in FINISHED, timeout_s=60)


def test_a_lesson_that_renders_can_t_be_deleted_and_a_put_reaches_only_the_next_render(client, project, piped):
    lesson = short_lesson(client)
    piped.pause_at = 10
    assert start(client, lesson["id"]).status_code == 202
    assert piped.reached.wait(10)

    deleted = client.delete(f"{LESSONS}/{lesson['id']}")
    assert (deleted.status_code, deleted.json()["code"]) == (409, "lesson_busy")
    renamed = short_lesson_put(client, lesson, title="NEW TITLE")
    assert renamed.status_code == 200
    piped.released.set()
    job = poll_until(client, RENDER, lambda job: job["state"] in FINISHED, timeout_s=60)
    [listed] = client.get(f"{LESSONS}/{lesson['id']}/renders").json()
    assert (job["state"], listed["title"]) == ("done", "FILL")


def short_lesson_put(client, lesson: dict, **changes):
    body = {k: v for k, v in lesson.items() if k not in ("id", "version", "updated_at", "length_s")} | changes
    return client.put(f"{LESSONS}/{lesson['id']}", json=body)


def test_a_cancel_while_frames_go_leaves_no_partial(client, project, piped):
    lesson = short_lesson(client)
    piped.pause_at = 10
    assert start(client, lesson["id"]).status_code == 202
    assert piped.reached.wait(10)

    assert client.post(f"{RENDER}/cancel", json={}).status_code == 200
    job = poll_until(client, RENDER, lambda job: job["state"] in FINISHED, timeout_s=30)
    assert job["state"] == "cancelled"
    assert list(renders_dir(project, lesson["id"]).iterdir()) == []
    assert not project.drums_render_dir.exists()
    response = client.post(f"{RENDER}/cancel", json={})
    assert (response.status_code, response.json()["code"]) == (409, "not_running")


def test_ffmpeg_stopping_at_its_start_fails_the_render_with_its_last_line(client, project, piped):
    lesson = short_lesson(client)
    # A fontsdir ffmpeg can't parse: the `ass` filter refuses it before the first frame.
    piped.change = lambda command: [arg.replace(":fontsdir=", ":nope=") for arg in command]

    job = rendered(client, lesson["id"])
    assert (job["state"], job["error"]) == ("failed", "ffmpeg_failed")
    assert job["message"] == "render ไม่สำเร็จ: Error opening output files: Option not found"
    assert list(renders_dir(project, lesson["id"]).iterdir()) == []


def test_a_backend_restart_removes_the_work_folder_and_every_partial(client, project):
    lesson = short_lesson(client)
    folder = renders_dir(project, lesson["id"])
    folder.mkdir(parents=True)
    (folder / "20261113-103000.mp4.partial").write_bytes(b"half")
    project.drums_render_dir.mkdir(parents=True)

    restart(client)
    assert list(folder.iterdir()) == []
    assert not project.drums_render_dir.exists()


# --- the results ---


def test_renders_are_listed_newest_first_served_counted_and_deleted(client, project):
    lesson = short_lesson(client)
    first = rendered(client, lesson["id"])["result"]
    second = rendered(client, lesson["id"])["result"]

    listed = client.get(f"{LESSONS}/{lesson['id']}/renders").json()
    assert [row["name"] for row in listed] == [second, first]
    assert listed[0]["length_s"] == pytest.approx(lesson["length_s"], abs=0.01)
    [row] = [row for row in client.get(LESSONS).json() if row["id"] == lesson["id"]]
    assert row["renders"] == 2
    mp4 = client.get(f"{LESSONS}/{lesson['id']}/renders/{second}.mp4")
    assert (mp4.status_code, mp4.headers["content-type"]) == (200, "video/mp4")
    srt = client.get(f"{LESSONS}/{lesson['id']}/renders/{second}.srt")
    assert srt.status_code == 200 and "FILL" in srt.text
    assert client.delete(f"{LESSONS}/{lesson['id']}/renders/{second}").status_code == 204
    assert client.get(f"{LESSONS}/{lesson['id']}/renders/{second}.mp4").status_code == 404
    assert client.delete(f"{LESSONS}/{lesson['id']}").status_code == 204
    assert not (project.lessons_dir / lesson["id"]).exists()


def test_a_render_a_player_holds_open_is_in_use(client, monkeypatch):
    lesson = short_lesson(client)
    name = rendered(client, lesson["id"])["result"]
    real_unlink = Path.unlink

    def unlink(path, missing_ok=False):
        if path.suffix == ".mp4":
            raise PermissionError(32, "The process cannot access the file")
        real_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", unlink)
    response = client.delete(f"{LESSONS}/{lesson['id']}/renders/{name}")
    assert (response.status_code, response.json()["code"]) == (409, "in_use")
