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
        self.fget = disable_graph()(fget)
        self.fset = disable_graph()(fset)
        self.fdel = disable_graph()(fdel)
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc
        self._name = ""

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError(f"property '{self._name}' has no getter")
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError(f"property '{self._name}' has no setter")
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError(f"property '{self._name}' has no deleter")
        self.fdel(obj)

    def getter(self, fget):
        prop = type(self)(fget, self.fset, self.fdel, self.__doc__)
        prop._name = self._name
        return prop

    def setter(self, fset):
        prop = type(self)(self.fget, fset, self.fdel, self.__doc__)
        prop._name = self._name
        return prop

    def deleter(self, fdel):
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
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        if self._uuid is not None:
            raise ValueError("uuid is already set")
        self._uuid = value

    def run(self):
        raise NotImplementedError


def get_graph():
    return NodeBaseMixin._graph_


def set_graph(value):
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
    instance: either a Node or FunctionFuture
    attribute:
        Node.attribute
        or FunctionFuture.result
        or None if the class is passed and not an attribute
    """

    instance: any
    attribute: any
    item: any = None

    def __post_init__(self):
        if self.attribute is not None and self.attribute.startswith("_"):
            raise ValueError("Private attributes are not allowed.")

    def __getitem__(self, item):
        return dataclasses.replace(self, instance=self, attribute=None, item=item)

    def __iter__(self):
        raise TypeError(f"Can not iterate over {self}.")

    def __add__(
        self, other: typing.Union[Connection, FunctionFuture, CombinedConnections]
    ) -> CombinedConnections:
        if isinstance(other, (Connection, FunctionFuture, CombinedConnections)):
            return CombinedConnections(connections=[self, other])
        raise TypeError(f"Can not add {type(other)} to {type(self)}.")

    def __radd__(self, other):
        """Enable 'sum([a, b], [])'"""
        return self if other == [] else self.__add__(other)

    @property
    def uuid(self):
        return self.instance.uuid

    @property
    def result(self):
        if self.attribute:
            result = getattr(self.instance, self.attribute)
        elif isinstance(self.instance, (FunctionFuture, self.__class__)):
            result = self.instance.result
        else:
            result = self.instance
        return result[self.item] if self.item else result


@dataclasses.dataclass(frozen=True)
class CombinedConnections:
    """Combine multiple Connections into one.

    This class allows to 'add' Connections and/or FunctionFutures.
    This only works if the Connection or FunctionFuture points to a 'list'.
    A new entry of 'CombinedConnections' will be created for every time a new
    item is added.

    Examples
    --------

    >>> import znflow
    >>> @znflow.nodfiy
    >>> def add(size) -> list:
    >>>     return list(range(size))
    >>> with znflow.DiGraph() as graph:
    >>>     outs = add(2) + add(3)
    >>> graph.run()
    >>> assert outs.result == [0, 1, 0, 1, 2]

    Attributes
    ----------
    connections : list[Connection|FunctionFuture|AddedConnections]
        The List of items to be added.
    item : any
        Any slice to be applied to the result.
    """

    connections: typing.List[Connection]
    item: any = None

    def __add__(
        self, other: typing.Union[Connection, FunctionFuture, CombinedConnections]
    ) -> CombinedConnections:
        """Implement add for AddedConnections.

        Raises
        ------
        ValueError
            If  self.item is set, we can not add another item.
        TypeError
            If other is not a Connection, FunctionFuture or AddedConnections.
        """
        if self.item is not None:
            raise ValueError("Can not combine multiple slices")
        if isinstance(other, (Connection, FunctionFuture)):
            return dataclasses.replace(self, connections=self.connections + [other])
        elif isinstance(other, CombinedConnections):
            return dataclasses.replace(
                self, connections=self.connections + other.connections
            )
        else:
            raise TypeError(f"Can not add {type(other)} to {type(self)}.")

    def __radd__(self, other):
        """Enable 'sum([a, b], [])'"""
        return self if other == [] else self.__add__(other)

    def __getitem__(self, item):
        return dataclasses.replace(self, item=item)

    def __iter__(self):
        raise TypeError(f"Can not iterate over {self}.")

    @property
    def result(self):
        try:
            results = []
            for connection in self.connections:
                results.extend(connection.result)
            return results[self.item] if self.item else results
        except TypeError as err:
            raise TypeError(
                f"The value {connection.result} is of type {type(connection.result)}. The"
                f" only supported type is list. Please change {connection}"
            ) from err


@dataclasses.dataclass
class FunctionFuture(NodeBaseMixin):
    function: typing.Callable
    args: typing.Tuple
    kwargs: typing.Dict
    item: any = None

    result: any = dataclasses.field(default=None, init=False, repr=True)

    _protected_ = NodeBaseMixin._protected_ + ["function", "args", "kwargs"]

    def run(self):
        self.result = self.function(*self.args, **self.kwargs)

    def __getitem__(self, item):
        return Connection(instance=self, attribute=None, item=item)

    def __iter__(self):
        raise TypeError(f"Can not iterate over {self}.")

    def __add__(
        self, other: typing.Union[Connection, FunctionFuture, CombinedConnections]
    ) -> CombinedConnections:
        if isinstance(other, (Connection, FunctionFuture, CombinedConnections)):
            return CombinedConnections(connections=[self, other])
        raise TypeError(f"Can not add {type(other)} to {type(self)}.")

    def __radd__(self, other):
        """Enable 'sum([a, b], [])'"""
        return self if other == [] else self.__add__(other)
