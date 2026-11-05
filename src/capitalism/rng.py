"""Seeded RNG. Same seed must produce the same sequence for golden tests."""

from __future__ import annotations

import random


class Rng:
    def __init__(self, seed: int = 0) -> None:
        self._seed = seed
        self._r = random.Random(seed)

    @property
    def seed(self) -> int:
        return self._seed

    def random(self) -> float:
        return self._r.random()

    def randint(self, a: int, b: int) -> int:
        """Inclusive integer in [a, b]."""
        return self._r.randint(a, b)

    def choice(self, seq):
        return self._r.choice(seq)

    def uniform(self, a: float, b: float) -> float:
        return self._r.uniform(a, b)

    def chance(self, p: float) -> bool:
        return self._r.random() < p
