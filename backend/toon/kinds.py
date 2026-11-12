"""What differs between a Series' characters and its backgrounds, one row per kind (toon spec ›
Series ตัวละคร ฉากหลัง, › คำสั่งภาพ, D23, D37): the code that handles both reads it here
instead of asking which kind it has.
"""

from typing import Literal, NamedTuple

from backend.toon.store import Background, Character, Layout

ItemKind = Literal["characters", "backgrounds"]

# The size of a card's picture by the Series' layout; a background is drawn as the card it
# sits behind (D37). 768 on the long side so a 16 GB Mac doesn't swap (D79); render scales
# every size up to the layout's, so pictures drawn at an older size still work.
CARD_SIZE: dict[Layout, tuple[int, int]] = {"frame": (768, 432), "full": (432, 768)}


class KindRow(NamedTuple):
    """One row of `KINDS`: what the code reads of an `ItemKind` instead of branching on it."""

    model: type[Character] | type[Background]
    id_prefix: str
    tagged: bool  # whether it has the short `tag` after its name on a name tag (D23)
    sizes: dict[str, tuple[int, int]]  # (width, height) of its reference picture, by layout
    # An uploaded picture keeps its own shape, its long side at most this; None: cropped to `sizes`.
    upload_side: int | None
    plot_max: int  # how many of it a plot may use (spec › Plot job)
    template: str  # the reference picture's prompt around Qwen's `{scene}` and the `{style}`
    scene_ask: tuple[str, str]  # what Qwen describes for that `{scene}`, and how


KINDS: dict[ItemKind, KindRow] = {
    "characters": KindRow(
        model=Character,
        id_prefix="c",
        tagged=True,
        sizes={layout: CARD_SIZE["full"] for layout in CARD_SIZE},  # upright, as a full card, whatever the layout
        upload_side=1536,
        plot_max=6,
        template="Full body, front view, standing, plain light gray background. {scene} {style}. No text, no letters.",
        scene_ask=(
            "a character, for a reference picture of them standing alone",
            "Describe how they look: body, hair, face, clothes and their colours.",
        ),
    ),
    "backgrounds": KindRow(
        model=Background,
        id_prefix="b",
        tagged=False,
        sizes=CARD_SIZE,
        upload_side=None,
        plot_max=6,
        template="{scene} Empty location, no people. {style}. No text, no letters, no signs.",
        scene_ask=(
            "a place, for a picture of it with nobody in it",
            "Describe the place: what is there, the camera's angle and distance, and the light.",
        ),
    ),
}
