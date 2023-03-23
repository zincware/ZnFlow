import typing

from znflow.base import CombinedConnections, Connection, FunctionFuture
from znflow.node import Node

NODE_OR_CONNECTION_OR_COMBINED_OR_FUNC_FUT = typing.Union[
    Node, Connection, CombinedConnections, FunctionFuture
]
ARGS_TYPE = typing.List[NODE_OR_CONNECTION_OR_COMBINED_OR_FUNC_FUT]


def combine(*args: ARGS_TYPE, attribute=None, only_getattr_on_nodes=True):
    """Combine Node outputs which are lists into a single flat list.

    Attributes
    ----------
    args : ARGS_TYPE
        The arguments to combine.
    attribute : str, default=None
        If not None, the attribute of the Node instance is gathered.
    only_getattr_on_nodes : bool, default=True
        If True, the attribute is only gathered from Node instances.

    Examples
    --------
    The following are all allowed:
    >>> a, b, c = Node(), Node(), Node()
    >>> combine([a, b, c])
    >>> combine(a, b, c)
    >>> combine([a, b, c], attribute="outs")
    >>> combine(a, b, c, attribute="outs")

    Returns
    -------
    CombinedConnections:
        A combined connections object.
    """
    if len(args) == 1:
        if isinstance(args[0], (list, tuple)):
            args = args[0]
    if attribute is not None:
        outs = []
        if only_getattr_on_nodes:
            for arg in args:
                if isinstance(arg, Node):
                    outs.append(getattr(arg, attribute))
                else:
                    outs.append(arg)
        else:
            outs = [getattr(arg, attribute) for arg in args]
    else:
        outs = args
    try:
        return sum(outs, [])
    except TypeError:
        try:
            return outs
        except TypeError as err:
            raise TypeError(f"{args=} with {attribute=} is not allowed.") from err
