import zninit

import znflow


class CustomDescriptor(zninit.Descriptor):
    def __set__(self, instance, value):
        super().__set__(instance, f"{value}_{znflow.get_attribute(instance, 'name')}")


class NodeWithDescriptor(zninit.ZnInit, znflow.Node):
    data = CustomDescriptor()
    name = "NodeWithDescriptor"

    def run(self):
        pass


def test_NodeWithDescriptor():
    node = NodeWithDescriptor(data=None)
    node.data = 42
    assert node.data == "42_NodeWithDescriptor"

    with znflow.DiGraph() as graph:
        node = NodeWithDescriptor(data=None)
        node.data = 42
        assert isinstance(node.data, znflow.Connection)

    assert node.data == "42_NodeWithDescriptor"
    assert node.uuid in graph
