import dataclasses
import typing as t

from znflow import handler

if t.TYPE_CHECKING:
    from znflow.graph import DiGraph


@dataclasses.dataclass
class VanillaDeployment:
    graph: "DiGraph"

    def run(self, nodes: t.Optional[t.List] = None):
        for node_uuid in self.graph.get_sorted_nodes():
            if self.graph.immutable_nodes and self.graph.nodes[node_uuid].get(
                "available", False
            ):
                continue
            node = self.graph.nodes[node_uuid]["value"]
            if nodes is None:
                if not node._external_:
                    self.graph._update_node_attributes(node, handler.UpdateConnectors())
                    node.run()
                    if self.graph.immutable_nodes:
                        self.graph.nodes[node_uuid]["available"] = True
            else:
                if node in nodes:
                    predecessors = list(self.graph.predecessors(node_uuid))
                    for predecessor in predecessors:
                        predecessor_node = self.graph.nodes[predecessor]["value"]
                        if self.graph.immutable_nodes and self.graph.nodes[
                            predecessor
                        ].get("available", False):
                            continue
                        self.graph._update_node_attributes(
                            predecessor_node, handler.UpdateConnectors()
                        )
                        predecessor_node.run()
                        if self.graph.immutable_nodes:
                            self.graph.nodes[predecessor]["available"] = True
                    self.graph._update_node_attributes(node, handler.UpdateConnectors())
                    node.run()
                    if self.graph.immutable_nodes:
                        self.graph.nodes[node_uuid]["available"] = True
