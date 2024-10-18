import pytest

import znflow
from znflow import handler

future = znflow.FunctionFuture(function=lambda x: x, args=(10,), kwargs={})
future_connection = znflow.Connection(future, attribute=None)

node = znflow.Node()
node_connection = znflow.Connection(node, attribute=None)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1, 1),
        ("a", "a"),
        (None, None),
        (future, future_connection),
        (node, node_connection),
        (node_connection, node),
        (node_connection, node_connection),
    ],
)
def test_AttributeToConnection(value, expected):
    with znflow.DiGraph():
        assert handler.AttributeToConnection()(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1, 1),
        ("a", "a"),
        (None, None),
        (future_connection, 10),
        (node_connection, node),
    ],
)
def test_UpdateConnectors(value, expected):
    if value == future_connection:
        future.run()
    with znflow.DiGraph():
        assert handler.UpdateConnectors()(value) == expected
