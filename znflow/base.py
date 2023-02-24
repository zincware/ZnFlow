from __future__ import annotations

import contextlib
import dataclasses
import typing
from uuid import UUID


@contextlib.contextmanager
def disable_graph():
    """Temporarily disable set the graph to None.

    This can be useful, if you e.g. want to use 'get_attribute'.
    """
    graph = get_graph()
    set_graph(None)
    try:
        yield
    finally:
        set_graph(graph)


class NodeBaseMixin:
    """A Parent for all Nodes.

    This class is used to globally access and change all classes that inherit from it.

    Attributes
    ----------
    _graph_ : DiGraph
    uuid : UUID
    """

    _graph_ = None
    _uuid: UUID = None

    _protected_ = [
        "_graph_",
        "uuid",
        "_uuid",
        "result",
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

    def __getitem__(self, item):
        if self.item is not None:
            raise TypeError(
                f"'__getitem__' call to {self} where 'item is not None' is currently not"
                " supported."
            )
        return dataclasses.replace(self, item=item)

    @property
    def uuid(self):
        return self.instance.uuid

    @property
    def result(self):
        result = (
            getattr(self.instance, self.attribute) if self.attribute else self.instance
        )

        if self.item is None:
            return result
        return result[self.item]


@dataclasses.dataclass
class FunctionFuture(NodeBaseMixin):
    function: typing.Callable
    args: typing.Tuple
    kwargs: typing.Dict
    item: any = None

    _result: any = dataclasses.field(default=None, init=False, repr=True)

    _protected_ = NodeBaseMixin._protected_ + ["function", "args", "kwargs"]

    def run(self):
        self._result = self.function(*self.args, **self.kwargs)

    def __getitem__(self, item):
        return Connection(instance=self, attribute="result", item=item)

    @property
    def result(self):
        if self._result is None:
            self.run()
        return self._result
