"""ZnFlow deployment using Dask."""

import dataclasses
import typing
import typing as t
import uuid

from dask.distributed import Client, Future, wait

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


@dataclasses.dataclass
class DaskDeployment(DeploymentBase):
    client: Client = dataclasses.field(default_factory=Client)
    results: typing.Dict[uuid.UUID, Future] = dataclasses.field(
        default_factory=dict, init=False
    )

    def run(self, nodes: t.Optional[list] = None):
        if nodes is None:
            for node_uuid in self.graph.reverse():
                assert self.graph.immutable_nodes
                node = self.graph.nodes[node_uuid]["value"]
                predecessors = list(self.graph.predecessors(node.uuid))

                if len(predecessors) == 0:
                    if node.uuid not in self.results:
                        self.results[node.uuid] = self.client.submit(  # TODO how to name
                            node_submit, node=node, pure=False
                        )
                else:
                    if node.uuid not in self.results:
                        self.results[node.uuid] = self.client.submit(
                            node_submit,
                            node=node,
                            predecessors={
                                x: self.results[x]
                                for x in self.results
                                if x in predecessors
                            },
                            pure=False,
                        )
            # load the results when done
            for node_uuid in self.graph.reverse():
                node = self.graph.nodes[node_uuid]["value"]
                future = self.results[node.uuid]
                print(future.result())
                if isinstance(node, Node):
                    node.__dict__.update(self.results[node.uuid].result().__dict__)
                    self.graph._update_node_attributes(node, handler.UpdateConnectors())
                else:
                    node.result = self.results[node.uuid].result().result

        else:
            for node_uuid in self.graph.reverse():
                assert self.graph.immutable_nodes
                node = self.graph.nodes[node_uuid]["value"]
                if node in nodes:
                    predecessors = list(self.graph.predecessors(node.uuid))

                    if len(predecessors) == 0:
                        if node.uuid not in self.results:
                            self.results[node.uuid] = self.client.submit(  # TODO how to name
                                node_submit, node=node, pure=False
                            )
                    else:
                        if node.uuid not in self.results:
                            for predecessor in predecessors:
                                # submit the predecessors first
                                _node = self.graph.nodes[predecessor]["value"]
                                if _node.uuid not in self.results:
                                    self.results[predecessor] = self.client.submit(
                                        node_submit, node=_node, pure=False
                                    )

                            self.results[node.uuid] = self.client.submit(
                                node_submit,
                                node=node,
                                predecessors={
                                    x: self.results[x]
                                    for x in self.results
                                    if x in predecessors
                                },
                                pure=False,
                            )
            # load the results when done
            for node_uuid in self.graph.reverse():
                node = self.graph.nodes[node_uuid]["value"]
                try:
                    future = self.results[node.uuid]
                    print(future.result())
                    if isinstance(node, Node):
                        node.__dict__.update(self.results[node.uuid].result().__dict__)
                        self.graph._update_node_attributes(node, handler.UpdateConnectors())
                    else:
                        node.result = self.results[node.uuid].result().result
                except KeyError:
                    pass
