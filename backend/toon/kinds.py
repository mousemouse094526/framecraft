"""What differs between a Series' characters and its backgrounds, one row per kind (toon spec ›
Series ตัวละคร ฉากหลัง, › คำสั่งภาพ, D23, D37): the code that handles both reads it here
instead of asking which kind it has.
"""

from typing import Literal, NamedTuple

from backend.toon.store import Background, Character

Kind = Literal["characters", "backgrounds"]

# The size of a card's picture by the Series' layout; a background is drawn as the card it
# sits behind (D37).
CARD_SIZE = {"frame": (1024, 576), "full": (576, 1024)}


class ItemKind(NamedTuple):
    model: type[Character] | type[Background]
    id_prefix: str
    tagged: bool  # whether it has the short `tag` after its name on a name tag (D23)
    sizes: dict[str, tuple[int, int]]  # (width, height) of its reference picture, by layout
    # An uploaded picture keeps its own shape, its long side at most this; None: cropped to `sizes`.
    upload_side: int | None
    template: str  # the reference picture's prompt around Qwen's `{scene}` and the `{style}`
    scene_ask: tuple[str, str]  # what Qwen describes for that `{scene}`, and how


KINDS: dict[Kind, ItemKind] = {
    "characters": ItemKind(
        model=Character,
        id_prefix="c",
        tagged=True,
        sizes={layout: (576, 1024) for layout in CARD_SIZE},  # standing upright whatever the layout
        upload_side=1536,
        template="Full body, front view, standing, plain light gray background. {scene} {style}. No text, no letters.",
        scene_ask=(
            "a character, for a reference picture of them standing alone",
            "Describe how they look: body, hair, face, clothes and their colours.",
        ),
    ),
    "backgrounds": ItemKind(
        model=Background,
        id_prefix="b",
        tagged=False,
        sizes=CARD_SIZE,
        upload_side=None,
        template="{scene} Empty location, no people. {style}. No text, no letters, no signs.",
        scene_ask=(
            "a place, for a picture of it with nobody in it",
            "Describe the place: what is there, the camera's angle and distance, and the light.",
        ),
    ),
}
