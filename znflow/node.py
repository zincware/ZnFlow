from __future__ import annotations

import functools
import uuid

from znflow.base import Connection, FunctionFuture, NodeBaseMixin, get_graph


def _mark_init_in_construction(cls):
    if "__init__" in dir(cls):

        def wrap_init(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                cls._in_construction = True
                value = func(*args, **kwargs)
                cls._in_construction = False
                return value

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
        cls = _mark_init_in_construction(cls)
        instance.uuid = uuid.uuid4()

        # Connect the Node to the Grap
        graph = get_graph()
        if graph is not None:
            graph.add_node(instance)
        return instance

    def __getattribute__(self, item):
        value = super().__getattribute__(item)
        if get_graph() is not None:
            if item not in type(self)._protected_ and not item.startswith("_"):
                if self._in_construction:
                    return value
                connector = Connection(instance=self, attribute=item)
                return connector
        return value

    def __setattr__(self, item, value) -> None:
        if get_graph() is not None:
            if isinstance(value, Connection):
                assert (
                    self.uuid in self._graph_
                ), f"'{self.uuid=}' not in '{self._graph_=}'"
                assert value.uuid in self._graph_
                self._graph_.add_edge(
                    value.uuid, self.uuid, u_attr=value.attribute, v_attr=item
                )
        super().__setattr__(item, value)


def nodify(function):
    """Decorator to create a Node from a function."""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        """Wrapper function for the decorator."""
        graph = get_graph()
        if graph is not None:
            future = FunctionFuture(function, args, kwargs)
            future.uuid = uuid.uuid4()

            graph.add_node(future)
            return future
        return function(*args, **kwargs)

    return wrapper
