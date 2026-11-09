"""The prompts of the การ์ตูนเล่า tab and the reading of Qwen's answers (toon spec › คำสั่งภาพ, D36).

A picture's prompt is the app's fixed template around `{scene}`, the English Qwen writes from
a Thai description, and `{style}`, the Series' style.
"""

import json

SCENE_MAX_TOKENS = 200
SCENE_TEMPERATURE = 0.0

CHARACTER_TEMPLATE = "Full body, front view, standing, plain light gray background. {scene} {style}. No text, no letters."
BACKGROUND_TEMPLATE = "{scene} Empty location, no people. {style}. No text, no letters, no signs."

_REF_ASK = {
    "characters": (
        "a character, for a reference picture of them standing alone",
        "Describe how they look: body, hair, face, clothes and their colours.",
    ),
    "backgrounds": (
        "a place, for a picture of it with nobody in it",
        "Describe the place: what is there, the camera's angle and distance, and the light.",
    ),
}


def ref_scene_prompt(kind: str, name: str, description: str) -> str:
    """Asks Qwen for the English `{scene}` of a reference picture (spec › Ref job step 2)."""
    what, how = _REF_ASK[kind]
    text = description or name
    return (
        f"Write one or two short English sentences for an image model, describing {what}. {how}\n"
        "Do not name a style, and write no Thai.\n"
        f"Thai description: {text}\n"
        'Answer with JSON only: {"scene": "..."}'
    )


def parse_scene(reply: str) -> str | None:
    """`scene` of the JSON object in a reply, inside a code fence or not; None when there is
    none or it is empty."""
    start, end = reply.find("{"), reply.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        found = json.loads(reply[start : end + 1])
    except json.JSONDecodeError:
        return None
    scene = found.get("scene") if isinstance(found, dict) else None
    scene = " ".join(scene.split()) if isinstance(scene, str) else ""
    return scene or None


def ref_prompt(kind: str, scene: str, style: str) -> str:
    template = CHARACTER_TEMPLATE if kind == "characters" else BACKGROUND_TEMPLATE
    return template.format(scene=scene, style=style)
