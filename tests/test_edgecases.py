import znflow


class PlainNode(znflow.Node):
    """A Node with the 'result' attribute.

    'result' had been used internally before.
    """

    @property
    def result(self):
        raise TypeError("This value is not available until the node is run.")


class ConnectResults(znflow.Node):
    @property
    def result(self):
        return 42

    def run(self):
        pass


@znflow.nodify
def add_one(x):
    return x + 1


def test_PlainNode():
    with znflow.DiGraph():
        node1 = PlainNode()
        con = node1.result

    assert isinstance(con, znflow.Connection)


def test_ConnectResults():
    with znflow.DiGraph() as graph:
        node1 = ConnectResults()
        con = node1.result
        outs = add_one(con)

    assert isinstance(con, znflow.Connection)

    graph.run()
    assert outs.result == 43
