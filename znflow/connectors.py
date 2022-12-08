"""Node Connector Module.
Connectors define the connections between Nodes in the networkx Graph.
They act as proxy for the actual value until the graph is evaluated.
"""

from __future__ import annotations

import abc
import functools
import typing

import zninit

from znflow.utils import IterableHandler

if typing.TYPE_CHECKING:
    from znflow.graph import DiGraph

T = typing.TypeVar("T")


class _ReduceRepresentation(IterableHandler):
    """Create a representation which is not nested w.r.t. Connectors."""

    def default(self, value, **kwargs):
        """Prohibit nested display of Connectors."""
        if isinstance(value, Connector):
            return f"<{value.__class__.__name__} at {hex(abs(hash(value)))[:8]}>"
        return repr(value)


class Connector(zninit.ZnInit):
    graph: "DiGraph" = zninit.Descriptor(frozen=True, repr_func=lambda x: f"<{x}>")

    @abc.abstractmethod
    def get_result(self, *args):
        raise NotImplementedError

    def __eq__(self, other):
        return all(
            getattr(self, descriptor.name) == getattr(other, descriptor.name)
            for descriptor in zninit.get_descriptors(self=self)
        )

    def __hash__(self):
        try:
            hash_val = [
                getattr(self, descriptor.name)
                for descriptor in zninit.get_descriptors(self=self)
            ]
            return hash(tuple(hash_val))
        except AttributeError:
            # ZnInit checks weakref[instance] via __hash__ which is evaluated before
            #  descriptors are set. In this case we return the super hash.
            return super().__hash__()


class NodeConnector(Connector):
    node: T = zninit.Descriptor(
        frozen=True
    )  # , repr_func=lambda x: f"<{x} at {hex(abs(hash(x)))[:8]}>")
    attribute: str = zninit.Descriptor(None, frozen=True)

    def get_result(self):
        # this won't compute anything
        return getattr(self.node, self.attribute)


class FunctionConnector(Connector):
    func: typing.Callable = zninit.Descriptor(
        frozen=True, repr_func=lambda x: f"<function {x.__module__}.{x.__name__}>"
    )
    args: typing.Tuple = zninit.Descriptor(
        frozen=True, repr_func=_ReduceRepresentation().handle
    )
    kwargs: typing.Tuple = zninit.Descriptor(
        frozen=True,
        on_setattr=lambda kwargs: tuple(sorted(kwargs.items())),
        repr_func=_ReduceRepresentation().handle,
    )

    @functools.cache
    def get_result(self):
        # this will compute the full graph.
        args = [
            arg.get_result() if isinstance(arg, Connector) else arg for arg in self.args
        ]
        kwargs = {
            key: value.get_result() if isinstance(value, Connector) else value
            for key, value in self.kwargs
        }

        return self.func(*args, **kwargs)


@functools.singledispatch
def add_edge(node_a, node_b):
    """Add an edge between two nodes."""
    raise NotImplementedError


@add_edge.register
def _(node_a: NodeConnector, node_b):
    """Add an edge between a NodeConnector and a Node."""
    assert isinstance(node_b, Connector)
    if isinstance(node_b, NodeConnector):
        node_a.graph.add_edge(
            node_b.node,
            node_a.node,
        )
    elif isinstance(node_b, FunctionConnector):
        node_a.graph.add_edge(
            node_b,
            node_a.node,
        )


@add_edge.register
def _(node_a: FunctionConnector, node_b):
    """Add an edge between a FunctionConnector and a Node."""
    assert isinstance(node_b, Connector)
    if isinstance(node_b, NodeConnector):
        node_a.graph.add_edge(
            node_b.node,
            node_a,
            in_attribute=node_b.attribute,
            out_attribute=None,
        )
    elif isinstance(node_b, FunctionConnector):
        node_a.graph.add_edge(
            node_b,
            node_a,
            in_attribute=None,
            out_attribute=None,
        )
