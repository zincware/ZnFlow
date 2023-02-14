import dataclasses

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


def test_single_nodify():
    with znflow.DiGraph() as graph:
        node1 = compute_sum(1, 2, 3)

    depl = znflow.deployment.Deployment(graph=graph)
    depl.submit_graph()

    node1 = depl.get_results(node1)
    assert node1.result == 6


def test_single_Node():
    with znflow.DiGraph() as graph:
        node1 = ComputeSum(inputs=[1, 2, 3])

    depl = znflow.deployment.Deployment(graph=graph)
    depl.submit_graph()

    node1 = depl.get_results(node1)
    assert node1.outputs == 6


def test_multiple_nodify():
    with znflow.DiGraph() as graph:
        node1 = compute_sum(1, 2, 3)
        node2 = compute_sum(4, 5, 6)
        node3 = compute_sum(node1, node2)

    depl = znflow.deployment.Deployment(graph=graph)
    depl.submit_graph()

    node1 = depl.get_results(node1)
    node2 = depl.get_results(node2)
    node3 = depl.get_results(node3)
    assert node1.result == 6
    assert node2.result == 15
    assert node3.result == 21


def test_multiple_Node():
    with znflow.DiGraph() as graph:
        node1 = ComputeSum(inputs=[1, 2, 3])
        node2 = ComputeSum(inputs=[4, 5, 6])
        node3 = ComputeSum(inputs=[node1.outputs, node2.outputs])

    depl = znflow.deployment.Deployment(graph=graph)
    depl.submit_graph()

    node1 = depl.get_results(node1)
    node2 = depl.get_results(node2)
    node3 = depl.get_results(node3)
    assert node1.outputs == 6
    assert node2.outputs == 15
    assert node3.outputs == 21


def test_multiple_nodify_and_Node():
    with znflow.DiGraph() as graph:
        node1 = compute_sum(1, 2, 3)
        node2 = ComputeSum(inputs=[4, 5, 6])
        node3 = compute_sum(node1, node2.outputs)
        node4 = ComputeSum(inputs=[node1, node2.outputs, node3])
        node5 = add_to_ComputeSum(node4)

    depl = znflow.deployment.Deployment(graph=graph)
    depl.submit_graph()

    results = depl.get_results(graph.nodes)

    assert results[node1.uuid].result == 6
    assert results[node2.uuid].outputs == 15
    assert results[node3.uuid].result == 21
    assert results[node4.uuid].outputs == 42
    assert results[node5.uuid].result == 43
