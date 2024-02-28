"""ZnFlow deployment using Dask."""

import dataclasses
import typing
import typing as t
import uuid

from dask.distributed import Client, Future

from znflow import handler
from znflow.handler import UpdateConnectionsWithPredecessor
from znflow.node import Node

from .base import DeploymentBase

if typing.TYPE_CHECKING:
    pass


def node_submit(node, **kwargs):
    """Submit script for Dask worker.

    Parameters
    ----------
    node: any
        the Node class
    kwargs: dict
        predecessors: dict of {uuid: Connection} shape

    Returns
    -------
    any:
        the Node class with updated state (after calling "Node.run").

    """
    predecessors = kwargs.get("predecessors", {})
    updater = UpdateConnectionsWithPredecessor()
    for item in dir(node):
        # TODO this information is available in the graph,
        #  no need to expensively iterate over all attributes
        if item.startswith("_"):
            continue
        value = updater(getattr(node, item), predecessors=predecessors)
        if updater.updated:
            setattr(node, item, value)

    node.run()
    return node


# TODO: release the future objects
@dataclasses.dataclass
class DaskDeployment(DeploymentBase):
    client: Client = dataclasses.field(default_factory=Client)
    results: typing.Dict[uuid.UUID, Future] = dataclasses.field(
        default_factory=dict, init=False
    )

    def run(self, nodes: t.Optional[list] = None):
        super().run(nodes)
        self._load_results()

    def _run_node(self, node_uuid):
        node = self.graph.nodes[node_uuid]["value"]
        predecessors = list(self.graph.predecessors(node_uuid))
        for predecessor in predecessors:
            predecessor_available = self.graph.nodes[predecessor].get("available", False)
            if self.graph.immutable_nodes and predecessor_available:
                continue
            self._run_node(predecessor)

        node_available = self.graph.nodes[node_uuid].get("available", False)
        if self.graph.immutable_nodes and node_available:
            return
        if node._external_:
            raise NotImplementedError(
                "External nodes are not supported in Dask deployment"
            )

        self.results[node_uuid] = self.client.submit(
            node_submit,
            node=node,
            predecessors={x: self.results[x] for x in self.results if x in predecessors},
            pure=False,
            key=f"{node.__class__.__name__}-{node_uuid}",
        )
        self.graph.nodes[node_uuid]["available"] = True

    def _load_results(self):
        # TODO: only load nodes that have actually changed
        for node_uuid in self.graph.reverse():
            node = self.graph.nodes[node_uuid]["value"]
            try:
                result = self.results[node.uuid].result()
                if isinstance(node, Node):
                    node.__dict__.update(result.__dict__)
                    self.graph._update_node_attributes(node, handler.UpdateConnectors())
                else:
                    node.result = result.result
            except KeyError:
                pass
