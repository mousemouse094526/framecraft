"""The Spoil draft as the API shows and changes it, and the Draft job: one at a time,
a backend thread that owns the state and the file, and a child process that runs Qwen
(ADR 0010, ADR 0012, ADR 0015). A draft is of one EP of one Temp clip (D66, D67).

Steps and rules are in docs/features/spoil-maker/spec.md › Spoil draft and › Draft
job (D4, D7, D8, D18, D19, D25–D28, D39, D46, D51, D70–D76).
"""

import logging
import re
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend import checks, gate_rows, gpu, paths, spoil_maker, stories
from backend.errors import ApiError, JobFailed, require_rows
from backend.jobs import ModelJobSlot
from backend.models import qwen_for
from backend.paths import ProjectPaths
from backend.spoil import clips, transcribe
from backend.spoil.transcribe import Transcript
from backend.spoil_maker import draft_file, episodes, script, settings, shots, thai, voices
from backend.spoil_maker.draft_file import Draft, Ep, Layout, Ref, Sentence, ShotRef, Style
from backend.json_values import is_int
from backend.spoil_maker.llm import Generate, Generated, Ready, Timeouts, WorkerError, timeouts
from backend.spoil_maker.script import Brief
from backend.spoil_maker.shots import ShotsFile
from backend.workers import Worker

log = logging.getLogger(__name__)

State = Literal["writing", "polishing", "matching", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"writing", "polishing", "matching"})
ErrorCode = Literal["draft_failed", "polish_failed", "crashed", "model_failed", "internal"]
Status = Literal["no_shot", "no_audio", "stale_audio", "ready"]

LAYOUTS: tuple[Layout, ...] = ("A", "B", "C")
TARGET_MIN, TARGET_MAX = 30, 180  # D39
ATTEMPTS = 3
WINDOW_SECONDS = 30  # Shots this far around the lines a sentence cites (D18, D26)

# spec › ค่าการสร้างข้อความ; thinking is off for every step (`llm.generate`, `llm_windows.generate`), and each
# step's timeout is this OS's (`llm.TIMEOUTS`, windows-launch D7).
WRITE_TEMPERATURE = 0.3  # D61: 0.5 and 0.7 swing ±40% in length, 0.1 can run on
POLISH_ATTEMPTS = 2
POLISH_TEMPERATURE = 0.3
PICK_TEMPERATURE = 0.0
PICK_MAX_TOKENS = 64
# A pick reads about 0.4 s a Shot on an M2: 40 is 17 s, a 96-minute film's 840 are minutes (D61).
PICK_MAX_SHOTS = 40

SENTENCE_ID = re.compile(r"s_[0-9a-f]{8}")


class RefLine(BaseModel):
    clip_id: str
    line: int
    start: float
    end: float
    text: str


class Window(BaseModel):
    """Where a sentence's Shots come from: ±30 s around the lines it cites, inside the EP (D70)."""

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
    clip_title: str  # for the step bar (D68)
    estimated_total_s: float
    locked: bool


class DraftJobError(BaseModel):
    code: ErrorCode
    message: str


class DraftOrder(BaseModel):
    """What a `kind: "draft"` job was asked for, so a page opened later shows it (D82)."""

    clip_id: str
    clip_title: str
    ep: Ep
    style: Style
    layout: Layout
    target_s: int
    voice_id: str
    story_id: str | None  # the Story the job uses, None for "ไม่ใช้" (story-kb D15)
    story_title: str | None  # its title as the job started


class DraftJob(BaseModel):
    """Every spoil-maker job has these fields; the ones a kind doesn't use stay null (spec › API)."""

    kind: Literal["draft", "pick", "polish"]
    state: State
    clip_id: None = None  # every job reads the same shape; this one is of no single clip
    percent: None = None
    # While `matching`: sentences whose Shots are picked of those to pick. A finished `polish`:
    # sentences whose text changed of those asked to polish (spec › API).
    done: int | None = None
    total: int | None = None
    error: DraftJobError | None = None
    cancel_requested: bool = False
    started_at: str
    order: DraftOrder | None = None  # `kind: "draft"` only, kept after it ends (D82)


class _CheckedOrder(BaseModel):
    """A `kind: "draft"` request that passed every check, with the files its thread reads."""

    brief: Brief
    ep: Ep
    voice_id: str
    transcript: Transcript
    shots: ShotsFile


class DraftJobs(ModelJobSlot[DraftJob]):
    """Holds the latest Draft job: a whole new draft (`draft`), new Shots for one sentence
    (`pick`), or the draft's text polished again (`polish`)."""

    unfinished = UNFINISHED
    gpu_kind = "draft"
    nothing_to_cancel = "ไม่มีงานร่างบทที่ยังไม่จบ"
    worker_error = WorkerError
    child_name = "ตัวร่างบท"
    failure = "ร่างบทไม่สำเร็จ"
    error_type = DraftJobError

    def __init__(self):
        super().__init__()
        self._model: Worker | None = None  # the running child
        self._timeouts: Timeouts = timeouts()  # replaced by this OS's table as each job starts (`_run`)

    def start(self, body: dict) -> DraftJob:
        if body.get("kind") == "draft":
            return self._start_draft(body)
        if body.get("kind") == "pick":
            return self._start_pick(body.get("sentence_id"))
        if body.get("kind") == "polish":
            return self._start_polish(body)
        raise ApiError(400, "invalid_request", "ไม่รู้จักงานร่างบทแบบนี้")

    def _start_draft(self, body: dict) -> DraftJob:
        """Checks in spec order (Draft job step 1), then starts the thread. The draft's
        lock covers `draft_exists` and taking the GPU, so no edit slips between them (D51)."""
        project = paths.project()
        clip_id, transcript, ep = episodes.asked_ep(project, body.get("clip_id"), body.get("ep"))
        lines = episodes.lines_of(transcript, ep)
        if not lines:
            raise ApiError(400, "ep_empty", "EP นี้ไม่มีบทพูด")
        style, layout, target_s = body.get("style"), body.get("layout"), body.get("target_s")
        if style not in script.STYLES or layout not in LAYOUTS:
            raise ApiError(400, "invalid_request", "เลือกสไตล์และ layout จากรายการ")
        if not is_int(target_s) or not TARGET_MIN <= target_s <= TARGET_MAX:
            raise ApiError(400, "invalid_target", f"ความยาวต้องเป็นวินาทีเต็ม {TARGET_MIN}–{TARGET_MAX}")
        voice_id = body.get("voice_id")
        chars_per_s = voices.chars_per_s(project, voice_id) if isinstance(voice_id, str) else None
        if chars_per_s is None:
            raise ApiError(400, "voice_not_found", "ไม่พบเสียงที่เลือก")
        # After the Saved voice (step 1.4): the Story, read once for the whole job (story-kb D5).
        story = stories.for_draft(project, body.get("story_id"))
        counted = episodes.tokens(project, lines)
        story_tokens = stories.block_tokens(project, story)
        if counted + story_tokens > episodes.TOKEN_LIMIT:
            raise _too_long(counted, story_tokens)
        order = _CheckedOrder(
            brief=Brief(
                clip_id=clip_id,
                lines=lines,
                style=style,
                layout=layout,
                target_s=target_s,
                target_letters=round(target_s * chars_per_s),
                story=story,
            ),
            ep=Ep(n=ep.n, start_s=ep.start_s, end_s=ep.end_s),
            voice_id=voice_id,
            transcript=transcript,
            shots=shots.read_shots(project, clip_id),
        )
        # Read before the GPU is taken: nothing below may raise without releasing it (ADR-0015).
        asked = DraftOrder(
            clip_id=clip_id,
            clip_title=clips.read_clip(project, clip_id).title,
            ep=order.ep,
            style=style,
            layout=layout,
            target_s=target_s,
            voice_id=voice_id,
            story_id=story.id if story else None,
            story_title=story.title if story else None,
        )
        with self._lock:
            if self._taken():
                raise ApiError(409, "busy", "กำลังร่างบทอยู่")
            with gpu.slot.draft_lock:
                if body.get("replace") is not True and draft_file.read(project) is not None:
                    raise ApiError(409, "draft_exists", "มี Spoil draft อยู่แล้ว: ร่างใหม่จะทับของเดิม")
                # Under the draft's lock no voice is deleted: one may have been since the check above (D87).
                if voices.chars_per_s(project, voice_id) is None:
                    raise ApiError(400, "voice_not_found", "ไม่พบเสียงที่เลือก")
                require_rows(gate_rows.qwen_jobs(project))
                gpu.slot.take("draft", [clip_id], locks_draft=True)
                # Holding the GPU for the clip, no `PUT` can change its cut now; one may have
                # between the check above and here (D71).
                now = episodes.span(project, clip_id, order.ep.n)
                if now is None or not order.ep.matches(now.start_s, now.end_s):
                    gpu.slot.release("draft")
                    raise episodes.episodes_changed()
                # Every check passed and the GPU is the job's: only now does the clip remember
                # its Story (story-kb D15). One deleted since the check above is `story_not_found`;
                # a failed write raises too, and neither may keep the GPU (ADR-0015).
                try:
                    stories.set_clip_story(project, clip_id, asked.story_id)
                except Exception:
                    gpu.slot.release("draft")
                    raise
                # Set under the draft's lock, so a voice delete waiting on it sees the job (D87).
                self._job = DraftJob(kind="draft", state="writing", started_at=checks.now_iso(), order=asked)
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(lambda: self._draft(project, order),), daemon=True).start()
        return job

    def uses_voice(self, voice_id: str) -> bool:
        """Whether an unfinished job will write a draft with that voice (D87). Reads the job
        without the slot's lock (one attribute read), so a voice delete can ask under the
        draft's lock, where a starting job sets it, without breaking the lock order."""
        job = self._job
        return job is not None and job.state in UNFINISHED and job.order is not None and job.order.voice_id == voice_id

    def _start_pick(self, sentence_id: object) -> DraftJob:
        """New Shots for one sentence from its text now (spec › Draft job, D25, D27)."""
        project = paths.project()
        with self._lock:
            if self._taken():
                raise ApiError(409, "busy", "กำลังร่างบทอยู่")
            with gpu.slot.draft_lock:
                draft = _editable(project)
                sentence = _sentence(draft, sentence_id)
                if not sentence.refs:
                    raise ApiError(400, "no_refs", "ประโยคนี้ไม่ได้อ้างบรรทัดไหน: เลือกภาพเองจากทั้งคลิป")
                require_rows(gate_rows.qwen_jobs(project))
                gpu.slot.take("draft", [draft.clip_id], locks_draft=True)
            self._job = DraftJob(kind="pick", state="matching", done=0, total=1, started_at=checks.now_iso())
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        sentence_id = sentence.id
        threading.Thread(target=self._run, args=(lambda: self._pick(project, sentence_id),), daemon=True).start()
        return job

    def _start_polish(self, body: dict) -> DraftJob:
        """Checks in spec order under the draft's lock (spec › เรียบเรียงใหม่, D75), then
        takes the GPU for the draft's clip: its lines can't be edited meanwhile (D54)."""
        project = paths.project()
        with self._lock:
            if self._taken():
                raise ApiError(409, "busy", "กำลังร่างบทอยู่")
            with gpu.slot.draft_lock:
                draft = draft_file.read(project)
                if draft is None:
                    raise ApiError(404, "no_draft", "ยังไม่มี Spoil draft")
                include_edited = body.get("include_edited", False)
                if not isinstance(include_edited, bool):
                    raise ApiError(400, "invalid_request", "include_edited ต้องเป็น true หรือ false")
                asked = _to_polish(draft, include_edited)
                if not asked:
                    raise ApiError(400, "nothing_to_polish", "ทุกประโยคแก้เองแล้ว ไม่มีอะไรให้เรียบเรียง")
                require_rows(gate_rows.qwen_jobs(project))
                _editable(project)  # `draft_locked`
                # The Story the clip remembers now, read once as the request is taken (story-kb D5, ADR 0024).
                story = stories.read_clip_story(project, draft.clip_id)
                gpu.slot.take("draft", [draft.clip_id], locks_draft=True)
            self._job = DraftJob(kind="polish", state="polishing", started_at=checks.now_iso())
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(
            target=self._run, args=(lambda: self._polish_draft(project, include_edited, story),), daemon=True
        ).start()
        return job

    def _run(self, steps) -> None:
        """A cancelled or failed job leaves the draft as it was: it is written only at the end.
        No script in the log (spec › Ops)."""

        def clean_up(state: str) -> None:
            self._model = None  # `_finish` stops its process

        self._timeouts = timeouts()
        self._run_job(self.current().kind, steps, clean_up)

    def _draft(self, project: ProjectPaths, order: _CheckedOrder) -> None:
        """Steps 2–7: write the script, pick two Shots per sentence, replace the draft."""
        brief = order.brief
        written = None
        last: list[Sentence] | None = None  # the previous try's sentences, None when it gave no JSON
        for attempt in range(1, ATTEMPTS + 1):
            prompt = script.script_prompt(brief, last, asked_before=attempt > 1)
            last = None
            try:
                reply = self._ask(project, prompt, brief.max_tokens, WRITE_TEMPERATURE, self._timeouts.write)
            except TimeoutError:
                # One failed try of three (step 3); a stuck generation ends only with its
                # process, so the next ask starts a new one.
                log.warning("script attempt %d took longer than %g s", attempt, self._timeouts.write)
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
                "script attempt %d is %d letters, not about %d", attempt, script.spoken_letters(parsed[1]), brief.target_letters
            )
        if written is None:
            raise JobFailed("draft_failed", f"AI ร่างบทไม่สำเร็จ {ATTEMPTS} ครั้ง")
        top_text, sentences = written
        self.update(state="polishing")
        polished = self._ask_to_polish(
            project,
            brief.style,
            top_text,
            sentences,
            order.transcript,
            set(range(len(sentences))),
            lambda after: script.near_target(after, brief.target_letters),
            brief.story,
        )
        if polished is None:
            # Not the job's failure: a draft that reads less smoothly is still a draft (spec › เรียบเรียง).
            log.warning("polish_failed after %d attempts: the script stays as written", POLISH_ATTEMPTS)
        else:
            sentences = polished
        cited = [sentence for sentence in sentences if sentence.refs]
        self.update(state="matching", done=0, total=len(cited))
        for done, sentence in enumerate(cited, start=1):
            sentence.shots = self._shots_for(project, sentence, order.ep, order.transcript, order.shots)
            self.update(done=done)
        draft = Draft(
            clip_id=brief.clip_id,
            ep=order.ep,
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
        transcript = _transcript(project, draft.clip_id)
        picked = self._shots_for(project, sentence, draft.ep, transcript, shots.read_shots(project, draft.clip_id))
        self.update(done=1)
        with gpu.slot.draft_lock:
            draft = draft_file.read(project)
            _sentence(draft, sentence_id).shots = picked
            draft_file.write(project, draft)

    def _polish_draft(self, project: ProjectPaths, include_edited: bool, story: stories.Story | None) -> dict:
        """`kind: "polish"`: asks Qwen, then writes the draft. Only the text of the sentences that change is written, and a
        sentence `include_edited` let change is no longer `edited` (D75). The draft is locked
        meanwhile, so it is the one the checks read."""
        with gpu.slot.draft_lock:
            draft = draft_file.read(project)
        asked = _to_polish(draft, include_edited)
        polished = self._ask_to_polish(
            project,
            draft.style,
            draft.top_text,
            draft.sentences,
            _transcript(project, draft.clip_id),
            asked,
            # Not `near_target`: the draft may have been edited far from its target since (spec › เรียบเรียง).
            lambda after: script.grew_little(after, draft.sentences),
            story,
        )
        if polished is None:
            # The user asked for this polish, so here it is the job's failure; inside `kind: "draft"` it is not.
            raise JobFailed("polish_failed", "AI เรียบเรียงไม่สำเร็จ บทเดิมไม่เปลี่ยน")
        changed = 0
        with gpu.slot.draft_lock:
            draft = draft_file.read(project)
            for sentence, after in zip(draft.sentences, polished, strict=True):
                if after.text != sentence.text:
                    sentence.text, sentence.edited = after.text, False
                    changed += 1
            draft_file.write(project, draft)
        return {"done": changed, "total": len(asked)}

    def _ask_to_polish(
        self,
        project: ProjectPaths,
        style: Style,
        top_text: str,
        sentences: list[Sentence],
        transcript: Transcript | None,
        asked: set[int],
        fits: Callable[[list[Sentence]], bool],
        story: stories.Story | None,
    ) -> list[Sentence] | None:
        """Asks Qwen; returns the sentences with the text it rewrote for those in `asked`
        (spec › เรียบเรียง), or None after `POLISH_ATTEMPTS` tries that `fits`, the check of
        the whole script's length, refused. Writes nothing. A timeout is a failed try: its process is stopped and the next ask starts one."""
        fixed = set(range(len(sentences))) - asked
        prompt = script.polish_prompt(style, top_text, sentences, transcript, fixed, story)
        max_tokens = script.polish_max_tokens(sentences)
        for attempt in range(1, POLISH_ATTEMPTS + 1):
            try:
                reply = self._ask(project, prompt, max_tokens, POLISH_TEMPERATURE, self._timeouts.polish)
            except TimeoutError:
                log.warning("polish attempt %d took longer than %g s", attempt, self._timeouts.polish)
                self._stop_model()
                continue
            texts = script.parse_polish(reply, sentences, asked)
            if texts is None:
                log.warning("polish attempt %d is not the JSON asked for, or answers under half", attempt)
                continue
            after = [sentence.model_copy(update={"text": texts.get(i, sentence.text)}) for i, sentence in enumerate(sentences)]
            if fits(after):
                return after
            log.warning("polish attempt %d is %d letters, out of bounds", attempt, script.spoken_letters(after))
        return None

    def _shots_for(
        self, project, sentence: Sentence, ep: Ep, transcript: Transcript | None, found: ShotsFile | None
    ) -> list[ShotRef | None]:
        """Two Shots from the window around the lines the sentence cites (Draft job step 6)."""
        window = _window(sentence.refs, transcript, ep)
        candidates = [shot for shot in found.shots if shot.end > window.start and shot.start < window.end] if window and found else []
        if not candidates:
            return [None, None]
        if len(candidates) == 1:
            picked = [candidates[0].n] * 2  # a sentence shows two Shots: the only one fills both
        else:
            first = transcript.lines[sentence.refs[0].line]
            # Lines far apart make a window of most of the film: ask about the Shots nearest the first.
            asked = script.closest(candidates, first.start_s, PICK_MAX_SHOTS)
            prompt = script.pick_prompt(sentence, transcript, asked)
            try:
                reply = self._ask(project, prompt, PICK_MAX_TOKENS, PICK_TEMPERATURE, self._timeouts.pick)
            except TimeoutError:
                # Unlike the script, a stuck pick ends the job (spec › ค่าการสร้างข้อความ).
                raise JobFailed("model_failed", f"เลือกภาพเกิน {self._timeouts.pick:g} วินาที. {gpu.ADVICE}") from None
            picked = script.parse_pick(reply, asked) or script.nearest(asked, first.start_s)
        return [ShotRef(clip_id=window.clip_id, n=n) for n in picked]

    def _ask(self, project: ProjectPaths, prompt: str, max_tokens: int, temperature: float, timeout: float) -> str:
        """One answer from Qwen, starting its child first if none runs. Raises
        `TimeoutError` after `timeout` seconds, `Cancelled`, or `JobFailed`."""
        if self._model is None:
            qwen = qwen_for(checks.this_platform())
            worker = spoil_maker.start_worker(project.snapshot_dir(qwen, qwen.revision))
            self._model = self.start_child(worker, Ready)  # loading has no timeout
        return self.ask(self._model, Generate(prompt, None, max_tokens, temperature), (Generated,), timeout).text

    def _stop_model(self) -> None:
        self._model = None
        self.stop_child()


def _too_long(tokens: int, story_tokens: int) -> ApiError:
    """`transcript_too_long`: the EP's lines with the Story block over 32,000 (D46, story-kb D14)."""
    limit = episodes.TOKEN_LIMIT
    if not story_tokens:
        return ApiError(400, "transcript_too_long", f"Transcript ของ EP นี้ {tokens:,} token เกิน {limit:,}", tokens=tokens)
    total = tokens + story_tokens
    return ApiError(
        400,
        "transcript_too_long",
        f"EP กับเรื่องรวม {total:,} token เกิน {limit:,} (เรื่อง {story_tokens:,})",
        tokens=total,
        story_tokens=story_tokens,
    )


def job_reads_clip(clip_id: str) -> bool:
    """Whether a Draft job reads that clip's Transcript: its lines can't be edited (D54)."""
    return gpu.slot.reads_clip("draft", clip_id)


transcribe.clip_users.append(job_reads_clip)


voices.voice_users.append(lambda voice_id: draft_jobs.uses_voice(voice_id))


# --- Reading and changing the draft ---


def view(project: ProjectPaths) -> DraftView | None:
    """`GET /draft`: the draft with each sentence's status, estimate, cited lines and window."""
    with gpu.slot.draft_lock:
        draft = draft_file.read(project)
    if draft is None:
        return None
    transcript = _transcript(project, draft.clip_id)
    chars_per_s = voices.chars_per_s(project, draft.voice_id)
    sentences = [_sentence_view(draft, sentence, transcript, chars_per_s) for sentence in draft.sentences]
    return DraftView(
        **draft.model_dump(exclude={"sentences"}),
        sentences=sentences,
        clip_title=clips.read_clip(project, draft.clip_id).title,
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
        new = Sentence(id=script.new_sentence_id(taken), text=text, refs=[], shots=[None, None], edited=True)
        draft.sentences.insert(index, new)
        draft_file.write(project, draft)
    return view(project)


def change_sentence(project: ProjectPaths, sentence_id: str, body: dict) -> DraftView:
    """`PATCH /draft/sentences/{sid}`: `text` and `shots`, each optional. New text keeps
    the wav, so the sentence reads `stale_audio` until it is voiced again (D30), and
    makes it `edited`; the same text again does not (D74, D76)."""
    with gpu.slot.draft_lock:
        draft = _editable(project)
        sentence = _sentence(draft, sentence_id)
        if "text" in body:
            text = _sentence_text(body["text"])
            if text != sentence.text:
                sentence.text, sentence.edited = text, True
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


def sentence_audio(project: ProjectPaths, sentence_id: str) -> Path:
    """`GET /draft/sentences/{sid}/audio.wav`. Raises `ApiError` 404 `not_found` without one."""
    with gpu.slot.draft_lock:
        draft = draft_file.read(project)
        sentence = _sentence(draft, sentence_id) if draft else None
        path = project.draft_audio_dir / f"{sentence_id}.wav"
        if sentence is None or sentence.audio is None or not path.is_file():
            raise ApiError(404, "not_found", "ประโยคนี้ยังไม่มีเสียง")
        return path


def _to_polish(draft: Draft, include_edited: bool) -> set[int]:
    """The sentences to polish, by index: `edited` ones are fixed unless included (D74, D75)."""
    return {i for i, sentence in enumerate(draft.sentences) if include_edited or not sentence.edited}


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
    if thai.width(text) > script.TOP_TEXT_MAX:
        raise ApiError(400, "invalid_request", f"ข้อความด้านบนยาวได้ไม่เกิน {script.TOP_TEXT_MAX} ตัวอักษร")
    return text


def _checked_shots(project: ProjectPaths, draft: Draft, value: object) -> list[ShotRef | None]:
    """Two slots, each null or a Shot of the draft's clip inside its EP (D70). Raises
    `ApiError` 400 `invalid_shot`."""
    invalid = ApiError(400, "invalid_shot", "เลือกภาพจาก Shot ใน EP ของ Spoil draft")
    if not isinstance(value, list) or len(value) != 2:
        raise invalid
    found = shots.read_shots(project, draft.clip_id)
    checked: list[ShotRef | None] = []
    for slot in value:
        if slot is None:
            checked.append(None)
            continue
        if not isinstance(slot, dict) or slot.get("clip_id") != draft.clip_id:
            raise invalid
        n = slot.get("n")
        if not is_int(n) or found is None or not 0 <= n < len(found.shots):
            raise invalid
        if not draft.ep.overlaps(found.shots[n].start, found.shots[n].end):
            raise invalid
        checked.append(ShotRef(clip_id=draft.clip_id, n=n))
    return checked


def _sentence_view(draft: Draft, sentence: Sentence, transcript: Transcript | None, chars_per_s: float | None) -> SentenceView:
    status = status_of(draft, sentence)
    if status == "ready":
        estimated = sentence.audio.duration_s
    elif chars_per_s:
        estimated = round(thai.letters(thai.spoken(sentence.text)) / chars_per_s, 2)
    else:
        estimated = None
    ref_lines = []
    for ref in sentence.refs:
        if transcript and 0 <= ref.line < len(transcript.lines):
            line = transcript.lines[ref.line]
            ref_lines.append(RefLine(clip_id=ref.clip_id, line=ref.line, start=line.start_s, end=line.end_s, text=line.text))
    return SentenceView(
        **sentence.model_dump(),
        status=status,
        estimated_s=estimated,
        ref_lines=ref_lines,
        window=_window(sentence.refs, transcript, draft.ep),
    )


def status_of(draft: Draft, sentence: Sentence) -> Status:
    """In the table's order: a sentence with neither Shot nor voice is `no_shot` (D30)."""
    if None in sentence.shots:
        return "no_shot"
    if sentence.audio is None:
        return "no_audio"
    if sentence.audio.tts_text != thai.spoken(sentence.text) or sentence.audio.voice_id != draft.voice_id:
        return "stale_audio"
    return "ready"


def _window(refs: list[Ref], transcript: Transcript | None, ep: Ep) -> Window | None:
    """±30 s around the cited lines, cut to the EP (D26, D70); None without refs."""
    lines = transcript.lines if transcript else []
    cited = [lines[ref.line] for ref in refs if 0 <= ref.line < len(lines)]
    if not cited:
        return None
    start = max(ep.start_s, min(line.start_s for line in cited) - WINDOW_SECONDS)
    end = min(ep.end_s, max(line.end_s for line in cited) + WINDOW_SECONDS)
    return Window(clip_id=transcript.clip_id, start=start, end=end)


def _transcript(project: ProjectPaths, clip_id: str) -> Transcript | None:
    """None when it can't be read."""
    try:
        return transcribe.read_transcript(project, clip_id)
    except ApiError:
        return None


draft_jobs = DraftJobs()
