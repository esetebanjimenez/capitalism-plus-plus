"""_consume_cycles must match the original per-cycle loop exactly."""

import random
from types import SimpleNamespace

from capitalism.jobs import _consume_cycles


def _reference(stock, inputs, cycles):
    done = 0
    for _ in range(cycles):
        if any(stock.get(i.input_id, (0.0,))[0] < i.qty for i in inputs):
            break
        done += 1
        for i in inputs:
            stock[i.input_id][0] -= i.qty
    return done


def test_matches_reference_loop():
    rng = random.Random(7)
    for _ in range(5000):
        inputs = [
            SimpleNamespace(input_id=k, qty=rng.choice([1.0, 2.0, 3.0, 0.5, 0.1, 1.7]))
            for k in range(rng.randint(0, 3))
        ]
        stock = {}
        for i in inputs:
            if rng.random() < 0.9:
                have = rng.choice([float(rng.randint(0, 500)), rng.uniform(0, 500)])
                stock[i.input_id] = [have, 50.0, 3.0]
        a = {k: list(v) for k, v in stock.items()}
        b = {k: list(v) for k, v in stock.items()}
        cycles = rng.randint(0, 300)
        assert _consume_cycles(a, inputs, cycles) == _reference(b, inputs, cycles)
        assert a == b
