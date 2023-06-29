import znflow
import dataclasses
import pytest

@dataclasses.dataclass
class ComputeMean(znflow.Node):
    x: float
    y: float
    
    results: float = None
    
    def run(self):
        self.results = (self.x + self.y) / 2


def test_attribute_access():
    with znflow.DiGraph() as graph:
        n1 = ComputeMean(2, 8)
        with pytest.raises(znflow.exceptions.ConnectionAttributeError):
            n1.x.data
