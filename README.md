# Tiny Worker

A tiny utility for easy parallelism in Python that provides a simple, future-based API for parallel task processing using either threads or processes.

Unlike other parallelism / async libraries, `tiny_worker` focuses on a simple, local-only task queue with resource management.

## Disclaimer

1. This library is currently very barebones and mostly for learning purposes.
2. The API is restricted to single-input functions. You can get around this by using tuples or dataclasses / BaseModel as your input types.

## Features

- Simple, intuitive API for parallel processing
- Support for both thread and process-based parallelism
- Future-based result handling
- Custom worker implementations
- Chainable futures for complex workflows
- Automatic error propagation

## Installation

To install directly from GitHub:

```bash
pip install git+https://github.com/nopepper/tiny-worker.git
```

## Usage

There are only three main classes:

- `TinyWorker` is an abstract class that you inherit from to define worker agents
- `TinyTroupe` is a class not dissimilar to a `ThreadPoolExecutor`
- `TinyFuture` is emulates the classic future pattern

**Tips:**

- Use `context_type="thread"` for multithreading
- Functions, arguments and input/output types must be pickleable

### Parallelize a function

For simple, stateless tasks.

```python
from tiny_worker import TinyTroupe

def square(number: float) -> float:
    return number * number

with TinyTroupe(func=square, context_type="spawn", num_workers=4) as troupe:
    futures = [troupe.submit(i) for i in range(10)]
    print([f.result() for f in futures])

# [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```

### Parallelize a class

Oftentimes we want to initialize some resources and reuse them across tasks.

```python
from tiny_worker import TinyTroupe, TinyWorker

class ConnectedWorker(TinyWorker[float, float]):
    def __init__(self, foo: str) -> None:
        self.connection = connect(foo)  # Initialize some resources

    def tiny_call(self, value: float) -> list[str]:
        return self.connection.query(value)

with TinyTroupe(worker=ConnectedWorker, worker_kwargs={"foo": "bar"}, context_type="spawn", num_workers=4) as troupe:
    futures = [troupe.submit(i) for i in range(10)]
    print([f.result() for f in futures])
```

### Lazy chaining

`TinyTroupe` allows submitting unfinished futures, too:

```python
from tiny_worker import TinyTroupe

def square(number: float) -> float:
    return number * number

def half(number: float) -> float:
    return number / 2

with (
    TinyTroupe(func=square, context_type="spawn", num_workers=4) as troupe1,
    TinyTroupe(func=half, context_type="spawn", num_workers=4) as troupe2,
):
    futures = [troupe2.submit(troupe1.submit(i)) for i in range(10)]
    print([f.result() for f in futures])

# [0.0, 0.5, 2.0, 4.5, 8.0, 12.5, 18.0, 24.5, 32.0, 40.5]
```
