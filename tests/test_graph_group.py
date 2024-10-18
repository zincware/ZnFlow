import pytest

import znflow


class PlainNode(znflow.Node):
    def __init__(self, value):
        self.value = value

    def run(self):
        self.value += 1


def test_empty_grp_name():
    graph = znflow.DiGraph()

    with pytest.raises(ValueError):
        with graph.group():  # name required
            pass


def test_grp():
    graph = znflow.DiGraph()

    assert graph.active_group is None

    with graph.group("my_grp") as grp:
        assert graph.active_group == grp

        node = PlainNode(1)

    assert graph.active_group is None
    graph.run()

    assert grp.names == ("my_grp",)
    assert node.value == 2
    assert node.uuid in graph.nodes
    assert grp.names in graph.groups
    assert graph.get_group("my_grp").uuids == [node.uuid]

    assert len(graph.groups) == 1
    assert len(graph) == 1


def test_muliple_grps():
    graph = znflow.DiGraph()

    assert graph.active_group is None

    with graph.group("my_grp") as grp:
        assert graph.active_group == grp

        node = PlainNode(1)

    assert graph.active_group is None

    with graph.group("my_grp2") as grp2:
        assert graph.active_group == grp2

        node2 = PlainNode(2)

    assert graph.active_group is None

    graph.run()

    assert grp.names == ("my_grp",)
    assert grp2.names == ("my_grp2",)

    assert node.value == 2
    assert node2.value == 3

    assert node.uuid in graph.nodes
    assert node2.uuid in graph.nodes

    assert grp.names in graph.groups
    assert grp2.names in graph.groups

    assert graph.get_group(*grp.names).uuids == [node.uuid]
    assert graph.get_group(*grp2.names).uuids == [node2.uuid]

    assert len(graph.groups) == 2
    assert len(graph) == 2


def test_nested_grps():
    graph = znflow.DiGraph()

    with graph.group("my_grp") as grp:
        assert graph.active_group == grp
        with pytest.raises(TypeError):
            with graph.group("my_grp2"):
                pass


def test_grp_with_existing_nodes():
    with znflow.DiGraph() as graph:
        node = PlainNode(1)

        with graph.group("my_grp") as grp:
            assert graph.active_group == grp

            node2 = PlainNode(2)

    assert graph.active_group is None

    graph.run()

    assert grp.names == ("my_grp",)

    assert node.value == 2
    assert node2.value == 3

    assert node.uuid in graph.nodes
    assert node2.uuid in graph.nodes

    assert grp.names in graph.groups

    assert graph.get_group(*grp.names).uuids == [node2.uuid]

    assert len(graph.groups) == 1
    assert len(graph) == 2


def test_grp_with_multiple_nodes():
    with znflow.DiGraph() as graph:
        node = PlainNode(1)
        node2 = PlainNode(2)

        with graph.group("my_grp") as grp:
            assert graph.active_group == grp

            node3 = PlainNode(3)
            node4 = PlainNode(4)

    assert graph.active_group is None

    graph.run()

    assert grp.names == ("my_grp",)

    assert node.value == 2
    assert node2.value == 3
    assert node3.value == 4
    assert node4.value == 5

    assert node.uuid in graph.nodes
    assert node2.uuid in graph.nodes
    assert node3.uuid in graph.nodes
    assert node4.uuid in graph.nodes

    assert grp.names in graph.groups

    assert graph.get_group(*grp.names).uuids == [node3.uuid, node4.uuid]

    assert len(graph.groups) == 1
    assert len(graph) == 4


def test_reopen_grps():
    with znflow.DiGraph() as graph:
        with graph.group("my_grp") as grp:
            assert graph.active_group == grp

            node = PlainNode(1)

        with graph.group("my_grp") as grp2:
            assert graph.active_group == grp2

            node2 = PlainNode(2)

    assert graph.active_group is None

    graph.run()

    assert grp.names == ("my_grp",)
    assert grp.names == grp2.names

    assert node.value == 2
    assert node2.value == 3

    assert node.uuid in graph.nodes
    assert node2.uuid in graph.nodes

    assert grp.names in graph.groups

    assert graph.get_group(*grp.names).uuids == [node.uuid, node2.uuid]

    assert len(graph.groups) == 1
    assert len(graph) == 2


def test_tuple_grp_names():
    graph = znflow.DiGraph()

    assert graph.active_group is None
    with graph.group("grp", "1") as grp:
        assert graph.active_group == grp

        node = PlainNode(1)

    assert graph.active_group is None
    graph.run()

    assert grp.names == ("grp", "1")
    assert node.value == 2
    assert node.uuid in graph.nodes
    assert grp.names in graph.groups
    assert graph.get_group(*grp.names).uuids == [node.uuid]


def test_grp_nodify():
    @znflow.nodify
    def compute_mean(x, y):
        return (x + y) / 2

    graph = znflow.DiGraph()

    with graph.group("grp1"):
        n1 = compute_mean(2, 4)

    assert n1.uuid in graph.get_group("grp1").uuids


def test_grp_iter():
    graph = znflow.DiGraph()

    with graph.group("grp1") as grp:
        n1 = PlainNode(1)
        n2 = PlainNode(2)

    assert list(grp) == [n1.uuid, n2.uuid]


def test_grp_contains():
    graph = znflow.DiGraph()

    with graph.group("grp1") as grp:
        n1 = PlainNode(1)
        n2 = PlainNode(2)

    assert n1.uuid in grp
    assert n2.uuid in grp
    assert "foo" not in grp


def test_grp_len():
    graph = znflow.DiGraph()

    with graph.group("grp1") as grp:
        PlainNode(1)
        PlainNode(2)

    assert len(grp) == 2


def test_grp_getitem():
    graph = znflow.DiGraph()

    with graph.group("grp1") as grp:
        n1 = PlainNode(1)
        n2 = PlainNode(2)

    assert grp[n1.uuid] == n1
    assert grp[n2.uuid] == n2
    with pytest.raises(KeyError):
        grp["foo"]


def test_grp_nodes():
    graph = znflow.DiGraph()

    with graph.group("grp1") as grp:
        n1 = PlainNode(1)
        n2 = PlainNode(2)

    assert grp.nodes == [n1, n2]
    assert grp.uuids == [n1.uuid, n2.uuid]
    assert grp.names == ("grp1",)


def test_empty_grps():
    graph = znflow.DiGraph()

    with graph.group("grp1") as grp1:
        pass
    with graph.group("grp2") as grp2:
        pass

    assert len(grp1) == 0
    assert len(grp2) == 0
    assert grp1.uuids == []
    assert grp2.uuids == []

    assert grp1.names == ("grp1",)
    assert grp2.names == ("grp2",)

    assert len(graph.groups) == 2
    assert grp1.names in graph.groups
    assert grp2.names in graph.groups
