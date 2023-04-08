"""ZnFlow deployment using Dask."""

import dataclasses
import typing
import uuid

from dask.distributed import Client, Future
from networkx.classes.reportviews import NodeView

from znflow.graph import DiGraph
from znflow.handler import (
    LoadNodeFromDeploymentResults,
    UpdateConnectionsWithPredecessor,
)
from znflow.node import Node


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


@dataclasses.dataclass
class Deployment:
    """ZnFlow deployment using Dask.

    Attributes
    ----------
    graph: DiGraph
        the znflow graph containing the nodes.
    client: Client, optional
        the Dask client.
    results: Dict[uuid, Future]
        a dictionary of {uuid: Future} shape that is filled after the graph is submitted.

    """

    graph: DiGraph
    client: Client = dataclasses.field(default_factory=Client)
    results: typing.Dict[uuid.UUID, Future] = dataclasses.field(
        default_factory=dict, init=False
    )

    def submit_graph(self):
        """Submit the graph to Dask.

        When submitting to Dask, a Node is serialized, processed and a
        copy can be returned.

        This requires:
        - the connections to be updated to the respective Nodes coming from Dask futures.
        - the Node to be returned from the workers and passed to all successors.
        """
        for node_uuid in self.graph.reverse():
            node = self.graph.nodes[node_uuid]["value"]
            predecessors = list(self.graph.predecessors(node.uuid))

            if len(predecessors) == 0:
                self.results[node.uuid] = self.client.submit(  # TODO how to name
                    node_submit, node=node, pure=False
                )
            else:
                self.results[node.uuid] = self.client.submit(
                    node_submit,
                    node=node,
                    predecessors={
                        x: self.results[x] for x in self.results if x in predecessors
                    },
                    pure=False,
                )

    def get_results(self, obj: typing.Union[Node, list, dict, NodeView], /):
        """Get the results from Dask based on the original object.

        Parameters
        ----------
        obj: any
            either a single Node or multiple Nodes from the submitted graph.

        Returns
        -------
        any:
            Returns an instance of obj which is updated with the results from Dask.

        """
        if isinstance(obj, NodeView):
            data = LoadNodeFromDeploymentResults()(dict(obj), results=self.results)
            return {x: v["value"] for x, v in data.items()}
        elif isinstance(obj, DiGraph):
            raise NotImplementedError
        return LoadNodeFromDeploymentResults()(obj, results=self.results)
