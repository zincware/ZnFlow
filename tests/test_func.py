import pytest

import znflow


@znflow.nodify
def add(a, b):
    return a + b


def test_add():
    assert add(1, 2) == 3
    with znflow.DiGraph() as graph:
        out = add(1, 2)

    graph.run()
    assert out.result == 3


@pytest.mark.parametrize(
    ("args", "kwargs"),
    [(tuple(), dict()), ((5,), dict()), (tuple(), {"a": 5}), ((5, 6), {"a": 7})],
)
def test_add_args(args, kwargs):
    with pytest.raises(TypeError):
        add(*args, **kwargs)

    with pytest.raises(TypeError):
        with znflow.DiGraph():
            add(*args, **kwargs)
