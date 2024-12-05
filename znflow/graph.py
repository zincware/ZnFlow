import contextlib
import dataclasses
import functools
import logging
import typing
import uuid

import networkx as nx

from znflow import handler
from znflow.base import (
    Connection,
    FunctionFuture,
    NodeBaseMixin,
    empty_graph,
    get_graph,
    set_graph,
)
from znflow.deployment import VanillaDeployment
from znflow.node import Node

log = logging.getLogger(__name__)


@dataclasses.dataclass
class Group:
    names: tuple[str, ...]
    uuids: list[uuid.UUID]
    graph: "DiGraph"

    def __iter__(self) -> typing.Iterator[uuid.UUID]:
        return iter(self.uuids)

    def __len__(self) -> int:
        return len(self.uuids)

    def __contains__(self, item) -> bool:
        return item in self.uuids

    def __getitem__(self, item) -> NodeBaseMixin:
        return self.graph.nodes[item]["value"]

    @property
    def nodes(self) -> typing.List[NodeBaseMixin]:
        return [self.graph.nodes[uuid_]["value"] for uuid_ in self.uuids]


class DiGraph(nx.MultiDiGraph):
    def __init__(
        self, *args, disable=False, immutable_nodes=True, deployment=None, **kwargs
    ):
        """
        Attributes
        ----------
        immutable_nodes : bool
            If True, the nodes are assumed to be immutable and
            will not be rerun. If you change the inputs of a node
            after it has been run, the outputs will not be updated.
        """
        self.disable = disable
        self.immutable_nodes = immutable_nodes
        self.groups = {}
        self.active_group: typing.Union[Group, None] = None
        self.deployment = deployment or VanillaDeployment()
        self.deployment.set_graph(self)

        super().__init__(*args, **kwargs)

    @property
    def add_connections_from_iterable(self) -> typing.Callable:
        """Get a function that adds connections to the graph.

        Return a AddConnectionToGraph class with this Graph instance attached.
        """
        return functools.partial(handler.AddConnectionToGraph(), graph=self)

    def __enter__(self):
        if self.disable:
            return self
        if get_graph() is not empty_graph:
            raise ValueError("DiGraph already exists. Nested Graphs are not supported.")
        set_graph(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.disable:
            return
        if get_graph() is not self:
            raise ValueError(
                "Something went wrong. DiGraph was changed inside the context manager."
            )
        set_graph(empty_graph)
        for node in list(self.nodes):  # create a copy of the keys
            node_instance = self.nodes[node]["value"]
            if isinstance(node_instance, Node):
                # TODO only update Nodes if the graph is not empty
                if node_instance._znflow_resolved:
                    continue
                self._update_node_attributes(
                    node_instance, handler.AttributeToConnection()
                )
                node_instance._znflow_resolved = True
            elif isinstance(node_instance, FunctionFuture):
                pass  # moved to add_node
            log.debug(f"Node {node} ({node_instance}) was added to the graph.")

    def _update_function_future_arguments(self, node_instance: FunctionFuture) -> None:
        """Apply an update to args and kwargs of a FunctionFuture."""
        node_instance.args = handler.AttributeToConnection()(node_instance.args)
        node_instance.kwargs = handler.AttributeToConnection()(node_instance.kwargs)
        self.add_connections_from_iterable(
            node_instance.args, node_instance=node_instance
        )
        self.add_connections_from_iterable(
            node_instance.kwargs, node_instance=node_instance
        )

    def _update_node_attributes(self, node_instance: Node, updater) -> None:
        """Apply an updater to all attributes of a node."""
        for attribute in dir(node_instance):
            if attribute.startswith("_") or attribute in Node._protected_:
                # We do not allow connections to private attributes.
                continue
            if isinstance(
                getattr(type(node_instance), attribute, None),
                (property, functools.cached_property),
            ):
                # We do not want to call getter of properties.
                continue
            try:
                if dataclasses.is_dataclass(node_instance):
                    value = node_instance.__dict__[attribute]
                else:
                    value = getattr(node_instance, attribute)
            except Exception:
                # It might be, that the value is currently not available.
                #  For example, it could be a property that is not yet set.
                #  In this case we skip updating the attribute, no matter the exception.
                continue
            value = updater(value)
            if updater.updated:
                try:
                    setattr(node_instance, attribute, value)
                except AttributeError:
                    continue
            self.add_connections_from_iterable(
                value, node_instance=node_instance, attribute=attribute
            )

    def add_node(self, node_for_adding, this_uuid=None, **attr):
        if isinstance(node_for_adding, NodeBaseMixin):
            if this_uuid is None:
                this_uuid = node_for_adding.uuid
            super().add_node(this_uuid, value=node_for_adding, **attr)
        else:
            raise ValueError(f"Only Nodes are supported, found '{node_for_adding}'.")

        if isinstance(node_for_adding, FunctionFuture):
            self._update_function_future_arguments(node_for_adding)

    def add_connections(self, u_of_edge, v_of_edge, **attr):
        with contextlib.suppress(TypeError):
            # zninit does not like __repr__
            log.debug(f"Add edge between {u_of_edge=} and {v_of_edge=}.")
        if isinstance(u_of_edge, Connection) and isinstance(v_of_edge, NodeBaseMixin):
            if u_of_edge.uuid not in self:
                if u_of_edge._external_:
                    self.add_node(u_of_edge.instance)
                else:
                    raise ValueError(
                        f"The source node (uuid={u_of_edge.uuid}, connection={u_of_edge})"
                        " is not in the graph."
                    )
            if (
                v_of_edge.uuid not in self
            ):  # this might be impossible to reach. Let me know if you found a way.
                raise ValueError(
                    f"The target node (uuid={v_of_edge.uuid}, connection={v_of_edge}) is"
                    " not in the graph."
                )

            # TODO what if 'v_attr' is a list/dict/... that contains multiple connections?
            #  Is this relevant? We could do `v_attr.<dict_key>` or `v_attr.<list_index>`
            #  See test_node.test_ListConnection and test_node.test_DictionaryConnection
            self.add_edge(
                u_of_edge.uuid,
                v_of_edge.uuid,
                u_attr=u_of_edge.attribute,
                **attr,
            )
        else:
            raise ValueError("Only Connections and Nodes are supported.")

    def get_sorted_nodes(self):
        all_pipelines = []
        reverse = self.reverse(copy=False)
        for stage in reverse:
            all_pipelines += nx.dfs_postorder_nodes(reverse, stage)
        return list(dict.fromkeys(all_pipelines))  # remove duplicates but keep order

    def run(
        self,
        nodes: typing.Optional[typing.List[NodeBaseMixin]] = None,
    ):
        """Run the graph.

        Attributes
        ----------
        nodes : list[Node]
            The nodes to run. If None, all nodes are run.
        """
        self.deployment.run(nodes)

    def write_graph(self, *args):
        for node in args:
            if isinstance(node, (list, tuple)):
                self.write_graph(*node)
            else:
                self.add_node(node)
        with self:
            pass

    @contextlib.contextmanager
    def group(self, *names: str) -> typing.Generator[Group, None, None]:
        """Create a group of nodes.

        Allows to group nodes together, independent of their order in the graph.

        The group can be created within the graph context manager.
        Alternatively, the group can be created outside of the graph context manager,
        implicitly opening and closing the graph context manager.

        Attributes
        ----------
            *names : str
                Name of the group. If the name is already used, the nodes will be added
                to the existing group. Multiple names can be provided to create nested
                groups.

        Raises
        ------
            TypeError
                If a group with the same name is already active. Nested groups are not
                supported.

        Yields
        ------
            Group:
                A group of containing the nodes that are added within the context manager.
        """
        if len(names) == 0:
            raise ValueError("At least one name must be provided.")
        if self.active_group is not None:
            raise TypeError(
                f"Nested groups are not supported. Group with name '{self.active_group}'"
                " is still active."
            )

        existing_nodes = self.get_sorted_nodes()

        group = self.groups.get(names, Group(names=names, uuids=[], graph=self))

        def finalize_group():
            self.groups[group.names] = group
            for node_uuid in self.nodes:
                if node_uuid not in existing_nodes:
                    group.uuids.append(node_uuid)

        try:
            self.active_group = group
            if get_graph() is empty_graph:
                with self:
                    try:
                        yield group
                    finally:
                        finalize_group()
            else:
                try:
                    yield group
                finally:
                    finalize_group()
        finally:
            self.active_group = None

    def get_group(self, *names: str) -> Group:
        return self.groups[names]
