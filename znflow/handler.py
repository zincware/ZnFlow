from znflow import utils
from znflow.base import Connection, FunctionFuture
from znflow.node import Node


class AttributeToConnection(utils.IterableHandler):
    def default(self, value):
        if not isinstance(value, (FunctionFuture, Node)):
            return value
        return value if value._graph_ is None else Connection(value, attribute=None)
