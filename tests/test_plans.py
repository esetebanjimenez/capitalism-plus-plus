"""Plan system: capture, apply, scoring, folders and library."""

import pytest

from capitalism.firms import encode_links
from capitalism.jobs import Manufacturing, Purchasing, Sales
from capitalism.plans import (
    INVALID_SCORE,
    UNCONTESTED_SCORE,
    Plan,
    PlanFolder,
    PlanLibrary,
    PlanSlot,
    apply_plan,
    capture,
)
from capitalism.scenario import (
    DEPARTMENT_STORE,
    FACTORY,
    MANUFACTURING,
    bread_town,
    build_bread_chain,
    find_site,
)


class TestPlanSlot:
    def test_empty_slot(self):
        slot = PlanSlot()
        assert slot.empty
        assert slot.job_type == 0
        assert slot.product_id == 0

    def test_filled_slot(self):
        slot = PlanSlot(job_type=7, product_id=42, param1=1, param2=2)
        assert not slot.empty
        assert slot.job_type == 7
        assert slot.product_id == 42


class TestPlanCapture:
    def test_capture_bread_factory(self):
        sim, town = bread_town(1)
        chain = build_bread_chain(sim, town)
        plan = capture(chain.bread_factory)

        assert plan.valid
        assert plan.firm_type == FACTORY
        assert plan.connection_mask == chain.bread_factory.links

        filled = [s for s in plan.slots if not s.empty]
        assert len(filled) == 3
        assert plan.slots[0].job_type == Purchasing.type_id
        assert plan.slots[1].job_type == Manufacturing.type_id
        assert plan.slots[2].job_type == Sales.type_id

        bread = sim.economy.catalog["Bread"]
        assert plan.slots[2].product_id == bread.id

    def test_capture_preserves_connection_bitmask(self):
        sim, town = bread_town(1)
        chain = build_bread_chain(sim, town)
        plan = capture(chain.bread_factory)
        expected = encode_links([(0, 1), (1, 2)])
        assert plan.connection_mask == expected

    def test_capture_computes_demand_products(self):
        sim, town = bread_town(1)
        chain = build_bread_chain(sim, town)
        plan = capture(chain.bread_factory)
        bread = sim.economy.catalog["Bread"]
        assert plan.demand_products == [bread.id]

    def test_capture_store_with_one_sales_slot(self):
        sim, town = bread_town(1)
        chain = build_bread_chain(sim, town)
        plan = capture(chain.store)
        assert plan.firm_type == DEPARTMENT_STORE
        assert plan.valid
        bread = sim.economy.catalog["Bread"]
        assert plan.demand_products == [bread.id]


class TestPlanApply:
    def test_apply_recreates_factory_layout(self):
        sim, town = bread_town(1)
        chain = build_bread_chain(sim, town)
        plan = capture(chain.bread_factory)

        eco = sim.economy
        corp = eco.add_corp("New Corp")
        bread = eco.catalog["Bread"]
        corp.technology[bread.id] = bread.state.tech_level
        x, y = find_site(sim, town)
        new_firm = eco.build_firm(FACTORY, corp, x, y, town)

        apply_plan(plan, new_firm, eco)

        assert new_firm.links == plan.connection_mask
        jobs = new_firm.jobs()
        assert len(jobs) == 3
        assert isinstance(jobs[0], Purchasing)
        assert isinstance(jobs[1], Manufacturing)
        assert isinstance(jobs[2], Sales)
        assert jobs[2].product.id == bread.id

    def test_apply_rejects_wrong_firm_type(self):
        sim, town = bread_town(1)
        chain = build_bread_chain(sim, town)
        plan = capture(chain.bread_factory)  # type FACTORY

        eco = sim.economy
        x, y = find_site(sim, town)
        store = eco.build_firm(DEPARTMENT_STORE, None, x, y, town)

        with pytest.raises(ValueError, match="firm type"):
            apply_plan(plan, store, eco)

    def test_apply_rejects_invalid_plan(self):
        plan = Plan(description="empty", firm_type=FACTORY, valid=False)
        sim, town = bread_town(1)
        eco = sim.economy
        x, y = find_site(sim, town)
        firm = eco.build_firm(FACTORY, None, x, y, town)

        with pytest.raises(ValueError, match="invalid plan"):
            apply_plan(plan, firm, eco)

    def test_apply_clears_existing_slots(self):
        sim, town = bread_town(1)
        chain = build_bread_chain(sim, town)

        eco = sim.economy
        corp = eco.corps[0]
        corp.ledger.cash += 2_000_000  # the chain now buys town land (#285)
        x, y = find_site(sim, town)
        firm = eco.build_firm(FACTORY, corp, x, y, town)
        flour = eco.catalog["Flour"]
        firm.add_job(0, MANUFACTURING, flour)
        assert len(firm.jobs()) == 1

        plan = capture(chain.bread_factory)
        apply_plan(plan, firm, eco)
        assert len(firm.jobs()) == 3


class TestPlanScoring:
    def test_invalid_plan_scores_negative(self):
        plan = Plan(valid=False)
        sim, _town = bread_town(1)
        assert plan.score(sim.economy) == INVALID_SCORE

    def test_no_demand_products_scores_negative(self):
        plan = Plan(valid=True)
        plan.demand_products = []
        sim, _town = bread_town(1)
        assert plan.score(sim.economy) == INVALID_SCORE

    def test_uncontested_market_scores_maximum(self):
        sim, _town = bread_town(1)
        eco = sim.economy
        bread = eco.catalog["Bread"]
        plan = Plan(valid=True)
        plan.demand_products = [bread.id]
        assert plan.score(eco) == UNCONTESTED_SCORE

    def test_contested_market_scores_below_maximum(self):
        sim, town = bread_town(1)
        chain = build_bread_chain(sim, town)
        eco = sim.economy
        sim.advance_days(60)

        plan = capture(chain.bread_factory)
        score = plan.score(eco)
        assert score < UNCONTESTED_SCORE

    def test_revenue_estimate_positive_for_bread(self):
        sim, _town = bread_town(1)
        eco = sim.economy
        bread = eco.catalog["Bread"]
        plan = Plan(valid=True)
        plan.demand_products = [bread.id]
        assert plan.revenue_estimate(eco) > 0


class TestPlanFolder:
    def test_add_and_count(self):
        folder = PlanFolder("TEST")
        p1 = Plan(description="Plan A", firm_type=2, valid=True)
        p2 = Plan(description="Plan B", firm_type=2, valid=True)
        folder.add(p1)
        folder.add(p2)
        assert len(folder.plans) == 2

    def test_delete(self):
        folder = PlanFolder("TEST")
        folder.add(Plan(description="A", valid=True))
        folder.add(Plan(description="B", valid=True))
        folder.delete(0)
        assert len(folder.plans) == 1
        assert folder.plans[0].description == "B"

    def test_best_returns_highest_score(self):
        sim, _town = bread_town(1)
        eco = sim.economy
        bread = eco.catalog["Bread"]

        folder = PlanFolder("FACT")
        invalid = Plan(valid=False)
        valid = Plan(valid=True)
        valid.demand_products = [bread.id]
        folder.add(invalid)
        folder.add(valid)

        best = folder.best(eco)
        assert best is valid


class TestPlanLibrary:
    def test_folder_routing(self):
        lib = PlanLibrary()
        assert lib.folder_for(DEPARTMENT_STORE) is lib.store
        assert lib.folder_for(10) is lib.store  # Restaurant
        assert lib.folder_for(FACTORY) is lib.factory
        assert lib.folder_for(4) is lib.factory  # Farm

    def test_round_trip_capture_and_apply(self):
        """Capture a bread factory plan, store in library, apply to a new firm."""
        sim, town = bread_town(1)
        chain = build_bread_chain(sim, town)
        eco = sim.economy

        lib = PlanLibrary()
        plan = capture(chain.bread_factory)
        folder = lib.folder_for(plan.firm_type)
        folder.add(plan)
        assert len(lib.factory.plans) == 1

        corp = eco.add_corp("Builder")
        bread = eco.catalog["Bread"]
        corp.technology[bread.id] = bread.state.tech_level
        x, y = find_site(sim, town)
        new_firm = eco.build_firm(FACTORY, corp, x, y, town)

        retrieved = lib.factory.plans[0]
        apply_plan(retrieved, new_firm, eco)
        assert len(new_firm.jobs()) == 3
