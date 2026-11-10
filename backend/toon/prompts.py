"""The prompts of the การ์ตูนเล่า tab and the reading of Qwen's answers (toon spec › คำสั่งภาพ, D36).

A picture's prompt is the app's fixed template around `{scene}`, the English Qwen writes from
a Thai description, and `{style}`, the Series' style.
"""

from backend import llm_reply

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
    found = llm_reply.json_object(reply)
    scene = found.get("scene") if found is not None else None
    scene = " ".join(scene.split()) if isinstance(scene, str) else ""
    return scene or None


def ref_prompt(kind: str, scene: str, style: str) -> str:
    template = CHARACTER_TEMPLATE if kind == "characters" else BACKGROUND_TEMPLATE
    return template.format(scene=scene, style=style)


def card_scene_prompt(description: str, names: list[str]) -> str:
    """Asks Qwen for the English `{scene}` of a card's picture, its characters as `character 1`
    and `character 2` in the order of the card's `character_ids` (spec › คำสั่งภาพ)."""
    if names:
        who = ", ".join(f"{name} is character {n}" for n, name in enumerate(names, start=1))
        subjects = " and ".join(f'"character {n}"' for n in range(1, len(names) + 1))
        how = (
            f"Make {subjects} the subject ({who}), never their names. "
            "Say their pose and facial expression, the camera's angle and distance, and the light."
        )
    else:
        how = "Nobody is in it. Say what is there, the camera's angle and distance, and the light."
    return (
        f"Write one or two short English sentences for an image model, describing one picture of a story. {how}\n"
        "Do not name a style, and write no Thai.\n"
        f"Thai description: {description}\n"
        'Answer with JSON only: {"scene": "..."}'
    )


def fallback_scene(characters: int, description: str) -> str:
    """The `{scene}` of a card whose description is empty, or whose translation broke or took
    too long: a medium shot, then the description as written (spec › คำสั่งภาพ)."""
    shot = "character 1 in a medium shot." if characters else "A medium shot."
    return f"{shot} {description}" if description else shot


def card_prompt(scene: str, style: str, characters: int) -> str:
    """The app's template around a card's scene: each character bound to its reference image,
    then the background's, which comes after them (spec › คำสั่งภาพ)."""
    bound = "".join(f" character {n} is the character in reference image {n}." for n in range(1, characters + 1))
    return (
        f"{scene}{bound} In the setting of the background in reference image {characters + 1}. "
        f"{style}. No text, no letters, no signs."
    )
