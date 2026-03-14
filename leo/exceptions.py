class FetchError(RuntimeError):
    """Raised when there is an error fetching data from a source."""

    pass


class ParseError(RuntimeError):
    """Raised when there is an error parsing data from a source."""

    pass
