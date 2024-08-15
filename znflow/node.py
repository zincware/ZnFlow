from __future__ import annotations

import functools
import inspect
import uuid

from znflow.base import (
    Connection,
    FunctionFuture,
    NodeBaseMixin,
    disable_graph,
    empty_graph,
    get_graph,
)


def _mark_init_in_construction(cls, this_uuid=None):
    if "__init__" in dir(cls):

        def wrap_init(func):
            if hasattr(func, "_znflow_func"):
                # we wrap the original function, thereby updating the
                # uuid to be unique.
                func = func._znflow_func

            @functools.wraps(cls.__init__)
            def wrapper(self, *args, **kwargs):
                func(self, *args, **kwargs)
                self._in_construction = False
                if this_uuid is not None:
                    self._uuid = this_uuid

            wrapper._znflow_func = func

            return wrapper

        cls.__init__ = wrap_init(cls.__init__)
    return cls


class Node(NodeBaseMixin):
    _in_construction = True

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

        try:
            instance.uuid = this_uuid
            _mark_init_in_construction(cls, None)
        except AttributeError:
            # pydantic edge case
            _mark_init_in_construction(cls, this_uuid)

        # Connect the Node to the Graph
        graph = get_graph()
        if graph is not empty_graph:
            graph.add_node(instance, this_uuid=this_uuid)
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
                if self._in_construction:
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
                    self._graph_.add_node(value.instance)
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

            graph.add_node(future)
            return future
        return function(*args, **kwargs)

    return wrapper
