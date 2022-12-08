"""The 'ZnFlow' visualization module."""
import math

import networkx as nx


def get_count(node, graph) -> int:
    """Get the number of successors for the given node."""
    successors = list(graph.predecessors(node))
    return sum(get_count(x, graph) for x in successors) if len(successors) else 1


def get_colors(graph, log) -> list:
    """Get the color for each Node on the graph."""
    colors = [get_count(node, graph) for node in graph]
    return [math.log(x) for x in colors] if log else colors


def draw(graph, *args, log=True, **kwargs):
    """Draw the graph using networkx."""
    nx.draw(graph, *args, node_color=get_colors(graph, log), **kwargs)
