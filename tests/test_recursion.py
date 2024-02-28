import contextlib
import sys

import pytest

import znflow


class AddOne(znflow.Node):
    def __init__(self, x):
        super().__init__()
        self.x = x

    def run(self):
        self.x += 1


@contextlib.contextmanager
def setrecursionlimit(limit: int):
    """Set the recursion limit for the duration of the context manager."""
    _limit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(limit)
        yield
    finally:
        sys.setrecursionlimit(_limit)


@pytest.mark.parametrize(
    "deployment",
    ["vanilla_deployment"],
    # "dask_deployment" struggles with recursion limit
)
@pytest.mark.parametrize("depth", [1, 10, 100, 1000])
def test_AddOneLoop(depth, deployment, request):
    deployment = request.getfixturevalue(deployment)
    with setrecursionlimit(100):
        with znflow.DiGraph(deployment=deployment) as graph:
            start = AddOne(0)
            for _ in range(depth):
                start = AddOne(start.x)

        graph.run()
        assert len(graph.nodes) == depth + 1
        assert start.x == depth + 1


@pytest.mark.parametrize("depth", [1, 10, 100, 1000])
def test_AddOneLoopNoGraph(depth):
    with setrecursionlimit(100):
        start = AddOne(0)
        start.run()
        for _ in range(depth):
            start = AddOne(start.x)
            start.run()

        assert start.x == depth + 1
