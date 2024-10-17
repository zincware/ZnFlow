import dataclasses

from znflow import handler

from .base import DeploymentBase


@dataclasses.dataclass
class VanillaDeployment(DeploymentBase):
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
            return

        self.graph._update_node_attributes(node, handler.UpdateConnectors())
        node.run()
        self.graph.nodes[node_uuid]["available"] = True
