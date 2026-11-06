"""Pyodide smoke: bread chain plus a completed software title. Shared by the page and node."""

from capitalism import __version__
from capitalism.scenario import bread_town, build_bread_chain, find_site

sim, town = bread_town(1)
chain = build_bread_chain(sim, town)
sim.advance_days(10)
assert (sim.year, sim.month, sim.day) == (1990, 1, 11), (sim.year, sim.month, sim.day)
assert len(sim.economy.catalog) == 85
assert chain.store_link.quantity > 0
chain_hash = sim.state_hash()[:16]

# Software (4b): developer project -> publisher copies -> consumer sales after completion only.
sw_sim, sw_town = bread_town(1)
eco = sw_sim.economy
software = eco.catalog["Software"]
corp = eco.add_corp("Software publisher")
dev = eco.build_firm(8, corp, *find_site(sw_sim, sw_town), sw_town).add_job(0, 13, software)
dev.configure()
publisher = eco.build_firm(9, corp, *find_site(sw_sim, sw_town), sw_town)
publisher.add_job(0, 14, software)
publisher.link_slots(0, 1)
sw_link = eco.link_consumer(publisher.add_job(1, 12, software), sw_town)
sw_sim.advance_days(179)
assert dev.completed_count == 0 and sum(sw_link.units_month) == 0
sw_sim.advance_days(2)
assert dev.completed_count == 1 and sw_link.units_month[5] > 0
sold = sum(sw_link.units_month)

f"capitalism {__version__} ok: {town.name} day 10, hash {chain_hash}, software sold {sold:.1f}"
