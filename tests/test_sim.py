from capitalism import Sim
from capitalism.__main__ import main
from capitalism.calendar import real_days_in_month
from capitalism.rng import Rng
from capitalism.town import level_up_population
from capitalism.world import TileCategory, generate_world


def test_advance_days_updates_calendar():
    sim = Sim(seed=1, target_cities=4)
    sim.advance_days(30)
    assert (sim.year, sim.month, sim.day) == (1, 2, 1)
    assert len(sim.history) == 30


def test_advance_year():
    sim = Sim(seed=2, target_cities=3)
    # Start Y1 M1 D1; 12×30 game days later is Y2 M1 D1.
    sim.advance_days(359)
    assert (sim.year, sim.month, sim.day) == (1, 12, 30)
    sim.advance_days(1)
    assert (sim.year, sim.month, sim.day) == (2, 1, 1)
    assert sim.calendar.years_elapsed == 1
    assert len(sim.gnp_history) == 1


def test_same_seed_same_game():
    a = Sim(seed=42, target_cities=5)
    b = Sim(seed=42, target_cities=5)
    a.advance_days(90)
    b.advance_days(90)
    assert [(t.name, t.x, t.y, t.tier) for t in a.towns] == [
        (t.name, t.x, t.y, t.tier) for t in b.towns
    ]
    assert a.history == b.history
    assert [t.population for t in a.towns] == [t.population for t in b.towns]


def test_different_seed_diverges():
    a = Sim(seed=1, target_cities=5)
    b = Sim(seed=2, target_cities=5)
    assert [(t.x, t.y) for t in a.towns] != [(t.x, t.y) for t in b.towns] or [
        t.name for t in a.towns
    ] != [t.name for t in b.towns]


def test_weekday_and_real_month_length():
    sim = Sim(seed=0, target_cities=2)
    sim.advance_days(1)
    assert sim.calendar.weekday == 1  # day_serial 1
    assert real_days_in_month(1, 1) == 31
    assert real_days_in_month(1, 2) == 28
    assert real_days_in_month(4, 2) == 29
    assert sim.calendar.real_month_days == 31


def test_level_up_thresholds_match_doc():
    # Threshold to leave level L (become L+1) is L² × 160,000.
    assert level_up_population(1) == 160_000  # become level 2
    assert level_up_population(2) == 640_000  # become level 3
    assert level_up_population(3) == 1_440_000
    assert level_up_population(4) == 2_560_000


def test_map_size_and_cities_on_grass():
    world = generate_world(Rng(7), target_cities=6)
    assert world.width == 240 and world.height == 198
    assert 1 <= len(world.towns) <= 6
    for t in world.towns:
        assert world.tile_at(t.x, t.y).category == TileCategory.TOWN
        assert world.tile_at(t.x, t.y).data_id == t.id


def test_land_value_floor():
    sim = Sim(seed=3, target_cities=4)
    v = sim.world.land_value(0, 0)
    assert v >= 500_000


def test_staggered_town_ticks_change_population():
    sim = Sim(seed=11, target_cities=4, detailed_cities=True)
    before = {t.id: t.population for t in sim.towns}
    sim.advance_days(30)
    after = {t.id: t.population for t in sim.towns}
    assert before != after


def test_simple_cities_frozen():
    sim = Sim(seed=5, target_cities=3, detailed_cities=False)
    pops = [t.population for t in sim.towns]
    gnps = [t.per_capita_gnp for t in sim.towns]
    sim.advance_days(60)
    assert [t.population for t in sim.towns] == pops
    assert [t.per_capita_gnp for t in sim.towns] == gnps
    assert all(t.level == 3 for t in sim.towns)
    assert all(t.per_capita_gnp == 20_000 for t in sim.towns)


def test_runner_prints_report(capsys):
    assert main(["--days", "5", "--seed", "7", "--cities", "3"]) == 0
    out = capsys.readouterr().out
    assert "seed:   7" in out
    assert "days:   5" in out
    assert "map:" in out
