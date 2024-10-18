import dataclasses

from znflow import utils
from znflow.base import CombinedConnections, Connection, FunctionFuture
from znflow.node import Node


class AttributeToConnection(utils.IterableHandler):
    def default(self, value):
        if not isinstance(value, (FunctionFuture, Node)):
            return value
        return (
            value if value._graph_ is None else Connection(instance=value, attribute=None)
        )


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


class LoadNodeFromDeploymentResults(utils.IterableHandler):
    """Iterable handler for loading nodes."""

    def default(self, value, **kwargs):
        """Default handler for loading nodes.

        Parameters
        ----------
        value: any
            the value to be loaded from the results dict
        kwargs: dict
            results: results dictionary of {uuid: Future} shape.
        """
        results = kwargs["results"]

        if isinstance(value, Node):
            # results: dict[uuid, DaskFuture]
            return results[value.uuid].result()
        elif isinstance(value, (FunctionFuture, CombinedConnections, Connection)):
            return results[value.uuid].result().result
        else:
            return value


class UpdateConnectionsWithPredecessor(utils.IterableHandler):
    """Iterable handler for replacing connections."""

    def default(self, value, **kwargs):
        """Replace connections by its values.

        Parameters
        ----------
        value: Connection|any
            If a Connection, the connection will be replaced by its result.
        kwargs: dict
            predecessors: dict of {uuid: Connection} shape.

        Returns
        -------
        any:
            If a Connection, the connection will be replaced by its result.
            Otherwise, the input value is returned.

        """
        predecessors = kwargs["predecessors"]
        if isinstance(value, Connection):
            # We don't actually need the connection, we need the results.
            return dataclasses.replace(value, instance=predecessors[value.uuid]).result
        return value
