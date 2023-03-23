from znflow.node import Node


def combine(*args, attribute=None, only_getattr_on_nodes=True):
    """Combine Node outputs which are lists into a single flat list.

    Attributes
    ----------
    args : list of Node instances
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
        elif isinstance(args[0], Node):
            args = [args[0]]
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
    except TypeError as err:
        raise TypeError(f"{args=} with {attribute=} is not allowed.") from err
