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
def add(value):
    return value


@znflow.nodify
def compute_sum(*args):
    return sum(args)


@pytest.mark.parametrize("cls", [PlainNode, DataclassNode, ZnInitNode, add])
def test_Node(cls):
    with znflow.DiGraph() as graph:
        node = cls(value=42)

    if isinstance(node, (PlainNode, DataclassNode, ZnInitNode)):
        assert node.value == 42
    elif isinstance(node, znflow.FunctionFuture):
        assert node.result() == 42

    assert node.uuid in graph
    assert graph.nodes[node.uuid]["value"] is node


@pytest.mark.parametrize("cls2", [PlainNode, DataclassNode, ZnInitNode])
@pytest.mark.parametrize("cls1", [PlainNode, DataclassNode, ZnInitNode])
def test_ConnectionNodeNode(cls1, cls2):
    with znflow.DiGraph() as graph:
        node1 = cls1(value=42)
        node2 = cls2(value=node1.value)

    assert isinstance(node2.value, znflow.Connection)
    assert node2.value.uuid == node1.uuid

    assert node1.uuid in graph
    assert node2.uuid in graph

    edge: dict = graph.get_edge_data(node1.uuid, node2.uuid)
    assert edge is not None
    # we have one connection, so we use 0
    assert edge[0]["i_attr"] == "value"
    assert edge[0]["j_attr"] == "value"


@pytest.mark.parametrize("cls2", [add])
@pytest.mark.parametrize("cls1", [add])
def test_ConnectionNodifyNodify(cls1, cls2):
    with znflow.DiGraph() as graph:
        node1 = cls1(value=42)
        node2 = cls2(value=node1)

    assert node1.uuid in graph
    assert node2.uuid in graph

    edge: dict = graph.get_edge_data(node1.uuid, node2.uuid)

    assert edge is not None
    # # we have one connection, so we use 0
    assert edge[0]["u_attr"] == "result"


@pytest.mark.parametrize("cls1", [add])
@pytest.mark.parametrize("cls2", [PlainNode, DataclassNode, ZnInitNode])
def test_ConnectionNodeNodify(cls1, cls2):
    with znflow.DiGraph() as graph:
        node1 = cls1(value=42)
        node2 = cls2(value=node1)

    assert node1.uuid in graph
    assert node2.uuid in graph

    assert isinstance(node2.value, znflow.Connection)

    edge: dict = graph.get_edge_data(node1.uuid, node2.uuid)
    assert edge is not None
    # we have one connection, so we use 0
    assert edge[0]["u_attr"] == "result"
    assert edge[0]["v_attr"] == "value"


@pytest.mark.parametrize("cls2", [add])
@pytest.mark.parametrize("cls1", [PlainNode, DataclassNode, ZnInitNode])
def test_ConnectionNodifyNode(cls1, cls2):
    with znflow.DiGraph() as graph:
        node1 = cls1(value=42)
        node2 = cls2(value=node1)

    assert node1.uuid in graph
    assert node2.uuid in graph

    edge: dict = graph.get_edge_data(node1.uuid, node2.uuid)
    assert edge is not None
    # we have one connection, so we use 0
    assert edge[0]["u_attr"] is None


@pytest.mark.parametrize("cls2", [compute_sum])
@pytest.mark.parametrize("cls1", [PlainNode, DataclassNode, ZnInitNode])
def test_ConnectionNodifyMultiNode(cls1, cls2):
    with znflow.DiGraph() as graph:
        node1 = cls1(value=42)
        node2 = cls1(value=42)
        node3 = cls2(node1.value, node2.value)

    assert node1.uuid in graph
    assert node2.uuid in graph
    assert node3.uuid in graph
    #
    edge1: dict = graph.get_edge_data(node1.uuid, node3.uuid)
    edge2: dict = graph.get_edge_data(node1.uuid, node3.uuid)
    assert edge1 is not None
    assert edge2 is not None
    # # we have one connection, so we use 0
    assert edge1[0]["u_attr"] == "value"
    assert "v_attr" not in edge1[0]
    assert edge2[0]["u_attr"] == "value"
    assert "v_attr" not in edge2[0]


@pytest.mark.parametrize("cls1", [compute_sum])
@pytest.mark.parametrize("cls2", [PlainNode, DataclassNode, ZnInitNode])
def test_ConnectionNodeMultiNodify(cls1, cls2):
    with znflow.DiGraph() as graph:
        node1 = cls1(value=42)
        node2 = cls1(value=42)
        node3 = cls2(value=[node1, node2])

    assert node1.uuid in graph
    assert node2.uuid in graph
    assert node3.uuid in graph

    edge1: dict = graph.get_edge_data(node1.uuid, node3.uuid)
    edge2: dict = graph.get_edge_data(node1.uuid, node3.uuid)
    assert edge1 is not None
    assert edge2 is not None

    assert edge1[0]["u_attr"] == "result"
    assert edge1[0]["v_attr"] == "value"

    assert edge2[0]["u_attr"] == "result"
    assert edge2[0]["v_attr"] == "value"


def test_Connection():
    with znflow.DiGraph() as graph:
        node1 = PlainNode(value=42)
        node2 = PlainNode(value=node1)

        # node1.value = node2.value
    assert isinstance(node2.value, znflow.Connection)
    assert node2.value.uuid == node1.uuid
    assert node2.value.attribute is None
    #
    assert node1.uuid in graph
    assert node2.uuid in graph
    #
    edge: dict = graph.get_edge_data(node1.uuid, node2.uuid)
    assert edge is not None
    assert edge[0]["u_attr"] is None
    assert edge[0]["v_attr"] == "value"
