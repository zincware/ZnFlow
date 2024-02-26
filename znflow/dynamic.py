import typing as t

from znflow.base import Connection, disable_graph, get_graph


def resolve(value: t.Union[Connection, t.Any], immutable_nodes: bool = True) -> t.Any:
    """Resolve a Connection to its actual value.

    Allows dynamic resolution of connections to their actual values
    within a graph context. This will run all Nodes up to this connection.

    Attributes
    ----------
    value : Connection
        The connection to resolve.
    immutable_nodes : bool
        If True, the nodes are assumed to be immutable and
        will not be rerun. If you change the inputs of a node
        after it has been run, the outputs will not be updated.

    Returns
    -------
    t.Any
        The actual value of the connection.

    """
    # TODO: support nodify as well
    if not isinstance(value, (Connection)):
        return value
    # get the actual value
    with disable_graph():
        result = value.result
    if result is not None:
        return result
    # we assume, that if the result is None, the node has not been run yet
    graph = get_graph()

    with disable_graph():
        graph.run(nodes=[value.instance], immutable_nodes=immutable_nodes)
        result = value.result
    return result
