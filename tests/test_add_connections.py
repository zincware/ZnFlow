import znflow


@znflow.nodify
def create_list(size: int) -> list:
    return list(range(size))


class CreateList(znflow.Node):
    def __init__(self, size: int):
        super().__init__()
        self.size = size
        self.outs = None  # must be defined in __init__

    def run(self):
        self.outs = list(range(self.size))


@znflow.nodify
def add_one(value: list) -> list:
    return [x + 1 for x in value]


class AddOne(znflow.Node):
    def __init__(self, value: list):
        super().__init__()
        self.value = value
        self.outs = None

    def run(self):
        self.outs = [x + 1 for x in self.value]


def test_AddLists():
    with znflow.DiGraph() as graph:
        lst1 = CreateList(5)
        lst2 = CreateList(10)

        outs = AddOne(lst1.outs + lst2.outs)

    graph.run()

    assert outs.outs == list(range(5)) + list(range(10))


# def test_add_lists():
#     with znflow.DiGraph() as graph:
#         lst1 = create_list(5)
#         lst2 = create_list(10)

#         outs = add_one(lst1 + lst2)

#     graph.run()
