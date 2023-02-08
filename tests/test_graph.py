import dataclasses

import pytest
import zninit

import znflow


class PlainNode(znflow.Node):
    def __init__(self, value):
        self.value = value

    def run(self):
        self.value += 1


@dataclasses.dataclass
class DataclassNode(znflow.Node):
    value: int

    def run(self):
        self.value += 1


class ZnInitNode(zninit.ZnInit, znflow.Node):
    value: int = zninit.Descriptor()

    def run(self):
        self.value += 1


@znflow.nodify
def compute_sum(*args):
    return sum(args)


def test_run_graph():
    with znflow.DiGraph() as graph:
        node1 = DataclassNode(value=42)
        node2 = DataclassNode(value=18)
        node3 = compute_sum(node1.value, node2.value)

    assert node1.uuid in graph
    assert node2.uuid in graph
    assert node3.uuid in graph

    assert node1.value == 42
    assert node2.value == 18

    with pytest.raises(TypeError):
        node3.compute_result()

    graph.run()

    assert node1.value == 43
    assert node2.value == 19
    assert node3.result == 62


def test_nested_graph():
    """Test nested DiGraph."""
    with znflow.DiGraph():
        with pytest.raises(ValueError):
            with znflow.DiGraph():
                pass


def test_changed_graph():
    """Test changed DiGraph."""
    with pytest.raises(ValueError):
        with znflow.DiGraph():
            znflow.base.NodeBaseMixin._graph_ = znflow.DiGraph()
    znflow.base.NodeBaseMixin._graph_ = None  # reset after test
