import typing as t

from znflow.base import Connection, disable_graph, get_graph


def resolve(value: Connection | t.Any):
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
        graph.run()
        result = value.result
    return result
