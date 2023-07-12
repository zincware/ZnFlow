"""Test for adding 'frozen' Nodes from outside that graph.

These nodes are not run but only used as a source of data.
"""
import dataclasses

import znflow


@dataclasses.dataclass
class NodeWithExternal(znflow.Node):
    _external_ = True

    value = None

    def run(self):
        self.value = 42


def test_external_node_run():
    with znflow.DiGraph() as graph:
        node = NodeWithExternal()

    graph.run()

    assert node.value is None


@dataclasses.dataclass
class ExternalNode(znflow.Node):
    _external_ = True

    @property
    def number(self) -> int:
        return 42

    def run(self) -> None:
        pass


@dataclasses.dataclass
class AddNumber(znflow.Node):
    input: int
    shift: int

    result: int = None

    def run(self) -> None:
        self.result = self.input + self.shift


@dataclasses.dataclass
class AddNumberFromNodes(znflow.Node):
    input: znflow.Node
    shift: int

    result: int = None

    def run(self) -> None:
        self.result = self.input.number + self.shift


@dataclasses.dataclass
class SumNumbers(znflow.Node):
    inputs: list[int]

    result: int = None

    def run(self) -> None:
        self.result = sum(self.inputs)


def test_external_node():
    node = ExternalNode()

    with znflow.DiGraph() as graph:
        add_number = AddNumber(shift=1, input=node.number)

    graph.run()

    assert add_number.shift == 1
    assert add_number.result == 43


def test_external_node_from_node():
    node = ExternalNode()

    with znflow.DiGraph() as graph:
        add_number = AddNumberFromNodes(shift=1, input=node)

    graph.run()

    assert add_number.shift == 1
    assert add_number.result == 43


def test_external_node_lists():
    node1 = ExternalNode()
    node2 = ExternalNode()

    with znflow.DiGraph() as graph:
        sum_numbers = SumNumbers(inputs=[node1.number, node2.number])

    graph.run()

    assert sum_numbers.result == 84


# TODO with _external_ = False raise the correct error

# def test_not_external_node():
#     node = ExternalNode()
#     node._external_ = False

#     with znflow.DiGraph() as graph:
#         with pytest.raises(znflow.NotExternalNodeError):
#             add_number = AddNumber(shift=1, input=node.number)
