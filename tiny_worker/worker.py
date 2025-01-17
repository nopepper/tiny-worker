"""Tiny worker base class."""

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from multiprocessing.process import BaseProcess
import multiprocessing as mp
from multiprocessing.context import ForkContext, ForkServerContext, SpawnContext
import threading
from typing import Callable, Generic, Literal, TypeVar, Any, cast
from queue import Queue
import uuid

from .future import TinyFuture

T_IN = TypeVar("T_IN")
T_OUT = TypeVar("T_OUT")


class TinyWorker(ABC, Generic[T_IN, T_OUT]):
    """Base class for all tiny workers."""

    @abstractmethod
    def tiny_call(self, value: T_IN) -> T_OUT:
        """Call the worker."""
        pass


class TinyFuncWorker(TinyWorker[T_IN, T_OUT]):
    """A worker that simply calls a function."""

    def __init__(self, func: Callable[[T_IN], T_OUT]) -> None:
        """Initialize with a function to wrap.

        Args:
            func: The function to wrap and call in tiny_call.
        """
        self.func = func

    def tiny_call(self, value: T_IN) -> T_OUT:
        """Simply call the stored function on the input."""
        return self.func(value)


def _start_worker(
    worker_type: type[TinyWorker[T_IN, T_OUT]],
    worker_kwargs: dict[str, Any],
    input_queue: Queue[tuple[str, T_IN] | None],
    output_queue: Queue[tuple[str, T_OUT | Exception]],
) -> None:
    """Start a worker."""
    worker = worker_type(**worker_kwargs)
    while True:
        value = input_queue.get()
        if value is None:
            input_queue.put(None)
            break
        assert isinstance(value, tuple)
        uid, req = value
        try:
            resp = worker.tiny_call(req)
        except Exception as e:
            resp = e
        output_queue.put((uid, resp))


class TinyTroupe(Generic[T_IN, T_OUT]):
    """A tiny troupe of workers."""

    def __init__(
        self,
        worker_type: type[TinyWorker[T_IN, T_OUT]] | None = None,
        worker_kwargs: dict[str, Any] | None = None,
        func: Callable[[T_IN], T_OUT] | None = None,
        context_type: Literal["thread", "spawn", "fork", "forkserver"] = "thread",
        num_workers: int = 1,
        callback_pool_size: int = 64,
    ) -> None:
        """Initialize the troupe."""
        if func is not None:
            worker_type = TinyFuncWorker
            worker_kwargs = {"func": func}
        self._worker_type = worker_type
        self._worker_kwargs = worker_kwargs or {}

        self._workers: list[Thread | BaseProcess]
        self._input_queue: Queue[tuple[str, T_IN] | None] | mp.Queue[tuple[str, T_IN] | None]
        self._output_queue: Queue[tuple[str, T_OUT]] | mp.Queue[tuple[str, T_OUT]]
        if context_type == "thread":
            self._input_queue = Queue()
            self._output_queue = Queue()
            self._workers = [
                Thread(
                    target=_start_worker,
                    daemon=True,
                    kwargs={
                        "worker_type": self._worker_type,
                        "worker_kwargs": self._worker_kwargs,
                        "input_queue": self._input_queue,
                        "output_queue": self._output_queue,
                    },
                )
                for _ in range(num_workers)
            ]
        else:
            assert context_type in ["spawn", "fork", "forkserver"]
            ctx = cast(SpawnContext | ForkContext | ForkServerContext, mp.get_context(context_type))
            self._input_queue = ctx.Queue()
            self._output_queue = ctx.Queue()
            self._workers = [
                ctx.Process(
                    target=_start_worker,
                    daemon=True,
                    kwargs={
                        "worker_type": self._worker_type,
                        "worker_kwargs": self._worker_kwargs,
                        "input_queue": self._input_queue,
                        "output_queue": self._output_queue,
                    },
                )
                for _ in range(num_workers)
            ]

        self._started = False
        self._uid_to_future: dict[str, TinyFuture[T_OUT | Exception]] = {}
        self._futures_lock = threading.Lock()
        self._futures_thread = threading.Thread(target=self._process_futures, daemon=True)
        self._futures_thread.start()
        self._callback_pool = ThreadPoolExecutor(max_workers=callback_pool_size)

    def _process_futures(self) -> None:
        """Process the futures."""
        while True:
            val = self._output_queue.get()
            if val is None:
                break
            assert isinstance(val, tuple)
            uid, resp = val
            with self._futures_lock:
                self._uid_to_future[uid].set_result(resp)

    def submit(self, value: T_IN | TinyFuture[T_IN]) -> TinyFuture[T_OUT]:
        """Request a response from the troupe."""
        uid = str(uuid.uuid4())
        future = TinyFuture(uid, self._callback_pool)

        def _put_value(val: T_IN | Exception) -> None:
            if isinstance(val, Exception):
                future.set_result(val)
            else:
                self._input_queue.put((uid, val))
                with self._futures_lock:
                    self._uid_to_future[uid] = future

        if isinstance(value, TinyFuture):
            value.add_callback(_put_value)
        else:
            _put_value(value)

        return future

    def start(self) -> None:
        """Start the troupe."""
        if self._started:
            raise ValueError("Troupe already started")
        self._started = True

        for worker in self._workers:
            worker.start()

    def stop(self) -> None:
        """Stop the troupe."""
        if not self._started:
            raise ValueError("Troupe not started")
        self._input_queue.put(None)
        for worker in self._workers:
            worker.join()
        self._started = False
