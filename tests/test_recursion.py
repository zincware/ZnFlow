import znflow
import pytest


class AddOne(znflow.Node):
    def __init__(self, x):
        super().__init__()
        self.x = x

    def run(self):
        self.x += 1


@pytest.mark.parametrize("depth", [1, 10, 100, 1000])
def test_AddOneLoop(depth):
    with znflow.DiGraph() as graph:
        start = AddOne(0)
        for _ in range(depth):
            start = AddOne(start.x)

    graph.run()
    assert len(graph.nodes) == depth + 1
    assert start.x == depth + 1
