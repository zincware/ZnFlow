from znflow import utils
from znflow.base import CombinedConnections, Connection, FunctionFuture
from znflow.node import Node


class AttributeToConnection(utils.IterableHandler):
    def default(self, value):
        if not isinstance(value, (FunctionFuture, Node)):
            return value
        return value if value._graph_ is None else Connection(value, attribute=None)


class AddConnectionToGraph(utils.IterableHandler):
    def default(self, value, **kwargs):
        if isinstance(value, Connection):
            graph = kwargs["graph"]
            v_attr = kwargs.get("attribute")
            node_instance = kwargs["node_instance"]
            if v_attr is None:
                graph.add_connections(value, node_instance)
            else:
                graph.add_connections(value, node_instance, v_attr=v_attr)


class UpdateConnectors(utils.IterableHandler):
    def default(self, value, **kwargs):
        if isinstance(value, (Connection, CombinedConnections)):
            return value.result
        else:
            return value
