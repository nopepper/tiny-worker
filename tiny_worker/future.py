"""Provides a lightweight Future implementation for managing asynchronous results.

This module implements a simple Future class that represents a value that will be available
at some point in the future, with support for callbacks and error handling.
"""

from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class TinyFuture(Generic[T]):
    """A Future representing an eventual result of an asynchronous operation.

    Provides a way to check completion status, retrieve results when ready,
    and register callbacks for when the result becomes available.
    """

    def __init__(self, uid: str, callback_pool: ThreadPoolExecutor) -> None:
        """Initialize a new Future.

        Args:
            uid: Unique identifier for this future
            callback_pool: Thread pool for executing callbacks
        """
        self._uid = uid
        self._value: T | Exception | None = None
        self._callbacks: list[Callable[[T | Exception], None]] = []
        self._is_done = threading.Event()
        self._callback_pool = callback_pool

    def set_result(self, value: T | Exception) -> None:
        """Complete this Future with a result or exception.

        Once set, the result cannot be changed and all registered callbacks will be executed.

        Args:
            value: The result value or exception to store

        Raises:
            ValueError: If the Future already has a result
        """
        if self._value is not None:
            raise ValueError("Future already has a result. This should not happen.")
        self._value = value
        self._is_done.set()
        for callback in self._callbacks:
            self._callback_pool.submit(callback, value)

    def result(self, timeout: float | None = None) -> T:
        """Retrieve the result of this Future, waiting if necessary.

        Blocks until the result is available or timeout occurs. If the result
        is an exception, it will be raised.

        Args:
            timeout: Maximum seconds to wait for the result, or None to wait forever

        Returns:
            The result value

        Raises:
            TimeoutError: If the timeout is reached before completion
            Exception: If the Future completed with an exception
        """
        self._is_done.wait(timeout)
        assert self._value is not None  # for type checker
        if isinstance(self._value, Exception):
            raise self._value
        return self._value

    @property
    def done(self) -> bool:
        """Whether this Future has completed.

        Returns:
            True if the Future has a result or exception set, False if still pending
        """
        return self._is_done.is_set()

    def add_callback(self, callback: Callable[[T | Exception], None]) -> None:
        """Register a function to call when this Future completes.

        If the Future is already complete, the callback will be executed immediately.
        Otherwise, it will be called when the result is set. The callback receives
        either the result value or exception.

        Args:
            callback: Function to call with the Future's result when ready
        """
        # If the result is already set, invoke the callback immediately.
        if self._value is not None:
            # self._value can't be None at this point, so just call
            self._callback_pool.submit(callback, self._value)
        else:
            self._callbacks.append(callback)
