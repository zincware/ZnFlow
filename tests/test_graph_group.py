import pytest

import znflow


class PlainNode(znflow.Node):
    def __init__(self, value):
        self.value = value

    def run(self):
        self.value += 1


def test_empty_grp_name():
    graph = znflow.DiGraph()

    with pytest.raises(TypeError):
        with graph.group():  # name required
            pass


def test_grp():
    graph = znflow.DiGraph()

    assert graph.active_group is None

    with graph.group("my_grp") as grp_name:
        assert graph.active_group == grp_name

        node = PlainNode(1)

    assert graph.active_group is None
    graph.run()

    assert grp_name == "my_grp"
    assert node.value == 2
    assert node.uuid in graph.nodes
    assert grp_name in graph._groups
    assert graph.get_group(grp_name) == [node.uuid]

    assert len(graph._groups) == 1
    assert len(graph) == 1


def test_muliple_grps():
    graph = znflow.DiGraph()

    assert graph.active_group is None

    with graph.group("my_grp") as grp_name:
        assert graph.active_group == grp_name

        node = PlainNode(1)

    assert graph.active_group is None

    with graph.group("my_grp2") as grp_name2:
        assert graph.active_group == grp_name2

        node2 = PlainNode(2)

    assert graph.active_group is None

    graph.run()

    assert grp_name == "my_grp"
    assert grp_name2 == "my_grp2"

    assert node.value == 2
    assert node2.value == 3

    assert node.uuid in graph.nodes
    assert node2.uuid in graph.nodes

    assert grp_name in graph._groups
    assert grp_name2 in graph._groups

    assert graph.get_group(grp_name) == [node.uuid]
    assert graph.get_group(grp_name2) == [node2.uuid]

    assert len(graph._groups) == 2
    assert len(graph) == 2


def test_nested_grps():
    graph = znflow.DiGraph()

    with graph.group("my_grp") as grp_name:
        assert graph.active_group == grp_name
        with pytest.raises(TypeError):
            with graph.group("my_grp2"):
                pass


def test_grp_with_existing_nodes():
    with znflow.DiGraph() as graph:
        node = PlainNode(1)

        with graph.group("my_grp") as grp_name:
            assert graph.active_group == grp_name

            node2 = PlainNode(2)

    assert graph.active_group is None

    graph.run()

    assert grp_name == "my_grp"

    assert node.value == 2
    assert node2.value == 3

    assert node.uuid in graph.nodes
    assert node2.uuid in graph.nodes

    assert grp_name in graph._groups

    assert graph.get_group(grp_name) == [node2.uuid]

    assert len(graph._groups) == 1
    assert len(graph) == 2


def test_grp_with_multiple_nodes():
    with znflow.DiGraph() as graph:
        node = PlainNode(1)
        node2 = PlainNode(2)

        with graph.group("my_grp") as grp_name:
            assert graph.active_group == grp_name

            node3 = PlainNode(3)
            node4 = PlainNode(4)

    assert graph.active_group is None

    graph.run()

    assert grp_name == "my_grp"

    assert node.value == 2
    assert node2.value == 3
    assert node3.value == 4
    assert node4.value == 5

    assert node.uuid in graph.nodes
    assert node2.uuid in graph.nodes
    assert node3.uuid in graph.nodes
    assert node4.uuid in graph.nodes

    assert grp_name in graph._groups

    assert graph.get_group(grp_name) == [node3.uuid, node4.uuid]

    assert len(graph._groups) == 1
    assert len(graph) == 4


def test_reopen_grps():
    with znflow.DiGraph() as graph:
        with graph.group("my_grp") as grp_name:
            assert graph.active_group == grp_name

            node = PlainNode(1)

        with graph.group("my_grp") as grp_name2:
            assert graph.active_group == grp_name2

            node2 = PlainNode(2)

    assert graph.active_group is None

    graph.run()

    assert grp_name == "my_grp"
    assert grp_name2 == grp_name

    assert node.value == 2
    assert node2.value == 3

    assert node.uuid in graph.nodes
    assert node2.uuid in graph.nodes

    assert grp_name in graph._groups

    assert graph.get_group(grp_name) == [node.uuid, node2.uuid]

    assert len(graph._groups) == 1
    assert len(graph) == 2

def test_tuple_grp_names():
    graph = znflow.DiGraph()

    assert graph.active_group is None
    with graph.group(("grp", "1")) as grp_name:
        assert graph.active_group == grp_name

        node = PlainNode(1)
    
    assert graph.active_group is None
    graph.run()

    assert grp_name == ("grp", "1")
    assert node.value == 2
    assert node.uuid in graph.nodes
    assert grp_name in graph._groups
    assert graph.get_group(grp_name) == [node.uuid]
