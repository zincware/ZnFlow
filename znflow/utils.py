"""Utils of the 'ZnFlow' package."""
import abc
import functools


class IterableHandler(abc.ABC):
    """Iterable handler using single dispatch.

    Attributes
    ----------
    updated : bool, default=False
        Set to True if handle updated data.
    """

    updated: bool = False

    def __init__(self):
        """Update the signature of handle based on the default method."""
        self.updated = False

    def __call__(self, value, **kwargs):
        """Call the handle method."""
        return self.handle(value, **kwargs)

    @abc.abstractmethod
    def default(self, value, **kwargs):
        """How to handle the individual element inside the iterable.

        The first argument must be a positional only argument.
        All other arguments must be keyword only arguments.
        """
        raise NotImplementedError

    def handle(self, value, **kwargs):
        """Handle the iterable."""
        self.updated = False
        return self._handle(value, **kwargs)

    @functools.singledispatchmethod
    def _handle(self, value, **kwargs):
        """Fallback handling if no siggledispatch was triggered."""

        result = self.default(value, **kwargs)
        if result is not value:
            self.updated = True
        return result

    @_handle.register
    def _(self, value: list, **kwargs) -> list:
        """Handle a list."""
        return [self._handle(x, **kwargs) for x in value]

    @_handle.register
    def _(self, value: tuple, **kwargs) -> tuple:
        """Handle a tuple."""
        # without 'tuple' it would be a generator
        return tuple(self._handle(x, **kwargs) for x in value)

    @_handle.register
    def _(self, value: set, **kwargs) -> set:
        """Handle a set."""
        return {self._handle(x, **kwargs) for x in value}

    @_handle.register
    def _(self, value: dict, **kwargs) -> dict:
        """Handle a dict."""
        return {key: self._handle(val, **kwargs) for key, val in value.items()}
