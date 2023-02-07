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

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        if self._uuid is not None:
            raise ValueError(f"{self} already has a uuid assigned.")
        self._uuid = value


def get_graph():
    return NodeBaseMixin._graph_


def set_graph(value):
    NodeBaseMixin._graph_ = value


@dataclasses.dataclass
class FunctionFuture(NodeBaseMixin):
    function: typing.Callable
    args: typing.Tuple
    kwargs: typing.Dict

    def result(self):
        return self.function(*self.args, **self.kwargs)
