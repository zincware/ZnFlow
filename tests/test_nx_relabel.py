import dataclasses

import networkx as nx

import znflow


@dataclasses.dataclass
class DataclassNode(znflow.Node):
    value: int

    def run(self):
        self.value += 1


def test_nx_relabel_nodes():
    graph = znflow.DiGraph()

    with graph:
        node = DataclassNode(value=42)

    assert node.uuid in graph
    nx.relabel_nodes(graph, {node.uuid: "custom"}, copy=False)
    assert "custom" in graph
    assert node.uuid not in graph
