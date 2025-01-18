# tests/test_troupe_stress.py
import random
import time
from tiny_worker.worker import TinyTroupe


def test_race_condition_stress():
    """
    Somewhat stress-test: submit many tasks simultaneously, each sleeping
    random amounts of time, to see if any race conditions in the callback
    or scheduling logic appear.
    """

    def random_sleep_func(x: int) -> int:
        time.sleep(random.uniform(0.01, 0.05))
        return x * 2

    troupe = TinyTroupe(func=random_sleep_func, context_type="thread", num_workers=10)
    troupe.start()

    values = list(range(50))
    futures = [troupe.submit(v) for v in values]

    # Wait for all results
    results = [f.result() for f in futures]
    expected = [v * 2 for v in values]

    assert results == expected

    troupe.stop()
