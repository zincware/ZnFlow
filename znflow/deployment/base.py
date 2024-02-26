import abc
import typing as t

if t.TYPE_CHECKING:
    from znflow.graph import DiGraph

class DeploymentBase(abc.ABC):
    graph: "DiGraph"
    
    @abc.abstractmethod
    def run(self, nodes: t.Optional[t.List] = None):
        ...
    
    def set_graph(self, graph: "DiGraph"):
        self.graph = graph

   