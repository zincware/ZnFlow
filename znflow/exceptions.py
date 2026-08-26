"""ZnFlow exceptions."""


class ConnectionAttributeError(AttributeError):
    """Raised when a connection attribute is not found."""


class UnresolvedConnectionError(Exception):
    """Raised when a value is read that still points at another Node."""
