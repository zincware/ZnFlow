import dataclasses
import typing as t

from znflow import handler

from .base import DeploymentBase


@dataclasses.dataclass
class VanillaDeployment(DeploymentBase):

    def run(self, nodes: t.Optional[t.List] = None):
        for node_uuid in self.graph.get_sorted_nodes():
            node = self.graph.nodes[node_uuid]["value"]
            node_available = self.graph.nodes[node_uuid].get("available", False)

            if self.graph.immutable_nodes and node_available:
                continue

            if nodes is None and not node._external_:
                self._run_node(node, node_uuid)
            elif nodes is not None and node in nodes:
                self._run_predecessors(node_uuid)
                self._run_node(node, node_uuid)

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