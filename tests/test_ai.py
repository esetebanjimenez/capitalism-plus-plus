"""AI corporation strategy: spawning, modes, decisions, building."""

import pytest

from capitalism.ai import (
    DOMINANCE_INTERVALS,
    MODE_DORMANT,
    MODE_ESTABLISH,
    MODE_MANUFACTURE,
    MODE_RETAIL,
    PROFITABILITY_THRESHOLDS,
    AIState,
    ai_build_firm,
    ai_daily,
    find_ai_site,
    passes_profitability_gate,
    try_spawn_competitor,
)
from capitalism.economy import CORP_AI
from capitalism.person import (
    CHAR_CONSERVATIVE,
    CHAR_VERY_AGGRESSIVE,
    ROLE_CEO,
    STATE_LINKED,
)
from capitalism.rng import Rng
from capitalism.scenario import bread_town, build_bread_chain, find_site
from capitalism.tables import AI_RULES


class TestAIState:
    def test_init(self):
        rng = Rng(1)
        ai = AIState(0, 100, rng)
        assert ai.corp_id == 0
        assert ai.mode == MODE_ESTABLISH
        assert ai.mode_start_day == 100
        assert 0 <= ai.schedule_offset <= 14
        assert ai.pending_build is None
        assert ai.build_cooldowns == {}

    def test_mode_constants(self):
        assert MODE_ESTABLISH == 0
        assert MODE_MANUFACTURE == 1
        assert MODE_RETAIL == 2
        assert MODE_DORMANT == 3


class TestProfitabilityGating:
    def test_no_existing_firms_always_passes(self):
        sim, _town = bread_town(1)
        eco = sim.economy
        corp = eco.add_corp("Test", CORP_AI)
        assert passes_profitability_gate(eco, corp, 2, None)

    def test_conservative_needs_high_ratio(self):
        assert PROFITABILITY_THRESHOLDS[CHAR_CONSERVATIVE] == 0.80

    def test_aggressive_needs_low_ratio(self):
        assert PROFITABILITY_THRESHOLDS[CHAR_VERY_AGGRESSIVE] == 0.30


class TestDominanceIntervals:
    def test_conservative_longest(self):
        assert DOMINANCE_INTERVALS[CHAR_CONSERVATIVE] == 160

    def test_very_aggressive_shortest(self):
        assert DOMINANCE_INTERVALS[CHAR_VERY_AGGRESSIVE] == 40


class TestLocationSelection:
    def test_find_site_returns_valid(self):
        sim, town = bread_town(1)
        rng = Rng(42)
        site = find_ai_site(sim.economy, town, rng)
        assert site is not None
        x, y = site
        assert 0 <= x < sim.world.width
        assert 0 <= y < sim.world.height

    def test_find_core_site(self):
        sim, town = bread_town(1)
        rng = Rng(42)
        site = find_ai_site(sim.economy, town, rng, core=True)
        assert site is not None

    def test_sites_are_town_tiles_of_the_native_range(self):
        """#315: ring branch 0x3000..0x3007, core branch 0x3008..0x300c."""
        from capitalism.world import TileCategory

        sim, town = bread_town(1)
        for core, lo, hi in ((False, 0x3000, 0x3007), (True, 0x3008, 0x300C)):
            rng = Rng(7)
            sites = [find_ai_site(sim.economy, town, rng, core=core) for _ in range(30)]
            found = [site for site in sites if site is not None]
            assert found  # a failed search (20 tries) is native: the AI skips the build
            for site in found:
                tile = sim.world.tile_at(*site)
                assert tile.kind == TileCategory.TOWN and lo <= tile.town_kind <= hi

    def test_no_site_when_no_town_tile_in_reach(self):
        from capitalism.world import TileCategory

        sim, town = bread_town(1)
        for tile in sim.world.tiles:
            if tile.kind == TileCategory.TOWN:
                tile.kind, tile.town_kind = TileCategory.GRASSLAND, 0
        assert find_ai_site(sim.economy, town, Rng(3)) is None
        assert find_ai_site(sim.economy, town, Rng(3), core=True) is None

    def test_ai_firm_stands_on_a_town_tile_and_pays_wages(self):
        sim, town = bread_town(1)
        eco = sim.economy
        corp = eco.add_corp("AI Corp", CORP_AI)
        corp.ledger.cash = 10_000_000.0
        firm = ai_build_firm(eco, corp, 2, town, Rng(42))
        assert firm is not None
        assert 0x3000 <= firm.place_kind <= 0x300C and firm.place_town == town.id
        firm.add_job(1, 7, eco.catalog["Flour"])  # Manufacturing
        sim.advance_day()
        assert firm.ledger.month[1] > 0  # salaries

    def test_deposit_firms_keep_the_offtown_search(self):
        """#316 review: types 5-7 stay off town tiles until #317."""
        from capitalism.world import TileCategory

        sim, town = bread_town(1)
        site = find_ai_site(sim.economy, town, Rng(42), deposit=True)
        assert site is not None
        kind = sim.world.tile_at(*site).kind
        assert kind in (TileCategory.GRASSLAND, TileCategory.FOREST_HILL)


class TestAIBuildFirm:
    def test_build_department_store(self):
        sim, town = bread_town(1)
        eco = sim.economy
        corp = eco.add_corp("AI Corp", CORP_AI)
        corp.ledger.cash = 10_000_000.0
        rng = Rng(42)
        firm = ai_build_firm(eco, corp, 1, town, rng)
        assert firm is not None
        assert firm.owner is corp
        assert firm.type_id == 1

    def test_build_fails_no_cash(self):
        sim, town = bread_town(1)
        eco = sim.economy
        corp = eco.add_corp("AI Corp", CORP_AI)
        corp.ledger.cash = 0.0
        rng = Rng(42)
        firm = ai_build_firm(eco, corp, 1, town, rng)
        assert firm is None

    def test_build_factory(self):
        sim, town = bread_town(1)
        eco = sim.economy
        corp = eco.add_corp("AI Corp", CORP_AI)
        corp.ledger.cash = 10_000_000.0
        rng = Rng(42)
        firm = ai_build_firm(eco, corp, 2, town, rng)
        assert firm is not None
        assert firm.type_id == 2

    def test_build_farm(self):
        sim, town = bread_town(1)
        eco = sim.economy
        corp = eco.add_corp("AI Corp", CORP_AI)
        corp.ledger.cash = 10_000_000.0
        rng = Rng(42)
        firm = ai_build_firm(eco, corp, 4, town, rng, core=True)
        assert firm is not None
        assert firm.type_id == 4


class TestSpawning:
    def test_spawn_needs_available_person(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        result = try_spawn_competitor(eco, 100)
        assert result is None  # no persons exist

    def test_spawn_creates_corp(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        p = eco.add_person("Investor", randomize=True)
        # Override RNG to ensure spawn happens
        old_count = len(eco.corps)
        found = False
        for day in range(200):
            result = try_spawn_competitor(eco, day + 1)
            if result is not None:
                found = True
                break
        if found:
            assert len(eco.corps) == old_count + 1
            assert eco.corps[-1].corp_type == CORP_AI
            assert p.state == STATE_LINKED
            assert p.role == ROLE_CEO

    def test_spawn_respects_cap(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        for i in range(int(AI_RULES.max_competitors)):
            eco.add_corp(f"Corp{i}", CORP_AI)
        eco.add_person("Investor", randomize=True)
        for day in range(100):
            result = try_spawn_competitor(eco, day + 1)
            assert result is None


class TestAIDaily:
    def test_daily_no_crash_no_ai(self):
        sim, town = bread_town(1)
        build_bread_chain(sim, town)
        sim.advance_days(60)

    def test_daily_with_ai_corp(self):
        sim, _town = bread_town(1)
        eco = sim.economy
        ds = sim.calendar.day_serial
        corp = eco.add_corp("AI Corp", CORP_AI)
        corp.ledger.cash = 10_000_000.0
        p = eco.add_person("CEO", randomize=True)
        p.link_to_corp(corp.id)
        rng = Rng(42)
        ai = AIState(corp.id, ds, rng)
        eco.ai_states[corp.id] = ai
        sim.advance_days(60)
        # No $1B reset for competitors (audit A1): real cash only
        assert corp.ledger.cash <= 10_000_000.0

    def test_strategy_dispatch_fires(self):
        sim, _town = bread_town(1)
        eco = sim.economy
        ds = sim.calendar.day_serial
        corp = eco.add_corp("AI Corp", CORP_AI)
        corp.ledger.cash = 10_000_000.0
        p = eco.add_person("CEO", randomize=True)
        p.link_to_corp(corp.id)
        rng = Rng(42)
        ai = AIState(corp.id, ds, rng)
        ai.mode = MODE_ESTABLISH
        eco.ai_states[corp.id] = ai
        sim.advance_days(30)
        # May or may not have built depending on RNG, but shouldn't crash

    def test_dormant_mode_stays_dormant(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        ds = sim.calendar.day_serial
        corp = eco.add_corp("AI Corp", CORP_AI)
        corp.ledger.cash = 10_000_000.0
        rng = Rng(42)
        ai = AIState(corp.id, ds, rng)
        ai.mode = MODE_DORMANT
        ai.dormant_start_day = ds
        eco.ai_states[corp.id] = ai
        p = eco.add_person("CEO", randomize=True)
        p.salary_trait = 99
        p.link_to_corp(corp.id)
        sim.advance_days(30)
        # Dormant mode with salary_trait 99 means wake_years ~10 + random(0,5)
        # In 30 days, should still be dormant
        assert ai.mode == MODE_DORMANT


class TestModeTransitions:
    def test_manufacture_to_establish(self):
        sim, town = bread_town(1)
        eco = sim.economy
        corp = eco.add_corp("AI Corp", CORP_AI)
        corp.ledger.cash = 100_000_000.0
        p = eco.add_person("CEO", randomize=True)
        p.salary_trait = 80
        p.link_to_corp(corp.id)
        rng = Rng(42)
        ai = AIState(corp.id, 0, rng)
        ai.mode = MODE_MANUFACTURE
        ai.mode_start_day = -365 * 20  # 20 years ago
        eco.ai_states[corp.id] = ai
        # Build enough factories
        for _ in range(10):
            site = find_site(sim, town)
            try:
                eco.build_firm(2, corp, site[0], site[1], town)
            except (ValueError, RuntimeError):
                break
        from capitalism.ai import _check_mode_transition

        _check_mode_transition(eco, corp, ai, p, 365 * 20)
        # With 10 factories, threshold ~ 80//20+2=6, duration_threshold ~ 16 - 80//10=8
        # 20 years > 8, should transition
        assert ai.mode == MODE_ESTABLISH

    def test_empty_corp_goes_dormant(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        corp = eco.add_corp("AI Corp", CORP_AI)
        p = eco.add_person("CEO", randomize=True)
        p.character_type = CHAR_CONSERVATIVE
        p.link_to_corp(corp.id)
        rng = Rng(42)
        ai = AIState(corp.id, 0, rng)
        ai.mode = MODE_ESTABLISH
        ai.mode_start_day = 0
        eco.ai_states[corp.id] = ai
        from capitalism.ai import _check_mode_transition

        # Conservative: dormant_years = (4-0)*2 = 8
        _check_mode_transition(eco, corp, ai, p, 365 * 9)
        assert ai.mode == MODE_DORMANT


class TestBankruptcy:
    def test_no_bankruptcy_with_firms(self):
        sim, town = bread_town(1)
        build_bread_chain(sim, town)
        eco = sim.economy
        corp = eco.corps[0]
        corp.corp_type = CORP_AI
        rng = Rng(42)
        ai = AIState(corp.id, 0, rng)
        eco.ai_states[corp.id] = ai
        from capitalism.ai import _check_bankruptcy

        _check_bankruptcy(eco, corp, ai, 365 * 15)
        assert corp.ledger.cash != 0.0  # has firms, no bankruptcy

    def test_bankruptcy_triggers(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        corp = eco.add_corp("Bankrupt Corp", CORP_AI)
        corp.ledger.cash = 10_000.0  # total_assets = cash = 10k, well below threshold 100k
        rng = Rng(42)
        ai = AIState(corp.id, 0, rng)
        eco.ai_states[corp.id] = ai
        from capitalism.ai import _check_bankruptcy

        _check_bankruptcy(eco, corp, ai, 365 * 15)
        assert corp.ledger.cash == 0.0


class TestCashManagement:
    def test_no_competitor_cash_reset(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        ds = sim.calendar.day_serial
        corp = eco.add_corp("AI Corp", CORP_AI)
        corp.ledger.cash = 100.0
        p = eco.add_person("CEO", randomize=True)
        p.link_to_corp(corp.id)
        rng = Rng(42)
        ai = AIState(corp.id, ds, rng)
        eco.ai_states[corp.id] = ai
        ai_daily(eco, corp, ds + 1)
        assert corp.ledger.cash == pytest.approx(100.0)


class TestIntegration:
    def test_full_sim_with_ai(self):
        """Run a full sim with AI corps for 120 days without crashing."""
        sim, town = bread_town(1)
        eco = sim.economy
        ds = sim.calendar.day_serial
        build_bread_chain(sim, town)
        # Add some AI competitors
        for i in range(3):
            corp = eco.add_corp(f"AI {i}", CORP_AI)
            corp.ledger.cash = 10_000_000.0
            p = eco.add_person(f"CEO {i}", randomize=True)
            p.link_to_corp(corp.id)
            rng_ai = Rng(42 + i)
            ai = AIState(corp.id, ds, rng_ai)
            eco.ai_states[corp.id] = ai
        sim.advance_days(120)
        # Competitors spend real cash; nothing tops them up to $1B
        for corp in eco.corps:
            if corp.corp_type == CORP_AI:
                assert corp.ledger.cash <= 10_000_000.0

    def test_deterministic_with_ai(self):
        """Same seed produces same state with AI active."""

        def run(seed):
            sim, _town = bread_town(seed)
            eco = sim.economy
            ds = sim.calendar.day_serial
            corp = eco.add_corp("AI", CORP_AI)
            corp.ledger.cash = 10_000_000.0
            p = eco.add_person("CEO", randomize=True)
            p.link_to_corp(corp.id)
            rng_ai = Rng(seed + 100)
            ai = AIState(corp.id, ds, rng_ai)
            eco.ai_states[corp.id] = ai
            sim.advance_days(60)
            return sim.state_hash()

        assert run(1) == run(1)
