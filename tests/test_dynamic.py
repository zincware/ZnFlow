import dataclasses

import znflow


@dataclasses.dataclass
class AddOne(znflow.Node):
    inputs: float
    outputs: float = None

    def run(self):
        # if self.outputs is not None:
        #     raise ValueError("Node has already been run")
        self.outputs = self.inputs + 1


def test_break_loop():
    """Test loop breaking when output exceeds 5."""
    graph = znflow.DiGraph()
    with graph:
        node1 = AddOne(inputs=1)
        for _ in range(10):
            node1 = AddOne(inputs=node1.outputs)
            if znflow.resolve(node1.outputs) > 5:
                break

    graph.run()

    # Assert the correct number of nodes in the graph
    assert len(graph) == 5

    # Assert the final output value
    assert node1.outputs == 6


def test_break_loop_multiple():
    """Test loop breaking with multiple nodes and different conditions."""
    graph = znflow.DiGraph()
    with graph:
        node1 = AddOne(inputs=1)
        node2 = AddOne(inputs=node1.outputs)  # Add another node in the loop

        for _ in range(10):
            node1 = AddOne(inputs=node1.outputs)
            node2 = AddOne(inputs=node2.outputs)

            # Break if either node's output exceeds 5 or both reach 3
            if (
                znflow.resolve(node1.outputs) > 5
                or znflow.resolve(node2.outputs) > 5
                or znflow.resolve(node1.outputs) == 3
                and znflow.resolve(node2.outputs) == 3
            ):
                break

    graph.run()

    # Assert the correct number of nodes in the graph
    assert len(graph) <= 10  # Maximum number of iterations allowed

    # Assert that at least one node's output exceeds 5 or both reach 3
    assert (znflow.resolve(node1.outputs) > 5 or
            znflow.resolve(node2.outputs) > 5 or
            znflow.resolve(node1.outputs) == 3 and znflow.resolve(node2.outputs) == 3)


def test_resolvce_only_run_relevant_nodes():
    """Test that when using resolve only nodes that are direct predecessors are run."""
    # Check by asserting None to the output of the second node
    graph = znflow.DiGraph()
    with graph:
        node1 = AddOne(inputs=1)
        node2 = AddOne(inputs=1234)
        for _ in range(10):
            node1 = AddOne(inputs=node1.outputs)
            if znflow.resolve(node1.outputs) > 5:
                break
    
    # this has to be executed, because of the resolve
    assert node1.outputs == 6 
    
    # this should not be executed, because it is not relevant to the resolve
    assert node2.outputs is None 

    graph.run()
    assert node2.outputs == 1235
    assert node1.outputs == 6
