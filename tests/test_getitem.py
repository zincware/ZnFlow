import dataclasses

import znflow


@znflow.nodify
def get_list() -> list:
    return list(range(10))


@znflow.nodify
def add_lists(a, b):
    return a + b


@dataclasses.dataclass
class GetList(znflow.Node):
    maximum: int
    data: list = None

    def run(self):
        self.data = list(range(self.maximum))


def test_get_list():
    assert get_list() == list(range(10))
    assert get_list()[::2] == list(range(0, 10, 2))

    with znflow.DiGraph() as graph:
        x = get_list()
        y = x[::2]

    graph.run()

    assert isinstance(x, znflow.FunctionFuture)
    assert isinstance(y, znflow.Connection)

    assert y.instance is x
    assert len(graph) == 1

    assert x.result == list(range(10))
    assert y.result == list(range(0, 10, 2))


def test_GetList():
    instance = GetList(10)
    instance.run()
    assert instance.data == list(range(10))
    assert instance.data[::2] == list(range(0, 10, 2))

    with znflow.DiGraph() as graph:
        x = GetList(10)
        y = x.data[::2]

    graph.run()

    assert isinstance(y, znflow.Connection)

    assert y.instance.instance is x  # y.instance == Connection(instance=x, ...)
    assert len(graph) == 1

    assert x.data == list(range(10))
    assert y.result == list(range(0, 10, 2))


def test_getitem_with_sum():
    a = get_list()
    b = GetList(10)
    b.run()

    c = add_lists(a[:5], b.data[5:])

    assert a == list(range(10))
    assert b.data == list(range(10))
    assert c == list(range(10))

    with znflow.DiGraph() as graph:
        node_a = get_list()
        node_b = GetList(10)

        node_c = add_lists(node_a[:5], node_b.data[5:])

    graph.run()
    assert node_a.result == list(range(10))
    assert node_b.data == list(range(10))
    assert node_c.result == list(range(10))


def test_multi_getitem():
    with znflow.DiGraph() as graph:
        node_a = get_list()
        x = node_a[::2]
        y = x[::2]

        out = add_lists(x, y)

    graph.run()
    assert len(graph) == 2  # node_a and out
    assert node_a.result == list(range(10))
    assert x.result == list(range(0, 10, 2))
    assert y.result == list(range(0, 10, 4))
    assert out.result == list(range(0, 10, 2)) + list(range(0, 10, 4))
