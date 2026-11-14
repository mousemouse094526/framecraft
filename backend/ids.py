"""The ids the app makes for what it keeps: `{prefix}_` and 8 hex digits."""

import secrets


def new_id(prefix: str, taken: set[str] = frozenset()) -> str:
    """`{prefix}_` and 8 hex digits, not in `taken`. The prefix names what the id is: `s` a
    Series, `c` a character, `b` a background, `e` an EP, `a` an act, `g` a segment, `k` a
    card, `m` a sound of the library."""
    while (found := f"{prefix}_{secrets.token_hex(4)}") in taken:
        pass
    return found
