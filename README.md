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
