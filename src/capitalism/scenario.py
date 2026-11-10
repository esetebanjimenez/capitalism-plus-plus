"""Scripted scenarios for tests and the smoke page (no firm AI until slice 9)."""

from __future__ import annotations

from dataclasses import dataclass

from .firms import Firm
from .jobs import CAT_FREIGHT, CAT_OVERHEAD, CAT_SALARIES, CAT_TRAINING, Job
from .links import Link
from .sim import Sim
from .town import Town

# Firm and job type ids (firm_types / job_types tables).
DEPARTMENT_STORE, FACTORY, FARM, SEAPORT = 1, 2, 4, 14
CROP, INVENTORY, MANUFACTURING, PURCHASING, SALES, IMPORT = 1, 5, 7, 10, 12, 16


def find_site(sim: Sim, town: Town, min_dist: int | None = None) -> tuple[int, int]:
    """First buildable tile outside the town footprint, scanning rings outward."""
    world = sim.world
    start = town.level + 5 if min_dist is None else min_dist
    for d in range(start, max(world.width, world.height)):
        for dy in range(-d, d + 1):
            for dx in range(-d, d + 1):
                if max(abs(dx), abs(dy)) != d:
                    continue
                if world.can_build(town.x + dx, town.y + dy):
                    return town.x + dx, town.y + dy
    raise RuntimeError("no free land")


@dataclass
class BreadChain:
    seaport: Firm
    flour_factory: Firm
    bread_factory: Firm
    store: Firm
    store_sales: Job
    store_link: Link
    import_link: Link
    wheat_buy: Job
    flour_buy: Job
    bread_buy: Job


def build_bread_chain(sim: Sim, town: Town) -> BreadChain:
    """Seaport wheat → flour factory → bread factory → department store in `town`.

    Each factory is Purchasing (slot 0) – Manufacturing (1) – Sales (2), linked
    0–1 and 1–2; the store is Purchasing (0) – Sales (1).
    """
    eco = sim.economy
    cat = eco.catalog
    wheat, flour, bread = cat["Wheat"], cat["Flour"], cat["Bread"]
    corp = eco.corps[0] if eco.corps else eco.add_corp("Test Corp")
    # Preserve the 4a baseline: its scripted wheat chain used catalog tech as
    # provisional skill. New 4b firms instead start with no discovered technology.
    for product in (wheat, flour, bread):
        corp.technology[product.id] = product.state.tech_level

    def place(ftype: int, owner: object) -> Firm:
        # Each firm takes the next actually free tile; seed 1 gives (204..207, 148).
        x, y = find_site(sim, town)
        return eco.build_firm(ftype, owner, x, y, town)  # type: ignore[arg-type]

    port = place(SEAPORT, None)
    imp = port.add_job(0, IMPORT, wheat)

    def factory(inp: Job, out_product: object) -> tuple[Firm, Job, Job, Link]:
        f = place(FACTORY, corp)
        buy = f.add_job(0, PURCHASING, inp.product)
        f.add_job(1, MANUFACTURING, out_product)  # type: ignore[arg-type]
        sell = f.add_job(2, SALES, out_product)  # type: ignore[arg-type]
        f.link_slots(0, 1)
        f.link_slots(1, 2)
        return f, buy, sell, eco.link_b2b(inp, buy)

    flour_f, wheat_buy, flour_sales, import_link = factory(imp, flour)
    bread_f, flour_buy, bread_sales, _ = factory(flour_sales, bread)

    store = place(DEPARTMENT_STORE, corp)
    s_buy = store.add_job(0, PURCHASING, bread)
    s_sell = store.add_job(1, SALES, bread)
    store.link_slots(0, 1)
    eco.link_b2b(bread_sales, s_buy)
    link = eco.link_consumer(s_sell, town)
    return BreadChain(
        port, flour_f, bread_f, store, s_sell, link, import_link, wheat_buy, flour_buy, s_buy
    )


def chain_month_profit(chain: BreadChain, month0: int) -> dict[str, float]:
    """The chain's economic result for the month just closed (`month0`, 0 = Jan).

    Read right after that month's pass. Sales between the chain's own firms
    cancel out, so profit is consumers' money at the store minus what leaves
    the corporation: wheat bought from the (ownerless) seaport, wages,
    training, overhead and freight from the firms' closed-month ledgers.
    """
    firms = (chain.flour_factory, chain.bread_factory, chain.store)
    cost = {
        "wages": sum(f.ledger.last_month[CAT_SALARIES] for f in firms),
        "training": sum(f.ledger.last_month[CAT_TRAINING] for f in firms),
        "overhead": sum(f.ledger.last_month[CAT_OVERHEAD] for f in firms),
        "freight": sum(f.ledger.last_month[CAT_FREIGHT] for f in firms),
        "wheat": chain.import_link.money_month[month0],
    }
    revenue = chain.store_link.money_month[month0]
    return {"revenue": revenue, **cost, "profit": revenue - sum(cost.values())}


def bread_town(seed: int = 1, population: float = 640_000) -> tuple[Sim, Town]:
    """Simplified-mode sim whose first town is set to `population` (frozen indicators)."""
    sim = Sim(seed=seed, detailed_cities=False)
    town = sim.towns[0]
    town.population = population
    sim.economy.recompute_demand()
    return sim, town
