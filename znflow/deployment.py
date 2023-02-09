import dataclasses
import typing
import uuid

from dask.distributed import Client, Future

from znflow.base import NodeBaseMixin
from znflow.graph import DiGraph
from znflow.utils import IterableHandler


class _LoadNode(IterableHandler):
    def default(self, value, **kwargs):
        results = kwargs["results"]
        if isinstance(value, NodeBaseMixin):
            return results[value.uuid].result()

        return value


def node_submit(node, *args, **kwargs):
    # TODO you need to update all connections to the kwargs from previous
    #  dask futures. Maybe give a Connection a UUID as well?
    #  You can / have to use the graph and the edges to update the connections.

    # TODO look https://distributed.dask.org/en/stable/actors.html
    #  probably not want you want.
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
                    *(self.results[x] for x in self.results if x in predecessors),
                    pure=False,
                )

    def get_results(self, obj: typing.Union[NodeBaseMixin, list, dict], /):
        return _LoadNode()(obj, results=self.results)