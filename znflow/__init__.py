"""The 'ZnFlow' package."""

import importlib.metadata
import logging
import sys

from znflow import deployment, exceptions
from znflow.base import (
    CombinedConnections,
    Connection,
    FunctionFuture,
    Property,
    disable_graph,
    empty_graph,
    get_attribute,
    get_graph,
)
from znflow.combine import combine
from znflow.dynamic import resolve
from znflow.graph import DiGraph, Group
from znflow.node import Node, nodify
from znflow.visualize import draw

__version__ = importlib.metadata.version(__name__)

__all__ = [
    "DiGraph",
    "Node",
    "draw",
    "nodify",
    "FunctionFuture",
    "Connection",
    "get_attribute",
    "disable_graph",
    "Property",
    "CombinedConnections",
    "combine",
    "exceptions",
    "get_graph",
    "empty_graph",
    "resolve",
    "Group",
    "deployment",
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Formatter for advanced logging
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
formatter = logging.Formatter("%(asctime)s (%(levelname)s): %(message)s")

channel = logging.StreamHandler(sys.stdout)
channel.setLevel(logging.DEBUG)
channel.setFormatter(formatter)

logger.addHandler(channel)
