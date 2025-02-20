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


class ComputeSum(znflow.Node):
    def __init__(self, *args):
        self.args = args

    def run(self):
        self.result = sum(x.value for x in self.args)


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
    znflow.base.NodeBaseMixin._graph_ = znflow.empty_graph  # reset after test


def test_add_others():
    graph = znflow.DiGraph()
    with pytest.raises(ValueError):
        # it is only possible to add classes inheriting from NodeBaseMixin
        graph.add_znflow_node(42)


def test_add_connections():
    graph = znflow.DiGraph()
    with pytest.raises(ValueError):
        # it is only to connect Connection and NodeBaseMixin
        graph.add_connections(42, 42)


@dataclasses.dataclass
class ParameterContainer:
    value: int


def test_add_not_Node():
    parameter = ParameterContainer(value=42)
    with znflow.DiGraph() as graph:
        # ParameterContainer is not of type NodeBaseMixin,
        #  therefore, it won't be added to the graph
        node1 = DataclassNode(value=parameter.value)
        assert parameter.value == 42

    assert node1.value == 42

    graph.run()
    assert len(graph) == 1
    assert node1.value == 43


def test_not_added_to_graph():
    """Test, if a Node has a deliberately disabled _graph_ attribute

    You can set instance._graph_ = None to disable adding the node to the graph.
    """
    node1 = DataclassNode(value=42)
    node1._graph_ = None
    assert node1.value == 42

    with znflow.DiGraph() as graph:
        assert node1._graph_ is None
        node2 = DataclassNode(value=18)
        assert node2._graph_ is graph

        assert node1.value == 42

        node3 = compute_sum(node1.value, node2.value)  # test getattr
        node4 = ComputeSum(node1, node2)  # test AttributeToConnection
        assert node3.args[0] == 42  # not a connection
        assert isinstance(node3.args[1], znflow.Connection)

    assert node1.uuid not in graph
    assert node2.uuid in graph
    assert node3.uuid in graph
    assert node4.uuid in graph

    assert node1.value == 42
    assert node2.value == 18

    assert len(graph) == 3

    graph.run()

    assert node1.value == 42  # the value is not +1 because
    #  it was not added to the graph
    assert node2.value == 19
    assert node3.result == 61
    assert node4.result == 61


def test_disable_graph():
    graph = znflow.DiGraph()
    with graph:
        node1 = DataclassNode(value=42)
        assert node1._graph_ is graph
        with znflow.base.disable_graph():
            assert node1._graph_ is znflow.empty_graph
        assert node1._graph_ is graph
    assert node1._graph_ is znflow.empty_graph


def test_get_attribute():
    graph = znflow.DiGraph()
    with graph:
        node1 = DataclassNode(value=42)
        assert znflow.base.get_attribute(node1, "value") == 42
        assert isinstance(node1.value, znflow.Connection)

    assert znflow.base.get_attribute(node1, "value") == 42
    with pytest.raises(AttributeError):
        znflow.base.get_attribute(node1, "not_existing")

    assert znflow.base.get_attribute(node1, "not_existing", None) is None
    assert znflow.base.get_attribute(node1, "not_existing", 13) == 13


def test_node_not_on_graph():
    node1 = DataclassNode(value=42)

    with pytest.raises(ValueError):
        with znflow.DiGraph():
            with pytest.raises(ValueError):
                _ = DataclassNode(value=node1.value)
