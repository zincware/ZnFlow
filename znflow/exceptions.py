"""ZnFlow exceptions."""


class ConnectionAttributeError(AttributeError):
    """Raised when a connection attribute is not found."""


class UnresolvedConnectionError(Exception):
    """Raised when a value is read that still points at another Node.

    This inherits from 'Exception' and not from 'AttributeError', so that
    'hasattr' and 'getattr(obj, name, default)' pass it on instead of turning
    it into a missing attribute.
    """
