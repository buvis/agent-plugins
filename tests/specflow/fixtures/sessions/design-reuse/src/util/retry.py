"""Retry with exponential backoff (session fixture)."""

import time


def with_backoff(call, attempts: int = 3, base: float = 0.5):
    for n in range(attempts):
        try:
            return call()
        except TimeoutError:
            if n == attempts - 1:
                raise
            time.sleep(base * 2**n)
