import networkx as nx
import zninit

from znflow.base import NodeBaseMixin
from znflow.connectors import FunctionConnector, NodeConnector
from znflow.utils import IterableHandler


class UpdateValueWithConnector(IterableHandler):
    def default(self, value, *args, **kwargs):
        node = kwargs.pop("node")
        attribute_name = kwargs.pop("attribute_name")
        graph = kwargs.pop("graph")
        if isinstance(value, NodeConnector):
            NodeBaseMixin._graph_ = graph
            setattr(node, attribute_name, value)
            NodeBaseMixin._graph_ = None


class DiGraph(nx.MultiDiGraph):
    def __enter__(self):
        if NodeBaseMixin._graph_ is not None:
            raise ValueError("DiGraph already exists. Nested Graphs are not supported.")
        NodeBaseMixin._graph_ = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if NodeBaseMixin._graph_ is not self:
            raise ValueError(
                "Something went wrong. DiGraph was changed inside the context manager."
            )
        NodeBaseMixin._graph_ = None

    def write_graph(self, *args):
        for node in args:
            self.add_node(node)
            for descriptor in zninit.get_descriptors(self=node):
                value = getattr(node, descriptor.name)
                UpdateValueWithConnector().handle(
                    value, node=node, attribute_name=descriptor.name, graph=self
                )

    def get_sorted_nodes(self):
        all_pipelines = []
        for stage in self.reverse():
            all_pipelines += nx.dfs_postorder_nodes(self.reverse(), stage)
        return list(dict.fromkeys(all_pipelines))  # remove duplicates but keep order

    def run(self, method="run"):  # TODO why is there a method argument?
        for node in self.get_sorted_nodes():
            from znflow.node import update_connectors_to_results

            update_connectors_to_results(node)
            if hasattr(node, method):
                getattr(node, method)()
            if isinstance(node, FunctionConnector):
                node.get_result()
