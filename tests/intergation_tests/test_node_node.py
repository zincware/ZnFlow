import pytest

import znflow


class Node(znflow.Node):
    inputs = znflow.EdgeAttribute()
    outputs = znflow.EdgeAttribute(None)

    def run(self):
        self.outputs = self.inputs * 2


class SumNodes(znflow.Node):
    inputs = znflow.EdgeAttribute()
    outputs = znflow.EdgeAttribute(None)

    def run(self):
        self.outputs = sum(self.inputs)


def test_eager():
    node = Node(inputs=1)
    node.run()
    assert node.outputs == 2


def test_graph():
    with znflow.DiGraph() as dag:
        node = Node(inputs=1)

    dag.run()
    assert node.outputs == 2


def test_eager_connect():
    node = Node(inputs=1)
    node.run()
    node2 = Node(inputs=node.outputs)
    node2.run()
    assert node2.outputs == 4


def test_graph_connect():
    with znflow.DiGraph() as dag:
        node = Node(inputs=1)
        node2 = Node(inputs=node.outputs)

    dag.run()
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
    with znflow.DiGraph() as dag:
        [Node(inputs=i) for i in range(size)]

    assert len(dag) == size


# @pytest.mark.parametrize("size", range(1, 10))
# def test_graph_size_connected(size: int):
#     with znflow.DiGraph() as graph:
#         nodes = [Node(inputs=i) for i in range(size - 1)]
#         _ = SumNodes(inputs=[n.outputs for n in nodes])
#
#     assert len(graph) == size


def test_graph_multi():
    with znflow.DiGraph() as dag:
        node1 = Node(inputs=5)
        node2 = Node(inputs=10)
        node3 = Node(inputs=node1.outputs)
        node4 = Node(inputs=node2.outputs)
        node5 = SumNodes(inputs=[node3.outputs, node4.outputs])
        node6 = SumNodes(inputs=[node2.outputs, node5.outputs])
        node7 = SumNodes(inputs=[node6.outputs])
    dag.run()

    assert node7.outputs == 80
