import dataclasses
import typing as t

from znflow import handler

from .base import DeploymentBase


@dataclasses.dataclass
class VanillaDeployment(DeploymentBase):

    def _run_node(self, node, node_uuid):
        self.graph._update_node_attributes(node, handler.UpdateConnectors())
        node.run()
        if self.graph.immutable_nodes:
            self.graph.nodes[node_uuid]["available"] = True

    def _run_predecessors(self, node_uuid):
        predecessors = list(self.graph.predecessors(node_uuid))
        for predecessor in predecessors:
            predecessor_node = self.graph.nodes[predecessor]["value"]
            predecessor_available = self.graph.nodes[predecessor].get("available", False)

            if not (self.graph.immutable_nodes and predecessor_available):
                self._run_node(predecessor_node, predecessor)
