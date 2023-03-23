[![zincware](https://img.shields.io/badge/Powered%20by-zincware-darkcyan)](https://github.com/zincware)
[![Coverage Status](https://coveralls.io/repos/github/zincware/ZnFlow/badge.svg?branch=main)](https://coveralls.io/github/zincware/ZnFlow?branch=main)
[![PyPI version](https://badge.fury.io/py/znflow.svg)](https://badge.fury.io/py/znflow)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/zincware/ZnFlow/HEAD)

# ZnFlow

The `ZnFlow` package provides a basic structure for building computational graphs based on functions or classes. It is designed as a lightweight abstraction layer to 
- learn graph computing.
- build your own packages on top of it.

## Installation
```shell
pip install znflow
```

## Usage

### Connecting Functions

With ZnFlow you can connect functions to each other by using the `@nodify` decorator. Inside the ``znflow.DiGraph`` the decorator will return a `FunctionFuture` object that can be used to connect the function to other nodes. The `FunctionFuture` object will also be used to retrieve the result of the function.
Outside the ``znflow.DiGraph`` the function behaves as a normal function.
```python
import znflow

@znflow.nodify
def compute_mean(x, y):
    return (x + y) / 2

print(compute_mean(2, 8))
# >>> 5

with znflow.DiGraph() as graph:
    mean = compute_mean(2, 8)

graph.run()
print(mean.result)
# >>> 5

with znflow.DiGraph() as graph:
    n1 = compute_mean(2, 8)
    n2 = compute_mean(13, 7)
    n3 = compute_mean(n1, n2)

graph.run()
print(n3.result)
# >>> 7.5
```

### Connecting Classes
It is also possible to connect classes.
They can be connected either directly or via class attributes.
This is possible by returning ``znflow.Connections`` inside the ``znflow.DiGraph`` context manager.
Outside the ``znflow.DiGraph`` the class behaves as a normal class.

In the following example we use a dataclass, but it works with all Python classes that inherit from ``znflow.Node``.

```python
import znflow
import dataclasses

@znflow.nodify
def compute_mean(x, y):
    return (x + y) / 2

@dataclasses.dataclass
class ComputeMean(znflow.Node):
    x: float
    y: float
    
    results: float = None
    
    def run(self):
        self.results = (self.x + self.y) / 2
        
with znflow.DiGraph() as graph:
    n1 = ComputeMean(2, 8)
    n2 = compute_mean(13, 7)
    # connecting classes and functions to a Node
    n3 = ComputeMean(n1.results, n2) 
    
graph.run()
print(n3.results)
# >>> 7.5
```

### Working with lists
ZnFlow supports some special features for working with lists.
In the following example we want to ``combine`` two lists.

```python
import znflow

@znflow.nodify
def arange(size: int) -> list:
    return list(range(size))

print(arange(2) + arange(3))
>>> [0, 1, 0, 1, 2]

with znflow.DiGraph() as graph:
    lst = arange(2) + arange(3)

graph.run()
print(lst.result)
>>> [0, 1, 0, 1, 2]
```

This functionality is restricted to lists.
There are some further features that allow combining ``data: list[list]`` by either using ``data: list = znflow.combine(data)`` which has an optional ``attribute=None`` argument to be used in the case of classes or you can simply use ``data: list = sum(data, [])``.

### Attributes Access
Inside the `with znflow.DiGraph()` context manager, accessing class attributes yields `znflow.Connector` objects.
Sometimes, it may be required to obtain the actual attribute value instead of a `znflow.Connector` object.
It is not recommended to run class methods inside the `with znflow.DiGraph()` context manager since it should be exclusively used for building the graph and not for actual computation.

In the case of properties or other descriptor-based attributes, it might be necessary to access the actual attribute value. This can be achieved using the `znflow.get_attribute` method, which supports all features from `getattr` and can be imported as such:

```python
from znflow import get_attribute as getattr
```
Here's an example of how to use ``znflow.get_attribute``:
```python
import znflow

class POW2(znflow.Node):
    """Compute the square of x."""
    x_factor: float = 0.5
    results: float = None
    _x: float = None

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        # using "self._x = value * self.x_factor" inside "znflow.DiGraph()" would run 
        # "value * Connector(self, "x_factor")" which is not possible (TypeError)
        # therefore we use znflow.get_attribute.
        self._x = value * znflow.get_attribute(self, "x_factor")

    def run(self):
        self.results = self.x**2
    
with znflow.DiGraph() as graph:
    n1 = POW2()
    n1.x = 4.0

graph.run()
assert n1.results == 4.0

```

Instead, you can also use the ``znflow.disable_graph`` decorator / context manager to disable the graph for a specific block of code or the ``znflow.Property`` as a drop-in replacement for ``property``.


# Supported Frameworks
ZnFlow includes tests to ensure compatibility with:
- "Plain classes"
- ``dataclasses``
- ``ZnInit``
- ``attrs``

It is currently **not** compatible with pydantic.
I don't know what pydantic does internally and wasn't able to find a workaround.
