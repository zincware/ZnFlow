import logging

import networkx as nx

from znflow import utils
from znflow.base import Connection, FunctionFuture, NodeBaseMixin, get_graph, set_graph
from znflow.node import Node

log = logging.getLogger(__name__)


class _AttributeToConnection(utils.IterableHandler):
    def default(self, value, **kwargs):
        v_attr = kwargs.get("v_attr")
        node_instance = kwargs["node_instance"]
        graph = kwargs["graph"]

        if isinstance(value, FunctionFuture):
            connection = Connection(value, attribute="result")
            if v_attr is None:
                graph.add_connections(connection, node_instance)
            else:
                graph.add_connections(connection, node_instance, v_attr=v_attr)

            return connection
        elif isinstance(value, Node):
            connection = Connection(value, attribute=None)
            if v_attr is None:
                graph.add_connections(connection, node_instance)
            else:
                graph.add_connections(connection, node_instance, v_attr=v_attr)
            return connection
        elif isinstance(value, Connection):
            if v_attr is None:
                graph.add_connections(value, node_instance)
            else:
                graph.add_connections(value, node_instance, v_attr=v_attr)
            return value
        return value


class _UpdateConnectors(utils.IterableHandler):
    def default(self, value, **kwargs):
        if isinstance(value, Connection):
            return value.result
        return value


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
            log.debug(f"Node {node} ({node_instance}) was added to the graph.")
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
                    updater = _AttributeToConnection()
                    value = updater(
                        getattr(node_instance, attribute),
                        node_instance=node_instance,
                        graph=self,
                        v_attr=attribute,
                    )
                    if updater.updated:
                        setattr(node_instance, attribute, value)

    def add_node(self, node_for_adding, **attr):
        if isinstance(node_for_adding, NodeBaseMixin):
            super().add_node(node_for_adding.uuid, value=node_for_adding, **attr)
        else:
            raise ValueError("Only Nodes are supported.")

    def add_connections(self, u_of_edge, v_of_edge, **attr):
        log.debug(f"Add edge between {u_of_edge=} and {v_of_edge=}.")
        if isinstance(u_of_edge, Connection) and isinstance(v_of_edge, NodeBaseMixin):
            assert u_of_edge.uuid in self, f"'{u_of_edge.uuid=}' not in '{self=}'"
            assert v_of_edge.uuid in self, f"'{v_of_edge.uuid=}' not in '{self=}'"
            self.add_edge(
                u_of_edge.uuid,
                v_of_edge.uuid,
                u_attr=u_of_edge.attribute,
                **attr,
            )
        else:
            raise ValueError("Only Connections and Nodes are supported.")

    def get_sorted_nodes(self):
        all_pipelines = []
        for stage in self.reverse():
            all_pipelines += nx.dfs_postorder_nodes(self.reverse(), stage)
        return list(dict.fromkeys(all_pipelines))  # remove duplicates but keep order

    def run(self):
        for node_uuid in self.get_sorted_nodes():
            node = self.nodes[node_uuid]["value"]
            # update connectors
            for attribute in dir(node):
                if attribute.startswith("_") or attribute in Node._protected_:
                    continue
                value = getattr(node, attribute)
                setattr(
                    node,
                    attribute,
                    _UpdateConnectors()(
                        value,
                    ),
                )
            node.run()

    def write_graph(self, *args):
        for node in args:
            if isinstance(node, (list, tuple)):
                self.write_graph(*node)
            else:
                self.add_node(node)
        with self:
            pass
