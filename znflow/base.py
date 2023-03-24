"""The base module of znflow."""
from __future__ import annotations

import contextlib
import dataclasses
import typing
from uuid import UUID


@contextlib.contextmanager
def disable_graph(*args, **kwargs):
    """Temporarily disable set the graph to empty.

    This can be useful, if you e.g. want to use 'get_attribute'.
    """
    graph = get_graph()
    set_graph(empty)
    try:
        yield
    finally:
        set_graph(graph)


class Property:
    """Custom Property with disabled graph.

    References
    ----------
    Adapted from https://docs.python.org/3/howto/descriptor.html#properties
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        """Init method of the property class.

        References
        ----------
        Adapted from https://docs.python.org/3/howto/descriptor.html#properties
        """
        self.fget = disable_graph()(fget)
        self.fset = disable_graph()(fset)
        self.fdel = disable_graph()(fdel)
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc
        self._name = ""

    def __set_name__(self, owner, name):
        """Set Name Method of the Property class.

        References
        ----------
        Adapted from https://docs.python.org/3/howto/descriptor.html#properties
        """
        self._name = name

    def __get__(self, obj, objtype=None):
        """Get Method of the Property class.

        References
        ----------
        Adapted from https://docs.python.org/3/howto/descriptor.html#properties
        """
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError(f"property '{self._name}' has no getter")
        return self.fget(obj)

    def __set__(self, obj, value):
        """Set Method of the Property class.

        References
        ----------
        Adapted from https://docs.python.org/3/howto/descriptor.html#properties
        """
        if self.fset is None:
            raise AttributeError(f"property '{self._name}' has no setter")
        self.fset(obj, value)

    def __delete__(self, obj):
        """Delete Method of the Property class.

        References
        ----------
        Adapted from https://docs.python.org/3/howto/descriptor.html#properties
        """
        if self.fdel is None:
            raise AttributeError(f"property '{self._name}' has no deleter")
        self.fdel(obj)

    def getter(self, fget):
        """Getter Method of the Property class.

        References
        ----------
        Adapted from https://docs.python.org/3/howto/descriptor.html#properties
        """
        prop = type(self)(fget, self.fset, self.fdel, self.__doc__)
        prop._name = self._name
        return prop

    def setter(self, fset):
        """Setter Method of the Property class.

        References
        ----------
        Adapted from https://docs.python.org/3/howto/descriptor.html#properties
        """
        prop = type(self)(self.fget, fset, self.fdel, self.__doc__)
        prop._name = self._name
        return prop

    def deleter(self, fdel):
        """Set delete method for Property class.

        References
        ----------
        Adapted from https://docs.python.org/3/howto/descriptor.html#properties
        """
        prop = type(self)(self.fget, self.fset, fdel, self.__doc__)
        prop._name = self._name
        return prop


empty = object()


class NodeBaseMixin:
    """A Parent for all Nodes.

    This class is used to globally access and change all classes that inherit from it.

    Attributes
    ----------
    _graph_ : DiGraph
    uuid : UUID
    """

    _graph_ = empty
    _uuid: UUID = None

    _protected_ = [
        "_graph_",
        "uuid",
        "_uuid",
    ]  # TODO consider adding regex patterns

    @property
    def uuid(self):
        """A method that generates a UUID to create a hashable object for each node."""
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        """Check for an existing UUID.

        If no UUID exists, it sets the previously defined UUID for the node.

        Raises
        ------
        ValueError
            If a UUID is already set for the current node.
        """
        if self._uuid is not None:
            raise ValueError("uuid is already set")
        self._uuid = value

    def run(self):
        """Run Method of NodeBaseMixin."""
        raise NotImplementedError


def get_graph():
    """Get Graph from the NodeBaseMixin class."""
    return NodeBaseMixin._graph_


def set_graph(value):
    """Set a value for the NodeBaseMixin graph."""
    NodeBaseMixin._graph_ = value


_get_attribute_none = object()


def get_attribute(obj, name, default=_get_attribute_none):
    """Get the real value of the attribute and not a znflow.Connection."""
    with disable_graph():
        if default is _get_attribute_none:
            return getattr(obj, name)
        return getattr(obj, name, default)


@dataclasses.dataclass(frozen=True)
class Connection:
    """A Connector for Nodes.

    Instance
    --------
        Either a Node or FunctionFuture.

    Attributes
    ----------
    attribute : Node.attribute
        or FunctionFuture.result
        or None if the class is passed and not an attribute.
    """

    instance: any
    attribute: any
    item: any = None

    def __getitem__(self, item):
        """Create a new object of the same type as self with values from changes."""
        return dataclasses.replace(self, instance=self, attribute=None, item=item)

    def __post_init__(self):
        """Raise a Valueerror if a private attribute is called."""
        if self.attribute is not None and self.attribute.startswith("_"):
            raise ValueError("Private attributes are not allowed.")

    @property
    def uuid(self):
        """Gets value of the UUID."""
        return self.instance.uuid

    @property
    def result(self):
        """Returns the instance and if available, also the attribute."""
        if self.attribute:
            result = getattr(self.instance, self.attribute)
        elif isinstance(self.instance, (FunctionFuture, self.__class__)):
            result = self.instance.result
        else:
            result = self.instance
        return result[self.item] if self.item else result


@dataclasses.dataclass
class FunctionFuture(NodeBaseMixin):
    """A class that creates a future object out of a function.

    Attributes
    ----------
    function : callable
    args : tuple
    kwargs : dict
    """

    function: typing.Callable
    args: typing.Tuple
    kwargs: typing.Dict
    item: any = None

    result: any = dataclasses.field(default=None, init=False, repr=True)

    _protected_ = NodeBaseMixin._protected_ + ["function", "args", "kwargs"]

    def run(self):
        """Run Method of the FunctionFuture class.

        Executes the function with the given arguments and saves the result.
        """
        self.result = self.function(*self.args, **self.kwargs)

    def __getitem__(self, item):
        """Get the object with all the information of the Connection class."""
        return Connection(instance=self, attribute=None, item=item)
