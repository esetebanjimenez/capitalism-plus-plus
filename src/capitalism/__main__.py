"""Headless runner: advance the sim N days and print a report."""

from __future__ import annotations

import argparse

from .sim import Game


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="capitalism", description="Capitalism++ headless sim runner")
    p.add_argument("--days", type=int, default=30, help="number of days to advance (default: 30)")
    p.add_argument("--seed", type=int, default=0, help="RNG seed (default: 0)")
    p.add_argument(
        "--cities",
        type=int,
        default=8,
        help="target city count at map gen (default: 8, max 12)",
    )
    p.add_argument(
        "--simple-cities",
        action="store_true",
        help="freeze city indicators (Detailed City Development off)",
    )
    args = p.parse_args(argv)
    if args.days < 0:
        p.error("--days must be >= 0")
    game = Game(
        seed=args.seed,
        detailed_cities=not args.simple_cities,
        target_cities=min(12, max(0, args.cities)),
    )
    game.advance_days(args.days)
    print(game.report(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
