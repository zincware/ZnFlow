import dataclasses

import znflow


@dataclasses.dataclass
class Node(znflow.Node):
    inputs: float
    outputs: float = None

    def run(self):
        self.outputs = self.inputs * 2


@dataclasses.dataclass
class SumNodes(znflow.Node):
    inputs: float
    outputs: float = None

    def run(self):
        self.outputs = sum(self.inputs)


if __name__ == "__main__":
    import random

    from dask.distributed import Client

    from znflow.dask_jobs import submit_graph

    k = 3
    j = 3
    i = 3

    with znflow.DiGraph() as graph:
        kdx_nodes = []
        for kdx in range(k):
            jdx_nodes = []
            for jdx in range(j):
                idx_nodes = []
                for idx in range(i):
                    idx_nodes.append(Node(inputs=random.random()))
                jdx_nodes.append(SumNodes(inputs=[x.outputs for x in idx_nodes]))
            kdx_nodes.append(SumNodes(inputs=[x.outputs for x in jdx_nodes]))

        end_node = SumNodes(inputs=[x.outputs for x in kdx_nodes])

    client = Client()
    futures = submit_graph(graph, client)
