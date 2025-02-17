import dataclasses
import functools
import warnings

import pytest

import znflow


class PlainNode(znflow.Node):
    """A Node with the 'result' attribute.

    'result' had been used internally before.
    """

    @property
    def result(self):
        raise TypeError("This value is not available until the node is run.")


class NodeCachedProperty(znflow.Node):
    @functools.cached_property
    def result(self):
        raise TypeError("This value is not available until the node is run.")


class ConnectResults(znflow.Node):
    @property
    def result(self):
        return 42

    def run(self):
        pass


@dataclasses.dataclass
class DepsNode(znflow.Node):
    x: int

    @property
    def result(self):
        return self.x

    def run(self):
        pass


@znflow.nodify
def add_one(x):
    return x + 1


def test_PlainNode():
    with znflow.DiGraph():
        node1 = PlainNode()
        con = node1.result

    assert isinstance(con, znflow.Connection)

    with pytest.raises(TypeError):
        con.result


def test_NodeCachedProperty():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with znflow.DiGraph():
            node1 = NodeCachedProperty()
            con = node1.result
            DepsNode(x=con)

    assert isinstance(con, znflow.Connection)

    with pytest.raises(TypeError):
        con.result


def test_ConnectResults():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with znflow.DiGraph() as graph:
            node1 = ConnectResults()
            con = node1.result
            outs = add_one(con)
            DepsNode(x=con)

    assert isinstance(con, znflow.Connection)

    graph.run()
    assert outs.result == 43


class PropertyAddsValue(znflow.Node):
    def __init__(self, value):
        self.value = value

    @property
    def result(self):
        self.value += 1
        return self.value

    def run(self):
        pass


def test_PropertyAddsValue():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with znflow.DiGraph() as graph:
            node1 = PropertyAddsValue(1)
            con = node1.result
            outs = add_one(con)

    assert isinstance(con, znflow.Connection)

    assert node1.value == 1
    graph.run()
    assert node1.value == 2
    assert outs.result == 3
