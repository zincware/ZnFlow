import typing

from znflow.base import CombinedConnections, Connection, FunctionFuture
from znflow.node import Node

NODE_OR_CONNECTION_OR_COMBINED_OR_FUNC_FUT = typing.Union[
    Node, Connection, CombinedConnections, FunctionFuture
]
ARGS_TYPE = typing.List[NODE_OR_CONNECTION_OR_COMBINED_OR_FUNC_FUT]


def _return_dict_attr(data, attr_name) -> dict:
    """Return a dictionary with the attribute as key and the instances as values."""
    result_dict = {}
    for connection in data:
        key = (
            getattr(connection.instance, attr_name)
            if isinstance(connection, Connection)
            else getattr(connection, attr_name)
        )
        if key in result_dict:
            raise ValueError(
                f"znflow.combine: The attribute '{attr_name}=<{key}>' is"
                " not unique. Please use a different attribute."
            )
        result_dict[key] = connection
    return result_dict


def combine(
    *args: ARGS_TYPE,
    attribute=None,
    only_getattr_on_nodes=True,
    return_dict_attr: str = None,
    return_dict_attr_error: bool = True,
):
    """Combine Node outputs which are lists into a single flat list.

    Attributes
    ----------
    args : ARGS_TYPE
        The arguments to combine.
    attribute : str, default=None
        If not None, the attribute of the Node instance is gathered.
    only_getattr_on_nodes : bool, default=True
        If True, the attribute is only gathered from Node instances.
    return_dict_attr : str, default=None
        If provided, that return type will not be 'CombinedConnections' but a
        dictionary with the attribute as key and the instances as values.
        One example would be "uuid" to get {uuid: instance} back.
        The value will be taken from the Node and not the Connection.

        This only works if the args are Nodes. If they are not, an error is raised.
    return_dict_attr_error : bool, default=True
        If True, an error is raised if the return type is not 'CombinedConnections'
        or list[Node] and the 'return_dict_attr' is not None. Otherwise, this is
        silently ignored.

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
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        args = args[0]
    if attribute is not None:
        if only_getattr_on_nodes:
            args = [
                getattr(arg, attribute) if isinstance(arg, Node) else arg for arg in args
            ]
        else:
            try:
                args = [getattr(arg, attribute) for arg in args]
            except AttributeError as err:
                raise TypeError(
                    "znflow.combine tried to use 'getattr' on non-node type from"
                    f" '{args=}'. Consider using 'only_getattr_on_nodes=True'"
                ) from err
    try:
        result = sum(args, [])
    except TypeError:
        result = args

    if isinstance(result, CombinedConnections):
        if return_dict_attr:
            return _return_dict_attr(result.connections, return_dict_attr)
    elif isinstance(result, (Connection)):
        if return_dict_attr:
            return {getattr(result.instance, return_dict_attr): result}
    elif isinstance(result, (Node)):
        if return_dict_attr:
            return {getattr(result, return_dict_attr): result}
    elif isinstance(result, (list, tuple)) and isinstance(result[0], (Connection, Node)):
        # we assume if the first item is a Connection or Node, all are
        if return_dict_attr:
            return _return_dict_attr(result, return_dict_attr)
    elif return_dict_attr and return_dict_attr_error:
        raise TypeError(
            "znflow.combine can only return a dict if the result type is"
            f" 'CombinedConnections'. Found {result} instead."
        )
    return result
