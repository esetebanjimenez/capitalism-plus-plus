"""Pyodide smoke: build the bread chain and advance a few days. Shared by the page and node."""

from capitalism import __version__
from capitalism.scenario import bread_town, build_bread_chain

sim, town = bread_town(1)
chain = build_bread_chain(sim, town)
sim.advance_days(10)
assert (sim.year, sim.month, sim.day) == (1990, 1, 11), (sim.year, sim.month, sim.day)
assert len(sim.economy.catalog) == 84
assert chain.store_link.quantity > 0
f"capitalism {__version__} ok: {town.name} day 10, hash {sim.state_hash()[:16]}"
