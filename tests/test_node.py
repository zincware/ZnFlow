import dataclasses

import pytest
import zninit

import znflow


class PlainNode(znflow.Node):
    def __init__(self, value):
        self.value = value


@dataclasses.dataclass
class DataclassNode(znflow.Node):
    value: int


class ZnInitNode(zninit.ZnInit, znflow.Node):
    value: int = zninit.Descriptor()


@znflow.nodify
def add(value):
    return value + 1


@pytest.mark.parametrize("cls", [PlainNode, DataclassNode, ZnInitNode, add])
def test_Node(cls):
    with znflow.DiGraph() as graph:
        node = cls(value=42)

    assert node.uuid in graph
    assert graph.nodes[node.uuid]["value"] is node
