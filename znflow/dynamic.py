import typing as t

from znflow.base import Connection, disable_graph, get_graph


def resolve(value: t.Union[Connection, t.Any]):
    """Resolve a Connection to its actual value.

    Allows dynamic resolution of connections to their actual values within a graph context.
    This will run all Nodes up to this connection.
    
    Attributes
    ----------
    value : Connection
        The connection to resolve.
    
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
        # if the node has not been run yet, run it
        result = value.result
    if result is None:
        graph = get_graph()
    else:
        return result

    with disable_graph():
        graph.run(nodes=[value.instance])
        result = value.result
    return result
