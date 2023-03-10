import dataclasses

import pytest

import znflow


@dataclasses.dataclass
class Node(znflow.Node):
    inputs: float
    outputs: float = None

    def run(self):
        self.outputs = self.inputs * 2


@dataclasses.dataclass
class SumNodes(znflow.Node):
    inputs: list
    outputs: float = None

    def run(self):
        self.outputs = sum(self.inputs)


@dataclasses.dataclass
class SumNodesFromDict(znflow.Node):
    inputs: dict
    outputs: float = None

    def run(self):
        self.outputs = sum(self.inputs.values())


def test_eager():
    node = Node(inputs=1)
    node.run()
    assert node.outputs == 2


def test_graph():
    with znflow.DiGraph() as graph:
        node = Node(inputs=1)

    graph.run()
    assert node.outputs == 2


def test_eager_connect():
    node = Node(inputs=1)
    node.run()
    node2 = Node(inputs=node.outputs)
    node2.run()
    assert node2.outputs == 4


def test_graph_connect():
    with znflow.DiGraph() as graph:
        node = Node(inputs=1)
        node2 = Node(inputs=node.outputs)

    graph.run()
    assert node2.outputs == 4


def test_eager_multi():
    node1 = Node(inputs=5)
    node1.run()
    node2 = Node(inputs=10)
    node2.run()
    node3 = Node(inputs=node1.outputs)
    node3.run()
    node4 = Node(inputs=node2.outputs)
    node4.run()
    node5 = SumNodes(inputs=[node3.outputs, node4.outputs])
    node5.run()
    node6 = SumNodes(inputs=[node2.outputs, node5.outputs])
    node6.run()
    node7 = SumNodes(inputs=[node6.outputs])
    node7.run()

    assert node7.outputs == 80


@pytest.mark.parametrize("size", range(1, 10))
def test_graph_size(size: int):
    with znflow.DiGraph() as graph:
        [Node(inputs=i) for i in range(size)]

    assert len(graph) == size


@pytest.mark.parametrize("size", range(1, 10))
def test_graph_size_connected(size: int):
    with znflow.DiGraph() as graph:
        nodes = [Node(inputs=i) for i in range(size - 1)]
        _ = SumNodes(inputs=[n.outputs for n in nodes])

    assert len(graph) == size


def test_graph_multi():
    with znflow.DiGraph() as graph:
        node1 = Node(inputs=5)
        node2 = Node(inputs=10)
        node3 = Node(inputs=node1.outputs)
        node4 = Node(inputs=node2.outputs)
        node5 = SumNodes(inputs=[node3.outputs, node4.outputs])
        node6 = SumNodes(inputs=[node2.outputs, node5.outputs])
        node7 = SumNodes(inputs=[node6.outputs])

        assert isinstance(node6.outputs, znflow.Connection)
    graph.run()

    assert node7.outputs == 80


def test_SumNodesFromDict():
    with znflow.DiGraph() as graph:
        node1 = Node(inputs=5)
        node2 = Node(inputs=10)
        node3 = SumNodesFromDict(inputs={"a": node1.outputs, "b": node2.outputs})
    graph.run()

    assert node3.outputs == 30
