"""What the Draft job asks Qwen and how it reads the answers: the prompts, the JSON
in a reply, and the cleaning of a script (spoil-maker spec › Draft job steps 2–5,
D11, D18, D19). Plain functions, no job and no file.
"""

import json
import re
import secrets
from collections.abc import Sequence

from pydantic import BaseModel

from backend import clock
from backend.spoil.transcribe import Transcript, TranscriptLine
from backend.spoil_maker import thai
from backend.spoil_maker.draft_file import Layout, Ref, Sentence, Style
from backend.spoil_maker.shots import Shot

# How each style tells the story, and the layout it starts with (D7, D8).
STYLES: dict[Style, tuple[str, Layout]] = {
    "fast": ("Short, funny, fast sentences that tell the standout events.", "A"),
    "drama": ("A hook, the story, the twist, the motives, and a question at the end that invites comments.", "B"),
    "chrono": ("Scene by scene in time order; characters' lines may be quoted.", "C"),
}
TOP_TEXTS: dict[Layout, str] = {  # what the text on top of layouts A and C is (D19); B has none
    "A": "a hook that makes people want to watch",
    "C": "the episode's title",
}
SECONDS_PER_SENTENCE = 4
TOLERANCE = 0.25  # a script's letters within ±25% of the target pass (D18)
TOP_TEXT_MAX = 40  # letters that take space (spec › ข้อความบนวิดีโอ)

LINE_ID = re.compile(r"\d+")
# Han, Hiragana, Katakana and Hangul slip into Qwen's Thai (llm-trial › รอบ 2).
CJK = re.compile(
    "[ᄀ-ᇿ぀-ヿ㄰-㆏ㇰ-ㇿ㐀-䶿一-鿿"
    "가-힯豈-﫿ｦ-ﾟ\U00020000-\U0003134f]+"
)


NumberedLine = tuple[int, TranscriptLine]
"""A Transcript line with its index in the whole Transcript: what a ref cites (D70)."""


class Brief(BaseModel):
    """What a script is written from: the EP's lines (edited text included, D54) with
    their index in the clip's whole Transcript, and how to tell it."""

    clip_id: str
    lines: list[NumberedLine]
    style: Style
    layout: Layout
    target_s: int
    target_letters: int  # target_s × the Saved voice's speaking speed (D35)

    @property
    def max_tokens(self) -> int:
        """Room for every letter twice over, plus the JSON around them (spec › ค่าการสร้างข้อความ)."""
        return 2 * self.target_letters + 1000


def transcript_block(lines: Sequence[NumberedLine]) -> str:
    """`[{line} {hh:mm:ss}] {text}` per line, `line` its index in the whole Transcript
    (spec › Draft job step 2)."""
    return "".join(f"[{n} {clock.hms(line.start_s)}] {line.text}\n" for n, line in lines)


MAX_REFS = 3  # cited lines a sentence keeps (spec › Draft job step 2)
# Told "at most n letters a sentence", Qwen writes about 0.7–0.8 n (D61): this centres the total.
SENTENCE_ROOM = 1.2


def script_prompt(brief: Brief, last: list[Sentence] | None = None, asked_before: bool = False) -> str:
    """Step 2: the style, Thai only (D11), the target length, 1–3 cited lines per
    sentence, and `top_text` for layouts A and C (D19). Asked again (step 3), it says
    what was wrong with the `last` script, or that no JSON came back (D61)."""
    telling, _ = STYLES[brief.style]
    sentences = round(brief.target_s / SECONDS_PER_SENTENCE)
    top = TOP_TEXTS.get(brief.layout)
    top_rule = (
        f'"top_text" is {top}, in Thai, at most {TOP_TEXT_MAX} letters.' if top else '"top_text" is an empty string.'
    )
    rules = (
        f"How to tell it: {telling}\n"
        f"Write in Thai only: about {brief.target_letters} Thai letters in about {sentences} sentences, "
        f"each sentence at most {round(SENTENCE_ROOM * brief.target_letters / sentences)} Thai letters.\n"
        'Each sentence cites the 1 to 3 transcript lines it tells about by their ids, like "412"; '
        "never more than 3, never a run of lines.\n"
        f"{top_rule}\n"
        'Answer with JSON only: {"top_text": "...", "sentences": [{"text": "...", "refs": ["412"]}]}\n'
    )
    # The rules again after the Transcript: a whole film is ~30k tokens, and the model
    # follows best what it read last.
    return (
        "Write the narration script of a short vertical video that spoils the story in the transcript below.\n"
        f"{rules}\n"
        "Transcript, one line each as [line hh:mm:ss] text:\n"
        f"{transcript_block(brief.lines)}\n"
        f"Now write the script.\n{rules}"
        + (_retry_note(brief, last) if asked_before else "")
    )


def _retry_note(brief: Brief, last: list[Sentence] | None) -> str:
    if last is None:
        return "Your last answer was not complete JSON: write each sentence once, and stop when the story ends.\n"
    side = "long" if spoken_letters(last) > brief.target_letters else "short"
    return (
        f"Your last script was {spoken_letters(last)} letters in {len(last)} sentences: too {side}. "
        f"Write about {brief.target_letters} letters this time.\n"
    )


def pick_prompt(sentence: Sentence, transcript: Transcript, candidates: list[Shot]) -> str:
    """Step 5.3: the sentence, the lines it cites in `transcript`'s clip, and the Shots to pick from."""
    lines = transcript.lines
    cited = "".join(
        f"[{clock.hms(lines[ref.line].start_s)}] {lines[ref.line].text}\n"
        for ref in sentence.refs
        if ref.clip_id == transcript.clip_id
    )
    listed = "".join(f"{shot.n} [{clock.hms(shot.start)}-{clock.hms(shot.end)}] {shot.description}\n" for shot in candidates)
    return (
        "Pick the 2 shots that best show this Thai sentence of a narration.\n"
        f"Sentence: {sentence.text}\n"
        f"It tells about these transcript lines:\n{cited}\n"
        f"Shots, one each as number [start-end] description:\n{listed}\n"
        'Answer with JSON only: {"shots": [first number, second number]}'
    )


def parse_script(reply: str, brief: Brief) -> tuple[str, list[Sentence]] | None:
    """Steps 3–4: `top_text` and the sentences, cleaned; None when the reply isn't the
    JSON asked for. Han, kana and Hangul go, refs to lines that don't exist go, and
    sentences left empty go; `top_text` is cut to fit, and is empty in layout B."""
    found = _json_object(reply)
    if found is None or not isinstance(found.get("sentences"), list):
        return None
    sentences: list[Sentence] = []
    taken: set[str] = set()
    for item in found["sentences"]:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            continue
        text = _clean(item["text"])
        if text:
            refs = _refs(item.get("refs"), brief)
            sentences.append(Sentence(id=new_sentence_id(taken), text=text, refs=refs, shots=[None, None]))
    if not sentences:
        return None
    top_text = found.get("top_text")
    top_text = thai.cut_width(_clean(top_text), TOP_TEXT_MAX) if isinstance(top_text, str) and brief.layout != "B" else ""
    return top_text, sentences


def parse_pick(reply: str, candidates: list[Shot]) -> list[int] | None:
    """Two numbers of Shots among `candidates`, or None (step 5.4)."""
    found = _json_object(reply)
    numbers = found.get("shots") if found else None
    allowed = {shot.n for shot in candidates}
    if not isinstance(numbers, list) or len(numbers) != 2:
        return None
    if not all(isinstance(n, int) and not isinstance(n, bool) and n in allowed for n in numbers):
        return None
    return numbers


def nearest(candidates: list[Shot], at: float) -> list[int]:
    """The two Shots closest to `at`, the start of the first cited line, in clip order (step 5.4)."""
    return [shot.n for shot in closest(candidates, at, 2)]


def closest(candidates: list[Shot], at: float, count: int) -> list[Shot]:
    """The `count` Shots closest to `at`, in clip order; ties go to the one that starts first."""

    def distance(shot: Shot) -> float:
        return 0.0 if shot.start <= at < shot.end else min(abs(shot.start - at), abs(shot.end - at))

    found = sorted(candidates, key=lambda shot: (distance(shot), shot.start))[:count]
    return sorted(found, key=lambda shot: shot.n)


def near_target(sentences: list[Sentence], target_letters: int) -> bool:
    return abs(spoken_letters(sentences) - target_letters) <= TOLERANCE * target_letters


def spoken_letters(sentences: list[Sentence]) -> int:
    """After numbers become words, the way speaking speed was measured (D35, D36)."""
    return sum(thai.letters(thai.spoken(sentence.text)) for sentence in sentences)


def new_sentence_id(taken: set[str]) -> str:
    """`s_` and 8 hex digits, none of `taken`, which it joins."""
    while (sentence_id := f"s_{secrets.token_hex(4)}") in taken:
        pass
    taken.add(sentence_id)
    return sentence_id


def _json_object(reply: str) -> dict | None:
    """The JSON object in a reply, inside a code fence or not; one that is short of
    only its last "}" is read too (D61)."""
    start, end = reply.find("{"), reply.rfind("}")
    if start < 0 or end < start:
        return None
    body = reply[start:].rstrip().removesuffix("```").rstrip()
    for text in (reply[start : end + 1], body + "}"):
        try:
            found = json.loads(text)
        except json.JSONDecodeError:
            continue
        return found if isinstance(found, dict) else None
    return None


def _refs(value: object, brief: Brief) -> list[Ref]:
    """Ids of the EP's lines, in order, once each, the first `MAX_REFS`: a line outside
    the EP or not in the Transcript goes (D61, D70)."""
    in_ep = {n for n, _ in brief.lines}
    refs: list[Ref] = []
    for item in value if isinstance(value, list) else []:
        if len(refs) == MAX_REFS:
            break
        text = item.strip() if isinstance(item, str) else ""
        if not LINE_ID.fullmatch(text) or int(text) not in in_ep:
            continue
        ref = Ref(clip_id=brief.clip_id, line=int(text))
        if ref not in refs:
            refs.append(ref)
    return refs


def _clean(text: str) -> str:
    return " ".join(CJK.sub("", text).split())
