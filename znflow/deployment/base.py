import abc
import typing as t

if t.TYPE_CHECKING:
    from znflow.graph import DiGraph


class DeploymentBase(abc.ABC):
    graph: "DiGraph"

    def run(self, nodes: t.Optional[t.List] = None):
        # nodes = self.graph.get_sorted_nodes()
        if nodes is None:
            nodes = self.graph.get_sorted_nodes()
        else:
            # Apparently, we don't need to look for
            # parent nodes, because when running
            # a node this is done automatically
            nodes = [node.uuid for node in nodes]

        for node_uuid in nodes:
            self._run_node(node_uuid)

    def set_graph(self, graph: "DiGraph"):
        self.graph = graph

    @abc.abstractmethod
    def _run_node(self, node_uuid):
        pass
