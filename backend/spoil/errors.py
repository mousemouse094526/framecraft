"""The spoil API's refusals, raised by `jobs` and `clips` alike."""


class SpoilError(Exception):
    """A refusal the route turns into `{"code", "message"}` with `status`."""

    def __init__(self, status: int, code: str, message: str, **extra: str):
        super().__init__(message)
        self.status, self.code, self.message, self.extra = status, code, message, extra
