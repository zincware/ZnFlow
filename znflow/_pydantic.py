"""Support for 'pydantic' based Nodes.

Between building the graph and 'graph.run()' a field of a Node holds a
connection - a 'Connection', a 'CombinedConnections', a 'FunctionFuture' or a
'Node' - instead of the actual value. Pydantic validates every field against its
annotation, so it would coerce or reject such a connection. The helpers below let
connections pass the pydantic validation of every field, so a connection reaches
a pydantic Node the same way it reaches a dataclass or a plain class.
"""

import copy
import functools
import typing

from znflow.base import (
    CombinedConnections,
    Connection,
    FunctionFuture,
    NodeBaseMixin,
)

_CONNECTION = (Connection, CombinedConnections, FunctionFuture, NodeBaseMixin)
_VALIDATOR = "_znflow_connection_validator"


def carries_connection(value) -> bool:
    """Check if the value is or contains a connection to another Node.

    Parameters
    ----------
    value : any
        The value to inspect. Lists, tuples, sets and dicts are inspected
        recursively, matching the containers 'znflow.utils.IterableHandler'
        walks when it collects connections and replaces them by their results.

    Returns
    -------
    bool
        True if the value is a connection or holds one.
    """
    if isinstance(value, _CONNECTION):
        return True
    if isinstance(value, (list, tuple, set)):
        return any(carries_connection(item) for item in value)
    if isinstance(value, dict):
        return any(carries_connection(item) for item in value.values())
    return False


def _skip_connections(value, handler):
    """Validate the value unless it carries a connection."""
    if carries_connection(value):
        return value
    return handler(value)


def allow_connections(cls) -> None:
    """Let connections pass the pydantic validation of every field.

    The validator of the class is rebuilt once, on the first instantiation, and
    again whenever someone else rebuilds the class. Classes without a pydantic
    validator are left untouched.

    Parameters
    ----------
    cls : type
        The 'znflow.Node' subclass to prepare.
    """
    validator = getattr(cls, "__pydantic_validator__", None)
    if validator is None:
        return
    if cls.__dict__.get(_VALIDATOR) is validator:
        return

    import pydantic

    fields = getattr(cls, "__pydantic_fields__", None) or getattr(cls, "model_fields", {})
    if not fields:
        return

    wrap = pydantic.WrapValidator(_skip_connections)

    if issubclass(cls, pydantic.BaseModel):
        for name, field in fields.items():
            patched = copy.copy(field)
            patched.metadata = [*field.metadata, wrap]
            fields[name] = patched
        cls.model_rebuild(force=True, _parent_namespace_depth=0)
    else:
        # 'rebuild_dataclass' collects the fields from '__dataclass_fields__'
        # again, so the annotation is patched for the rebuild and restored after.
        annotations = {}
        for name, field in fields.items():
            dataclass_field = cls.__dataclass_fields__[name]
            annotations[name] = dataclass_field.type
            annotation = typing.Any if field.annotation is None else field.annotation
            dataclass_field.type = typing.Annotated[
                tuple([annotation, *field.metadata, wrap])
            ]
        try:
            pydantic.dataclasses.rebuild_dataclass(
                cls, force=True, _parent_namespace_depth=0
            )
        finally:
            for name, annotation in annotations.items():
                cls.__dataclass_fields__[name].type = annotation

    _wrap_setattr(cls)
    setattr(cls, _VALIDATOR, cls.__pydantic_validator__)


def _wrap_setattr(cls) -> None:
    """Keep the graph out of the pydantic validation of an assignment.

    'validate_assignment' makes pydantic install a '__setattr__' on the class
    which validates through 'validate_assignment'. Pydantic reads the remaining
    fields with 'getattr' on the way, which inside a graph yields a 'Connection'
    to the instance itself. The instance is marked for the length of the call, so
    that 'Node.__getattribute__' hands back the stored value.
    """
    func = cls.__dict__.get("__setattr__")
    if func is None or hasattr(func, "_znflow_func"):
        return

    @functools.wraps(func)
    def wrapper(self, item, value):
        object.__setattr__(self, "_in_validation", True)
        try:
            func(self, item, value)
        finally:
            object.__setattr__(self, "_in_validation", False)

    wrapper._znflow_func = func

    cls.__setattr__ = wrapper
