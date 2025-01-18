# tests/test_pickle_issues.py
import pytest
import multiprocessing as mp
from typing import Any

from tiny_worker.worker import TinyTroupe, TinyWorker


def test_unpickleable_worker_in_spawn():
    """
    Test that a local (unpickleable) worker in 'spawn' context
    raises an error when we try to start the Troupe.
    """

    class LocalWorker(TinyWorker[Any, Any]):
        # An inner class often cannot be pickled by default
        def tiny_call(self, value: Any) -> Any:
            return value

    # Only do this test if "spawn" is actually available
    # On Windows, "spawn" is default, but let's see if it fails with pickling
    if mp.get_start_method(allow_none=True) in ("spawn", "forkserver"):
        troupe = TinyTroupe(worker_type=LocalWorker, context_type="spawn")
        with pytest.raises(Exception):
            troupe.start()
        # We specifically expect a pickling error or something similar.


def test_unpickleable_input():
    """
    Test that an unpickleable input (like a lambda) in 'spawn' context
    raises an error when we try to submit it.
    """

    def identity(x: Any) -> Any:
        return x

    if mp.get_start_method(allow_none=True) in ("spawn", "forkserver"):
        troupe = TinyTroupe(func=identity, context_type="spawn")
        troupe.start()

        # A lambda is often unpickleable unless certain conditions are met
        unpickleable_input = lambda: "can't pickle me"  # nosec  # noqa: E731

        future = troupe.submit(unpickleable_input)

        # We expect a pickling error (or possibly an AttributeError) from the child process
        with pytest.raises(Exception):
            future.result()

        troupe.stop()
