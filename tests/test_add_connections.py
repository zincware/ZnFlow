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
        assert len(outs.value) == 2
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


def test_combine_get_dict():
    with znflow.DiGraph():
        g_data1 = [create_list(x) for x in range(5)]
        g_data2 = [CreateList(x) for x in range(5)]

        g_outs1 = znflow.combine(*g_data1, return_dict_attr="uuid")
        g_outs2 = znflow.combine(*g_data2, attribute="outs", return_dict_attr="uuid")
        with pytest.raises(
            ValueError
        ):  # nodes occur multiple times, dict is not possible
            znflow.combine(g_data1 + g_data1, return_dict_attr="uuid")

    assert isinstance(g_outs1, dict)
    assert len(g_outs1) == 5
    assert isinstance(g_outs2, dict)
    assert len(g_outs2) == 5

    for node in g_data1:
        assert node.uuid in g_outs1
        assert g_outs1[node.uuid] == node

    # without graph
    g_data1 = [create_list(x) for x in range(5)]
    with pytest.raises(TypeError):
        znflow.combine(*g_data1, return_dict_attr="uuid")

    assert znflow.combine(
        *g_data1, return_dict_attr="uuid", return_dict_attr_error=False
    ) == znflow.combine(*g_data1)


def test_Node_list_wo_graph():
    # Nodes without graph
    data1 = [CreateList(x) for x in range(5)]
    for idx, x in enumerate(data1):
        x._uuid = idx

    outs1 = znflow.combine(*data1, return_dict_attr="uuid")
    assert isinstance(outs1, dict)
    assert len(outs1) == 5
    for node in data1:
        assert outs1[node.uuid] == node


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


@pytest.mark.parametrize("unpack", [True, False])
@pytest.mark.parametrize("use_graph", [True, False])
def test_combine_advanced(use_graph, unpack):
    """test the znflow.combine with various inputs"""

    def get_connections(node) -> list:
        if unpack:
            return [
                # test list[node]
                znflow.combine(node, attribute="outs"),
                # test list[node]
                znflow.combine(*[node, node], attribute="outs"),
                # test connection
                znflow.combine(node.outs, attribute="outs"),
                # test list[connection]
                znflow.combine(*[node.outs, node.outs], attribute="outs"),
                # test list[combined_node]
                znflow.combine(
                    *[node.outs + node.outs, node.outs + node.outs], attribute="outs"
                ),
                # test list[node, connection, combined_node]
                znflow.combine(
                    *[node, node.outs, node.outs + node.outs], attribute="outs"
                ),
            ]
        else:
            return [
                # test list[node]
                znflow.combine([node], attribute="outs"),
                # test list[node]
                znflow.combine([node, node], attribute="outs"),
                # test connection
                znflow.combine([node.outs], attribute="outs"),
                # test list[connection]
                znflow.combine([node.outs, node.outs], attribute="outs"),
                # test list[combined_node]
                znflow.combine(
                    [node.outs + node.outs, node.outs + node.outs], attribute="outs"
                ),
                # test list[node, connection, combined_node]
                znflow.combine(
                    [node, node.outs, node.outs + node.outs], attribute="outs"
                ),
            ]

    if use_graph:
        with znflow.DiGraph() as graph:
            node = CreateList(10)
            func_fut = create_list(10)
            outs = get_connections(node)

            outs.append(
                znflow.combine(
                    [node, node.outs, node.outs + node.outs, func_fut], attribute="outs"
                ),
            )

        graph.run()
        outs = [x.result for x in outs]
    else:
        node = CreateList(10)
        func_fut = create_list(10)
        node.run()
        outs = get_connections(node)
        outs.append(
            znflow.combine(
                [node, node.outs, node.outs + node.outs, func_fut], attribute="outs"
            ),
        )

    assert outs[0] == list(range(10))
    assert outs[1] == list(range(10)) * 2
    assert outs[2] == list(range(10))
    assert outs[3] == list(range(10)) * 2
    assert outs[4] == list(range(10)) * 4
    assert outs[5] == list(range(10)) * 4
    assert outs[6] == list(range(10)) * 5


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


def test_combine_error():
    with pytest.raises(TypeError):
        znflow.combine([1, 2, 3], attribute="outs", only_getattr_on_nodes=False)

    assert znflow.combine([1, 2, 3], attribute="outs") == [1, 2, 3]


def test_append_connection():
    with znflow.DiGraph():
        a = CreateList(size=5)
        b = CreateList(size=4)

        assert isinstance(a.outs, znflow.Connection)

        with pytest.raises(TypeError):
            a.outs.append(b.outs)


def test_extend_connection():
    with znflow.DiGraph():
        a = CreateList(size=5)
        b = CreateList(size=4)

        with pytest.raises(TypeError):
            a.outs.extend(b.outs)


def test_append_function_future():
    with znflow.DiGraph():
        a = create_list(5)
        b = create_list(5)

        assert isinstance(a, znflow.FunctionFuture)

        with pytest.raises(TypeError):
            a.append(b)


def test_extend_function_future():
    with znflow.DiGraph():
        a = create_list(5)
        b = create_list(5)

        with pytest.raises(TypeError):
            a.extend(b)


def test_append_combined_connection():
    with znflow.DiGraph():
        a = create_list(5)
        b = create_list(5)

        assert isinstance(a + b, znflow.CombinedConnections)

        with pytest.raises(TypeError):
            a.append(a + b)


def test_extend_combined_connection():
    with znflow.DiGraph():
        a = create_list(5)
        b = create_list(5)

        with pytest.raises(TypeError):
            a.extend(a + b)


@pytest.mark.parametrize("use_graph", [True, False])
def test_connection_plus_combined_connection(use_graph):
    """Test Connection + CombinedConnection operation"""
    if use_graph:
        with znflow.DiGraph() as graph:
            lst1 = CreateList(3)
            lst2 = CreateList(4)
            lst3 = CreateList(5)

            # Create CombinedConnection first
            combined = lst2.outs + lst3.outs
            # Then add Connection to it
            result = lst1.outs + combined

        assert isinstance(result, CombinedConnections)
        assert len(result.connections) == 3
        graph.run()
        result_value = result.result
    else:
        lst1 = CreateList(3)
        lst2 = CreateList(4)
        lst3 = CreateList(5)
        lst1.run()
        lst2.run()
        lst3.run()

        combined = lst2.outs + lst3.outs
        result_value = lst1.outs + combined

    assert result_value == [0, 1, 2] + [0, 1, 2, 3] + [0, 1, 2, 3, 4]


def test_no_nested_combined_connections():
    """Test that Connection + CombinedConnection
    doesn't create nested CombinedConnections"""
    with znflow.DiGraph():
        lst1 = CreateList(2)
        lst2 = CreateList(3)
        lst3 = CreateList(4)

        # Create initial CombinedConnection
        combined = lst1.outs + lst2.outs
        assert isinstance(combined, CombinedConnections)
        assert len(combined.connections) == 2

        # Add another Connection - should flatten, not nest
        result = lst3.outs + combined
        assert isinstance(result, CombinedConnections)
        assert len(result.connections) == 3

        # Verify no nested CombinedConnections in the connections list
        for conn in result.connections:
            assert not isinstance(conn, CombinedConnections)


def test_add_sliced_combined_connections_error():
    """Test that slicing a CombinedConnection raises an error when adding"""
    with znflow.DiGraph():
        lst1 = CreateList(5)
        lst2 = CreateList(5)

        combined = lst1.outs + lst2.outs
        assert isinstance(combined, CombinedConnections)

        with pytest.raises(ValueError, match="Can not combine multiple slices"):
            _ = combined[::2] + combined[1::2]
