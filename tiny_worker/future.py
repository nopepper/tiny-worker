"""Tiny future class."""

from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class TinyFuture(Generic[T]):
    """A simple future class that represents a value that will be available in the future."""

    def __init__(self, uid: str, callback_pool: ThreadPoolExecutor) -> None:
        """Initialize the future."""
        self._uid = uid
        self._value: T | Exception | None = None
        self._callbacks: list[Callable[[T | Exception], None]] = []
        self._is_done = threading.Event()
        self._callback_pool = callback_pool

    def set_result(self, value: T | Exception) -> None:
        """Set the result of the future."""
        if self._value is not None:
            raise ValueError("Future already has a result. This should not happen.")
        self._value = value
        self._is_done.set()
        for callback in self._callbacks:
            self._callback_pool.submit(callback, value)

    def result(self) -> T:
        """Get the result of the future.

        Returns:
            The result of the future.

        Raises:
            Exception: If the future has an exception.
        """
        self._is_done.wait()
        assert self._value is not None  # for type checker
        if isinstance(self._value, Exception):
            raise self._value
        return self._value

    @property
    def done(self) -> bool:
        """Check if the future is done.

        Returns:
            True if the future is done, False otherwise.
        """
        return self._is_done.is_set()

    def add_callback(self, callback: Callable[[T | Exception], None]) -> None:
        """Add a callback to the future."""
        self._callbacks.append(callback)
