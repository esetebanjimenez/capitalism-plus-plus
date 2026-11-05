"""City names with tiers. Stand-in for the original name database (gamelogic.md)."""

from __future__ import annotations

# (name, tier) — tiers drive starting GNP and population.
CITY_NAMES: list[tuple[str, int]] = [
    ("Newhaven", 3),
    ("Portsmouth", 3),
    ("Metropole", 3),
    ("Riverside", 2),
    ("Oakridge", 2),
    ("Fairview", 2),
    ("Milltown", 2),
    ("Cedar Falls", 1),
    ("Ironwood", 1),
    ("Bayshore", 1),
    ("Hillcrest", 1),
    ("Dustfield", 0),
    ("Redrock", 0),
    ("Pine Hollow", 0),
    ("Southpoint", 2),
    ("Westgate", 3),
    ("Eastbrook", 1),
    ("Northfield", 0),
    ("Silverlake", 2),
    ("Goldcrest", 3),
    ("Maplewood", 1),
    ("Stonebridge", 2),
    ("Harborview", 3),
    ("Greenfield", 1),
]
