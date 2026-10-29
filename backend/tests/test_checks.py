from backend.checks import DeviceProbe, run_checks
from backend.models import OMNIVOICE
from backend.paths import ProjectPaths

from .fakes import cuda_device, item, ok_ffmpeg, write_marker


def test_complete_root_with_cuda_is_ready_with_nine_ok(fake_root):
    result = run_checks(fake_root, device_probe=cuda_device, ffmpeg_probe=ok_ffmpeg)

    assert result.ready is True
    assert result.ok_count == 9
    assert result.total == 9


def test_cpu_only_device_is_a_warning_but_still_ready(fake_root):
    result = run_checks(fake_root, device_probe=lambda: "cpu", ffmpeg_probe=ok_ffmpeg)

    assert result.ok_count == 8
    assert result.warning_count == 1
    assert item(result, "device").status == "warning"
    assert result.ready is True


def test_missing_omnivoice_marker_makes_it_missing_and_not_ready(fake_root):
    ProjectPaths(fake_root).marker(OMNIVOICE).unlink()

    result = run_checks(fake_root, device_probe=cuda_device, ffmpeg_probe=ok_ffmpeg)

    assert item(result, "model_omnivoice").status == "missing"
    assert result.ready is False


def test_marker_with_a_deleted_file_makes_model_missing(fake_root):
    snapshot = ProjectPaths(fake_root).snapshot_dir(OMNIVOICE, OMNIVOICE.revision)
    (snapshot / "model.safetensors").unlink()

    result = run_checks(fake_root, device_probe=cuda_device, ffmpeg_probe=ok_ffmpeg)

    assert item(result, "model_omnivoice").status == "missing"
    assert "model.safetensors" in item(result, "model_omnivoice").detail


def test_marker_with_a_wrong_file_size_makes_model_missing(fake_root):
    snapshot = ProjectPaths(fake_root).snapshot_dir(OMNIVOICE, OMNIVOICE.revision)
    (snapshot / "config.json").write_bytes(b"short")

    result = run_checks(fake_root, device_probe=cuda_device, ffmpeg_probe=ok_ffmpeg)

    assert item(result, "model_omnivoice").status == "missing"


def test_marker_with_another_revision_makes_model_missing(fake_root):
    write_marker(fake_root, OMNIVOICE, revision="0" * 40)

    result = run_checks(fake_root, device_probe=cuda_device, ffmpeg_probe=ok_ffmpeg)

    assert item(result, "model_omnivoice").status == "missing"


def test_ffmpeg_probe_that_raises_makes_only_ffmpeg_missing(fake_root):
    def broken_ffmpeg():
        raise RuntimeError("ffmpeg exited with 1")

    result = run_checks(fake_root, device_probe=cuda_device, ffmpeg_probe=broken_ffmpeg)

    assert item(result, "ffmpeg").status == "missing"
    assert item(result, "ffmpeg").detail == "ffmpeg exited with 1"
    assert len(result.items) == 9


def test_cpu_device_is_not_cached_but_cuda_is(fake_root):
    answers = iter(["cpu", "cuda", "cpu"])
    probe = DeviceProbe(detect=lambda: next(answers))

    first = run_checks(fake_root, device_probe=probe, ffmpeg_probe=ok_ffmpeg)
    second = run_checks(fake_root, device_probe=probe, ffmpeg_probe=ok_ffmpeg)
    third = run_checks(fake_root, device_probe=probe, ffmpeg_probe=ok_ffmpeg)

    assert item(first, "device").detail == "cpu"
    assert item(second, "device").detail == "cuda"
    assert item(third, "device").detail == "cuda"


def test_only_model_rows_carry_a_license(fake_root):
    result = run_checks(fake_root, device_probe=cuda_device, ffmpeg_probe=ok_ffmpeg)

    omnivoice = item(result, "model_omnivoice").license
    assert omnivoice.name == "CC BY-NC 4.0"
    assert omnivoice.url == "https://creativecommons.org/licenses/by-nc/4.0/"
    assert omnivoice.author == "k2-fsa"
    assert omnivoice.model_url == "https://huggingface.co/k2-fsa/OmniVoice"
    assert item(result, "model_whisper").license.name == "MIT"
    others = [i for i in result.items if not i.id.startswith("model_")]
    assert [i.license for i in others] == [None] * 7


def test_items_come_in_the_spec_order(fake_root):
    result = run_checks(fake_root, device_probe=cuda_device, ffmpeg_probe=ok_ffmpeg)

    assert [i.id for i in result.items] == [
        "python",
        "torch",
        "transformers",
        "omnivoice",
        "fastapi",
        "ffmpeg",
        "model_omnivoice",
        "model_whisper",
        "device",
    ]


def test_corrupt_marker_makes_model_missing(fake_root):
    ProjectPaths(fake_root).marker(OMNIVOICE).write_text("{not json", encoding="utf-8")

    result = run_checks(fake_root, device_probe=cuda_device, ffmpeg_probe=ok_ffmpeg)

    assert item(result, "model_omnivoice").status == "missing"
    assert item(result, "model_omnivoice").detail.startswith("marker เสีย")
