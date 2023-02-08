from __future__ import annotations

import functools
import uuid

from znflow.base import Connection, FunctionFuture, NodeBaseMixin, get_graph


class Node(NodeBaseMixin):
    def __new__(cls, *args, **kwargs):
        try:
            instance = super().__new__(cls, *args, **kwargs)
        except TypeError:  # e.g. in dataclasses the arguments are passed to __new__
            # print("TypeError: ...")
            instance = super().__new__(cls)

        instance.uuid = uuid.uuid4()

        # Connect the Node to the Grap
        graph = get_graph()
        if graph is not None:
            graph.add_node(instance)
        return instance

    def __getattribute__(self, item):
        value = super().__getattribute__(item)
        if get_graph() is not None:
            if (
                item not in type(self)._protected_
                and not item.startswith("__")
                and not item.startswith("_")
            ):
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
                    value.uuid, self.uuid, i_attr=value.attribute, j_attr=item
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
