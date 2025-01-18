# tests/test_troupe_advanced.py
import pytest
from tiny_worker.worker import TinyTroupe, TinyWorker


def test_future_chaining():
    """Test chaining results between multiple Troupes using TinyFutures."""

    def add_one(x: int) -> int:
        return x + 1

    def multiply_two(x: int) -> int:
        return x * 2

    add_troupe = TinyTroupe(func=add_one)
    mul_troupe = TinyTroupe(func=multiply_two)

    add_troupe.start()
    mul_troupe.start()

    # Chain operations: (5 + 1) * 2 == 12
    future1 = add_troupe.submit(5)
    future2 = mul_troupe.submit(future1)

    assert future2.result() == 12

    add_troupe.stop()
    mul_troupe.stop()


def test_deep_future_chaining():
    def add_one(x: int) -> int:
        return x + 1

    troupe = TinyTroupe(func=add_one)
    troupe.start()

    current_future = troupe.submit(0)
    # Do 9 times, so total increments = 10
    for _ in range(9):
        current_future = troupe.submit(current_future)

    result = current_future.result()
    assert result == 10  # Now it matches
    troupe.stop()


def test_error_handling():
    """Test that exceptions raised in the worker propagate to the caller."""

    def failing_func(x):
        raise ValueError("Test error")

    troupe = TinyTroupe(func=failing_func)
    troupe.start()

    future = troupe.submit(42)
    with pytest.raises(ValueError, match="Test error"):
        future.result()

    troupe.stop()


class CustomWorker(TinyWorker[str, str]):
    def tiny_call(self, value: str) -> str:
        return value.upper()


def test_custom_worker():
    """Test using a custom worker class."""
    troupe = TinyTroupe(worker_type=CustomWorker)
    troupe.start()

    future = troupe.submit("hello")
    assert future.result() == "HELLO"

    troupe.stop()
