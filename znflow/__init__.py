import zninit
import dataclasses
import typing
import networkx as nx

T = typing.TypeVar("T")


@dataclasses.dataclass(frozen=True)
class NodeConnector:
    node: T
    attribute: str = None

    def __rshift__(self, other):
        if self.node not in self.node._dag_.graph:
            self.node._dag_.graph.add_node(self.node)
        if not isinstance(other, NodeConnector):
            other = NodeConnector(node=other)
        if other.node not in self.node._dag_.graph:
            self.node._dag_.graph.add_node(other.node)

        # TODO check if the connection already exists
        self.node._dag_.graph.add_edge(
            self.node, other.node, in_attribute=self.attribute, out_attribute=other.attribute
        )

        return other

    def __lshift__(self, other):
        if not isinstance(other, NodeConnector):
            other = NodeConnector(node=other)
        return other >> self


class Parameters(zninit.Descriptor):
    def __get__(self, instance, owner=None):
        if getattr(instance, "_dag_", None) is None:
            return super().__get__(instance, owner)
        return NodeConnector(node=instance, attribute=self.name)


class DAG:
    def __init__(self):
        self.nodes = []
        self.graph = nx.MultiDiGraph()

    def attach(self, node):
        self.nodes.append(node)

    def __repr__(self):
        return f"DAG({self.nodes})"

    def __enter__(self):
        Node._dag_ = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        Node._dag_ = None


class Node(zninit.ZnInit):
    _dag_: DAG = None

    def post_init(self):
        if self._dag_ is not None:
            self._dag_.attach(self)

    def __repr__(self):
        return object.__repr__(self) if self._dag_ else super().__repr__()

    def __rshift__(self, other):
        if not self._dag_:
            raise TypeError("Must be inside a DAG context manager")
        return NodeConnector(node=self) >> other

    def __lshift__(self, other):
        if not self._dag_:
            raise TypeError("Must be inside a DAG context manager")
        return NodeConnector(node=self) << other

