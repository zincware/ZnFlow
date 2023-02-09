import dataclasses
import typing
import uuid

from dask.distributed import Client, Future
from networkx.classes.reportviews import NodeView

from znflow.base import Connection, NodeBaseMixin
from znflow.graph import DiGraph
from znflow.utils import IterableHandler


class _LoadNode(IterableHandler):
    def default(self, value, **kwargs):
        results = kwargs["results"]
        if isinstance(value, NodeBaseMixin):
            return results[value.uuid].result()

        return value


class _UpdateConnections(IterableHandler):
    def default(self, value, **kwargs):
        predecessors = kwargs["predecessors"]
        if isinstance(value, Connection):
            # We don't actually need the connection, we need the results.
            return dataclasses.replace(value, instance=predecessors[value.uuid]).result
        return value


def node_submit(node, **kwargs):
    predecessors = kwargs.get("predecessors", {})
    for item in dir(node):
        # TODO this information is available in the graph,
        #  no need to expensively iterate over all attributes
        if item.startswith("_"):
            continue
        updater = _UpdateConnections()
        value = updater(getattr(node, item), predecessors=predecessors)
        if updater.updated:
            setattr(node, item, value)

    node.run()
    return node


@dataclasses.dataclass
class Deployment:
    graph: DiGraph
    client: Client = dataclasses.field(default_factory=Client)
    results: typing.Dict[uuid.UUID, Future] = dataclasses.field(
        default_factory=dict, init=False
    )

    def submit_graph(self):
        """

        When submitting to Dask, a Node is serialized, processed and a
        copy can be returned.

        This requires:
        - the connections to be updated to the respective Nodes coming from Dask futures.
        - the Node to be returned from the workers and passed to all successors.
        """
        for node_uuid in self.graph.reverse():
            node = self.graph.nodes[node_uuid]["value"]
            predecessors = list(self.graph.predecessors(node.uuid))

            if len(predecessors) == 0:
                self.results[node.uuid] = self.client.submit(  # TODO how to name
                    node_submit, node=node, pure=False
                )
            else:
                self.results[node.uuid] = self.client.submit(
                    node_submit,
                    node=node,
                    predecessors={
                        x: self.results[x] for x in self.results if x in predecessors
                    },
                    pure=False,
                )

    def get_results(self, obj: typing.Union[NodeBaseMixin, list, dict, NodeView], /):
        if isinstance(obj, NodeView):
            data = _LoadNode()(dict(obj), results=self.results)
            return {x: v["value"] for x, v in data.items()}
        elif isinstance(obj, DiGraph):
            raise NotImplementedError
        return _LoadNode()(obj, results=self.results)
