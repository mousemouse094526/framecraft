"""The Spoil draft as the API shows and changes it, the token count of the chosen
Transcripts, and the Draft job: one at a time, a backend thread that owns the state
and the file, and a child process that runs Qwen (ADR 0010, ADR 0012, ADR 0015).

Steps and rules are in docs/features/spoil-maker/spec.md › Spoil draft and › Draft
job (D4, D5, D7, D8, D18, D19, D25–D28, D39, D46, D51).
"""

import logging
import re
import threading
import time
from typing import Literal

from pydantic import BaseModel

from backend import checks, gpu, paths, spoil_maker
from backend.errors import ApiError, JobFailed, require_rows
from backend.jobs import Cancelled, ModelJobSlot, short, stop_process
from backend.models import QWEN
from backend.paths import ProjectPaths
from backend.spoil import transcribe
from backend.spoil.transcribe import Transcript
from backend.spoil_maker import describe, draft_file, script, settings, shots, thai, voices
from backend.spoil_maker.draft_file import Draft, Layout, Ref, Sentence, ShotRef
from backend.spoil_maker.llm import Generate, Generated, Ready, WorkerError
from backend.spoil_maker.script import Brief
from backend.spoil_maker.shots import ShotsFile

log = logging.getLogger(__name__)

State = Literal["writing", "matching", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"writing", "matching"})
ErrorCode = Literal["draft_failed", "crashed", "model_failed", "internal"]
Status = Literal["no_shot", "no_audio", "stale_audio", "ready"]

LAYOUTS: tuple[Layout, ...] = ("A", "B", "C")
TARGET_MIN, TARGET_MAX = 30, 180  # D39
TOKEN_LIMIT = 32_000  # D46
ATTEMPTS = 3
WINDOW_SECONDS = 30  # Shots this far around the lines a sentence cites (D18, D26)

# spec › ค่าการสร้างข้อความ; thinking is off for every step (llm.generate).
WRITE_TEMPERATURE = 0.3  # D61: 0.5 and 0.7 swing ±40% in length, 0.1 can run on
WRITE_TIMEOUT_SECONDS = 600
PICK_TEMPERATURE = 0.0
PICK_MAX_TOKENS = 64
PICK_TIMEOUT_SECONDS = 60
# A pick reads about 0.4 s a Shot on an M2: 40 is 17 s, a 96-minute film's 840 are minutes (D61).
PICK_MAX_SHOTS = 40

SENTENCE_ID = re.compile(r"s_[0-9a-f]{8}")

class TokenCount(BaseModel):
    per_clip: dict[str, int]
    total: int
    limit: int = TOKEN_LIMIT


class RefLine(BaseModel):
    clip_id: str
    line: int
    start: float
    end: float
    text: str


class Window(BaseModel):
    """Where a sentence's Shots come from: ±30 s around the lines it cites in one clip."""

    clip_id: str
    start: float
    end: float


class SentenceView(Sentence):
    status: Status
    estimated_s: float | None  # None only when the draft's voice is gone
    ref_lines: list[RefLine]
    window: Window | None


class DraftView(Draft):
    """`GET /draft`: the file plus what is worked out on reading (spec › API)."""

    sentences: list[SentenceView]
    estimated_total_s: float
    locked: bool


class DraftJobError(BaseModel):
    code: ErrorCode
    message: str


class DraftJob(BaseModel):
    """Every spoil-maker job has these fields; the ones a kind doesn't use stay null (spec › API)."""

    kind: Literal["draft", "pick"]
    state: State
    clip_id: None = None
    percent: None = None
    done: int | None = None
    total: int | None = None
    error: DraftJobError | None = None
    cancel_requested: bool = False
    started_at: str


class _CheckedOrder(BaseModel):
    """A `kind: "draft"` request that passed every check, with the files its thread reads."""

    brief: Brief
    voice_id: str
    shots: dict[str, ShotsFile]


class DraftJobs(ModelJobSlot[DraftJob]):
    """Holds the latest Draft job: a whole new draft (`draft`), or new Shots for one sentence (`pick`)."""

    unfinished = UNFINISHED
    gpu_kind = "draft"
    nothing_to_cancel = "ไม่มีงานร่างบทที่ยังไม่จบ"
    worker_error = WorkerError
    child_name = "ตัวร่างบท"
    failure = "ร่างบทไม่สำเร็จ"

    def __init__(self):
        super().__init__()
        self._model = None  # (process, requests, replies) of the running child

    def start(self, body: dict) -> DraftJob:
        if body.get("kind") == "draft":
            return self._start_draft(body)
        if body.get("kind") == "pick":
            return self._start_pick(body.get("sentence_id"))
        raise ApiError(400, "invalid_request", "ไม่รู้จักงานร่างบทแบบนี้")

    def _start_draft(self, body: dict) -> DraftJob:
        """Checks in spec order (Draft job step 1), then starts the thread. The draft's
        lock covers `draft_exists` and taking the GPU, so no edit slips between them (D51)."""
        project = ProjectPaths(paths.ROOT)
        clip_ids = _ready_clips(project, body.get("clip_ids"))
        style, layout, target_s = body.get("style"), body.get("layout"), body.get("target_s")
        if style not in script.STYLES or layout not in LAYOUTS:
            raise ApiError(400, "invalid_request", "เลือกสไตล์และ layout จากรายการ")
        if isinstance(target_s, bool) or not isinstance(target_s, int) or not TARGET_MIN <= target_s <= TARGET_MAX:
            raise ApiError(400, "invalid_target", f"ความยาวต้องเป็นวินาทีเต็ม {TARGET_MIN}–{TARGET_MAX}")
        voice_id = body.get("voice_id")
        chars_per_s = voices.chars_per_s(project, voice_id) if isinstance(voice_id, str) else None
        if chars_per_s is None:
            raise ApiError(400, "voice_not_found", "ไม่พบเสียงที่เลือก")
        transcripts = {clip_id: transcribe.read_transcript(project, clip_id) for clip_id in clip_ids}
        count = _count(project, clip_ids, transcripts)
        if count.total > TOKEN_LIMIT:
            raise ApiError(
                400, "transcript_too_long", f"Transcript รวม {count.total:,} token เกิน {TOKEN_LIMIT:,}", tokens=count.total
            )
        order = _CheckedOrder(
            brief=Brief(
                clip_ids=clip_ids,
                transcripts=transcripts,
                style=style,
                layout=layout,
                target_s=target_s,
                target_letters=round(target_s * chars_per_s),
            ),
            voice_id=voice_id,
            shots={clip_id: shots.read_shots(project, clip_id) for clip_id in clip_ids},
        )
        with self._lock:
            if self._taken():
                raise ApiError(409, "busy", "กำลังร่างบทอยู่")
            with gpu.slot.draft_lock:
                if body.get("replace") is not True and draft_file.read(project) is not None:
                    raise ApiError(409, "draft_exists", "มี Spoil draft อยู่แล้ว: ร่างใหม่จะทับของเดิม")
                require_rows(describe.needed_rows(project))
                gpu.slot.take("draft", clip_ids, draft=True)
            self._job = DraftJob(kind="draft", state="writing", started_at=checks.now_iso())
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(project, lambda: self._draft(project, order)), daemon=True).start()
        return job

    def _start_pick(self, sentence_id: object) -> DraftJob:
        """New Shots for one sentence from its text now (spec › Draft job, D25, D27)."""
        project = ProjectPaths(paths.ROOT)
        with self._lock:
            if self._taken():
                raise ApiError(409, "busy", "กำลังร่างบทอยู่")
            with gpu.slot.draft_lock:
                draft = _editable(project)
                sentence = _sentence(draft, sentence_id)
                if not sentence.refs:
                    raise ApiError(400, "no_refs", "ประโยคนี้ไม่ได้อ้างบรรทัดไหน: เลือกภาพเองจากทั้งคลิป")
                require_rows(describe.needed_rows(project))
                gpu.slot.take("draft", draft.clip_ids, draft=True)
            self._job = DraftJob(kind="pick", state="matching", done=0, total=1, started_at=checks.now_iso())
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        sentence_id = sentence.id
        threading.Thread(target=self._run, args=(project, lambda: self._pick(project, sentence_id)), daemon=True).start()
        return job

    def _run(self, project: ProjectPaths, steps) -> None:
        # Stays `failed` only if something escapes every handler below.
        ending: dict = {"state": "failed"}
        started = time.monotonic()
        kind = self.current().kind
        log.info("%s started", kind)
        try:
            steps()
            ending = {"state": "done"}
        except Cancelled:
            ending = {"state": "cancelled"}  # the draft is as it was: it is written only at the end
        except JobFailed as failure:
            ending = _failed(failure.code, failure.message)
        except Exception as error:
            log.exception("%s failed", kind)  # the full error, for [api]
            ending = _failed("internal", f"ร่างบทไม่สำเร็จ: {short(error)}")
        finally:
            process = self._model[0] if self._model else None
            self._model = None
            self._finish(process, ending)
            # No script in the log: only what happened and how long (spec › Ops).
            code = ending["error"].code if ending.get("error") else None
            log.info("%s ended %s %s after %.0f s", kind, ending["state"], code or "", time.monotonic() - started)

    def _draft(self, project: ProjectPaths, order: _CheckedOrder) -> None:
        """Steps 2–6: write the script, pick two Shots per sentence, replace the draft."""
        brief = order.brief
        written = None
        last: list[Sentence] | None = None  # the previous try's sentences, None when it gave no JSON
        for attempt in range(1, ATTEMPTS + 1):
            prompt = script.script_prompt(brief, last, asked_before=attempt > 1)
            last = None
            try:
                reply = self._ask(project, prompt, brief.max_tokens, WRITE_TEMPERATURE, WRITE_TIMEOUT_SECONDS)
            except TimeoutError:
                # One failed try of three (step 3); a stuck generation ends only with its
                # process, so the next ask starts a new one.
                log.warning("script attempt %d took longer than %d s", attempt, WRITE_TIMEOUT_SECONDS)
                self._stop_model()
                continue
            parsed = script.parse_script(reply, brief)
            if parsed is None:
                log.warning("script attempt %d is not the JSON asked for", attempt)
                continue
            written = parsed  # the latest that could be read, if none passes
            last = parsed[1]
            if script.near_target(parsed[1], brief.target_letters):
                break
            log.warning(
                "script attempt %d is %d letters, not about %d", attempt, script.letters(parsed[1]), brief.target_letters
            )
        if written is None:
            raise JobFailed("draft_failed", f"AI ร่างบทไม่สำเร็จ {ATTEMPTS} ครั้ง")
        top_text, sentences = written
        cited = [sentence for sentence in sentences if sentence.refs]
        self._update(state="matching", done=0, total=len(cited))
        for done, sentence in enumerate(cited, start=1):
            sentence.shots = self._shots_for(project, sentence, brief.transcripts, order.shots)
            self._update(done=done)
        draft = Draft(
            clip_ids=brief.clip_ids,
            style=brief.style,
            layout=brief.layout,
            target_s=brief.target_s,
            voice_id=order.voice_id,
            original_volume=settings.read(project).original_volume,  # D40
            top_text=top_text,
            sentences=sentences,
        )
        with gpu.slot.draft_lock:
            draft_file.write(project, draft)
            draft_file.remove_audio(project)  # the old draft's voice (D28)
        settings.remember(project, last_voice_id=order.voice_id)

    def _pick(self, project: ProjectPaths, sentence_id: str) -> None:
        """Step 5 for one sentence, then only its `shots` change. The draft is locked
        meanwhile, so the sentence is still there and the same."""
        with gpu.slot.draft_lock:
            draft = draft_file.read(project)
        sentence = _sentence(draft, sentence_id)
        transcripts, shot_files = _clip_files(project, draft.clip_ids)
        picked = self._shots_for(project, sentence, transcripts, shot_files)
        self._update(done=1)
        with gpu.slot.draft_lock:
            draft = draft_file.read(project)
            _sentence(draft, sentence_id).shots = picked
            draft_file.write(project, draft)

    def _shots_for(self, project, sentence: Sentence, transcripts, shot_files) -> list[ShotRef | None]:
        """Two Shots from the window around the lines the sentence cites (Draft job step 5)."""
        window = _window(sentence.refs, transcripts)
        found = shot_files.get(window.clip_id) if window else None
        candidates = [shot for shot in found.shots if shot.end > window.start and shot.start < window.end] if found else []
        if not candidates:
            return [None, None]
        if len(candidates) == 1:
            picked = [candidates[0].n] * 2
        else:
            transcript = transcripts[window.clip_id]
            first = transcript.lines[sentence.refs[0].line]
            # Lines far apart make a window of most of the film: ask about the Shots nearest the first.
            asked = script.closest(candidates, first.start_s, PICK_MAX_SHOTS)
            prompt = script.pick_prompt(sentence, transcript, asked)
            try:
                reply = self._ask(project, prompt, PICK_MAX_TOKENS, PICK_TEMPERATURE, PICK_TIMEOUT_SECONDS)
            except TimeoutError:
                # Unlike the script, a stuck pick ends the job (spec › ค่าการสร้างข้อความ).
                raise JobFailed("model_failed", f"เลือกภาพเกิน {PICK_TIMEOUT_SECONDS} วินาที. {gpu.ADVICE}") from None
            picked = script.parse_pick(reply, asked) or script.nearest(asked, first.start_s)
        return [ShotRef(clip_id=window.clip_id, n=n) for n in picked]

    def _ask(self, project: ProjectPaths, prompt: str, max_tokens: int, temperature: float, timeout: float) -> str:
        """One answer from Qwen, starting its child first if none runs. Raises
        `TimeoutError` after `timeout` seconds, `Cancelled`, or `JobFailed`."""
        if self._model is None:
            process, requests, replies = spoil_maker.start_worker(project.snapshot_dir(QWEN, QWEN.revision))
            self._model = (process, requests, replies)
            self._track(process)
            self._reply(process, replies, (Ready,))  # loading has no timeout
        process, requests, replies = self._model
        requests.put(Generate(prompt, None, max_tokens, temperature))
        return self._reply(process, replies, (Generated,), timeout).text

    def _stop_model(self) -> None:
        process = self._model[0]
        self._model = None
        self._track(None)
        stop_process(process)


def uses_clip(clip_id: str) -> bool:
    """Whether a Draft job reads that clip's Transcript: its lines can't be edited (D54)."""
    return gpu.slot.reads_clip("draft", clip_id)


transcribe.clip_users.append(uses_clip)


# --- The token count (D46) ---


def tokens(project: ProjectPaths, clip_ids: str) -> TokenCount:
    """`GET /tokens?clip_ids=a,b`: each Transcript as the Draft job sends it, in this order."""
    ordered = [clip_id.strip() for clip_id in clip_ids.split(",") if clip_id.strip()]
    if not ordered or len(set(ordered)) < len(ordered):
        raise ApiError(400, "clip_not_ready", "เลือกคลิปที่ไม่ซ้ำกันอย่างน้อยหนึ่งคลิป", clip_ids=ordered)
    not_ready = [clip_id for clip_id in ordered if not _transcribed(project, clip_id)]
    if not_ready:
        raise ApiError(400, "clip_not_ready", "คลิปนี้ยังไม่ได้ถอดบทพูด", clip_ids=not_ready)
    transcripts = {clip_id: transcribe.read_transcript(project, clip_id) for clip_id in ordered}
    return _count(project, ordered, transcripts)


def _count(project: ProjectPaths, clip_ids: list[str], transcripts: dict[str, Transcript]) -> TokenCount:
    """Needs Qwen's tokenizer: `503` `not_ready` without it (D60)."""
    require_rows({QWEN.check_id: describe.needed_rows(project)[QWEN.check_id]})
    snapshot = project.snapshot_dir(QWEN, QWEN.revision)
    try:
        per_clip = {
            clip_id: spoil_maker.count_tokens(snapshot, script.transcript_block(ep, transcripts[clip_id]))
            for ep, clip_id in enumerate(clip_ids, start=1)
        }
    except FileNotFoundError:
        # A marker without its snapshot: the install is broken the same way.
        raise ApiError(503, "not_ready", f"ยังติดตั้งไม่ครบ: {QWEN.label}", rows=[QWEN.check_id]) from None
    return TokenCount(per_clip=per_clip, total=sum(per_clip.values()))


# --- Reading and changing the draft ---


def view(project: ProjectPaths) -> DraftView | None:
    """`GET /draft`: the draft with each sentence's status, estimate, cited lines and window."""
    with gpu.slot.draft_lock:
        draft = draft_file.read(project)
    if draft is None:
        return None
    transcripts, _ = _clip_files(project, draft.clip_ids, with_shots=False)
    chars_per_s = voices.chars_per_s(project, draft.voice_id)
    sentences = [_sentence_view(draft, sentence, transcripts, chars_per_s) for sentence in draft.sentences]
    return DraftView(
        **draft.model_dump(exclude={"sentences"}),
        sentences=sentences,
        estimated_total_s=round(sum(sentence.estimated_s or 0 for sentence in sentences), 2),
        locked=gpu.slot.holds_draft(),
    )


def change_draft(project: ProjectPaths, body: dict) -> DraftView:
    """`PATCH /draft`: `top_text`, `layout`, `voice_id`, `original_volume`, each optional.
    A new voice makes every voiced sentence `stale_audio`; the volume is remembered too (D40)."""
    fields = {}
    if "top_text" in body:
        fields["top_text"] = _top_text(body["top_text"])
    if "layout" in body:
        if body["layout"] not in LAYOUTS:
            raise ApiError(400, "invalid_request", "layout ต้องเป็น A, B หรือ C")
        fields["layout"] = body["layout"]
    if "original_volume" in body:
        if not settings.is_volume(body["original_volume"]):
            raise ApiError(400, "invalid_request", "เสียงต้นฉบับต้องเป็น 0–100 ทีละ 5")
        fields["original_volume"] = body["original_volume"]
    with gpu.slot.draft_lock:
        if "voice_id" in body:
            if not isinstance(body["voice_id"], str) or voices.chars_per_s(project, body["voice_id"]) is None:
                raise ApiError(400, "voice_not_found", "ไม่พบเสียงที่เลือก")
            fields["voice_id"] = body["voice_id"]
        draft = _editable(project)
        draft_file.write(project, draft.model_copy(update=fields))
    if "original_volume" in fields:
        settings.remember(project, original_volume=fields["original_volume"])
    return view(project)


def insert_sentence(project: ProjectPaths, body: dict) -> DraftView:
    """`POST /draft/sentences`: a new sentence under `after_id`, or first when it is null;
    it cites no line and has no Shot (D27)."""
    text = _sentence_text(body.get("text"))
    after_id = body.get("after_id")
    with gpu.slot.draft_lock:
        draft = _editable(project)
        if after_id is None:
            index = 0
        else:
            index = next((i + 1 for i, sentence in enumerate(draft.sentences) if sentence.id == after_id), None)
            if index is None:
                raise ApiError(400, "invalid_request", "ไม่พบประโยคที่จะแทรกต่อ")
        taken = {sentence.id for sentence in draft.sentences}
        new = Sentence(id=script.new_sentence_id(taken), text=text, refs=[], shots=[None, None])
        draft.sentences.insert(index, new)
        draft_file.write(project, draft)
    return view(project)


def change_sentence(project: ProjectPaths, sentence_id: str, body: dict) -> DraftView:
    """`PATCH /draft/sentences/{sid}`: `text` and `shots`, each optional. New text keeps
    the wav, so the sentence reads `stale_audio` until it is voiced again (D30)."""
    with gpu.slot.draft_lock:
        draft = _editable(project)
        sentence = _sentence(draft, sentence_id)
        if "text" in body:
            sentence.text = _sentence_text(body["text"])
        if "shots" in body:
            sentence.shots = _checked_shots(project, draft, body["shots"])
        draft_file.write(project, draft)
    return view(project)


def delete_sentence(project: ProjectPaths, sentence_id: str) -> DraftView:
    """Removes the sentence and its wav."""
    with gpu.slot.draft_lock:
        draft = _editable(project)
        sentence = _sentence(draft, sentence_id)
        draft.sentences.remove(sentence)
        draft_file.write(project, draft)
        (project.draft_audio_dir / f"{sentence.id}.wav").unlink(missing_ok=True)
    return view(project)


def _editable(project: ProjectPaths) -> Draft:
    """The draft, for a change. Call with the draft's lock held. Raises `ApiError`
    404 `no_draft`, or 409 `draft_locked` while a job changes it (D51)."""
    draft = draft_file.read(project)
    if draft is None:
        raise ApiError(404, "no_draft", "ยังไม่มี Spoil draft")
    if gpu.slot.holds_draft():
        raise ApiError(409, "draft_locked", "รอให้งานที่ใช้ Spoil draft เสร็จก่อนแล้วแก้")
    return draft


def _sentence(draft: Draft, sentence_id: object) -> Sentence:
    """Only a well-formed id is looked up. Raises `ApiError` 404 `not_found`."""
    if isinstance(sentence_id, str) and SENTENCE_ID.fullmatch(sentence_id):
        for sentence in draft.sentences:
            if sentence.id == sentence_id:
                return sentence
    raise ApiError(404, "not_found", "ไม่พบประโยคนี้")


def _sentence_text(text: object) -> str:
    """One line of text; empty once spaces are cut is refused."""
    text = " ".join(text.split()) if isinstance(text, str) else ""
    if not text:
        raise ApiError(400, "invalid_request", "ประโยคต้องมีข้อความ")
    return text


def _top_text(text: object) -> str:
    """Empty draws nothing (D19); up to 40 letters that take space."""
    if not isinstance(text, str):
        raise ApiError(400, "invalid_request", "ข้อความด้านบนต้องเป็นข้อความ")
    text = " ".join(text.split())
    if script.width(text) > script.TOP_TEXT_MAX:
        raise ApiError(400, "invalid_request", f"ข้อความด้านบนยาวได้ไม่เกิน {script.TOP_TEXT_MAX} ตัวอักษร")
    return text


def _checked_shots(project: ProjectPaths, draft: Draft, value: object) -> list[ShotRef | None]:
    """Two slots, each null or a Shot of a clip in the draft. Raises `ApiError` 400 `invalid_shot`."""
    invalid = ApiError(400, "invalid_shot", "เลือกภาพจาก Shot ของคลิปใน Spoil draft")
    if not isinstance(value, list) or len(value) != 2:
        raise invalid
    checked: list[ShotRef | None] = []
    for slot in value:
        if slot is None:
            checked.append(None)
            continue
        if not isinstance(slot, dict) or slot.get("clip_id") not in draft.clip_ids:
            raise invalid
        n = slot.get("n")
        found = shots.read_shots(project, slot["clip_id"])
        if isinstance(n, bool) or not isinstance(n, int) or found is None or not 0 <= n < len(found.shots):
            raise invalid
        checked.append(ShotRef(clip_id=slot["clip_id"], n=n))
    return checked


def _sentence_view(draft: Draft, sentence: Sentence, transcripts, chars_per_s: float | None) -> SentenceView:
    status = _status(draft, sentence)
    if status == "ready":
        estimated = sentence.audio.duration_s
    elif chars_per_s:
        estimated = round(thai.letters(thai.spoken(sentence.text)) / chars_per_s, 2)
    else:
        estimated = None
    ref_lines = []
    for ref in sentence.refs:
        transcript = transcripts.get(ref.clip_id)
        if transcript and 0 <= ref.line < len(transcript.lines):
            line = transcript.lines[ref.line]
            ref_lines.append(RefLine(clip_id=ref.clip_id, line=ref.line, start=line.start_s, end=line.end_s, text=line.text))
    return SentenceView(
        **sentence.model_dump(),
        status=status,
        estimated_s=estimated,
        ref_lines=ref_lines,
        window=_window(sentence.refs, transcripts),
    )


def _status(draft: Draft, sentence: Sentence) -> Status:
    """In the table's order: a sentence with neither Shot nor voice is `no_shot` (D30)."""
    if None in sentence.shots:
        return "no_shot"
    if sentence.audio is None:
        return "no_audio"
    if sentence.audio.tts_text != thai.spoken(sentence.text) or sentence.audio.voice_id != draft.voice_id:
        return "stale_audio"
    return "ready"


def _window(refs: list[Ref], transcripts: dict[str, Transcript | None]) -> Window | None:
    """±30 s around the cited lines of the first ref's clip only (D51); None without refs."""
    if not refs or transcripts.get(refs[0].clip_id) is None:
        return None
    clip_id = refs[0].clip_id
    lines = transcripts[clip_id].lines
    cited = [lines[ref.line] for ref in refs if ref.clip_id == clip_id and 0 <= ref.line < len(lines)]
    if not cited:
        return None
    start = max(0.0, min(line.start_s for line in cited) - WINDOW_SECONDS)
    return Window(clip_id=clip_id, start=start, end=max(line.end_s for line in cited) + WINDOW_SECONDS)


def _clip_files(project: ProjectPaths, clip_ids: list[str], with_shots: bool = True):
    """Each clip's Transcript and Shots; one that can't be read is None."""
    transcripts: dict[str, Transcript | None] = {}
    for clip_id in clip_ids:
        try:
            transcripts[clip_id] = transcribe.read_transcript(project, clip_id)
        except ApiError:
            transcripts[clip_id] = None
    shot_files = {clip_id: shots.read_shots(project, clip_id) for clip_id in clip_ids} if with_shots else {}
    return transcripts, shot_files


def _ready_clips(project: ProjectPaths, value: object) -> list[str]:
    """Step 1.1: not empty, no repeats, each transcribed and described. Raises
    `ApiError` 400 `clip_not_ready` with the ids that aren't (D5, D16)."""
    if not isinstance(value, list) or not value or not all(isinstance(clip_id, str) for clip_id in value):
        raise ApiError(400, "clip_not_ready", "เลือกคลิปอย่างน้อยหนึ่งคลิป", clip_ids=[])
    repeated = sorted({clip_id for clip_id in value if value.count(clip_id) > 1})
    if repeated:
        raise ApiError(400, "clip_not_ready", "เลือกคลิปซ้ำกัน", clip_ids=repeated)
    not_ready = [c for c in value if not _transcribed(project, c) or not shots.is_described(project, c)]
    if not_ready:
        raise ApiError(400, "clip_not_ready", "คลิปนี้ยังไม่ได้ถอดบทพูดหรือบรรยายฉาก", clip_ids=not_ready)
    return list(value)


def _transcribed(project: ProjectPaths, clip_id: str) -> bool:
    try:
        transcribe.read_transcript(project, clip_id)
    except ApiError:
        return False
    return True


def _failed(code: ErrorCode, message: str) -> dict:
    return {"state": "failed", "error": DraftJobError(code=code, message=message)}


draft_jobs = DraftJobs()
