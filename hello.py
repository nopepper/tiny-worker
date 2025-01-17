import time
from tiny_worker.worker import TinyWorker
from typing import List
import math


class NumberCruncherWorker(TinyWorker[List[float], float]):
    """A worker that performs some time-consuming calculations on a list of numbers."""

    def tiny_call(self, numbers: List[float]) -> List[float]:
        # Simulate some CPU-intensive work
        time.sleep(0.1)  # Artificial delay to simulate work
        return [math.sin(x) for x in numbers]


def cruncher(numbers: List[float]) -> list[float]:
    time.sleep(0.1)
    return [math.sin(x) for x in numbers]
