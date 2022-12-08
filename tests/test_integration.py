"""Some 'ZnFlow' integration tests."""

import znflow.connectors


class Node(znflow.Node):
    inputs = znflow.EdgeAttribute()
    outputs = znflow.EdgeAttribute(None)

    def run(self):
        self.outputs = self.inputs * 2


@znflow.nodify
def add(*args):
    return sum(args)


def test_single_node_creation():
    with znflow.DiGraph() as dag:
        node = Node(inputs=2)
        assert node.inputs == znflow.connectors.NodeConnector(
            graph=dag, node=node, attribute="inputs"
        )
    assert node in dag
    # access to the attribute outside the graph works just fine
    assert node.inputs == 2
    node.run()
    assert node.outputs == 4

    node = Node(inputs=2)
    assert node.inputs == 2
    node.run()
    assert node.outputs == 4


def test_single_nodify_creation():
    with znflow.DiGraph() as dag:
        func = add(1, 2, 3)
        assert isinstance(func, znflow.connectors.FunctionConnector)
        assert func.graph == dag
        assert func.args == (1, 2, 3)

    assert func in dag

    assert func.get_result() == 6
    assert add(1, 2, 3) == 6
