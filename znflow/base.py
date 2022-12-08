from __future__ import annotations

import contextlib
import functools


def disable_dag(func):
    """Decorator to disable DiGraph in 'NodeBaseMixin'."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with update__graph_():
            return func(*args, **kwargs)

    return wrapper


@contextlib.contextmanager
def update__graph_(value=None):
    """Temporarily update the DiGraph in 'NodeBaseMixin'."""
    dag = NodeBaseMixin._graph_
    NodeBaseMixin._graph_ = value
    try:
        yield
    finally:
        NodeBaseMixin._graph_ = dag


class NodeBaseMixin:
    """A Parent for all Nodes.

    This class is used to globally access and change all classes that inherit from it.
    """

    _graph_ = None
