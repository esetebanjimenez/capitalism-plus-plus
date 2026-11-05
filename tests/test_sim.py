from capitalism import Sim
from capitalism.__main__ import main


def test_advance_days_updates_calendar():
    sim = Sim(seed=1)
    sim.advance_days(31)
    assert sim.year == 1
    assert sim.month == 2
    assert sim.day == 1
    assert len(sim.history) == 31


def test_advance_year():
    sim = Sim()
    sim.advance_days(360)
    assert (sim.year, sim.month, sim.day) == (1, 12, 30)
    sim.advance_days(1)
    assert (sim.year, sim.month, sim.day) == (2, 1, 1)


def test_same_seed_same_length_history():
    a = Sim(seed=42)
    b = Sim(seed=42)
    a.advance_days(10)
    b.advance_days(10)
    assert a.history == b.history


def test_runner_prints_report(capsys):
    assert main(["--days", "5", "--seed", "7"]) == 0
    out = capsys.readouterr().out
    assert "seed:  7" in out
    assert "days:  5" in out
