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


def test_external_node():
    node = ExternalNode()

    with znflow.DiGraph() as graph:
        # add_number = AddNumber(input=42, shift=1)
        add_number = AddNumber(shift=1, input=node.number)

    graph.run()

    assert add_number.shift == 1
    assert add_number.result == 43
