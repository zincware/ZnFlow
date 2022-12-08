# ZnFlow

The `ZnFlow` package provides a basic structure for building computational graphs based on functions or classes. It is designed as a lightweight abstraction layer to 
- learn graph computing.
- build your own packages on top of it.

## Installation
```shell
pip install znflow
```

## Usage

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
print(mean.get_result())
# >>> 5

with znflow.DiGraph() as graph:
    n1 = compute_mean(2, 8)
    n2 = compute_mean(13, 7)
    n3 = compute_mean(n1, n2)

graph.run()
print(n3.get_result())
# >>> 7.5
```