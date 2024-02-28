import abc
import typing as t

if t.TYPE_CHECKING:
    from znflow.graph import DiGraph


class DeploymentBase(abc.ABC):
    graph: "DiGraph"

    def run(self, nodes: t.Optional[t.List] = None):
        if nodes is None:
            nodes = self.graph.get_sorted_nodes()
        else:
            # convert nodes to UUIDs
            nodes = [node.uuid for node in nodes]

        for node_uuid in nodes:
            node_available = self.graph.nodes[node_uuid].get("available", False)
            if self.graph.immutable_nodes and node_available:
                continue
            self._run_node(node_uuid)

    def set_graph(self, graph: "DiGraph"):
        self.graph = graph

    @abc.abstractmethod
    def _run_node(self, node_uuid):
        pass
