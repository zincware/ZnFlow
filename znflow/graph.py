import functools
import logging
import typing

import networkx as nx

from znflow import handler
from znflow.base import (
    Connection,
    FunctionFuture,
    NodeBaseMixin,
    empty,
    get_graph,
    set_graph,
)
from znflow.node import Node

log = logging.getLogger(__name__)


class DiGraph(nx.MultiDiGraph):
    def __init__(self, *args, disable=False, **kwargs):
        self.disable = disable
        super().__init__(*args, **kwargs)

    @property
    def add_connections_from_iterable(self) -> typing.Callable:
        """Get a function that adds connections to the graph.

        Return a AddConnectionToGraph class with this Graph instance attached.
        """
        return functools.partial(handler.AddConnectionToGraph(), graph=self)

    def __enter__(self):
        if self.disable:
            return self
        if get_graph() is not empty:
            raise ValueError("DiGraph already exists. Nested Graphs are not supported.")
        set_graph(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.disable:
            return
        if get_graph() is not self:
            raise ValueError(
                "Something went wrong. DiGraph was changed inside the context manager."
            )
        set_graph(empty)
        for node in self.nodes:
            node_instance = self.nodes[node]["value"]
            log.debug(f"Node {node} ({node_instance}) was added to the graph.")
            if isinstance(node_instance, FunctionFuture):
                self._update_function_future_arguments(node_instance)
            elif isinstance(node_instance, Node):
                # TODO only update Nodes if the graph is not empty
                self._update_node_attributes(
                    node_instance, handler.AttributeToConnection()
                )

    def _update_function_future_arguments(self, node_instance: FunctionFuture) -> None:
        """Apply an update to args and kwargs of a FunctionFuture."""
        node_instance.args = handler.AttributeToConnection()(node_instance.args)
        node_instance.kwargs = handler.AttributeToConnection()(node_instance.kwargs)
        self.add_connections_from_iterable(
            node_instance.args, node_instance=node_instance
        )
        self.add_connections_from_iterable(
            node_instance.kwargs, node_instance=node_instance
        )

    def _update_node_attributes(self, node_instance: Node, updater) -> None:
        """Apply an updater to all attributes of a node."""
        for attribute in dir(node_instance):
            if attribute.startswith("_") or attribute in Node._protected_:
                # We do not allow connections to private attributes.
                continue
            if isinstance(getattr(type(node_instance), attribute, None), property):
                # We do not want to call getter of properties.
                continue
            try:
                value = getattr(node_instance, attribute)
            except Exception:
                # It might be, that the value is currently not available.
                #  For example, it could be a property that is not yet set.
                #  In this case we skip updating the attribute, no matter the exception.
                continue
            value = updater(value)
            if updater.updated:
                try:
                    setattr(node_instance, attribute, value)
                except AttributeError:
                    continue
            self.add_connections_from_iterable(
                value, node_instance=node_instance, attribute=attribute
            )

    def add_node(self, node_for_adding, **attr):
        if isinstance(node_for_adding, NodeBaseMixin):
            super().add_node(node_for_adding.uuid, value=node_for_adding, **attr)
        else:
            raise ValueError("Only Nodes are supported.")

    def add_connections(self, u_of_edge, v_of_edge, **attr):
        log.debug(f"Add edge between {u_of_edge=} and {v_of_edge=}.")
        if isinstance(u_of_edge, Connection) and isinstance(v_of_edge, NodeBaseMixin):
            if u_of_edge.uuid not in self:
                raise ValueError(
                    f"The source node (uuid={u_of_edge.uuid}, connection={u_of_edge}) is"
                    " not in the graph."
                )
            if (
                v_of_edge.uuid not in self
            ):  # this might be impossible to reach. Let me know if you found a way.
                raise ValueError(
                    f"The target node (uuid={v_of_edge.uuid}, connection={v_of_edge}) is"
                    " not in the graph."
                )

            # TODO what if 'v_attr' is a list/dict/... that contains multiple connections?
            #  Is this relevant? We could do `v_attr.<dict_key>` or `v_attr.<list_index>`
            #  See test_node.test_ListConnection and test_node.test_DictionaryConnection
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
        reverse = self.reverse(copy=False)
        for stage in reverse:
            all_pipelines += nx.dfs_postorder_nodes(reverse, stage)
        return list(dict.fromkeys(all_pipelines))  # remove duplicates but keep order

    def run(self):
        for node_uuid in self.get_sorted_nodes():
            node = self.nodes[node_uuid]["value"]
            # update connectors
            self._update_node_attributes(node, handler.UpdateConnectors())
            node.run()

    def write_graph(self, *args):
        for node in args:
            if isinstance(node, (list, tuple)):
                self.write_graph(*node)
            else:
                self.add_node(node)
        with self:
            pass
