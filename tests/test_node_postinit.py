import dataclasses
import typing

import pytest
import zninit

import znflow


class ConvertInputsPlain(znflow.Node):
    def __init__(self, inputs):
        self.inputs = inputs
        self.inputs = float(self.inputs)

    def run(self):
        pass


class ConverInputsZnInit(zninit.ZnInit, znflow.Node):
    inputs: typing.Union[str, float] = zninit.Descriptor()

    def _post_init_(self):
        self.inputs = float(self.inputs)

    def run(self):
        pass


@dataclasses.dataclass
class ConvertInputsDataclass(znflow.Node):
    inputs: typing.Union[str, float]

    def __post_init__(self):
        self.inputs = float(self.inputs)

    def run(self):
        pass


@znflow.nodify
def compute_sum(*args):
    return sum(args)


@pytest.mark.parametrize(
    "cls", [ConvertInputsPlain, ConverInputsZnInit, ConvertInputsDataclass]
)
def test_ConvertInputs(cls):
    with znflow.DiGraph() as graph:
        node1 = cls(inputs="1")
        node2 = cls(inputs="2")
        node3 = compute_sum(node1.inputs, node2.inputs)
    graph.run()
    assert node3.result == 3.0
