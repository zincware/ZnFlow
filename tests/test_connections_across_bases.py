"""Every base connects the same way, through the constructor and by assignment."""

import dataclasses
import json

import attrs
import pydantic
import pytest
import zninit

import znflow


@dataclasses.dataclass
class Source(znflow.Node):
    tag: str = "seed"
    outs: list = dataclasses.field(default_factory=list)

    def run(self):
        self.outs = [self.tag]


@znflow.nodify
def source(tag) -> list:
    return [tag]


def _received(node) -> list:
    return [f"got({entry})" for entry in node.deps]


class PlainSink(znflow.Node):
    def __init__(self, deps=None):
        self.deps = deps
        self.outs = []

    def run(self):
        self.outs = _received(self)


@dataclasses.dataclass
class DataclassSink(znflow.Node):
    deps: list = dataclasses.field(default_factory=list)
    outs: list = dataclasses.field(default_factory=list)

    def run(self):
        self.outs = _received(self)


class ZnInitSink(zninit.ZnInit, znflow.Node):
    deps = zninit.Descriptor(None)
    outs = zninit.Descriptor(None)

    def run(self):
        self.outs = _received(self)


@attrs.define
class AttrsSink(znflow.Node):
    deps: list = attrs.field(factory=list)
    outs: list = attrs.field(factory=list)

    def run(self):
        self.outs = _received(self)


class ModelSink(znflow.Node, pydantic.BaseModel):
    deps: list = []
    outs: list = []

    def run(self):
        self.outs = _received(self)


class ReversedModelSink(pydantic.BaseModel, znflow.Node):
    deps: list = []
    outs: list = []

    def run(self):
        self.outs = _received(self)


class ValidateAssignmentModelSink(znflow.Node, pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    deps: list = []
    outs: list = []

    def run(self):
        self.outs = _received(self)


class DepsBase(pydantic.BaseModel):
    """A pydantic base class that declares the fields itself."""

    deps: list = []
    outs: list = []


class InheritedModelSink(DepsBase, znflow.Node):
    def run(self):
        self.outs = _received(self)


@pydantic.dataclasses.dataclass
class PydanticDataclassSink(znflow.Node):
    deps: list = dataclasses.field(default_factory=list)
    outs: list = dataclasses.field(default_factory=list)

    def run(self):
        self.outs = _received(self)


@pydantic.dataclasses.dataclass(config=pydantic.ConfigDict(validate_assignment=True))
class ValidateAssignmentDataclassSink(znflow.Node):
    deps: list = dataclasses.field(default_factory=list)
    outs: list = dataclasses.field(default_factory=list)

    def run(self):
        self.outs = _received(self)


SINKS = [
    PlainSink,
    DataclassSink,
    ZnInitSink,
    AttrsSink,
    ModelSink,
    ReversedModelSink,
    ValidateAssignmentModelSink,
    InheritedModelSink,
    PydanticDataclassSink,
    ValidateAssignmentDataclassSink,
]


@pytest.mark.parametrize("cls", SINKS)
def test_connection_kwarg(cls):
    with znflow.DiGraph() as graph:
        sink = cls(deps=Source().outs)

    assert isinstance(sink.deps, znflow.Connection)
    edge = graph.get_edge_data(*list(graph.edges)[0][:2])
    assert edge[0] == {"u_attr": "outs", "v_attr": "deps"}
    graph.run()
    assert sink.outs == ["got(seed)"]


@pytest.mark.parametrize("cls", SINKS)
def test_connection_assignment(cls):
    with znflow.DiGraph() as graph:
        sink = cls()
        sink.deps = Source().outs

    assert graph.number_of_edges() == 1
    graph.run()
    assert sink.outs == ["got(seed)"]


@pytest.mark.parametrize("cls", SINKS)
def test_connection_list(cls):
    with znflow.DiGraph() as graph:
        sink = cls(deps=[Source(tag="a").outs, Source(tag="b").outs])

    assert graph.number_of_edges() == 2
    graph.run()
    assert sink.outs == ["got(['a'])", "got(['b'])"]


@pytest.mark.parametrize("cls", SINKS)
def test_connection_node(cls):
    with znflow.DiGraph() as graph:
        sink = cls(deps=[Source()])

    assert graph.number_of_edges() == 1
    graph.run()
    assert sink.outs == ["got(Source(tag='seed', outs=['seed']))"]


@pytest.mark.parametrize("cls", SINKS)
def test_connection_function_future(cls):
    with znflow.DiGraph() as graph:
        sink = cls(deps=source("future"))

    assert graph.number_of_edges() == 1
    graph.run()
    assert sink.outs == ["got(future)"]


def test_connection_positional():
    with znflow.DiGraph() as graph:
        sink = PydanticDataclassSink(Source().outs)

    assert graph.number_of_edges() == 1
    graph.run()
    assert sink.outs == ["got(seed)"]


def test_required_field():
    class Sink(znflow.Node, pydantic.BaseModel):
        deps: list
        outs: list = []

        def run(self):
            self.outs = _received(self)

    with znflow.DiGraph() as graph:
        sink = Sink(deps=Source().outs)

    graph.run()
    assert sink.outs == ["got(seed)"]
    with pytest.raises(pydantic.ValidationError):
        Sink()


def test_values_are_validated():
    assert ModelSink(deps=[1]).deps == [1]
    with pytest.raises(pydantic.ValidationError):
        ModelSink(deps=42)
    with znflow.DiGraph():
        with pytest.raises(pydantic.ValidationError):
            ModelSink(deps=42)


def test_constraints_are_validated():
    class Sink(znflow.Node, pydantic.BaseModel):
        count: int = pydantic.Field(default=1, gt=0)

        def run(self): ...

    with znflow.DiGraph():
        Sink(count=Source().outs)
        with pytest.raises(pydantic.ValidationError):
            Sink(count=-1)


def test_json_schema_is_unchanged():
    schema = json.dumps(ModelSink.model_json_schema(), sort_keys=True)
    with znflow.DiGraph():
        ModelSink(deps=Source().outs)

    assert json.dumps(ModelSink.model_json_schema(), sort_keys=True) == schema


def test_dataclass_fields_are_unchanged():
    types = [field.type for field in dataclasses.fields(PydanticDataclassSink)]
    with znflow.DiGraph():
        PydanticDataclassSink(deps=Source().outs)

    assert [field.type for field in dataclasses.fields(PydanticDataclassSink)] == types


def test_base_class_is_unchanged():
    with znflow.DiGraph():
        InheritedModelSink(deps=Source().outs)

    with pytest.raises(pydantic.ValidationError):
        DepsBase(deps=42)


def test_model_rebuild():
    with znflow.DiGraph():
        ModelSink(deps=Source().outs)

    ModelSink.model_rebuild(force=True)

    with znflow.DiGraph() as graph:
        sink = ModelSink(deps=Source().outs)

    graph.run()
    assert sink.outs == ["got(seed)"]


def test_model_dump():
    with znflow.DiGraph() as graph:
        sink = ModelSink(deps=Source().outs)

    graph.run()
    assert sink.model_dump() == {"deps": ["seed"], "outs": ["got(seed)"]}


def test_validators_see_connections():
    """A pydantic validator sees a connection, just like a '__post_init__'."""
    seen = []

    class Sink(znflow.Node, pydantic.BaseModel):
        deps: list = []

        @pydantic.model_validator(mode="after")
        def _collect(self):
            seen.append(type(self.__dict__["deps"]).__name__)
            return self

        def run(self): ...

    with znflow.DiGraph():
        Sink(deps=Source().outs)

    assert seen == ["Connection"]


def test_carries_connection():
    with znflow.DiGraph():
        connection = Source().outs
        assert znflow.carries_connection(connection)
        assert znflow.carries_connection([connection])
        assert znflow.carries_connection({"a": (connection,)})
        assert znflow.carries_connection(Source())
        assert znflow.carries_connection(source("future"))
    assert not znflow.carries_connection([1, 2])
    assert not znflow.carries_connection({"a": "b"})


def test_validated_assignment_keeps_the_graph_acyclic():
    """Pydantic reads the remaining fields while it validates an assignment."""
    with znflow.DiGraph() as graph:
        sink = ValidateAssignmentDataclassSink()
        sink.deps = Source().outs

    assert graph.number_of_edges() == 1
    assert [(u == v) for u, v in graph.edges()] == [False]
    assert isinstance(sink.__dict__["outs"], list)
    graph.run()
    assert sink.outs == ["got(seed)"]
