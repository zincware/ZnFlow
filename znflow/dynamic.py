import typing as t

from znflow.base import Connection, disable_graph, get_graph, FunctionFuture


def resolve(value: t.Union[Connection, t.Any]) -> t.Any:
    """Resolve a Connection to its actual value.

    Allows dynamic resolution of connections to their actual values
    within a graph context. This will run all Nodes up to this connection.

    Attributes
    ----------
    value : Connection
        The connection to resolve.

    Returns
    -------
    t.Any
        The actual value of the connection.

    """
    if not isinstance(value, (Connection, FunctionFuture)):
        return value
    # get the actual value
    with disable_graph():
        result = value.result
    if result is not None:
        return result
    # we assume, that if the result is None, the node has not been run yet
    graph = get_graph()

    with disable_graph():
        if isinstance(value, FunctionFuture):
            graph.run(nodes=[value])
        else:
            graph.run(nodes=[value.instance])
        result = value.result
    return result
