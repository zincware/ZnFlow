"""Test dynamic connection resolving using magic methods."""

import dataclasses

import pytest

import znflow


@dataclasses.dataclass
class ComputeMean(znflow.Node):
    inp1: int
    inp2: int
    out: int = None

    def run(self):
        self.out = (self.inp1 + self.inp2) / 2

    @property
    def no_comparison(self):
        return object()


@dataclasses.dataclass
class ToList(znflow.Node):
    inp1: int
    inp2: int
    out: list = None

    def run(self):
        self.out = [self.inp1, self.inp2]


@znflow.nodify
def compute_mean(inp1: int, inp2: int) -> int:
    return (inp1 + inp2) / 2


@znflow.nodify
def to_list(inp1: int, inp2: int) -> list:
    return [inp1, inp2]


@znflow.nodify
def to_tuple(inp1: int, inp2: int) -> tuple:
    return (inp1, inp2)


def test_connection_equal():
    graph = znflow.DiGraph()

    with graph:
        node1 = ComputeMean(1, 2)
        node2 = ComputeMean(1, 2)

        mean = ComputeMean(node1.out, node2.out)
        assert mean.out == 1.5

    assert node1.out == 1.5
    assert node2.out == 1.5
    assert mean.out == 1.5


def test_connection_lt():
    graph = znflow.DiGraph()

    with graph:
        node1 = ComputeMean(1, 2)
        node2 = ComputeMean(1, 2)

        with pytest.raises(TypeError):
            node1.no_comparison < 2

        mean = ComputeMean(node1.out, node2.out)
        assert mean.out < 2

    assert node1.out == 1.5
    assert node2.out == 1.5
    assert mean.out == 1.5


def test_connection_le():
    graph = znflow.DiGraph()

    with graph:
        node1 = ComputeMean(1, 2)
        node2 = ComputeMean(1, 2)

        with pytest.raises(TypeError):
            node1.no_comparison <= 1.5

        mean = ComputeMean(node1.out, node2.out)
        assert mean.out <= 1.5

    assert node1.out == 1.5
    assert node2.out == 1.5
    assert mean.out == 1.5


def test_connection_gt():
    graph = znflow.DiGraph()

    with graph:
        node1 = ComputeMean(1, 2)
        node2 = ComputeMean(1, 2)

        with pytest.raises(TypeError):
            node1.no_comparison > 1

        mean = ComputeMean(node1.out, node2.out)
        assert mean.out > 1

    assert node1.out == 1.5
    assert node2.out == 1.5
    assert mean.out == 1.5


def test_connection_ge():
    graph = znflow.DiGraph()

    with graph:
        node1 = ComputeMean(1, 2)
        node2 = ComputeMean(1, 2)

        with pytest.raises(TypeError):
            node1.no_comparison >= 1.5

        mean = ComputeMean(node1.out, node2.out)
        assert mean.out >= 1.5

    assert node1.out == 1.5
    assert node2.out == 1.5
    assert mean.out == 1.5


def test_connection_iter():
    graph = znflow.DiGraph()

    with graph:
        node1 = ComputeMean(1, 2)
        node2 = ComputeMean(1, 2)

        with pytest.raises(TypeError):
            list(node1.out)

        lst = ToList(node1.out, node2.out)
        assert list(lst.out) == [1.5, 1.5]

    assert node1.out == 1.5
    assert node2.out == 1.5
    assert lst.out == [1.5, 1.5]


def test_function_future_equal():
    graph = znflow.DiGraph()

    with graph:
        mean = compute_mean(1, 2)
        assert mean == 1.5

    assert mean.result == 1.5


def test_function_future_lt():
    graph = znflow.DiGraph()

    with graph:
        with pytest.raises(TypeError):
            to_tuple(1, 2) < 2

        mean = compute_mean(1, 2)
        assert mean < 2

    assert mean.result == 1.5


def test_function_future_le():
    graph = znflow.DiGraph()

    with graph:
        with pytest.raises(TypeError):
            to_tuple(1, 2) <= 1.5

        mean = compute_mean(1, 2)
        assert mean <= 1.5

    assert mean.result == 1.5


def test_function_future_gt():
    graph = znflow.DiGraph()

    with graph:
        with pytest.raises(TypeError):
            to_tuple(1, 2) > 1

        mean = compute_mean(1, 2)
        assert mean > 1

    assert mean.result == 1.5


def test_function_future_ge():
    graph = znflow.DiGraph()

    with graph:
        with pytest.raises(TypeError):
            to_tuple(1, 2) >= 1.5

        mean = compute_mean(1, 2)
        assert mean >= 1.5

    assert mean.result == 1.5


def test_function_future_iter():
    graph = znflow.DiGraph()

    with graph:
        mean = compute_mean(1, 2)
        with pytest.raises(TypeError):
            list(mean)

        lst = to_list(1, 2)
        assert list(lst) == [1, 2]

    assert mean.result == 1.5
    assert lst.result == [1, 2]
