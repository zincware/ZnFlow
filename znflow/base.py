from __future__ import annotations

import dataclasses
import logging
import typing
from uuid import UUID

log = logging.getLogger(__name__)


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

    _protected_ = ["_graph_", "uuid", "_uuid"]  # TODO consider addign regex patterns

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        if self._uuid is not None:
            raise ValueError("uuid is already set")
        self._uuid = value

    def __getattribute__(self, item):
        value = super().__getattribute__(item)
        if get_graph() is not None:
            if (
                item not in type(self)._protected_
                and not item.startswith("__")
                and not item.startswith("_")
            ):
                connector = Connection(instance=self, attribute=item)
                return connector
        return value

    def __setattr__(self, item, value) -> None:
        if isinstance(value, Connection):
            assert self.uuid in self._graph_, f"'{self.uuid=}' not in '{self._graph_=}'"
            assert value.uuid in self._graph_
            self._graph_.add_edge(
                value.uuid, self.uuid, i_attr=value.attribute, j_attr=item
            )
        super().__setattr__(item, value)


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


@dataclasses.dataclass
class FunctionFuture(NodeBaseMixin):
    function: typing.Callable
    args: typing.Tuple
    kwargs: typing.Dict

    _protected_ = NodeBaseMixin._protected_ + ["function", "args", "kwargs"]

    def result(self):
        return self.function(*self.args, **self.kwargs)
