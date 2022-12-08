"""Test the 'znflow.DiGraph' class."""
import znflow


@znflow.nodify
def add(*args):
    """Add node."""
    return sum(args)


class ComputeSum(znflow.Node):
    """Compute sum node."""

    inputs: list = znflow.EdgeAttribute()
    outputs: float = znflow.EdgeAttribute(None)

    def run(self):
        """run method."""
        self.outputs = sum(self.inputs)


# def test_repeat_function():
#     with znflow.DiGraph():
#         add(1, 2, 3)
#         add(4, 5, 6)
#         with pytest.raises(ValueError):
#             add(1, 2, 3)
#         with pytest.raises(ValueError):
#             add(4, 5, 6)
#
#
# def test_repeat_node():
#     with znflow.DiGraph():
#         ComputeSum(inputs=[1, 2, 3])
#         ComputeSum(inputs=[4, 5, 6])
#         with pytest.raises(ValueError):
#             ComputeSum(inputs=[1, 2, 3])
#         with pytest.raises(ValueError):
#             ComputeSum(inputs=[4, 5, 6])


def test_combine_nodes():
    with znflow.DiGraph() as dag:
        n1 = ComputeSum(inputs=(1, 2, 3))
        n2 = ComputeSum(inputs=(4, 5, 6))
        n3 = ComputeSum(inputs=(n1.outputs, n2.outputs))

    dag.run()

    assert n3.outputs == 21
