import znflow


class PlainNode(znflow.Node):
    """A Node with the 'result' attribute.

    'result' had been used internally before.
    """

    @property
    def result(self):
        raise TypeError("This value is not available until the node is run.")


def test_PlainNode():
    with znflow.DiGraph():
        node1 = PlainNode()
        con = node1.result

    assert isinstance(con, znflow.Connection)
