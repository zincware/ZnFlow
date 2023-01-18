from __future__ import annotations

import zninit

from znflow.base import NodeBaseMixin, disable_dag
from znflow.connectors import Connector, FunctionConnector, NodeConnector, add_edge
from znflow.utils import IterableHandler


class GetResult(IterableHandler):
    def default(self, value, *args, **kwargs):
        return value.get_result() if isinstance(value, Connector) else value


class AddEdge(IterableHandler):
    def default(self, value, *args, **kwargs):
        node = kwargs.pop("node")
        attribute_name = kwargs.pop("attribute_name")
        dag = NodeBaseMixin._graph_
        if isinstance(value, NodeConnector):
            if value.graph is not None:
                assert (
                    value.graph == dag
                ), f"DAGs are not the same '{value.graph}' != '{dag}'"
            connector = NodeConnector(graph=dag, node=node, attribute=attribute_name)
            add_edge(connector, value)
        elif isinstance(value, NodeBaseMixin):
            connector = NodeConnector(graph=dag, node=node, attribute=attribute_name)
            node_connector = NodeConnector(dag=dag, node=value)
            add_edge(connector, node_connector)
        elif isinstance(value, FunctionConnector):
            connector = NodeConnector(graph=dag, node=node, attribute=attribute_name)
            add_edge(connector, value)


def update_connectors_to_results(node):
    if isinstance(node, zninit.ZnInit):
        for attribute in zninit.get_descriptors(EdgeAttribute, self=node):
            value = getattr(node, attribute.name)
            setattr(node, attribute.name, GetResult().handle(value))


class EdgeAttribute(zninit.Descriptor):
    def __get__(self, instance, owner=None):
        if getattr(instance, "_graph_", None) is None:
            return super().__get__(instance, owner)
        return NodeConnector(
            graph=NodeBaseMixin._graph_, node=instance, attribute=self.name
        )

    def __set__(self, instance, value):
        if getattr(instance, "_graph_", None) is not None:
            AddEdge().handle(value, node=instance, attribute_name=self.name)

        super().__set__(instance, value)


class Node(zninit.ZnInit, NodeBaseMixin):
    def __post_init__(self):
        if self._graph_ is not None:
            """Add the Node to the DiGraph upon instantiating."""
            self._graph_.add_node(self)

    @disable_dag
    def __repr__(self):
        """Get the representation.

        We temporarily disable the _graph_ to so __getattribute__ won't trigger.
        """
        return super().__repr__()

    def __matmul__(self, other: str) -> NodeConnector:
        """Method overload to get a NodeConnector.

        Can also be used outside 'DiGraph' contextmanager.
        """
        if not isinstance(other, str):
            raise ValueError(
                f"{self} @ <other> only supports type string. Found {type(other)}."
            )
        return NodeConnector(graph=self._graph_, node=self, attribute=other)

    def __getattribute__(self, item):
        if not isinstance(getattr(type(self), item), property):
            _ = super().__getattribute__(item)  # does not work with properties
        if (
            item in ["post_init", "_post_init_", "_graph_", "_id_"]
            or item.startswith("__")
            or item.startswith("_")
        ):
            return super().__getattribute__(item)
        return super().__getattribute__(item) if self._graph_ is None else self @ item


def nodify(function):
    """Decorator to create a Node from a function."""

    def wrapper(*args, **kwargs):
        """Wrapper function for the decorator."""
        dag = NodeBaseMixin._graph_
        if dag is not None:
            connector = FunctionConnector(
                func=function, args=args, kwargs=kwargs, graph=dag
            )
            dag.add_node(connector)
            AddFunctionConnection().handle(args, connector=connector)
            AddFunctionConnection().handle(kwargs, connector=connector)

            return connector
        return function(*args, **kwargs)

    return wrapper


class AddFunctionConnection(IterableHandler):
    """Connect 'FunctionConnector' or 'NodeConnector' to a given FunctionConnector."""

    def default(self, value, **kwargs):
        """Default method of IterableHandler."""
        connector: FunctionConnector = kwargs.pop("connector")
        if isinstance(value, FunctionConnector):
            add_edge(connector, value)
        if isinstance(value, NodeConnector):
            add_edge(connector, value)
