# tests/test_tiny_future.py
import pytest
from concurrent.futures import ThreadPoolExecutor
from tiny_worker.future import TinyFuture


def test_tiny_future_set_and_get_result():
    """Test setting and then retrieving a future's result."""
    future = TinyFuture(uid="test1", callback_pool=ThreadPoolExecutor())
    future.set_result(123)
    assert future.result() == 123


def test_tiny_future_double_result():
    """
    Test that calling set_result on a TinyFuture twice raises an error.
    """
    future = TinyFuture(uid="test2", callback_pool=ThreadPoolExecutor())
    future.set_result(123)
    with pytest.raises(ValueError, match="Future already has a result"):
        future.set_result(999)


def test_tiny_future_exception():
    """Test that setting an exception as the result raises that exception on result()."""
    future = TinyFuture(uid="test3", callback_pool=ThreadPoolExecutor())
    future.set_result(ValueError("Test error"))
    with pytest.raises(ValueError, match="Test error"):
        future.result()


def test_tiny_future_callback():
    """
    Test that callbacks are called exactly once when the result is set,
    and that they receive the correct value.
    """
    future = TinyFuture(uid="test4", callback_pool=ThreadPoolExecutor())

    callback_invocations = []

    def callback(value):
        callback_invocations.append(value)

    future.add_callback(callback)
    future.set_result(42)

    assert len(callback_invocations) == 1
    assert callback_invocations[0] == 42


def test_tiny_future_done_property():
    """Test the .done property reflects the status of the future."""
    future = TinyFuture(uid="test5", callback_pool=ThreadPoolExecutor())
    assert not future.done
    future.set_result("Hello")
    assert future.done
