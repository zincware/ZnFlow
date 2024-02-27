import dataclasses

import attrs
import pydantic
import pytest
import zninit

import znflow
from znflow.node import _mark_init_in_construction


class PlainNode(znflow.Node):
    def __init__(self, value):
        self.value = value

    def run(self):
        self.value += 1

    @property
    def output(self):
        return znflow.get_attribute(self, "value")

    def do_stuff(self):
        raise NotImplementedError


@dataclasses.dataclass
class DataclassNode(znflow.Node):
    value: int

    def run(self):
        self.value += 1

    @property
    def output(self):
        return znflow.get_attribute(self, "value")


class ZnInitNode(zninit.ZnInit, znflow.Node):
    value: int = zninit.Descriptor()

    def run(self):
        self.value += 1

    @property
    def output(self):
        return znflow.get_attribute(self, "value")


@attrs.define
class AttrsNode(znflow.Node):
    value: int

    def run(self):
        self.value += 1

    @property
    def output(self):
        return znflow.get_attribute(self, "value")


class PydanticNode(pydantic.BaseModel, znflow.Node):
    value: pydantic.SkipValidation[int]

    def run(self):
        self.value += 1

    @property
    def output(self):
        return znflow.get_attribute(self, "value")


@znflow.nodify
def add(value):
    return value


@znflow.nodify
def compute_sum(*args):
    return sum(args)


@pytest.mark.parametrize(
    "cls", [PlainNode, DataclassNode, ZnInitNode, add, AttrsNode, PydanticNode]
)
def test_Node_init(cls):
    with pytest.raises((TypeError, AttributeError, pydantic.ValidationError)):
        # TODO only raise TypeError and not AttributeError when TypeError is expected.
        # Pydantic does not raise TypeError, but ValidationError
        with znflow.DiGraph():
            cls()


@pytest.mark.parametrize(
    "cls", [PlainNode, DataclassNode, ZnInitNode, add, AttrsNode, PydanticNode]
)
def test_Node(cls):
    with znflow.DiGraph() as graph:
        node = cls(value=42)

    if isinstance(node, (PlainNode, DataclassNode, ZnInitNode)):
        assert node.value == 42
        assert not node._in_construction
        assert cls._in_construction
        assert hasattr(node, "__init__")

    elif isinstance(node, znflow.FunctionFuture):
        assert node.kwargs["value"] == 42

    assert node.uuid in graph
    assert graph.nodes[node.uuid]["value"] is node


@pytest.mark.parametrize(
    "cls2", [PlainNode, DataclassNode, ZnInitNode, AttrsNode, PydanticNode]
)
@pytest.mark.parametrize(
    "cls1", [PlainNode, DataclassNode, ZnInitNode, AttrsNode, PydanticNode]
)
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
    assert edge[0]["u_attr"] == "value"
    assert edge[0]["v_attr"] == "value"


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
    assert edge[0]["u_attr"] is None


@pytest.mark.parametrize("cls1", [add])
@pytest.mark.parametrize(
    "cls2", [PlainNode, DataclassNode, ZnInitNode, AttrsNode, PydanticNode]
)
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
    assert edge[0]["u_attr"] is None
    assert edge[0]["v_attr"] == "value"


@pytest.mark.parametrize("cls2", [add])
@pytest.mark.parametrize(
    "cls1", [PlainNode, DataclassNode, ZnInitNode, AttrsNode, PydanticNode]
)
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
@pytest.mark.parametrize(
    "cls1", [PlainNode, DataclassNode, ZnInitNode, AttrsNode, PydanticNode]
)
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
@pytest.mark.parametrize(
    "cls2", [PlainNode, DataclassNode, ZnInitNode, AttrsNode, PydanticNode]
)
def test_ConnectionNodeMultiNodify(cls1, cls2):
    with znflow.DiGraph() as graph:
        node1 = cls1(42)
        node2 = cls1(42)
        node3 = cls2(value=[node1, node2])

    assert node1.uuid in graph
    assert node2.uuid in graph
    assert node3.uuid in graph

    edge1: dict = graph.get_edge_data(node1.uuid, node3.uuid)
    edge2: dict = graph.get_edge_data(node1.uuid, node3.uuid)
    assert edge1 is not None
    assert edge2 is not None

    assert edge1[0]["u_attr"] is None
    assert edge1[0]["v_attr"] == "value"

    assert edge2[0]["u_attr"] is None
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


def test_CheckWrapInit():
    @_mark_init_in_construction
    class CheckWrapInit:
        _in_construction: bool = True

        def __init__(self):
            assert self._in_construction

    instance = CheckWrapInit()
    assert not instance._in_construction


@dataclasses.dataclass
class DictionaryConnection(znflow.Node):
    nodes: dict
    results: float = None

    def run(self):
        return sum(self.nodes.values())


@dataclasses.dataclass
class ListConnection(znflow.Node):
    nodes: list
    results: float = None

    def run(self):
        return sum(self.nodes)


@pytest.mark.parametrize(
    "deployment",
    ["vanilla_deployment", "dask_deployment"],
)
def test_DictionaryConnection(deployment, request):
    deployment = request.getfixturevalue(deployment)
    with znflow.DiGraph(deployment=deployment) as graph:
        node1 = PlainNode(value=42)
        node2 = PlainNode(value=42)
        node3 = DictionaryConnection(nodes={"node1": node1.value, "node2": node2.value})

    assert node1.uuid in graph
    assert node2.uuid in graph
    assert node3.uuid in graph

    assert "node1" in node3.nodes
    assert "node2" in node3.nodes

    assert isinstance(node3.nodes["node1"], znflow.Connection)
    assert node3.nodes["node1"].uuid == node1.uuid
    assert node3.nodes["node1"].attribute == "value"

    assert isinstance(node3.nodes["node2"], znflow.Connection)
    assert node3.nodes["node2"].uuid == node2.uuid
    assert node3.nodes["node2"].attribute == "value"

    graph.run()

    edge1: dict = graph.get_edge_data(node1.uuid, node3.uuid)
    edge2: dict = graph.get_edge_data(node1.uuid, node3.uuid)
    assert edge1 is not None
    assert edge2 is not None

    assert isinstance(edge1, dict)
    assert edge1[0]["u_attr"] == "value"
    assert edge1[0]["v_attr"] == "nodes"

    assert isinstance(edge2, dict)
    assert edge2[0]["u_attr"] == "value"
    assert edge2[0]["v_attr"] == "nodes"


@pytest.mark.parametrize(
    "deployment",
    ["vanilla_deployment", "dask_deployment"],
)
def test_ListConnection(deployment, request):
    deployment = request.getfixturevalue(deployment)
    with znflow.DiGraph(deployment=deployment) as graph:
        node1 = PlainNode(value=42)
        node2 = PlainNode(value=42)
        node3 = ListConnection(nodes=[node1.value, node2.value])

    assert node1.uuid in graph
    assert node2.uuid in graph
    assert node3.uuid in graph

    assert isinstance(node3.nodes[0], znflow.Connection)
    assert node3.nodes[0].uuid == node1.uuid
    assert node3.nodes[0].attribute == "value"

    assert isinstance(node3.nodes[1], znflow.Connection)
    assert node3.nodes[1].uuid == node2.uuid
    assert node3.nodes[1].attribute == "value"

    graph.run()

    edge1: dict = graph.get_edge_data(node1.uuid, node3.uuid)
    edge2: dict = graph.get_edge_data(node1.uuid, node3.uuid)
    assert edge1 is not None
    assert edge2 is not None

    assert isinstance(edge1, dict)
    assert edge1[0]["u_attr"] == "value"
    assert edge1[0]["v_attr"] == "nodes"

    assert isinstance(edge2, dict)
    assert edge2[0]["u_attr"] == "value"
    assert edge2[0]["v_attr"] == "nodes"
