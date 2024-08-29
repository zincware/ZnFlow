"""Test for raising an error when building a graph."""

import dataclasses

import znflow


@dataclasses.dataclass
class MyNode(znflow.Node):
    value: int

    def run(self):
        pass


def test_graph_build_exception():
    graph = znflow.DiGraph()

    try:
        with graph:
            node = MyNode(value=42)
            raise ValueError("This is a test")
    except ValueError:
        pass

    assert node.uuid in graph


def test_group_build_exception():
    graph = znflow.DiGraph()

    try:
        with graph.group("group") as grp:
            node = MyNode(value=42)
            raise ValueError("This is a test")
    except ValueError:
        pass

    assert node.uuid in graph
    assert node.uuid in grp
