"""Headless runner: advance the sim N days and print a report.

Usage:
  python -m capitalism --days 30 --seed 1
  capitalism --days 365
"""

from __future__ import annotations

import argparse

from .sim import Sim


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="capitalism", description="Capitalism++ headless sim runner")
    p.add_argument("--days", type=int, default=30, help="number of days to advance (default: 30)")
    p.add_argument("--seed", type=int, default=0, help="RNG seed (default: 0)")
    args = p.parse_args(argv)
    if args.days < 0:
        p.error("--days must be >= 0")
    sim = Sim(seed=args.seed)
    sim.advance_days(args.days)
    print(sim.report(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
