from __future__ import annotations

import contextlib
import dataclasses
import typing
from typing import Any
from uuid import UUID

from znflow import exceptions

if typing.TYPE_CHECKING:
    from znflow.graph import DiGraph


@contextlib.contextmanager
def disable_graph(*args, **kwargs):
    """Temporarily disable set the graph to empty.

    This can be useful, if you e.g. want to use 'get_attribute'.
    """
    graph = get_graph()
    set_graph(empty_graph)
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


@dataclasses.dataclass(frozen=True)
class EmptyGraph:
    """An empty class used as a default value for _graph_."""


empty_graph = EmptyGraph()


class NodeBaseMixin:
    """A Parent for all Nodes.

    This class is used to globally access and change all classes that inherit from it.

    Attributes
    ----------
        _graph_ : DiGraph
            The graph this node belongs to.
            This is only available within the graph context.
        uuid : UUID
            The unique identifier of this node.
        _external_ : bool
            If true, the node is allowed to be created outside of a graph context.
            In this case connections can be created to this node, otherwise
            an exception is raised.
    """

    _graph_ = empty_graph
    _external_ = False
    _uuid: UUID = None
    _znflow_resolved: bool = False

    _protected_ = [
        "_graph_",
        "uuid",
        "_uuid",
        "model_fields",  # pydantic
        "model_computed_fields",  # pydantic
    ]

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


def get_graph() -> DiGraph:
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

    Attributes
    ----------
        instance: Node|FunctionFuture
            the object this connection points to
        attribute: str
            Node.attribute
            or FunctionFuture.result
            or None if the class is passed and not an attribute
        item: any
            any slice or list index to be applied to the result
    """

    instance: any
    attribute: str
    item: any = None

    def __post_init__(self):
        if self.attribute is not None and self.attribute.startswith("_"):
            raise ValueError("Private attributes are not allowed.")

    def __getitem__(self, item):
        return dataclasses.replace(self, instance=self, attribute=None, item=item)

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
    def _external_(self):
        return self.instance._external_

    @property
    def result(self):
        if self.attribute:
            result = getattr(self.instance, self.attribute)
        elif isinstance(self.instance, (FunctionFuture, self.__class__)):
            result = self.instance.result
        else:
            result = self.instance
        return result[self.item] if self.item else result

    def __getattribute__(self, __name: str) -> Any:
        try:
            return super().__getattribute__(__name)
        except AttributeError as e:
            raise exceptions.ConnectionAttributeError(
                "Connection does not support further attributes to its result."
            ) from e

    def __eq__(self, other) -> bool:
        """Overwrite for dynamic break points."""
        from znflow import resolve, get_graph, empty_graph

        if isinstance(other, (Connection)):
            return self.instance == other.instance
        if isinstance(other, (FunctionFuture)):
            return False

        if get_graph() is empty_graph:
            return super().__eq__(other)
        return resolve(self).__eq__(other)

    def __lt__(self, other) -> bool:
        """Overwrite for dynamic break points."""
        from znflow import resolve, get_graph, empty_graph

        if get_graph() is empty_graph:
            return super().__lt__(other)
        return resolve(self).__lt__(other)

    def __le__(self, other) -> bool:
        """Overwrite for dynamic break points."""
        from znflow import resolve, get_graph, empty_graph

        if get_graph() is empty_graph:
            return super().__le__(other)
        return resolve(self).__le__(other)

    def __gt__(self, other) -> bool:
        """Overwrite for dynamic break points."""
        from znflow import resolve, get_graph, empty_graph

        if get_graph() is empty_graph:
            return super().__gt__(other)
        return resolve(self).__gt__(other)

    def __ge__(self, other) -> bool:
        """Overwrite for dynamic break points."""
        from znflow import resolve, get_graph, empty_graph

        if get_graph() is empty_graph:
            return super().__ge__(other)
        return resolve(self).__ge__(other)

    def __iter__(self):
        from znflow import resolve

        try:
            return resolve(self).__iter__()
        except AttributeError:
            raise TypeError(f"'{self}' object is not iterable")


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

    def __add__(
        self, other: typing.Union[Connection, FunctionFuture, CombinedConnections]
    ) -> CombinedConnections:
        if isinstance(other, (Connection, FunctionFuture, CombinedConnections)):
            return CombinedConnections(connections=[self, other])
        raise TypeError(f"Can not add {type(other)} to {type(self)}.")

    def __radd__(self, other):
        """Enable 'sum([a, b], [])'"""
        return self if other == [] else self.__add__(other)

    def __eq__(self, other) -> bool:
        """Overwrite for dynamic break points."""
        from znflow import resolve, get_graph, empty_graph

        if isinstance(other, (Connection)):
            return False
        if isinstance(other, (FunctionFuture)):
            return (
                self.function == other.function
                and self.args == other.args
                and self.kwargs == other.kwargs
                and self.item == other.item
            )

        if get_graph() is empty_graph:
            return super().__eq__(other)
        return resolve(self).__eq__(other)

    def __lt__(self, other) -> bool:
        """Overwrite for dynamic break points."""
        from znflow import resolve, get_graph, empty_graph

        if get_graph() is empty_graph:
            return super().__lt__(other)
        return resolve(self).__lt__(other)

    def __le__(self, other) -> bool:
        """Overwrite for dynamic break points."""
        from znflow import resolve, get_graph, empty_graph

        if get_graph() is empty_graph:
            return super().__le__(other)
        return resolve(self).__le__(other)

    def __gt__(self, other) -> bool:
        """Overwrite for dynamic break points."""
        from znflow import resolve, get_graph, empty_graph

        if get_graph() is empty_graph:
            return super().__gt__(other)
        return resolve(self).__gt__(other)

    def __ge__(self, other) -> bool:
        """Overwrite for dynamic break points."""
        from znflow import resolve, get_graph, empty_graph

        if get_graph() is empty_graph:
            return super().__ge__(other)
        return resolve(self).__ge__(other)

    def __iter__(self):
        from znflow import resolve

        try:
            return resolve(self).__iter__()
        except AttributeError:
            raise TypeError(f"'{self}' object is not iterable")
