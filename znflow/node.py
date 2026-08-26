from __future__ import annotations

import functools
import inspect
import uuid

from znflow._pydantic import allow_connections
from znflow.base import (
    Connection,
    FunctionFuture,
    NodeBaseMixin,
    disable_graph,
    empty_graph,
    get_graph,
)


def _get_init(cls):
    """Get the '__init__' of the class without any znflow wrapper.

    A class without an own '__init__' is wrapped as well, so that
    '_in_construction' is unset. Such a wrapper is skipped here, because a base
    class of 'cls' may define the '__init__' that is to be wrapped.
    """
    for klass in cls.__mro__:
        func = klass.__dict__.get("__init__")
        if func is None:
            continue
        func = getattr(func, "_znflow_func", func)
        if func is object.__init__ and klass is not object:
            continue
        return func
    return None


def _mark_init_in_construction(cls):
    func = _get_init(cls)
    if func is not None:

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if func is object.__init__:
                func(self)
            else:
                func(self, *args, **kwargs)
            object.__setattr__(self, "_in_construction", False)
            this_uuid = getattr(self, "_uuid", None)
            if this_uuid is not None:
                object.__setattr__(self, "_uuid", this_uuid)

        wrapper._znflow_func = func

        cls.__init__ = wrapper
    return cls


class Node(NodeBaseMixin):
    def run(self):
        raise NotImplementedError

    def __matmul__(self, other):
        return Connection(self, other)

    def __new__(cls, *args, **kwargs):
        this_uuid = uuid.uuid4()
        try:
            instance = super().__new__(cls, *args, **kwargs)
        except TypeError:
            # e.g. in dataclasses the arguments are passed to __new__
            # but even dataclasses seem to have an __init__ afterwards.
            # print("TypeError: ...")
            instance = super().__new__(cls)

        object.__setattr__(instance, "_uuid", this_uuid)
        allow_connections(cls)
        _mark_init_in_construction(cls)

        # Connect the Node to the Graph
        graph = get_graph()
        if graph is not empty_graph:
            graph.add_znflow_node(instance, this_uuid=this_uuid)
        return instance

    def __getattribute__(self, item: str):
        if item.startswith("_"):
            return super().__getattribute__(item)
        if self._graph_ not in [empty_graph, None]:
            with disable_graph():
                if item not in set(dir(self)):
                    raise AttributeError(
                        f"'{self.__class__.__name__}' object has no attribute '{item}'"
                    )

            if item not in self._protected_:
                if self._in_construction or self._in_validation:
                    return super().__getattribute__(item)
                return Connection(instance=self, attribute=item)
        return super().__getattribute__(item)

    def __setattr__(self, item, value) -> None:
        super().__setattr__(item, value)
        if self._graph_ not in [empty_graph, None] and isinstance(value, Connection):
            if self.uuid not in self._graph_:
                # self._external_ must be False
                raise ValueError(f"'{self.uuid=}' not in '{self._graph_=}'")
            if value.uuid not in self._graph_:
                if value._external_:
                    self._graph_.add_znflow_node(value.instance)
                else:
                    raise ValueError(f"'{value.uuid=}' not in '{self._graph_=}'")

            self._graph_.add_edge(
                value.uuid, self.uuid, u_attr=value.attribute, v_attr=item
            )


def nodify(function):
    """Decorator to create a Node from a function."""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        """Wrapper function for the decorator.

        Raises
        ------
        TypeError:
            if the args / kwargs do not match the function signature
        """
        graph = get_graph()
        if graph is not empty_graph:
            # check if the args / kwargs match the function
            inspect.signature(function).bind(*args, **kwargs)

            future = FunctionFuture(function, args, kwargs)
            future.uuid = uuid.uuid4()

            graph.add_znflow_node(future)
            return future
        return function(*args, **kwargs)

    return wrapper
