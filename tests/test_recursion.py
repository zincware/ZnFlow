import znflow
import pytest
import sys


class AddOne(znflow.Node):
    def __init__(self, x):
        super().__init__()
        self.x = x

    def run(self):
        self.x += 1


# @pytest.mark.parametrize("depth", [1, 10, 100, 1000])
# def test_AddOneLoop(depth):
#     try:
#         sys.setrecursionlimit(100) # TODO REMOVE
#         with znflow.DiGraph() as graph:
#             start = AddOne(0)
#             for _ in range(depth):
#                 start = AddOne(start.x)

#         graph.run()
#         assert len(graph.nodes) == depth + 1
#         assert start.x == depth + 1
#     finally:
#         sys.setrecursionlimit(1000)


@pytest.mark.parametrize("depth", [1, 10, 100, 1000])
def test_AddOneLoopNoGraph(depth):
    try:
        sys.setrecursionlimit(100)  # TODO REMOVE
        start = AddOne(0)
        start.run()
        for _ in range(depth):
            start = AddOne(start.x)
            start.run()

        assert start.x == depth + 1
    finally:
        sys.setrecursionlimit(1000)
