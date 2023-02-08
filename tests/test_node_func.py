import dataclasses
import random

import znflow


@znflow.nodify
def random_number(seed):
    random.seed(seed)
    print(f"Get random number with {seed = }")
    return random.random()


@dataclasses.dataclass
class ComputeSum(znflow.Node):
    inputs: list
    outputs: float = None

    def run(self):
        self.outputs = sum(self.inputs)


def test_eager():
    n1 = random_number(5)
    n2 = random_number(10)

    compute_sum = ComputeSum(inputs=[n1, n2])
    compute_sum.run()
    n3 = random_number(compute_sum.outputs)
    assert n3 == 0.2903973544626711


def test_graph():
    with znflow.DiGraph() as graph:
        n1 = random_number(5)
        n2 = random_number(10)
        compute_sum = ComputeSum(inputs=[n1, n2])
        n3 = random_number(compute_sum.outputs)

    graph.run()
    assert n3.result == 0.2903973544626711
