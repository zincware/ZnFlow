"""Mock version of IPS LotF workflow for testing purposes."""

import dataclasses
import random

import pytest

import znflow


@dataclasses.dataclass
class AddData(znflow.Node):
    file: str

    def run(self):
        if self.file is None:
            raise ValueError("File is None")
        print(f"Adding data from {self.file}")

    @property
    def atoms(self):
        return "Atoms"


@dataclasses.dataclass
class TrainModel(znflow.Node):
    data: str
    model: str = None

    def run(self):
        if self.data is None:
            raise ValueError("Data is None")
        self.model = "Model"
        print(f"Model: {self.model}")


@dataclasses.dataclass
class MD(znflow.Node):
    model: str
    atoms: str = None

    def run(self):
        if self.model is None:
            raise ValueError("Model is None")
        self.atoms = "Atoms"
        print(f"Atoms: {self.atoms}")


@dataclasses.dataclass
class EvaluateModel(znflow.Node):
    model: str
    seed: int
    metrics: float = None

    def run(self):
        random.seed(self.seed)
        if self.model is None:
            raise ValueError("Model is None")
        self.metrics = random.random()
        print(f"Metrics: {self.metrics}")


@pytest.mark.parametrize("deployment", ["vanilla_deployment", "dask_deployment"])
def test_lotf(deployment, request):
    deployment = request.getfixturevalue(deployment)

    graph = znflow.DiGraph(deployment=deployment)
    with graph:
        data = AddData(file="data.xyz")
        model = TrainModel(data=data.atoms)
        md = MD(model=model.model)
        metrics = EvaluateModel(model=model.model, seed=0)
        for idx in range(10):
            model = TrainModel(data=md.atoms)
            md = MD(model=model.model)
            metrics = EvaluateModel(model=model.model, seed=idx)
            if znflow.resolve(metrics.metrics) == pytest.approx(0.623, 1e-3):
                # break loop after 6th iteration
                break

    assert len(graph) == 22
