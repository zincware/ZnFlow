import pytest
from distributed.utils_test import (  # noqa: F401
    cleanup,
    client,
    cluster_fixture,
    loop,
    loop_in_thread,
)

import znflow


@pytest.fixture
def vanilla_deployment():
    return znflow.deployment.VanillaDeployment()


@pytest.fixture
def dask_deployment(client):  # noqa: F811
    return znflow.deployment.DaskDeployment(client=client)
