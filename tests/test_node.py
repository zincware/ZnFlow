"""Test 'znflow.node' module."""
from unittest import mock

import pytest

import znflow
import znflow.base
import znflow.connectors
import znflow.utils


class MyNode(znflow.Node):
    """Custom Node."""

    inputs: str = None


def test_matmul():
    """Test the matmul overload."""
    node = MyNode()
    assert isinstance(node @ "inputs", znflow.connectors.NodeConnector)
    assert (node @ "inputs").node == node
    assert (node @ "inputs").attribute == "inputs"

    with pytest.raises(ValueError):
        node @ 25


class NodeWithAttribute(znflow.Node):
    """Custom Node."""

    inputs: str = znflow.EdgeAttribute()


def test_set_edge_attribute():
    """Check '__set__' and '__get__' of 'EdgeAttribute'."""
    node = NodeWithAttribute(inputs="HelloWorld")
    assert node.inputs == "HelloWorld"


def test_set_edge_attribute_graph():
    """Check '__set__' and '__get__' of 'EdgeAttribute' inside a DiGraph."""

    magic_mock = mock.MagicMock()
    with znflow.base.update__graph_(value=magic_mock):
        node = NodeWithAttribute(inputs="HelloWorld")
        assert node.inputs == znflow.connectors.NodeConnector(
            graph=magic_mock, node=node, attribute="inputs"
        )
    assert node.inputs == "HelloWorld"


def test_get_node_attribute():
    """Check '__set__' and '__get__' of 'EdgeAttribute' inside a DiGraph."""

    with pytest.raises(AttributeError):
        _ = NodeWithAttribute(inputs=42).does_not_exist

    with znflow.base.update__graph_(value=mock.MagicMock()):
        with pytest.raises(AttributeError):
            _ = NodeWithAttribute(inputs=42).does_not_exist
