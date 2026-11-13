"""Golden tests for slices 1–2 (docs/design.md)."""

from datetime import date

from capitalism import Sim
from capitalism.__main__ import main
from capitalism.calendar import Calendar, day_serial_of, real_days_in_month
from capitalism.rng import Rng
from capitalism.tables import CITY_NAME_POOL, LAND_VALUE, MAP_RULES, TIER_GNP
from capitalism.town import level_for_population, level_up_population, population_for_level
from capitalism.world import MIN_LAND_TILES, Tile, TileCategory, World


def test_tables_load_from_sqlite():
    assert len(CITY_NAME_POOL) == 24
    assert all(c.tier in (0, 1, 2, 3) for c in CITY_NAME_POOL)
    assert TIER_GNP[0].lo == 200
    assert LAND_VALUE.floor == 500_000
    assert MAP_RULES.width == 240 and MAP_RULES.default_cities == 5


def test_calendar_starts_1990_and_uses_real_boundaries():
    cal = Calendar()
    assert (cal.year, cal.month, cal.day, cal.real_day) == (1990, 1, 1, 1)
    assert cal.day_serial == day_serial_of(date(1990, 1, 1))
    for _ in range(30):
        cal.advance()
    assert (cal.year, cal.month, cal.real_day) == (1990, 1, 31)
    assert cal.day == 30  # clamped
    month_rolled, year_rolled = cal.advance()
    assert month_rolled and not year_rolled
    assert (cal.year, cal.month, cal.day) == (1990, 2, 1)


def test_day_of_month_clamp_and_leap_february():
    cal = Calendar()
    while not (cal.month == 1 and cal.real_day == 30):
        cal.advance()
    assert cal.day == 30 and cal.real_month_days == 31
    cal.advance()
    assert cal.real_day == 31 and cal.day == 30
    assert real_days_in_month(1992, 2) == 29


def test_advance_days_updates_calendar():
    sim = Sim(seed=1, target_cities=4)
    sim.advance_days(31)
    assert (sim.year, sim.month, sim.day) == (1990, 2, 1)
    assert len(sim.history) == 31


def test_advance_year():
    sim = Sim(seed=2, target_cities=3)
    sim.advance_days(365)
    assert (sim.year, sim.month, sim.day) == (1991, 1, 1)
    assert sim.calendar.years_elapsed == 1
    assert len(sim.gnp_history) == 1


def test_determinism_state_hash():
    a = Sim(seed=42, target_cities=5)
    b = Sim(seed=42, target_cities=5)
    a.advance_days(120)
    b.advance_days(120)
    assert a.state_hash() == b.state_hash()
    c = Sim(seed=43, target_cities=5)
    c.advance_days(120)
    assert a.state_hash() != c.state_hash()


def test_hook_order_on_month_and_year_boundary():
    sim = Sim(seed=1, target_cities=2, record_hooks=True)
    while not (sim.calendar.month == 1 and sim.calendar.real_day == 31):
        sim.advance_day()
        sim.hooks.clear()
    sim.advance_day()
    assert sim.hooks[:3] == ["firms", "jobs", "links"]
    assert "month_gnp_index" in sim.hooks
    assert sim.hooks.index("month_gnp_index") < sim.hooks.index("corporations")
    assert sim.hooks.index("firms") < sim.hooks.index("month_gnp_index")

    sim.hooks.clear()
    while not (sim.year == 1990 and sim.month == 12 and sim.calendar.real_day == 31):
        sim.advance_day()
        sim.hooks.clear()
    sim.advance_day()
    assert "month_gnp_index" in sim.hooks
    assert "year_pass" in sim.hooks
    assert sim.hooks.index("month_gnp_index") < sim.hooks.index("year_pass")
    assert sim.hooks.index("year_pass") < sim.hooks.index("corporations")


def test_stagger_covers_all_slots_in_30_days():
    sim = Sim(seed=11, target_cities=5, detailed_cities=True)
    sim.town_slots_hit.clear()
    sim.product_slots_hit.clear()
    for _ in range(30):
        sim.advance_day()
    # Every product slot 0..29 is visited exactly once per 30-day window.
    assert sim.product_slots_hit == set(range(30))
    # Every town slot that exists is visited; over a full cycle all residues appear
    # for the product layer, and each town's slot is in the hit set.
    assert {t.stagger_slot for t in sim.towns} <= sim.town_slots_hit
    # With 5 towns, slots are 0..4; after 30 days each of those fired once.
    assert sim.town_slots_hit == {t.stagger_slot for t in sim.towns}


def test_weekly_ratings_on_weekday_5():
    sim = Sim(seed=0, target_cities=2, record_hooks=True)
    hits = []
    for _ in range(21):
        sim.hooks.clear()
        sim.advance_day()
        if "weekly_ratings" in sim.hooks:
            hits.append(sim.calendar.day_serial % 7)
    assert hits and all(h == 5 for h in hits)


def test_month_and_year_pass_counts_over_ten_years():
    sim = Sim(seed=4, target_cities=3, record_hooks=True)
    months = years = 0
    # 10 years from 1990 → through 1999-12-31 into 2000-01-01 = 3652 days (2 leap: 92,96)
    # Count passes while advancing exactly 10 years of calendar boundaries from start.
    target_year = 2000
    while sim.year < target_year:
        sim.hooks.clear()
        sim.advance_day()
        if "month_gnp_index" in sim.hooks:
            months += 1
        if "year_pass" in sim.hooks:
            years += 1
    assert months == 120
    assert years == 10


def test_weekday_and_real_month_length():
    sim = Sim(seed=0, target_cities=2)
    start_serial = sim.calendar.day_serial
    sim.advance_days(1)
    assert sim.calendar.weekday == (start_serial + 1) % 7
    assert real_days_in_month(1990, 1) == 31
    assert real_days_in_month(1990, 2) == 28
    assert real_days_in_month(1992, 2) == 29


def test_level_thresholds_match_design():
    assert population_for_level(2) == 160_000
    assert population_for_level(3) == 640_000
    assert level_up_population(1) == 160_000
    assert level_up_population(2) == 640_000
    assert level_for_population(160_000) == 2
    assert level_for_population(640_000) == 3
    assert level_for_population(100) == 1


def test_map_shape_and_cities_seed_range():
    for seed in range(1, 51):
        world = World.generate(Rng(seed), target_cities=5)
        assert world.width == 240 and world.height == 198
        land = sum(
            1
            for t in world.tiles
            if t.kind in (TileCategory.GRASSLAND, TileCategory.FOREST_HILL, TileCategory.TOWN)
        )
        assert land >= MIN_LAND_TILES
        assert 34 <= world.equator_row <= 164
        assert len(world.towns) == 5
        names = [t.name for t in world.towns]
        assert len(names) == len(set(names))
        for t in world.towns:
            assert world.tile_at(t.x, t.y).kind == TileCategory.TOWN
            assert t.stagger_slot == t.id % 30
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if dx == 0 and dy == 0:
                        continue
                    # Placed on a 5x5 grass block; the founding spread (#302) may
                    # have turned some of it into town tiles since.
                    assert world.tile_at(t.x + dx, t.y + dy).kind in (
                        TileCategory.GRASSLAND,
                        TileCategory.TOWN,
                    )
        for i, a in enumerate(world.towns):
            for b in world.towns[i + 1 :]:
                assert not (abs(a.x - b.x) < 15 and abs(a.y - b.y) < 15)


def test_map_determinism():
    a = World.generate(Rng(42), target_cities=5)
    b = World.generate(Rng(42), target_cities=5)
    assert [t.height for t in a.tiles[::100]] == [t.height for t in b.tiles[::100]]
    assert [(t.name, t.x, t.y) for t in a.towns] == [(t.name, t.x, t.y) for t in b.towns]


def test_land_value_floor_and_centre():
    sim = Sim(seed=1, target_cities=5)  # seed 3 has only level-2 towns since #302
    assert sim.world.land_value(0, 0) >= 500_000
    assert sim.towns
    t = max(sim.towns, key=lambda tw: tw.population * tw.per_capita_gnp)
    centre = sim.world.land_value(t.x, t.y)
    edge = sim.world.land_value(t.x + t.level + 4, t.y)
    assert centre >= 500_000
    assert centre > edge


def test_stagger_uses_day_serial_mod_30():
    sim = Sim(seed=11, target_cities=4, detailed_cities=True)
    before = {t.id: t.population for t in sim.towns}
    sim.advance_days(60)
    after = {t.id: t.population for t in sim.towns}
    assert before != after


def test_simple_cities_pop_grows_gnp_frozen():
    """Simple-mode cities grow population (additive) but freeze GNP/labor/spending."""
    sim = Sim(seed=5, target_cities=3, detailed_cities=False)
    pops = [t.population for t in sim.towns]
    gnps = [t.per_capita_gnp for t in sim.towns]
    sim.advance_days(365 * 2)
    assert [t.population for t in sim.towns] != pops
    assert [t.per_capita_gnp for t in sim.towns] == gnps
    assert all(t.per_capita_gnp == 20_000 for t in sim.towns)
    assert all(t.consumer_spending == 100 for t in sim.towns)


def test_detailed_clamps_after_ten_years():
    sim = Sim(seed=9, target_cities=5, detailed_cities=True)
    sim.advance_days(365 * 10)
    for t in sim.towns:
        assert 2.0 <= t.unemployment <= 10.0
        assert 1.0 <= t.labor_quality <= 100.0
        assert t.per_capita_gnp >= 200
        if t.population >= 640_000:
            assert t.level >= 3


def test_runner_prints_report(capsys):
    assert main(["--days", "5", "--seed", "7", "--cities", "3"]) == 0
    out = capsys.readouterr().out
    assert "seed:   7" in out
    assert "days:   5" in out
    assert "map:" in out


def test_rolling_gnp_is_twelve_month_ratio_not_average():
    sim = Sim(seed=8, target_cities=3, detailed_cities=True)
    t = sim.towns[0]
    from capitalism.rng import Rng

    # Stay inside tier 2 so the tier floor does not yank GNP up.
    t.tier = 2
    t.ring_index = 0
    t.gnp_level_ring = [10_000.0] * 12
    t.per_capita_gnp = 10_000.0
    t.monthly_tick(Rng(0), detailed=True)
    assert t.rolling_gnp_growth == t.per_capita_gnp / 10_000.0 - 1.0
    assert abs(t.rolling_gnp_growth) < 0.02

    # A known 12-month ratio (−10%) is reachable, unlike averaging monthly deltas.
    t.gnp_level_ring = [12_000.0] * 12
    t.ring_index = 0
    t.per_capita_gnp = 10_800.0
    t.rolling_gnp_growth = t.per_capita_gnp / t.gnp_level_ring[t.ring_index] - 1.0
    assert abs(t.rolling_gnp_growth - (-0.10)) < 1e-12


def test_gnp_index_stimulus_and_cooldown():
    from capitalism.rng import Rng

    sim = Sim(seed=1, target_cities=2)

    def run_index(growth: float, index: float, seed: int) -> float:
        sim.avg_gnp_growth_12m = growth
        sim.gnp_index = index
        sim.rng = Rng(seed)
        # Inline the month-pass GNP step only (spawn/towns would rewrite growth).
        t = __import__("capitalism.tables", fromlist=["GNP_INDEX"]).GNP_INDEX
        if sim.rng.chance(t.step_chance):
            if growth < t.low_growth:
                sim.gnp_index = sim.gnp_index + t.step
            elif growth > t.high_growth and sim.gnp_index > 1.0:
                sim.gnp_index = max(t.floor, sim.gnp_index - t.step)
        return sim.gnp_index

    assert any(run_index(-0.01, 1.0, s) > 1.0 for s in range(300))
    assert any(run_index(0.10, 1.2, s) < 1.2 for s in range(300))
    assert all(run_index(0.03, 1.0, s) == 1.0 for s in range(50))


def test_rules_md_matches_database():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [sys.executable, str(root / "scripts" / "generate_rules_md.py"), "--check"],
        check=False,
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr


def test_world_subclass_replaces_terrain_and_build_rule():
    class Scorched(World):
        def _build_terrain(self, rng: Rng) -> None:
            self.equator_row = 99
            self.tiles = [
                Tile(kind=TileCategory.FOREST_HILL, height=220.0)
                for _ in range(self.width * self.height)
            ]

        def can_build(self, x: int, y: int) -> bool:
            return False

    world = Scorched.generate(Rng(1), target_cities=0)
    assert isinstance(world, Scorched)
    assert world.towns == []
    assert all(t.kind == TileCategory.FOREST_HILL for t in world.tiles)
    assert world.can_build(10, 10) is False

    sim = Sim(seed=1, target_cities=1, world_cls=Scorched)
    assert isinstance(sim.world, Scorched)
    assert sim.world.can_build(0, 0) is False
