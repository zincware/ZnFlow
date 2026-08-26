"""Computed fields for 'pydantic' based Nodes.

A computed attribute is a graph visible port: inside a 'znflow.DiGraph' reading
it yields a 'Connection', so another Node can be connected to it, and outside the
graph it is computed from the fields it reads. 'pydantic.computed_field' makes
such an attribute part of the model and of its serialization JSON Schema.

The getter runs with the graph disabled, so a plain field it reads is the value
itself and not a 'Connection' to the Node the getter belongs to. A field that is
connected to another Node holds a value that only exists once the graph has run,
so reading it inside a getter raises 'UnresolvedConnectionError'.

Examples
--------
>>> import znflow
>>> import pydantic
>>> class Source(znflow.Node, pydantic.BaseModel):
...     out: list = []
...     def run(self):
...         self.out = [1, 2, 3]
>>> class Frames(znflow.Node, pydantic.BaseModel):
...     data: list = []
...     @znflow.pydantic.computed_field
...     def frames(self) -> list:
...         return [f"x({value})" for value in self.data]
...     def run(self): ...
>>> with znflow.DiGraph() as graph:
...     source = Source()
...     frames = Frames(data=source.out)
>>> graph.run()
>>> frames.frames
['x(1)', 'x(2)', 'x(3)']
"""

import functools

import pydantic

from znflow._pydantic import carries_connection
from znflow.base import NodeBaseMixin, Property, disable_graph

__all__ = ["computed_field", "carries_connection"]


def _guard(func):
    """Run the function with the graph disabled and the connection guard on.

    The flag is set on 'NodeBaseMixin', so that it reaches as far as
    'disable_graph' does: every Node the getter reads hands back its stored
    values, and every one of them is guarded. 'previous' is restored instead of
    cleared, so that one guarded getter can read another.

    Parameters
    ----------
    func : callable
        The getter to wrap. It receives the Node as its first argument.

    Returns
    -------
    callable
        The wrapped getter.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        previous = NodeBaseMixin._in_property_
        NodeBaseMixin._in_property_ = True
        try:
            with disable_graph():
                return func(self, *args, **kwargs)
        finally:
            NodeBaseMixin._in_property_ = previous

    return wrapper


class GraphProperty(property):
    """A 'property' whose getter runs outside the graph.

    Subclassing 'property' is what makes pydantic accept the descriptor: it
    reads the return annotation through '.fget' and 'znflow.DiGraph' skips the
    getter while it collects the attributes of a Node.
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        super().__init__(
            None if fget is None else _guard(fget),
            None if fset is None else _guard(fset),
            None if fdel is None else _guard(fdel),
            doc,
        )


def _getter(func):
    """Get the plain function out of whatever the decorator was handed.

    Raises
    ------
    TypeError
        If the decorated object is a 'functools.cached_property'. It keeps the
        first value it computes, which inside a graph is the value from before
        'graph.run()'.
    """
    if isinstance(func, functools.cached_property):
        raise TypeError(
            "'functools.cached_property' keeps the first value it computes,"
            " which inside a graph is the value from before 'graph.run()'."
            " Use a plain method or a 'property'."
        )
    if isinstance(func, (property, Property)):
        return func.fget
    if isinstance(func, (classmethod, staticmethod)):
        return func.__func__
    return func


def computed_field(func=None, /, **kwargs):
    """Turn a method into a computed field of a pydantic Node.

    Inside a 'znflow.DiGraph' the attribute is a 'Connection', so it can be
    connected to another Node. Outside the graph it is computed and it is part
    of 'model_dump' and of 'model_json_schema(mode="serialization")'.

    Parameters
    ----------
    func : callable or property, optional
        The getter. A plain function, a 'property' or a 'znflow.Property' are
        all accepted. Left out when the decorator is called with keywords.
    **kwargs
        Passed on to 'pydantic.computed_field', e.g. 'alias', 'title',
        'description', 'repr', 'return_type', 'deprecated', 'examples' or
        'json_schema_extra'. 'repr' defaults to False here, because pydantic
        builds the repr of a Node by reading every computed field, which inside
        a graph is a value that does not exist yet. Pass 'repr=True' for a
        computed field that reads plain values only.

    Returns
    -------
    pydantic.fields.ComputedFieldInfo
        The decorated attribute, or the decorator itself when called with
        keywords.

    Raises
    ------
    TypeError
        If the getter has no return annotation and no 'return_type' is given.
        Pydantic needs the type to build the serialization schema.

    Examples
    --------
    >>> import znflow
    >>> import pydantic
    >>> class Frames(znflow.Node, pydantic.BaseModel):
    ...     data: list = []
    ...     @znflow.pydantic.computed_field
    ...     def frames(self) -> list:
    ...         return [f"x({value})" for value in self.data]
    ...     def run(self): ...
    >>> Frames(data=[1]).frames
    ['x(1)']
    """
    if func is None:
        return functools.partial(computed_field, **kwargs)

    kwargs.setdefault("repr", False)
    getter = _getter(func)
    if "return_type" not in kwargs:
        annotation = getattr(getter, "__annotations__", {}).get("return")
        if annotation is None:
            raise TypeError(
                f"'{getattr(getter, '__qualname__', getter)}' has no return"
                " annotation. Annotate the getter, e.g. 'def frames(self) ->"
                " list:', or pass 'return_type' to 'computed_field'."
            )
        kwargs["return_type"] = annotation

    return pydantic.computed_field(GraphProperty(getter), **kwargs)
