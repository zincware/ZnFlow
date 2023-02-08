import logging

import networkx as nx

from znflow import utils
from znflow.base import Connection, FunctionFuture, NodeBaseMixin, get_graph, set_graph
from znflow.node import Node


class _AttributeToConnection(utils.IterableHandler):
    def default(self, value, **kwargs):
        if isinstance(value, FunctionFuture):
            node_instance = kwargs["node_instance"]
            graph = kwargs["graph"]
            connection = Connection(value, attribute="result")

            graph.add_edge(connection, node_instance)

            return connection
        elif isinstance(value, Node):
            node_instance = kwargs["node_instance"]
            graph = kwargs["graph"]
            v_attr = kwargs["v_attr"]
            connection = Connection(value, attribute=None)
            graph.add_edge(connection, node_instance, v_attr=v_attr)
            return connection
        return value


log = logging.getLogger(__name__)


class DiGraph(nx.MultiDiGraph):
    def __enter__(self):
        if get_graph() is not None:
            raise ValueError("DiGraph already exists. Nested Graphs are not supported.")
        set_graph(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if get_graph() is not self:
            raise ValueError(
                "Something went wrong. DiGraph was changed inside the context manager."
            )
        set_graph(None)

        for node in self.nodes:
            node_instance = self.nodes[node]["value"]
            log.warning(f"Node {node} ({node_instance}) was added to the graph.")
            if isinstance(node_instance, FunctionFuture):
                node_instance.args = _AttributeToConnection()(
                    node_instance.args, node_instance=node_instance, graph=self
                )
                node_instance.kwargs = _AttributeToConnection()(
                    node_instance.kwargs, node_instance=node_instance, graph=self
                )
            elif isinstance(node_instance, Node):
                for attribute in dir(node_instance):
                    if attribute.startswith("_") or attribute in Node._protected_:
                        continue
                    value = getattr(node_instance, attribute)
                    setattr(
                        node_instance,
                        attribute,
                        _AttributeToConnection()(
                            value, node_instance=node_instance, graph=self, v_attr=attribute
                        ),
                    )

    def add_node(self, node_for_adding, **attr):
        if len(attr):
            raise ValueError("Attributes are not supported for Nodes.")
        # TODO what if it is a list of nodes?
        if isinstance(node_for_adding, NodeBaseMixin):
            super().add_node(node_for_adding.uuid, value=node_for_adding, **attr)
        else:
            raise ValueError("Only Nodes are supported.")
            # super().add_node(node_for_adding, **attr)

    def add_edge(self, u_of_edge, v_of_edge, **attr):
        if isinstance(u_of_edge, Connection) and isinstance(v_of_edge, NodeBaseMixin):
            assert u_of_edge.uuid in self, f"'{u_of_edge.uuid=}' not in '{self=}'"
            assert v_of_edge.uuid in self, f"'{v_of_edge.uuid=}' not in '{self=}'"
            super().add_edge(
                u_of_edge.uuid,
                v_of_edge.uuid,
                u_attr=u_of_edge.attribute,
                **attr,
            )
        else:
            super().add_edge(u_of_edge, v_of_edge, **attr)
