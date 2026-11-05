"""Scripted scenarios for tests and the smoke page (no firm AI until slice 9)."""

from __future__ import annotations

from dataclasses import dataclass

from .firms import Firm
from .jobs import Job
from .links import Link
from .sim import Sim
from .town import Town
from .world import TileCategory

# Firm and job type ids (firm_types / job_types tables).
DEPARTMENT_STORE, FACTORY, FARM, SEAPORT = 1, 2, 4, 14
CROP, INVENTORY, MANUFACTURING, PURCHASING, SALES, IMPORT = 1, 5, 7, 10, 12, 16

FREE_LAND = (TileCategory.GRASSLAND, TileCategory.FOREST_HILL)


def find_site(sim: Sim, town: Town, min_dist: int | None = None) -> tuple[int, int]:
    """First free land tile outside the town footprint, scanning rings outward."""
    world = sim.world
    start = town.level + 5 if min_dist is None else min_dist
    for d in range(start, max(world.width, world.height)):
        for dy in range(-d, d + 1):
            for dx in range(-d, d + 1):
                if max(abs(dx), abs(dy)) != d:
                    continue
                x, y = town.x + dx, town.y + dy
                inside = 0 <= x < world.width and 0 <= y < world.height
                if inside and world.tile_at(x, y).kind in FREE_LAND:
                    return x, y
    raise RuntimeError("no free land")


@dataclass
class BreadChain:
    seaport: Firm
    flour_factory: Firm
    bread_factory: Firm
    store: Firm
    store_sales: Job
    store_link: Link


def build_bread_chain(sim: Sim, town: Town) -> BreadChain:
    """Seaport wheat → flour factory → bread factory → department store in `town`.

    Each factory is Purchasing (slot 0) – Manufacturing (1) – Sales (2), linked
    0–1 and 1–2; the store is Purchasing (0) – Sales (1).
    """
    eco = sim.economy
    cat = eco.catalog
    wheat, flour, bread = cat["Wheat"], cat["Flour"], cat["Bread"]
    corp = eco.corps[0] if eco.corps else eco.add_corp("Test Corp")

    def place(ftype: int, owner: object) -> Firm:
        x, y = find_site(sim, town)
        return eco.build_firm(ftype, owner, x, y, town)  # type: ignore[arg-type]

    port = place(SEAPORT, None)
    imp = port.add_job(0, IMPORT, wheat)

    def factory(inp: Job, out_product: object) -> tuple[Firm, Job]:
        f = place(FACTORY, corp)
        buy = f.add_job(0, PURCHASING, inp.product)
        f.add_job(1, MANUFACTURING, out_product)  # type: ignore[arg-type]
        sell = f.add_job(2, SALES, out_product)  # type: ignore[arg-type]
        f.link_slots(0, 1)
        f.link_slots(1, 2)
        eco.link_b2b(inp, buy)
        return f, sell

    flour_f, flour_sales = factory(imp, flour)
    bread_f, bread_sales = factory(flour_sales, bread)

    store = place(DEPARTMENT_STORE, corp)
    s_buy = store.add_job(0, PURCHASING, bread)
    s_sell = store.add_job(1, SALES, bread)
    store.link_slots(0, 1)
    eco.link_b2b(bread_sales, s_buy)
    link = eco.link_consumer(s_sell, town)
    return BreadChain(port, flour_f, bread_f, store, s_sell, link)


def bread_town(seed: int = 1, population: float = 640_000) -> tuple[Sim, Town]:
    """Simplified-mode sim whose first town is set to `population` (frozen indicators)."""
    sim = Sim(seed=seed, detailed_cities=False)
    town = sim.towns[0]
    town.population = population
    sim.economy.recompute_demand()
    return sim, town
