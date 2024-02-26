import contextlib

from .vanilla import VanillaDeployment

__all__ = ["VanillaDeployment"]

with contextlib.suppress(ImportError):
    from .dask_depl import DaskDeployment

    __all__ += ["DaskDeployment"]
