# tests/test_troupe_basics.py
import pytest
from tiny_worker.worker import TinyTroupe, TinyWorker


def test_basic_function_worker():
    """Basic test verifying single submission with a function-based worker."""

    def square(x: int) -> int:
        return x * x

    troupe = TinyTroupe(func=square)
    troupe.start()

    future = troupe.submit(5)
    assert future.result() == 25

    troupe.stop()


def test_threaded_workers():
    """Test multiple submissions in a threaded worker environment."""
    import time

    def slow_square(x: int) -> int:
        time.sleep(0.1)  # Simulate work
        return x * x

    troupe = TinyTroupe(func=slow_square, context_type="thread", num_workers=4)
    troupe.start()

    futures = [troupe.submit(i) for i in range(10)]
    results = [f.result() for f in futures]
    assert results == [i * i for i in range(10)]

    troupe.stop()


def test_start_already_started():
    """
    Test that attempting to start an already-started troupe raises an error.
    """
    troupe = TinyTroupe(func=lambda x: x)
    troupe.start()
    with pytest.raises(ValueError, match="Troupe already started"):
        troupe.start()
    troupe.stop()


def test_stop_not_started():
    """
    Test that stopping a troupe that was never started raises an error.
    """
    troupe = TinyTroupe(func=lambda x: x)
    with pytest.raises(ValueError, match="Troupe not started"):
        troupe.stop()


def test_worker_cleanup():
    """
    Test that once the troupe is stopped, it does not accept new submissions,
    and cannot be stopped again without error.
    """

    def simple_func(x: int) -> int:
        return x

    troupe = TinyTroupe(func=simple_func)
    troupe.start()
    troupe.stop()

    # Should raise an error when submitting after stop
    with pytest.raises(ValueError, match="Troupe not started"):
        troupe.submit(1)

    # Should raise an error when stopping twice
    with pytest.raises(ValueError, match="Troupe not started"):
        troupe.stop()


def test_cannot_specify_both_func_and_worker_type():
    """
    Test that specifying both a worker_type and a func at the same time
    raises an error.
    """

    class CustomWorker(TinyWorker[int, int]):
        def tiny_call(self, value: int) -> int:
            return value + 1

    with pytest.raises(ValueError, match="Cannot specify both worker_type and func"):
        TinyTroupe(worker_type=CustomWorker, func=lambda x: x)


def test_context_manager():
    """Test that TinyTroupe works correctly as a context manager."""

    def square(x: int) -> int:
        return x * x

    # Test normal operation
    with TinyTroupe(func=square) as troupe:
        future = troupe.submit(5)
        assert future.result() == 25

    # Test that the troupe is properly stopped after the context
    with pytest.raises(ValueError, match="Troupe not started"):
        troupe.submit(1)

    # Test that context manager handles exceptions properly
    def failing_func(x: int) -> int:
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        with TinyTroupe(func=failing_func) as troupe:
            future = troupe.submit(5)
            future.result()  # This should raise the error

    # Verify troupe is stopped even after exception
    with pytest.raises(ValueError, match="Troupe not started"):
        troupe.submit(1)
