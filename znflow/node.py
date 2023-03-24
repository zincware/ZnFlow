from __future__ import annotations

import functools
import inspect
import uuid

from znflow.base import (
    Connection,
    FunctionFuture,
    NodeBaseMixin,
    disable_graph,
    empty,
    get_graph,
)


def _mark_init_in_construction(cls):
    if "__init__" in dir(cls):

        def wrap_init(func):
            if getattr(func, "_already_wrapped", False):
                # if the function is already wrapped, return it
                #  TODO this is solving the error but not the root cause
                return func

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                cls._in_construction = True
                value = func(*args, **kwargs)
                cls._in_construction = False
                return value

            wrapper._already_wrapped = True

            return wrapper

        cls.__init__ = wrap_init(cls.__init__)
    return cls


class Node(NodeBaseMixin):
    _in_construction = False

    def run(self):
        raise NotImplementedError

    def __matmul__(self, other):
        return Connection(self, other)

    def __new__(cls, *args, **kwargs):
        cls._in_construction = True
        try:
            instance = super().__new__(cls, *args, **kwargs)
        except TypeError:  # e.g. in dataclasses the arguments are passed to __new__
            # print("TypeError: ...")
            instance = super().__new__(cls)
        cls._in_construction = False
        _mark_init_in_construction(cls)
        instance.uuid = uuid.uuid4()

        # Connect the Node to the Grap
        graph = get_graph()
        if graph is not empty:
            graph.add_node(instance)
        return instance

    def __getattribute__(self, item):
        if item.startswith("_"):
            return super().__getattribute__(item)
        if self._graph_ not in [empty, None]:
            with disable_graph():
                if item not in set(dir(self)):
                    raise AttributeError(
                        f"'{self.__class__.__name__}' object has no attribute '{item}'"
                    )

            if item not in type(self)._protected_:
                if self._in_construction:
                    return super().__getattribute__(item)
                return Connection(instance=self, attribute=item)
        return super().__getattribute__(item)

    def __setattr__(self, item, value) -> None:
        super().__setattr__(item, value)
        if self._graph_ not in [empty, None] and isinstance(value, Connection):
            assert self.uuid in self._graph_, f"'{self.uuid=}' not in '{self._graph_=}'"
            assert value.uuid in self._graph_
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
        if graph is not empty:
            # check if the args / kwargs match the function
            inspect.signature(function).bind(*args, **kwargs)

            future = FunctionFuture(function, args, kwargs)
            future.uuid = uuid.uuid4()

            graph.add_node(future)
            return future
        return function(*args, **kwargs)

    return wrapper
