"""Ostrom error type definition."""


class OstromError:
    """Custom exception class for Ostrom API errors."""

    def __init__(
        self, message: str, error_code: int = 1, exception: Exception | None = None
    ):
        """Initialize an Ostrom API error."""
        self.message = message
        self.error_code = error_code
        self.exception = exception

    def __str__(self) -> str:
        """Return a readable message for logs and UI."""
        message: str = f"{self.message} ({self.error_code})"

        if self.exception is not None:
            message += f": {self.exception}"

        return message
