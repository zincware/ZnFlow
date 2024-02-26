import dis
from znflow.node import Node
from znflow.base import Connection, disable_graph, get_graph
import typing as t

def resolve(value: Connection| t.Any):
    # TODO: support nodify as well
    if not isinstance(value, (Connection)):
        raise ValueError(f"Expected a Node, got {value}")
    # get the actual value
    with disable_graph():
        # if the node has not been run yet, run it
        result = value.result
    if result is None:
        graph = get_graph()
    
    with disable_graph():
        graph.run()
        result = value.result
    return result
