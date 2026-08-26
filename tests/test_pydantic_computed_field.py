"""Tests for 'znflow.pydantic.computed_field'."""

import functools

import pydantic
import pytest
from pydantic_core import PydanticSerializationError

import znflow


class Source(znflow.Node, pydantic.BaseModel):
    out: list = []

    def run(self):
        self.out = [1, 2, 3]


class Frames(znflow.Node, pydantic.BaseModel):
    data: list = []

    @znflow.pydantic.computed_field
    def frames(self) -> list:
        return [f"x({value})" for value in self.data]

    def run(self): ...


class Sink(znflow.Node, pydantic.BaseModel):
    inputs: list = []

    def run(self): ...


class Scaled(znflow.Node, pydantic.BaseModel):
    """A computed field that reads a plain field next to a connected one."""

    factor: float = 2.0
    data: list = []

    @znflow.pydantic.computed_field
    def scaled(self) -> float:
        return self.factor * 10

    def run(self): ...


def test_computed_field_in_model():
    assert "frames" in Frames.model_computed_fields


def test_json_schema():
    assert list(Frames.model_json_schema()["properties"]) == ["data"]

    schema = Frames.model_json_schema(mode="serialization")
    assert schema["properties"]["frames"]["readOnly"] is True
    assert "frames" in schema["required"]


def test_connectable_in_graph():
    with znflow.DiGraph() as graph:
        source = Source()
        frames = Frames(data=source.out)
        assert isinstance(frames.frames, znflow.Connection)
        sink = Sink(inputs=frames.frames)

    assert graph.has_edge(frames.uuid, sink.uuid)


def test_computed_after_run():
    with znflow.DiGraph() as graph:
        source = Source()
        frames = Frames(data=source.out)

    graph.run()

    assert frames.frames == ["x(1)", "x(2)", "x(3)"]
    assert frames.model_dump() == {
        "data": [1, 2, 3],
        "frames": ["x(1)", "x(2)", "x(3)"],
    }
    assert frames.model_dump_json() == '{"data":[1,2,3],"frames":["x(1)","x(2)","x(3)"]}'


def test_unresolved_raises():
    """Reading the computed field before 'graph.run()' names the connected field."""
    with znflow.DiGraph():
        source = Source()
        frames = Frames(data=source.out)

    with pytest.raises(
        znflow.exceptions.UnresolvedConnectionError, match="'Frames.data'"
    ):
        frames.frames


def test_unconnected_node_computes():
    """Without an upstream connection the guard stays quiet."""
    with znflow.DiGraph():
        frames = Frames(data=[7])

    assert frames.frames == ["x(7)"]


def test_reads_plain_attribute_in_graph():
    """A plain field is the value itself and not a connection to the Node."""
    with znflow.DiGraph():
        source = Source()
        scaled = Scaled(factor=3.0, data=source.out)

    assert scaled.scaled == 30.0


def test_missing_return_annotation():
    with pytest.raises(TypeError, match="has no return annotation"):

        class Broken(znflow.Node, pydantic.BaseModel):
            @znflow.pydantic.computed_field
            def value(self):
                return 1

            def run(self): ...


def test_return_type_keyword():
    """'return_type' replaces the annotation, and keywords reach pydantic."""

    class Titled(znflow.Node, pydantic.BaseModel):
        @znflow.pydantic.computed_field(return_type=int, title="Answer")
        def value(self):
            return 42

        def run(self): ...

    assert Titled().value == 42
    schema = Titled.model_json_schema(mode="serialization")
    assert schema["properties"]["value"]["title"] == "Answer"


def test_repr_skips_the_computed_field():
    """The repr of a Node does not read a value that does not exist yet."""
    with znflow.DiGraph():
        source = Source()
        frames = Frames(data=source.out)

    assert "frames" not in repr(frames)


def test_protected_pydantic_api():
    """The pydantic API stays callable while the graph is built."""
    with znflow.DiGraph():
        source = Source()
        frames = Frames(data=source.out)

        assert callable(frames.model_dump)
        assert isinstance(frames.data, znflow.Connection)


def test_model_dump_in_graph():
    """While the graph is built a dump holds the connections, and not values."""
    with znflow.DiGraph():
        source = Source()
        frames = Frames(data=source.out)

        with pytest.warns(UserWarning, match="serializer warnings"):
            assert list(frames.model_dump()) == ["data", "frames"]

        # the computed field points back at the Node it belongs to
        with pytest.raises(PydanticSerializationError, match="Circular"):
            frames.model_dump_json()


def test_property_as_getter():
    """A 'property' or a 'znflow.Property' is accepted as the getter."""

    class FromProperty(znflow.Node, pydantic.BaseModel):
        data: list = []

        @znflow.pydantic.computed_field
        @property
        def size(self) -> int:
            return len(self.data)

        def run(self): ...

    assert FromProperty(data=[1, 2]).size == 2


def test_guard_covers_a_direct_call():
    """Calling the getter directly is guarded, not only attribute access."""
    with znflow.DiGraph():
        source = Source()
        frames = Frames(data=source.out)

    with pytest.raises(znflow.exceptions.UnresolvedConnectionError):
        Frames.frames.fget(frames)


def test_guard_covers_another_node():
    """The guard reaches as far as 'disable_graph' does, not only 'self'."""
    other = None

    class Reader(znflow.Node, pydantic.BaseModel):
        @znflow.pydantic.computed_field
        def size(self) -> int:
            return len(other.data)

        def run(self): ...

    with znflow.DiGraph():
        source = Source()
        other = Frames(data=source.out)
        reader = Reader()

    with pytest.raises(
        znflow.exceptions.UnresolvedConnectionError, match="'Frames.data'"
    ):
        reader.size


def test_a_connected_node_field_is_guarded():
    """A field that was given a Node holds a connection once the graph is left."""

    class Reader(znflow.Node, pydantic.BaseModel):
        other: Frames = None

        @znflow.pydantic.computed_field
        def size(self) -> int:
            return len(self.other.data)

        def run(self): ...

    with znflow.DiGraph():
        source = Source()
        frames = Frames(data=source.out)
        reader = Reader(other=frames)

    with pytest.raises(
        znflow.exceptions.UnresolvedConnectionError, match="'Reader.other'"
    ):
        reader.size


def test_guard_is_released_after_an_error():
    """The graph and the guard survive a getter that raised."""
    with znflow.DiGraph() as graph:
        source = Source()
        frames = Frames(data=source.out)

        with pytest.raises(znflow.exceptions.UnresolvedConnectionError):
            Frames.frames.fget(frames)

        assert znflow.get_graph() is graph
        assert isinstance(frames.data, znflow.Connection)


def test_getter_is_not_called_while_the_graph_is_built():
    """Leaving the graph does not read a value that does not exist yet."""
    calls = []

    class Counted(znflow.Node, pydantic.BaseModel):
        data: list = []

        @znflow.pydantic.computed_field
        def frames(self) -> list:
            calls.append(1)
            return list(self.data)

        def run(self): ...

    with znflow.DiGraph() as graph:
        source = Source()
        counted = Counted(data=source.out)

    assert calls == []

    graph.run()
    assert calls == []

    assert counted.frames == [1, 2, 3]
    assert calls == [1]


def test_cached_property_is_rejected():
    with pytest.raises(TypeError, match="cached_property"):

        class Cached(znflow.Node, pydantic.BaseModel):
            @znflow.pydantic.computed_field
            @functools.cached_property
            def value(self) -> int:
                return 1

            def run(self): ...


def test_module_is_not_pydantic():
    assert znflow.pydantic is not pydantic
    assert znflow.pydantic.computed_field is not pydantic.computed_field
    assert znflow.pydantic.carries_connection is znflow.carries_connection
