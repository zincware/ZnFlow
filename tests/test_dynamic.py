import dataclasses

import znflow


@dataclasses.dataclass
class AddOne(znflow.Node):
    inputs: float
    outputs: float = None

    def run(self):
        self.outputs = self.inputs + 1


def test_break_loop():
    graph = znflow.DiGraph()
    with graph:
        node1 = AddOne(inputs=1)
        for _ in range(10):
            node1 = AddOne(inputs=node1.outputs)
            if znflow.resolve(node1.outputs) > 5:
                break

    graph.run()
    assert len(graph) == 5
    assert node1.outputs == 6
