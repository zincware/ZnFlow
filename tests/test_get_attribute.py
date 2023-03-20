import pytest

import znflow


class POW2Base(znflow.Node):
    x_factor: float = 1.0
    results: float = None
    _x: float = None

    @property
    def x_(self):
        return self._x

    @x_.setter
    def x_(self, value):
        """
        Raises
        ------
        TypeError: unsupported operand type(s) for *: 'float' and 'Connection'
            if inside DiGraph
        """
        self._x = value * self.x_factor

    def run(self):
        self.results = self.x**1


class POW2GetAttr(POW2Base):
    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value * znflow.get_attribute(self, "x_factor")


class POW2Decorate(POW2Base):
    @property
    def x(self):
        return self._x

    @znflow.disable_graph()
    @x.setter
    def x(self, value):
        self._x = value * self.x_factor


class POW2Decorate2(POW2Base):
    @znflow.Property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value * self.x_factor


class POW2Context(POW2Base):
    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        with znflow.disable_graph():
            self._x = value * self.x_factor


@pytest.mark.parametrize("cls", [POW2GetAttr, POW2Decorate, POW2Context, POW2Decorate2])
def test_get_attribute(cls):
    with znflow.DiGraph() as graph:
        n1 = cls()
        n1.x = 4.0  # converted to 2.0

    graph.run()
    assert n1.x == 4.0
    assert n1.results == 4.0

    with znflow.DiGraph() as graph:
        n1 = cls()
        with pytest.raises(TypeError):
            # TypeError: unsupported operand type(s) for *: 'float' and 'Connection'
            n1.x_ = 4.0


class InvalidAttribute(znflow.Node):
    @property
    def invalid_attribute(self):
        raise ValueError("attribute not available")


def test_invalid_attribute():
    node = InvalidAttribute()
    with pytest.raises(ValueError):
        node.invalid_attribute

    with znflow.DiGraph() as graph:
        node = InvalidAttribute()
        invalid_attribute = node.invalid_attribute
    assert isinstance(invalid_attribute, znflow.Connection)
    assert invalid_attribute.instance == node
    assert invalid_attribute.attribute == "invalid_attribute"
    assert node.uuid in graph


class NodeWithInit(znflow.Node):
    def __init__(self):
        self.x = 1.0


def test_attribute_not_found():
    """Try to access an Attribute which does not exist."""
    with pytest.raises(AttributeError):
        node = InvalidAttribute()
        node.this_does_not_exist

    with znflow.DiGraph():
        node = POW2GetAttr()
        with pytest.raises(AttributeError):
            node.this_does_not_exist

    with znflow.DiGraph():
        node = NodeWithInit()
        with pytest.raises(AttributeError):
            node.this_does_not_exist
        outs = node.x

    assert outs.result == 1.0
