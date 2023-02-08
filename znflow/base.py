from __future__ import annotations

import dataclasses
import typing
from uuid import UUID


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


@dataclasses.dataclass(frozen=True)
class Connection:
    """A Connector for Nodes.
    instance: either a Node or FucntionFuture
    attribute:
        Node.attribute
        or FunctionFuture.result
        or None if the class is passed and not an attribute
    """

    instance: any
    attribute: any

    @property
    def uuid(self):
        return self.instance.uuid

    @property
    def result(self):
        if self.attribute is None:
            return self.instance
        return getattr(self.instance, self.attribute)


@dataclasses.dataclass
class FunctionFuture(NodeBaseMixin):
    function: typing.Callable
    args: typing.Tuple
    kwargs: typing.Dict

    _result: any = dataclasses.field(default=None, init=False, repr=True)

    _protected_ = NodeBaseMixin._protected_ + ["function", "args", "kwargs"]

    def run(self):
        self._result = self.function(*self.args, **self.kwargs)

    @property
    def result(self):
        if self._result is None:
            self.run()

        return self._result
