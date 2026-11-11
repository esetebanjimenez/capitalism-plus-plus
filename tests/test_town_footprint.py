"""Town footprint table (client map only): Designer rule from PR #50."""

from capitalism.tables import TOWN_FOOTPRINTS
from capitalism.town import LEVEL_RULES


def test_every_town_level_has_a_footprint():
    assert set(TOWN_FOOTPRINTS) == set(range(1, LEVEL_RULES.max_level + 1))


def test_footprint_steps_at_levels_3_and_5():
    radius = {lv: r.radius for lv, r in TOWN_FOOTPRINTS.items()}
    block = {lv: r.block_level for lv, r in TOWN_FOOTPRINTS.items()}
    assert radius == {1: 0, 2: 0, 3: 1, 4: 1, 5: 2, 6: 2}
    assert block == {1: 0, 2: 0, 3: 1, 4: 1, 5: 2, 6: 2}
    assert all(r.provisional == {"radius", "block_level"} for r in TOWN_FOOTPRINTS.values())
