"""What every Qwen job does to a reply before reading it: the JSON object in it, and
Thai text without the Chinese, Japanese or Korean letters that slip in (spoil-maker
D18, D61; toon's writer reads replies the same way).
"""

import json
import re

# Han, Hiragana, Katakana and Hangul slip into Qwen's Thai (llm-trial › รอบ 2).
CJK = re.compile(
    "[ᄀ-ᇿ぀-ヿ㄰-㆏ㇰ-ㇿ㐀-䶿一-鿿"
    "가-힯豈-﫿ｦ-ﾟ\U00020000-\U0003134f]+"
)


def json_object(reply: str) -> dict | None:
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


def clean(text: str) -> str:
    """Without Chinese, Japanese or Korean letters and with its spaces squeezed (Draft job step 4, D18)."""
    return " ".join(CJK.sub("", text).split())
