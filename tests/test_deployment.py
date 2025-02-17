import dataclasses
import random

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
    "deployment",
    ["vanilla_deployment", "dask_deployment"],
)
def test_single_nodify(request, deployment):
    deployment = request.getfixturevalue(deployment)

    with znflow.DiGraph(deployment=deployment) as graph:
        node1 = compute_sum(1, 2, 3)

    graph.run()

    assert node1.result == 6


@pytest.mark.parametrize(
    "deployment",
    ["vanilla_deployment", "dask_deployment"],
)
def test_single_Node(request, deployment):
    deployment = request.getfixturevalue(deployment)

    with znflow.DiGraph(deployment=deployment) as graph:
        node1 = ComputeSum(inputs=[1, 2, 3])

    graph.run()
    assert node1.outputs == 6


@pytest.mark.parametrize(
    "deployment",
    ["vanilla_deployment", "dask_deployment"],
)
def test_multiple_nodify(request, deployment):
    deployment = request.getfixturevalue(deployment)

    with znflow.DiGraph(deployment=deployment) as graph:
        node1 = compute_sum(1, 2, 3)
        node2 = compute_sum(4, 5, 6)
        node3 = compute_sum(node1, node2)

    graph.run()

    assert node1.result == 6
    assert node2.result == 15
    assert node3.result == 21


@pytest.mark.parametrize(
    "deployment",
    ["vanilla_deployment", "dask_deployment"],
)
def test_multiple_Node(request, deployment):
    deployment = request.getfixturevalue(deployment)

    with znflow.DiGraph(deployment=deployment) as graph:
        node1 = ComputeSum(inputs=[1, 2, 3])
        node2 = ComputeSum(inputs=[4, 5, 6])
        node3 = ComputeSum(inputs=[node1.outputs, node2.outputs])

    graph.run()

    assert node1.outputs == 6
    assert node2.outputs == 15
    assert node3.outputs == 21


@pytest.mark.parametrize(
    "deployment",
    ["vanilla_deployment", "dask_deployment"],
)
def test_multiple_nodify_and_Node(request, deployment):
    deployment = request.getfixturevalue(deployment)

    with znflow.DiGraph(deployment=deployment) as graph:
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
    return [random.random() for _ in range(3)]


@znflow.nodify
def concatenate(forces):
    return sum(forces, [])


@pytest.mark.parametrize(
    "deployment",
    ["vanilla_deployment", "dask_deployment"],
)
def test_concatenate(request, deployment):
    deployment = request.getfixturevalue(deployment)

    with znflow.DiGraph(deployment=deployment) as graph:
        forces = [get_forces() for _ in range(10)]
        forces = concatenate(forces)

    graph.run()

    assert isinstance(forces.result, list)
    assert len(forces.result) == 30
