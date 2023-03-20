"""The base module of ZnFlow."""
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
        """A method that generates a UUID to create a hashable object for each node."""
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        """A method that checks for an existing UUID.

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
    """Gets Graph from the NodeBaseMixin class."""
    return NodeBaseMixin._graph_


def set_graph(value):
    """Sets a value for the NodeBaseMixin graph."""
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

    @property
    def uuid(self):
        """Gets value of the UUID."""
        return self.instance.uuid

    @property
    def result(self):
        """Returns the instance and if available, also the attribute."""
        if self.attribute is None:
            return self.instance
        return getattr(self.instance, self.attribute)


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

    _result: any = dataclasses.field(default=None, init=False, repr=True)

    _protected_ = NodeBaseMixin._protected_ + ["function", "args", "kwargs"]

    def run(self):
        """Run Method of the FunctionFuture class.

        Executes the function with the given arguments.

        Returns
        -------
        TODO
        """
        self._result = self.function(*self.args, **self.kwargs)

    @property
    def result(self):
        """TODO.

        Returns
        -------
        TODO
        """
        if self._result is None:
            self.run()

        return self._result
