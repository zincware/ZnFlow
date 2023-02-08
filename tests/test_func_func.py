import znflow


@znflow.nodify
def add(*args):
    return sum(args)


@znflow.nodify
def multiply(a, b):
    return a * b


@znflow.nodify
def divide(a, b):
    print("Computing")
    return a / b


def test_eager(capsys):
    n1 = add(1, 2, 3)
    n2 = add(10, 20, 30)
    n3 = add(n1, n2)
    n4 = multiply(n1, n3)
    n5 = divide(n4, n1)
    captured = capsys.readouterr()
    assert captured.out == "Computing\n"

    assert n5 == 66


def test_graph(capsys):
    with znflow.DiGraph() as graph:
        n1 = add(1, 2, 3)
        n2 = add(10, 20, 30)
        n3 = add(n1, n2)
        n4 = multiply(n1, n3)
        n5 = divide(n4, n1)

    graph.run()
    captured = capsys.readouterr()
    assert captured.out == "Computing\n"

    assert n5.result == 66
    captured = capsys.readouterr()
    assert captured.out == ""
