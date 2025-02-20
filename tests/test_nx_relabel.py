import dataclasses

import networkx as nx

import znflow


@dataclasses.dataclass
class DataclassNode(znflow.Node):
    value: int
    _primary_key = "name"
    _protected_ = znflow.Node._protected_ + ["name"]

    def __post_init__(self):
        if "custom" not in self._graph_:
            nx.relabel_nodes(self._graph_, {self.uuid: "custom"}, copy=False)
            self.__dict__["name"] = "custom"

    def run(self):
        self.value += 1

    @property
    def name(self):
        return self.__dict__.get("name", self.uuid)


def test_nx_relabel_nodes():
    graph = znflow.DiGraph()

    with graph:
        a = DataclassNode(value=42)
        b = DataclassNode(value=a.value)  # testing the connection

    assert "custom" in graph
    assert b.uuid in graph
    assert a.uuid not in graph
    assert len(graph) == 2
