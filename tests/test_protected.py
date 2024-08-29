import znflow


class MyNode(znflow.Node):
    _protected_ = znflow.Node._protected_ + ["a"]

    a: int = 42
    b: int = 42


def test_protected():
    with znflow.DiGraph():
        node = MyNode()
        assert node.a == 42
        assert isinstance(node.b, znflow.Connection)
