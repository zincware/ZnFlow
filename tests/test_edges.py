import dataclasses

import znflow


@dataclasses.dataclass
class Node(znflow.Node):
    a: int
    b: int
    c: int | None = None


def test_no_duplicate_edges():
    """Test that connections don't create duplicate edges."""
    project = znflow.DiGraph()

    with project:
        a = Node(a=1, b=2)
        b = Node(a=3, b=4)
        _ = Node(a=a.c, b=b.c)

    # Should have 3 nodes
    assert len(project.nodes) == 3

    # Should have 2 unique edges: a.c -> c.a and b.c -> c.b
    assert len(project.edges) == 2

    # Verify the edges are what we expect
    edges_with_attrs = list(project.edges(data=True))
    edge_descriptions = []
    for edge in edges_with_attrs:
        u_attr = edge[2]["u_attr"]
        v_attr = edge[2]["v_attr"]
        edge_descriptions.append(f"{u_attr}->{v_attr}")

    assert "c->a" in edge_descriptions
    assert "c->b" in edge_descriptions


def test_multiple_connections_same_nodes():
    """Test that multiple different connections between same nodes work."""

    @dataclasses.dataclass
    class MultiNode(znflow.Node):
        x: int | None = None
        y: int | None = None
        z: int | None = None

    project = znflow.DiGraph()

    with project:
        a = MultiNode()
        _ = MultiNode(x=a.x, y=a.y)

    # Should have 2 edges: a.x -> b.x and a.y -> b.y
    assert len(project.edges) == 2

    # Verify the edges are what we expect
    edges_with_attrs = list(project.edges(data=True))
    edge_descriptions = []
    for edge in edges_with_attrs:
        u_attr = edge[2]["u_attr"]
        v_attr = edge[2]["v_attr"]
        edge_descriptions.append(f"{u_attr}->{v_attr}")

    assert "x->x" in edge_descriptions
    assert "y->y" in edge_descriptions


def test_no_duplicate_edges_group():
    project = znflow.DiGraph()

    with project.group("group"):
        a = Node(a=1, b=2)
        b = Node(a=3, b=4)
        _ = Node(a=a.c, b=b.c)

    with project:
        pass

    with project.group("other-group"):
        pass

    # Should have 3 nodes
    assert len(project.nodes) == 3

    # Should have 2 unique edges: a.c -> c.a and b.c -> c.b
    assert len(project.edges) == 2


def test_no_duplicate_edges_iterable():
    project = znflow.DiGraph()

    with project.group("subgraph"):
        a = Node(a=1, b=2)
        b = Node(a=3, b=4)
        c = Node(a=5, b=6)
        _ = Node(a=[a.a], b=[b.b, c.c])

    with project:
        pass

    with project.group("other-subgraph"):
        pass

    assert len(project.nodes) == 4
    assert len(project.edges) == 3

    edges_with_attrs = list(project.edges(data=True))
    edge_descriptions = []
    for edge in edges_with_attrs:
        u_attr = edge[2]["u_attr"]
        v_attr = edge[2]["v_attr"]
        edge_descriptions.append(f"{u_attr}->{v_attr}")

    assert "a->a" in edge_descriptions
    assert "b->b" in edge_descriptions
    assert "c->b" in edge_descriptions
