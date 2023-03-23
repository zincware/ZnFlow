import pytest

import znflow
from znflow.base import CombinedConnections


@znflow.nodify
def create_list(size: int) -> list:
    return list(range(size))


class CreateList(znflow.Node):
    def __init__(self, size: int):
        super().__init__()
        self.size = size
        self.outs = None  # must be defined in __init__

    def run(self):
        self.outs = list(range(self.size))


@znflow.nodify
def add_one(value: list) -> list:
    return [x + 1 for x in value]


class AddOne(znflow.Node):
    def __init__(self, value: list):
        super().__init__()
        self.value = value
        self.outs = None

    def run(self):
        self.outs = [x + 1 for x in self.value]


def test_AddLists():
    with znflow.DiGraph() as graph:
        lst1 = CreateList(5)
        lst2 = CreateList(10)

        outs = AddOne(lst1.outs + lst2.outs)

    assert isinstance(outs.value, CombinedConnections)
    assert len(outs.value.connections) == 2
    assert outs.value.connections[0].instance is lst1
    assert outs.value.connections[0].attribute == "outs"
    assert outs.value.connections[1].instance is lst2
    assert outs.value.connections[1].attribute == "outs"

    graph.run()

    assert outs.outs == list(range(1, 6)) + list(range(1, 11))


def test_add_lists():
    with znflow.DiGraph() as graph:
        lst1 = create_list(5)
        lst2 = create_list(10)

        outs = add_one(lst1 + lst2)

    graph.run()

    assert outs.result == list(range(1, 6)) + list(range(1, 11))


def test_add_node_nodify():
    with znflow.DiGraph() as graph:
        lst1 = create_list(5)
        lst2 = CreateList(10)

        outs = add_one(lst1 + lst2.outs)

    graph.run()

    assert outs.result == list(range(1, 6)) + list(range(1, 11))


def test_add_node_nodify_getitem():
    with znflow.DiGraph() as graph:
        lst1 = create_list(5)
        lst2 = CreateList(10)

        data = lst1 + lst2.outs

        outs = add_one(data[::2])

    graph.run()

    assert outs.result == (list(range(1, 6)) + list(range(1, 11)))[::2]
    assert data.result == list(range(5)) + list(range(10))


def test_add_node_nodify_nested():
    with znflow.DiGraph() as graph:
        data = create_list(5)
        for _ in range(5):
            data += create_list(5)

        for _ in range(5):
            data += CreateList(5).outs

        outs = add_one(data)

    graph.run()

    assert outs.result == list(range(1, 6)) * 11


def test_sum_list():
    with znflow.DiGraph() as graph:
        data1 = [create_list(x) for x in range(5)]
        data2 = [CreateList(x).outs for x in range(5)]

        outs1 = sum(data1)
        outs2 = sum(data2)
        outs = sum([outs1, outs2])

    graph.run()

    result = []
    for x in [list(range(x)) for x in range(5)]:
        result.extend(x)
    assert outs.result == result + result


def test_combine():
    with znflow.DiGraph() as graph:
        data1 = [create_list(x) for x in range(5)]
        data2 = [CreateList(x) for x in range(5)]

        outs1 = znflow.combine(data1)
        outs2 = znflow.combine(*data1)
        outs3 = znflow.combine(data2, attribute="outs")
        outs4 = znflow.combine(*data2, attribute="outs")
        outs = sum([outs1, outs2, outs3, outs4])

    graph.run()

    result = []
    for x in [list(range(x)) for x in range(5)]:
        result.extend(x)
    assert outs.result == result + result + result + result


# test errors


def test_nested_getitem_error():
    with znflow.DiGraph():
        a = create_list(3) + create_list(4)
        b = create_list(5) + create_list(6)
        with pytest.raises(ValueError):
            _ = a[::2] + b[1::2]


def test_raises_error_on_iter():
    with znflow.DiGraph():
        data = []
        for _ in range(1):
            with pytest.raises(TypeError):
                data += create_list(5)


def test_raises_error_on_add():
    with znflow.DiGraph():
        with pytest.raises(TypeError):
            create_list(5) + "a"

    with znflow.DiGraph():
        a = create_list(5)
        b = create_list(5)
        data = a + b
        with pytest.raises(TypeError):
            data + "a"

    with znflow.DiGraph():
        x = CreateList(5)
        with pytest.raises(TypeError):
            x + "a"

    with znflow.DiGraph():
        x = CreateList(5).outs
        with pytest.raises(TypeError):
            x + "a"


@znflow.nodify
def return_one():
    return 1


def test_combine_none():
    with znflow.DiGraph() as graph:
        a = return_one()
        b = return_one()
        add_one(a + b)

    with pytest.raises(TypeError):
        graph.run()
