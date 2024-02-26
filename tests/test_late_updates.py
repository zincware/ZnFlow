import dataclasses

import znflow


@dataclasses.dataclass
class AddOne(znflow.Node):
    inputs: int
    outputs: int = None

    def run(self):
        self.outputs = self.inputs + 1


def test_update_after_exit():
    graph = znflow.DiGraph(immutable_nodes=False)
    with graph:
        node1 = AddOne(inputs=1)

    node1.inputs = 2
    graph.run()
    assert node1.outputs == 3

    node1.inputs = 3
    graph.run()
    assert node1.outputs == 4


def test_update_after_exit_immutable():
    graph = znflow.DiGraph()
    with graph:
        node1 = AddOne(inputs=1)

    node1.inputs = 2
    graph.run()
    assert node1.outputs == 3

    node1.inputs = 3
    graph.run()
    assert node1.outputs == 3
