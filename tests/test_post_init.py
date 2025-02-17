import dataclasses
import typing as t

import znflow


@dataclasses.dataclass
class NodeWithPostInit(znflow.Node):
    input: int
    output: t.Optional[int] = None

    def __post_init__(self):
        self.input = self.input * 2

    def run(self):
        self.output = self.input + 1


def test_post_init():
    graph = znflow.DiGraph()

    with graph:
        node = NodeWithPostInit(input=10)

    assert node.input == 20

    graph.run()

    assert node.output == 21
    assert node.input == 20
