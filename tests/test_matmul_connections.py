import dataclasses

import znflow


@dataclasses.dataclass
class Node(znflow.Node):
    inputs: int
    outputs: int = None

    def run(self):
        self.outputs = self.inputs * 2


def test_connect_nodes():
    node1 = Node(inputs=25)
    node2 = Node(inputs=node1 @ "outputs")
    print(f"{node1.outputs = }")
    print(f'{node1 @ "outputs" = }')
    print(f"{node2 = }")

    graph = znflow.DiGraph()
    graph.write_graph(node1, node2)

    assert node1.uuid in graph
    assert node2.uuid in graph

    edge: dict = graph.get_edge_data(node1.uuid, node2.uuid)
    assert edge is not None
    # we have one connection, so we use 0
    assert edge[0]["v_attr"] == "inputs"
    assert edge[0]["u_attr"] == "outputs"

    graph.run()
    assert node1.outputs == 50
    assert len(graph) == 2

    # Try again with passing a list
    graph = znflow.DiGraph()
    graph.write_graph([node1, node2])
    graph.run()
    assert node1.outputs == 50
    assert len(graph) == 2
