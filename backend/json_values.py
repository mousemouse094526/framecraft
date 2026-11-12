"""Checks of values read from a JSON body or a file: JSON `true` is an int to Python."""


def is_int(value: object) -> bool:
    """An int that is not a boolean."""
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value: object) -> bool:
    """An int or float that is not a boolean."""
    return isinstance(value, int | float) and not isinstance(value, bool)
