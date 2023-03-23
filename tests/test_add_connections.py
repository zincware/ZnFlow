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


@pytest.mark.parametrize("use_graph", [True, False])
def test_AddLists(use_graph):
    if use_graph:
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
    else:
        lst1 = CreateList(5)
        lst1.run()
        lst2 = CreateList(10)
        lst2.run()
        outs = AddOne(lst1.outs + lst2.outs)
        outs.run()

    assert outs.outs == list(range(1, 6)) + list(range(1, 11))


@pytest.mark.parametrize("use_graph", [True, False])
def test_add_lists(use_graph):
    if use_graph:
        with znflow.DiGraph() as graph:
            lst1 = create_list(5)
            lst2 = create_list(10)

            outs = add_one(lst1 + lst2)

        graph.run()
        result = outs.result
    else:
        lst1 = create_list(5)
        lst2 = create_list(10)
        result = add_one(lst1 + lst2)

    assert result == list(range(1, 6)) + list(range(1, 11))


@pytest.mark.parametrize("use_graph", [True, False])
def test_add_node_nodify(use_graph):
    if use_graph:
        with znflow.DiGraph() as graph:
            lst1 = create_list(5)
            lst2 = CreateList(10)

            outs = add_one(lst1 + lst2.outs)

        graph.run()
        result = outs.result
    else:
        lst1 = create_list(5)
        lst2 = CreateList(10)
        lst2.run()
        result = add_one(lst1 + lst2.outs)

    assert result == list(range(1, 6)) + list(range(1, 11))


@pytest.mark.parametrize("use_graph", [True, False])
def test_add_node_nodify_getitem(use_graph):
    if use_graph:
        with znflow.DiGraph() as graph:
            lst1 = create_list(5)
            lst2 = CreateList(10)

            data = lst1 + lst2.outs

            outs = add_one(data[::2])

        graph.run()
        assert data.result == list(range(5)) + list(range(10))
        result = outs.result
    else:
        lst1 = create_list(5)
        lst2 = CreateList(10)
        lst2.run()
        data = lst1 + lst2.outs
        result = add_one(data[::2])

    assert result == (list(range(1, 6)) + list(range(1, 11)))[::2]


@pytest.mark.parametrize("use_graph", [True, False])
def test_add_node_nodify_nested(use_graph):
    if use_graph:
        with znflow.DiGraph() as graph:
            data = create_list(5)
            for _ in range(5):
                data += create_list(5)

            for _ in range(5):
                data += CreateList(5).outs

            outs = add_one(data)

        graph.run()
        result = outs.result
    else:
        data = create_list(5)
        for _ in range(5):
            data += create_list(5)

        for _ in range(5):
            x = CreateList(5)
            x.run()
            data += x.outs

        result = add_one(data)

    assert result == list(range(1, 6)) * 11


@pytest.mark.parametrize("use_graph", [True, False])
def test_combine_unpack(use_graph):
    if use_graph:
        with znflow.DiGraph() as graph:
            a = create_list(2)
            b = create_list(3)
            c = znflow.combine(a, b)
        graph.run()
        c = c.result
    else:
        a = create_list(2)
        b = create_list(3)
        c = znflow.combine(a, b)

    assert c == [0, 1, 0, 1, 2]


@pytest.mark.parametrize("use_graph", [True, False])
def test_combine_list(use_graph):
    if use_graph:
        with znflow.DiGraph() as graph:
            a = create_list(2)
            b = create_list(3)
            c = znflow.combine([a, b])
        graph.run()
        c = c.result
    else:
        a = create_list(2)
        b = create_list(3)
        c = znflow.combine([a, b])

    assert c == [0, 1, 0, 1, 2]


@pytest.mark.parametrize("unpack", [True, False])
@pytest.mark.parametrize("use_graph", [True, False])
def test_combine(use_graph, unpack):
    if use_graph:
        with znflow.DiGraph() as graph:
            data1 = [create_list(x) for x in range(5)]
            data2 = [CreateList(x) for x in range(5)]
            if unpack:
                data1 = znflow.combine(*data1)
                data2 = znflow.combine(*data2, attribute="outs")
                outs = znflow.combine(data1, data2)
            else:
                data1 = znflow.combine(data1)
                data2 = znflow.combine(data2, attribute="outs")
                outs = znflow.combine([data1, data2])
        graph.run()
        result = outs.result
    else:
        data1 = [create_list(x) for x in range(5)]
        data2 = [CreateList(x) for x in range(5)]
        [x.run() for x in data2]
        if unpack:
            data1 = znflow.combine(*data1)
            data2 = znflow.combine(*data2, attribute="outs")
            result = znflow.combine(data1, data2)
        else:
            data1 = znflow.combine(data1)
            data2 = znflow.combine(data2, attribute="outs")
            result = znflow.combine([data1, data2])

    assert result == sum([list(range(x)) for x in range(5)] * 2, [])


def test_combine_w_wo_graph():
    with znflow.DiGraph() as graph:
        g_data1 = [create_list(x) for x in range(5)]
        g_data2 = [CreateList(x) for x in range(5)]

        g_outs1 = znflow.combine(*g_data1)
        g_outs2 = znflow.combine(*g_data1)
        g_outs3 = znflow.combine(*g_data2, attribute="outs")
        g_outs4 = znflow.combine(*g_data2, attribute="outs")
        g_outs = znflow.combine(*[g_outs1, g_outs2, g_outs3, g_outs4])

    graph.run()
    # now without graph
    data1 = [create_list(x) for x in range(5)]
    data2 = [CreateList(x) for x in range(5)]
    [x.run() for x in data2]

    outs1 = znflow.combine(*data1)
    outs2 = znflow.combine(*data1)
    outs3 = znflow.combine(*data2, attribute="outs")
    outs4 = znflow.combine(*data2, attribute="outs")
    outs = znflow.combine(*[outs1, outs2, outs3, outs4])

    assert g_outs1.result == outs1
    assert g_outs.result == outs

    expected = []
    for x in [list(range(x)) for x in range(5)]:
        expected.extend(x)
    assert outs == expected + expected + expected + expected


@pytest.mark.parametrize("use_graph", [True, False])
def test_sum_list(use_graph):
    if use_graph:
        with znflow.DiGraph() as graph:
            data1 = [create_list(x) for x in range(5)]
            data2 = [CreateList(x) for x in range(5)]

            outs1 = sum(data1, [])
            outs2 = sum((x.outs for x in data2), [])
            outs = sum([outs1, outs2], [])

        graph.run()
        result = outs.result
    else:
        data1 = [create_list(x) for x in range(5)]
        data2 = [CreateList(x) for x in range(5)]
        [x.run() for x in data2]

        outs1 = sum(data1, [])
        outs2 = sum((x.outs for x in data2), [])
        result = sum([outs1, outs2], [])

    assert result == sum([list(range(x)) for x in range(5)] * 2, [])


@pytest.mark.parametrize("use_graph", [True, False])
def test_combine_advanced(use_graph):
    """test the znflow.combine with various inputs"""

    if use_graph:
        with znflow.DiGraph() as graph:
            node = CreateList(10)
            a = znflow.combine(node, attribute="outs")
            b = znflow.combine([node], attribute="outs")
            c = znflow.combine(node, node.outs, attribute="outs")
            d = znflow.combine([node, node.outs], attribute="outs")
        graph.run()
        a = a.result
        b = b.result
        c = c.result
        d = d.result

    else:
        node = CreateList(10)
        node.run()
        a = znflow.combine(node, attribute="outs")
        b = znflow.combine([node], attribute="outs")

        c = znflow.combine(node, node.outs, attribute="outs")
        d = znflow.combine([node, node.outs], attribute="outs")

    assert a == b
    assert a == list(range(10))
    assert c == d
    assert c == 2 * list(range(10))


# test errors


def test_nested_getitem_error():
    with znflow.DiGraph():
        a = create_list(3) + create_list(4)
        b = create_list(5) + create_list(6)
        with pytest.raises(ValueError):
            _ = a[::2] + b[1::2]


def test_raises_error_on_normal_sum():
    with znflow.DiGraph():
        with pytest.raises(TypeError):
            sum([create_list(5), create_list(5)])


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
