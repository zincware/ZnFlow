from __future__ import annotations

import functools
import uuid

from znflow.base import FunctionFuture, NodeBaseMixin, get_graph


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
