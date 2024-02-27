import abc
import typing as t

if t.TYPE_CHECKING:
    from znflow.graph import DiGraph


class DeploymentBase(abc.ABC):
    graph: "DiGraph"

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

    def set_graph(self, graph: "DiGraph"):
        self.graph = graph

    @abc.abstractmethod
    def _run_node(self, node, node_uuid):
        pass

    @abc.abstractmethod
    def _run_predecessors(self, node_uuid):
        pass
