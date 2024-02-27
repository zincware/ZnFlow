from distributed.utils_test import client, loop, cluster_fixture, loop_in_thread, cleanup # noqa: F401

import pytest
import znflow


@pytest.fixture
def vanilla_deployment():
    return znflow.deployment.VanillaDeployment()

@pytest.fixture
def dask_deployment(client):
    return znflow.deployment.DaskDeployment(client=client)