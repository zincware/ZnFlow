"""Test the 'znflow.DiGraph' class."""
import znflow


@znflow.nodify
def add(*args):
    """Add node."""
    return sum(args)


class ComputeSum(znflow.Node):
    """Compute sum node."""

    def __init__(self, inputs):
        self.inputs = inputs
        self.outputs = None

    def run(self):
        """run method."""
        self.outputs = sum(self.inputs)


def test_combine_nodes():
    with znflow.DiGraph() as graph:
        n1 = ComputeSum(inputs=(1, 2, 3))
        n2 = ComputeSum(inputs=(4, 5, 6))
        n3 = ComputeSum(inputs=(n1.outputs, n2.outputs))

    graph.run()

    assert n3.outputs == 21
