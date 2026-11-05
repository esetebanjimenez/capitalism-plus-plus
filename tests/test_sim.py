"""Golden tests for slices 1–2 (docs/design.md)."""

from datetime import date

from capitalism import Sim
from capitalism.__main__ import main
from capitalism.calendar import Calendar, day_serial_of, real_days_in_month
from capitalism.rng import Rng
from capitalism.town import level_for_population, level_up_population, population_for_level
from capitalism.world import MAP_TILES, TileCategory, generate_world


def test_calendar_starts_1990_and_uses_real_boundaries():
    cal = Calendar()
    assert (cal.year, cal.month, cal.day, cal.real_day) == (1990, 1, 1, 1)
    assert cal.day_serial == day_serial_of(date(1990, 1, 1))
    # Advance through January (31 real days) → Feb 1
    for _ in range(30):
        cal.advance()
    assert (cal.year, cal.month, cal.real_day) == (1990, 1, 31)
    assert cal.day == 30  # clamped
    month_rolled, year_rolled = cal.advance()
    assert month_rolled and not year_rolled
    assert (cal.year, cal.month, cal.day) == (1990, 2, 1)


def test_advance_days_updates_calendar():
    sim = Sim(seed=1, target_cities=4)
    sim.advance_days(31)  # Jan has 31 real days
    assert (sim.year, sim.month, sim.day) == (1990, 2, 1)
    assert len(sim.history) == 31


def test_advance_year():
    sim = Sim(seed=2, target_cities=3)
    # 1990 is not a leap year → 365 days to 1991-01-01
    sim.advance_days(364)
    assert (sim.year, sim.month, sim.day) == (1990, 12, 30) or (
        sim.year,
        sim.month,
        sim.calendar.real_day,
    ) == (1990, 12, 31)
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
    # Advance to Jan 31, then one more day rolls into Feb 1
    while not (sim.calendar.month == 1 and sim.calendar.real_day == 31):
        sim.advance_day()
        sim.hooks.clear()
    sim.advance_day()  # → Feb 1, month pass
    assert sim.hooks[:3] == ["firms", "jobs", "links"]
    assert "month_gnp_index" in sim.hooks
    assert sim.hooks.index("month_gnp_index") < sim.hooks.index("corporations")
    assert sim.hooks.index("firms") < sim.hooks.index("month_gnp_index")

    # Year boundary: into 1991-01-01
    sim.hooks.clear()
    while not (sim.year == 1990 and sim.month == 12 and sim.calendar.real_day == 31):
        sim.advance_day()
        sim.hooks.clear()
    sim.advance_day()
    assert "month_gnp_index" in sim.hooks
    assert "year_pass" in sim.hooks
    assert sim.hooks.index("month_gnp_index") < sim.hooks.index("year_pass")
    assert sim.hooks.index("year_pass") < sim.hooks.index("corporations")


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


def test_map_shape_and_cities():
    world = generate_world(Rng(7), target_cities=5)
    assert world.width == 240 and world.height == 198
    land = sum(
        1
        for t in world.tiles
        if t.kind in (TileCategory.GRASSLAND, TileCategory.FOREST_HILL, TileCategory.TOWN)
    )
    assert land >= MAP_TILES // 3
    assert 34 <= world.equator_row <= 164
    assert len(world.towns) == 5
    names = [t.name for t in world.towns]
    assert len(names) == len(set(names))
    for t in world.towns:
        assert world.tile_at(t.x, t.y).kind == TileCategory.TOWN
        assert t.stagger_slot == t.id % 30
        # 5×5 grassland around centre was required at placement; centre is now TOWN
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx == 0 and dy == 0:
                    continue
                tile = world.tile_at(t.x + dx, t.y + dy)
                assert tile.kind == TileCategory.GRASSLAND
    for i, a in enumerate(world.towns):
        for b in world.towns[i + 1 :]:
            assert not (abs(a.x - b.x) < 15 and abs(a.y - b.y) < 15)


def test_map_determinism():
    a = generate_world(Rng(42), target_cities=5)
    b = generate_world(Rng(42), target_cities=5)
    assert [t.height for t in a.tiles[::100]] == [t.height for t in b.tiles[::100]]
    assert [(t.name, t.x, t.y) for t in a.towns] == [(t.name, t.x, t.y) for t in b.towns]


def test_land_value_floor_and_centre():
    sim = Sim(seed=3, target_cities=5)
    assert sim.world.land_value(0, 0) >= 500_000
    assert sim.towns
    # Pick the town with the highest centre base so it clears the floor.
    t = max(sim.towns, key=lambda tw: tw.level * tw.per_capita_gnp)
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


def test_simple_cities_frozen():
    sim = Sim(seed=5, target_cities=3, detailed_cities=False)
    pops = [t.population for t in sim.towns]
    gnps = [t.per_capita_gnp for t in sim.towns]
    sim.advance_days(365 * 2)
    assert [t.population for t in sim.towns] == pops
    assert [t.per_capita_gnp for t in sim.towns] == gnps
    assert all(t.level == 3 for t in sim.towns)
    assert all(t.per_capita_gnp == 20_000 for t in sim.towns)


def test_detailed_clamps_after_ten_years():
    sim = Sim(seed=9, target_cities=5, detailed_cities=True)
    sim.advance_days(365 * 10)
    for t in sim.towns:
        assert 2.0 <= t.unemployment <= 10.0
        assert 1.0 <= t.labor_quality <= 100.0
        assert t.per_capita_gnp >= 200  # at least tier-0 floor band
        if t.population >= 640_000:
            assert t.level >= 3


def test_runner_prints_report(capsys):
    assert main(["--days", "5", "--seed", "7", "--cities", "3"]) == 0
    out = capsys.readouterr().out
    assert "seed:   7" in out
    assert "days:   5" in out
    assert "map:" in out
