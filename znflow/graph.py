import networkx as nx

from znflow.base import NodeBaseMixin, get_graph, set_graph


class DiGraph(nx.MultiDiGraph):
    def __enter__(self):
        if get_graph() is not None:
            raise ValueError("DiGraph already exists. Nested Graphs are not supported.")
        set_graph(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if get_graph() is not self:
            raise ValueError(
                "Something went wrong. DiGraph was changed inside the context manager."
            )
        set_graph(None)

    def add_node(self, node_for_adding, **attr):
        if len(attr):
            raise ValueError("Attributes are not supported for Nodes.")
        # TODO what if it is a list of nodes?
        if isinstance(node_for_adding, NodeBaseMixin):
            super().add_node(node_for_adding.uuid, value=node_for_adding, **attr)
        else:
            raise ValueError("Only Nodes are supported.")
            # super().add_node(node_for_adding, **attr)
