import dataclasses

import numpy as np
import pytest

import znflow


@znflow.nodify
def compute_sum(*args):
    return sum(args)


@dataclasses.dataclass
class ComputeSum(znflow.Node):
    inputs: list
    outputs: float = None

    def run(self):
        # this will just call the function compute_sum and won't construct a graph!
        self.outputs = compute_sum(*self.inputs)


@znflow.nodify
def add_to_ComputeSum(instance: ComputeSum):
    return instance.outputs + 1


@pytest.mark.parametrize(
    "depl", [znflow.deployment.VanillaDeployment(), znflow.deployment.DaskDeployment()]
)
def test_single_nodify(depl):

    with znflow.DiGraph(deployment=depl) as graph:
        node1 = compute_sum(1, 2, 3)

    graph.run()

    assert node1.result == 6


@pytest.mark.parametrize(
    "depl", [znflow.deployment.VanillaDeployment(), znflow.deployment.DaskDeployment()]
)
def test_single_Node(depl):

    with znflow.DiGraph(deployment=depl) as graph:
        node1 = ComputeSum(inputs=[1, 2, 3])

    graph.run()
    assert node1.outputs == 6


@pytest.mark.parametrize(
    "depl", [znflow.deployment.VanillaDeployment(), znflow.deployment.DaskDeployment()]
)
def test_multiple_nodify(depl):

    with znflow.DiGraph(deployment=depl) as graph:
        node1 = compute_sum(1, 2, 3)
        node2 = compute_sum(4, 5, 6)
        node3 = compute_sum(node1, node2)

    graph.run()

    assert node1.result == 6
    assert node2.result == 15
    assert node3.result == 21


@pytest.mark.parametrize(
    "depl", [znflow.deployment.VanillaDeployment(), znflow.deployment.DaskDeployment()]
)
def test_multiple_Node(depl):

    with znflow.DiGraph(deployment=depl) as graph:
        node1 = ComputeSum(inputs=[1, 2, 3])
        node2 = ComputeSum(inputs=[4, 5, 6])
        node3 = ComputeSum(inputs=[node1.outputs, node2.outputs])

    graph.run()

    assert node1.outputs == 6
    assert node2.outputs == 15
    assert node3.outputs == 21


@pytest.mark.parametrize(
    "depl", [znflow.deployment.VanillaDeployment(), znflow.deployment.DaskDeployment()]
)
def test_multiple_nodify_and_Node(depl):

    with znflow.DiGraph(deployment=depl) as graph:
        node1 = compute_sum(1, 2, 3)
        node2 = ComputeSum(inputs=[4, 5, 6])
        node3 = compute_sum(node1, node2.outputs)
        node4 = ComputeSum(inputs=[node1, node2.outputs, node3])
        node5 = add_to_ComputeSum(node4)

    graph.run()

    assert node1.result == 6
    assert node2.outputs == 15
    assert node3.result == 21
    assert node4.outputs == 42
    assert node5.result == 43


@znflow.nodify
def get_forces():
    return np.random.normal(size=(100, 3))


@znflow.nodify
def concatenate(forces):
    return np.concatenate(forces)


@pytest.mark.parametrize(
    "depl", [znflow.deployment.VanillaDeployment(), znflow.deployment.DaskDeployment()]
)
def test_concatenate(depl):

    with znflow.DiGraph(deployment=depl) as graph:
        forces = [get_forces() for _ in range(10)]
        forces = concatenate(forces)

    graph.run()

    assert isinstance(forces.result, np.ndarray)
    assert forces.result.shape == (1000, 3)
