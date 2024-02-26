import dataclasses
import znflow
from znflow import node

@dataclasses.dataclass
class AddOne(znflow.Node):
    inputs: int
    outputs: int = None

    def run(self):
        self.outputs = self.inputs + 1

def test_update_after_exit():
    graph = znflow.DiGraph()
    with graph:
        node1 = AddOne(inputs=1)

    node1.inputs = 2
    graph.run(immutable_nodes=False)
    assert node1.outputs == 3

    node1.inputs = 3
    graph.run(immutable_nodes=False)
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
