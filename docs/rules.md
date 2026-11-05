# Capitalism++ rules tables

Generated from `src/capitalism/data/capitalism.db` by
`scripts/generate_rules_md.py`. Do not edit by hand — change the
database, then regenerate. Numbers marked **provisional** are ours,
not the original game's.

## 1 — Clock and passes

| Key | Value | Units | Reference |
|---|---|---|---|
| `gnp_index_floor` | 0.5 **provisional** | index | Day, month, and year — GNP index (design.md provisional) |
| `gnp_index_high_growth` | 0.06 **provisional** | fraction / year | Day, month, and year — GNP index (design.md provisional) |
| `gnp_index_low_growth` | 0 **provisional** | fraction / year | Day, month, and year — GNP index (design.md provisional) |
| `gnp_index_step` | 0.01 **provisional** | index points | Day, month, and year — GNP index (design.md provisional) |
| `gnp_index_step_chance` | 0.1 **provisional** | probability / month | Day, month, and year — GNP index (design.md provisional) |
| `stagger_mod` | 30 | days | Day, month, and year — stagger (design.md call) |
| `start_year` | 1990 | year | Starting a new game |

## 2 — World data (map, terrain, towns)

| Key | Value | Units | Reference |
|---|---|---|---|
| `city_border` | 5 | tiles | Towns and cities — placement border |
| `city_min_dist` | 15 | tiles (Chebyshev) | Towns and cities — spacing |
| `default_cities` | 5 | cities | Towns and cities — default setup |
| `land_value_base_mult` | 50 **provisional** | $ per (level × $/capita) | Towns and cities — land value base (design.md provisional) |
| `land_value_bonus_cap` | 50000000 **provisional** | $ | Towns and cities — building bonus cap (design.md provisional) |
| `land_value_floor` | 500000 | $ | Towns and cities — land value floor |
| `land_value_small_town_factor` | 0.6 **provisional** | multiplier | Towns and cities — small-town factor (design.md provisional) |
| `land_value_small_town_level_max` | 2 **provisional** | level | Towns and cities — small-town factor (design.md provisional) |
| `map_height` | 198 | tiles | Map and terrain |
| `map_width` | 240 | tiles | Map and terrain |
| `max_cities` | 12 | cities | Towns and cities |
| `min_land_fraction` | 0.333333 | fraction of tiles | Map and terrain — land share (design.md golden) |
| `spawn_chance` | 0.1 | probability / month | Towns and cities — town spawning (design.md call) |
| `spawn_min_days` | 700 | days | Towns and cities — town spawning gate |

## 2 — Town indicators and land value

| Key | Value | Units | Reference |
|---|---|---|---|
| `climate_boom` | 0.08 | fraction / 12 months | Towns and cities — climate table |
| `climate_normal` | -0.01 | fraction / 12 months | Towns and cities — climate table |
| `climate_prosperous` | 0.04 | fraction / 12 months | Towns and cities — climate table |
| `climate_recession` | -0.06 | fraction / 12 months | Towns and cities — climate table |
| `env_chance` | 0.1 **provisional** | probability / month | Towns and cities — environmental factors (design.md provisional) |
| `env_hi` | 3 | index | Towns and cities — environmental factors |
| `env_lo` | -3 | index | Towns and cities — environmental factors |
| `gnp_divisor` | 200 **provisional** | $/capita per index point | Towns and cities — labor cost (design.md provisional) |
| `gnp_factor_hi` | 1.013 | multiplier / month | Towns and cities — per-capita GNP factor |
| `gnp_factor_lo` | 0.983 | multiplier / month | Towns and cities — per-capita GNP factor |
| `labor_quality_hi` | 100 | index | Towns and cities — labor quality clamp |
| `labor_quality_lo` | 1 | index | Towns and cities — labor quality clamp |
| `labor_step` | 0.2 **provisional** | fraction toward target / month | Towns and cities — labor/spend/quality (design.md provisional) |
| `large_pop` | 4000000 **provisional** | people | Towns and cities — population (design.md provisional) |
| `level_max` | 6 | level | Towns and cities — level table |
| `level_pop_per_sq` | 160000 | people | Towns and cities — level = (L−1)² × this |
| `pop_growth_hi` | 0.004 **provisional** | fraction / month | Towns and cities — population (design.md provisional) |
| `pop_growth_lo` | -0.002 **provisional** | fraction / month | Towns and cities — population (design.md provisional) |
| `pop_per_tier` | 300000 | people | Towns and cities — initial population |
| `pop_tier_noise` | 30000 | people | Towns and cities — initial population noise |
| `rolling_gnp_weight` | 0.05 **provisional** | weight | Towns and cities — population (design.md provisional) |
| `simple_labor_cost` | 100 | index | Towns and cities — simplified mode |
| `simple_labor_quality` | 100 | index | Towns and cities — simplified mode |
| `simple_level` | 3 | level | Towns and cities — simplified mode |
| `simple_per_capita_gnp` | 20000 | $/capita | Towns and cities — simplified mode |
| `simple_spending` | 100 | index | Towns and cities — simplified mode |
| `simple_unemployment` | 2 | percentage points | Towns and cities — simplified mode |
| `small_pop` | 50000 **provisional** | people | Towns and cities — population (design.md provisional) |
| `spend_floor` | 1 **provisional** | index | Towns and cities — consumer spending floor (design.md provisional) |
| `unemp_baseline` | 5 **provisional** | percentage points | Towns and cities — population (design.md provisional) |
| `unemp_hi` | 10 | percentage points | Towns and cities — unemployment clamp |
| `unemp_lo` | 2 | percentage points | Towns and cities — unemployment clamp |
| `unemp_weight` | 0.05 **provisional** | weight | Towns and cities — population (design.md provisional) |

## City name pool

| Name | Tier | Reference |
|---|---|---|
| Goldcrest | 3 **provisional** | Towns and cities — name pool (placeholder) |
| Harborview | 3 **provisional** | Towns and cities — name pool (placeholder) |
| Metropole | 3 **provisional** | Towns and cities — name pool (placeholder) |
| Newhaven | 3 **provisional** | Towns and cities — name pool (placeholder) |
| Portsmouth | 3 **provisional** | Towns and cities — name pool (placeholder) |
| Westgate | 3 **provisional** | Towns and cities — name pool (placeholder) |
| Fairview | 2 **provisional** | Towns and cities — name pool (placeholder) |
| Milltown | 2 **provisional** | Towns and cities — name pool (placeholder) |
| Oakridge | 2 **provisional** | Towns and cities — name pool (placeholder) |
| Riverside | 2 **provisional** | Towns and cities — name pool (placeholder) |
| Southpoint | 2 **provisional** | Towns and cities — name pool (placeholder) |
| Stonebridge | 2 **provisional** | Towns and cities — name pool (placeholder) |
| Bayshore | 1 **provisional** | Towns and cities — name pool (placeholder) |
| Cedar Falls | 1 **provisional** | Towns and cities — name pool (placeholder) |
| Eastbrook | 1 **provisional** | Towns and cities — name pool (placeholder) |
| Hillcrest | 1 **provisional** | Towns and cities — name pool (placeholder) |
| Ironwood | 1 **provisional** | Towns and cities — name pool (placeholder) |
| Maplewood | 1 **provisional** | Towns and cities — name pool (placeholder) |
| Ashvale | 0 **provisional** | Towns and cities — name pool (placeholder) |
| Dustfield | 0 **provisional** | Towns and cities — name pool (placeholder) |
| Greenfield | 0 **provisional** | Towns and cities — name pool (placeholder) |
| Northfield | 0 **provisional** | Towns and cities — name pool (placeholder) |
| Pine Hollow | 0 **provisional** | Towns and cities — name pool (placeholder) |
| Redrock | 0 **provisional** | Towns and cities — name pool (placeholder) |

## Per-capita GNP by tier

| Tier | Low | High | Units | Reference |
|---|---|---|---|---|
| 0 | 200 | 2000 | $/capita | Towns and cities — per-capita GNP by tier |
| 1 | 2200 | 7000 | $/capita | Towns and cities — per-capita GNP by tier |
| 2 | 7200 | 14000 | $/capita | Towns and cities — per-capita GNP by tier |
| 3 | 14200 | 20000 | $/capita | Towns and cities — per-capita GNP by tier |

## Consumer spending climate factors

| Climate | Label | Factor | Units | Reference |
|---|---|---|---|---|
| 4 | Boom | 1.1 **provisional** | multiplier | Towns and cities — consumer spending climate factor |
| 3 | Prosperous | 1.05 **provisional** | multiplier | Towns and cities — consumer spending climate factor |
| 2 | Normal | 1 **provisional** | multiplier | Towns and cities — consumer spending climate factor |
| 1 | Recession | 0.95 **provisional** | multiplier | Towns and cities — consumer spending climate factor |
| 0 | Panic | 0.9 **provisional** | multiplier | Towns and cities — consumer spending climate factor |

## Unemployment drift by climate

| Climate | Label | Drift | Swing | Units | Reference |
|---|---|---|---|---|---|
| 4 | Boom | -0.15 | 0.3 **provisional** | percentage points / month | Towns and cities — unemployment (design.md provisional) |
| 3 | Prosperous | -0.1 | 0.2 **provisional** | percentage points / month | Towns and cities — unemployment (design.md provisional) |
| 2 | Normal | 0 | 0.1 **provisional** | percentage points / month | Towns and cities — unemployment (design.md provisional) |
| 1 | Recession | 0.1 | 0.2 **provisional** | percentage points / month | Towns and cities — unemployment (design.md provisional) |
| 0 | Panic | 0.15 | 0.3 **provisional** | percentage points / month | Towns and cities — unemployment (design.md provisional) |
