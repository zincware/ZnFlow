import contextlib

__all__ = []

with contextlib.suppress(ImportError):
    from .dask_depl import DaskDeployment
    __all__ += ["DaskDeployment"]
