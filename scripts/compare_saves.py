#!/usr/bin/env python3
"""Compare two Capitalism Plus save files via the sim.

Parses save A (earlier), loads its town state into the sim, advances
the sim to save B's date, then diffs the sim's towns against save B's
parsed towns.  This validates the sim's monthly-tick formulas against
the real game without needing RNG seed agreement.

Usage:
  python scripts/compare_saves.py path/to/save_A.SAV path/to/save_B.SAV
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_sav import SaveState, parse_sav
from parse_sav import Town as ParsedTown

from capitalism.calendar import EPOCH, Calendar
from capitalism.rng import Rng
from capitalism.town import Climate, Town, level_for_population


def game_date_to_date(gd) -> date:
    """Convert parsed GameDate to Python date using its year/month/day fields."""
    return date(gd.year, gd.month, gd.day)


def load_town(pt: ParsedTown) -> Town:
    """Create a sim Town from parsed save data."""
    env = (float(pt.env_factors[0]), float(pt.env_factors[1]), float(pt.env_factors[2]))
    climate_map = {0: Climate.BOOM, 1: Climate.PROSPEROUS, 2: Climate.NORMAL,
                   3: Climate.RECESSION, 4: Climate.PANIC}
    town = Town(
        id=pt.index,
        name=pt.name,
        tier=pt.tier,
        x=pt.x,
        y=pt.y,
        stagger_slot=pt.stagger_slot,
        population=pt.population,
        per_capita_gnp=pt.gnp_per_capita,
        level=pt.level,
        unemployment=pt.unemployment,
        labor_cost=pt.labor_cost,
        labor_quality=pt.labor_quality,
        consumer_spending=pt.consumer_spending,
        climate=climate_map.get(pt.econ_climate, Climate.NORMAL),
        env_factors=env,
    )
    town.pop_ring = list(pt.pop_ring)
    town.gnp_level_ring = list(pt.gnp_ring)
    return town


# (label, sim_attr, parsed_attr)
FIELDS = [
    ("population", "population", "population"),
    ("gnp_per_capita", "per_capita_gnp", "gnp_per_capita"),
    ("unemployment", "unemployment", "unemployment"),
    ("labor_cost", "labor_cost", "labor_cost"),
    ("labor_quality", "labor_quality", "labor_quality"),
    ("consumer_spending", "consumer_spending", "consumer_spending"),
]


def compare_towns(
    sim_towns: list[Town], sav_towns: list[ParsedTown], sav_a_towns: list[ParsedTown]
) -> None:
    """Print detailed comparison of sim vs save B, with save A as baseline."""
    by_name_sim = {t.name: t for t in sim_towns}
    by_name_sav = {t.name: t for t in sav_towns}
    by_name_a = {t.name: t for t in sav_a_towns}

    header = f"{'Town':<14} {'Field':<18} {'Save A':>12} {'Save B':>12} {'Sim':>12} {'B-A':>10} {'Sim-A':>10} {'Err':>8}"
    print(header)
    print("-" * len(header))

    for pt_b in sav_towns:
        name = pt_b.name
        st = by_name_sim.get(name)
        pt_a = by_name_a.get(name)
        if st is None or pt_a is None:
            print(f"{name:<14} MISSING")
            continue

        for label, sim_attr, sav_attr in FIELDS:
            val_a = getattr(pt_a, sav_attr)
            val_b = getattr(pt_b, sav_attr)
            val_sim = getattr(st, sim_attr)
            delta_real = val_b - val_a
            delta_sim = val_sim - val_a
            if abs(val_b) > 1e-6:
                err_pct = (val_sim - val_b) / abs(val_b) * 100
            else:
                err_pct = 0.0
            flag = " ***" if abs(err_pct) > 5.0 else ""
            if label == "population":
                print(f"{name:<14} {label:<18} {val_a:>12,.0f} {val_b:>12,.0f} {val_sim:>12,.0f} {delta_real:>+10,.0f} {delta_sim:>+10,.0f} {err_pct:>+7.1f}%{flag}")
            else:
                print(f"{name:<14} {label:<18} {val_a:>12.1f} {val_b:>12.1f} {val_sim:>12.1f} {delta_real:>+10.1f} {delta_sim:>+10.1f} {err_pct:>+7.1f}%{flag}")

        # Level
        if st.level != pt_b.level:
            print(f"{name:<14} {'level':<18} {pt_a.level:>12} {pt_b.level:>12} {st.level:>12} {'':>10} {'':>10}  MISMATCH")
        print()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compare two SAV files via sim")
    ap.add_argument("save_a", type=Path, help="Earlier save file")
    ap.add_argument("save_b", type=Path, help="Later save file")
    ap.add_argument("--seed", type=int, default=42, help="RNG seed for sim (arbitrary)")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args(argv)

    print("Parsing save A...")
    state_a = parse_sav(args.save_a)
    print("Parsing save B...")
    state_b = parse_sav(args.save_b)

    date_a = game_date_to_date(state_a.game_date)
    date_b = game_date_to_date(state_b.game_date)
    days_between = (date_b - date_a).days
    print(f"Save A: {date_a} (serial {state_a.game_date.day_serial})")
    print(f"Save B: {date_b} (serial {state_b.game_date.day_serial})")
    print(f"Days to advance: {days_between}")
    print()

    if days_between <= 0:
        print("Error: save B must be later than save A", file=sys.stderr)
        return 1

    # Load save A towns into sim Town objects
    sim_towns = [load_town(pt) for pt in state_a.towns]
    rng = Rng(args.seed)
    cal = Calendar(date_a)

    if args.verbose:
        print("=== Save A towns (loaded into sim) ===")
        for t in sim_towns:
            print(f"  {t.name}: pop={t.population:,.0f} gnp={t.per_capita_gnp:,.0f}"
                  f" unemp={t.unemployment:.1f}% level={t.level}")
        print()

    # Advance day by day, running town monthly ticks on stagger boundaries
    from capitalism.tables import STAGGER_MOD
    months_ticked = 0
    for _ in range(days_between):
        month_rolled, _year_rolled = cal.advance()
        slot = cal.day_serial % STAGGER_MOD
        for town in sim_towns:
            if town.stagger_slot == slot:
                town.monthly_tick(rng, detailed=False)
                months_ticked += 1

    print(f"Sim advanced to {cal.year}-{cal.month:02d}-{cal.day:02d}"
          f" (serial {cal.day_serial})")
    print(f"Town monthly ticks fired: {months_ticked}")
    print()

    # Compare
    if args.verbose:
        print("=== Sim towns (after advance) ===")
        for t in sim_towns:
            print(f"  {t.name}: pop={t.population:,.0f} gnp={t.per_capita_gnp:,.0f}"
                  f" unemp={t.unemployment:.1f}% level={t.level}")
        print()
        print("=== Save B towns (expected) ===")
        for t in state_b.towns:
            print(f"  {t.name}: pop={t.population:,.0f} gnp={t.gnp_per_capita:,.0f}"
                  f" unemp={t.unemployment:.1f}% level={t.level}")
        print()

    print("=== Town Comparison: Save A → Save B vs Save A → Sim ===")
    print()
    compare_towns(sim_towns, state_b.towns, state_a.towns)

    return 0


if __name__ == "__main__":
    sys.exit(main())
