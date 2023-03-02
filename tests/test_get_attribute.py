import pytest

import znflow


class POW2(znflow.Node):
    x_factor: float = 0.5
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

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value * znflow.get_attribute(self, "x_factor")

    def run(self):
        self.results = self.x**2


def test_get_attribute():
    with znflow.DiGraph() as graph:
        n1 = POW2()
        n1.x = 4.0  # converted to 2.0

    graph.run()
    assert n1.x == 2.0
    assert n1.results == 4.0

    with znflow.DiGraph() as graph:
        n1 = POW2()
        with pytest.raises(TypeError):
            # TypeError: unsupported operand type(s) for *: 'float' and 'Connection'
            n1.x_ = 4.0
