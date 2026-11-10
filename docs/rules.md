# Capitalism++ rules tables

Generated from `src/capitalism/data/capitalism.db` by
`scripts/generate_rules_md.py`. Do not edit by hand — change the
database, then regenerate. Numbers marked **provisional** (or **p** in
the wide catalog tables) are ours, not the original game's.

## Research durations by tech-year bucket

| Bucket | Months | Reference |
|---|---|---|
| 0 | 0 | design.md slice 4b R&D duration table |
| 1 | 6 | design.md slice 4b R&D duration table |
| 2 | 12 | design.md slice 4b R&D duration table |
| 3 | 24 | design.md slice 4b R&D duration table |
| 4 | 36 | design.md slice 4b R&D duration table |
| 5 | 60 | design.md slice 4b R&D duration table |
| 6 | 120 | design.md slice 4b R&D duration table |

## Provisional livestock processing

| Livestock | Output | Output / input | Input ratio | Reference |
|---|---|---|---|---|
| 19 | 23 | 20 **provisional** | 1 | M1 provisional livestock yield and conversion; source yield missing |
| 20 | 24 | 1 **provisional** | 1 | M1 provisional livestock yield and conversion; source yield missing |
| 22 | 25 | 40 **provisional** | 1 | M1 provisional livestock yield and conversion; source yield missing |

## Rating efficiency and storage

| Rating | Efficiency % | Storage multiplier | Reference |
|---|---|---|---|
| 1 | 100 | 8 | docs/reference/gamelogic.md 558–585 — rating efficiency and storage |
| 2 | 130 | 10 | docs/reference/gamelogic.md 558–585 — rating efficiency and storage |
| 3 | 160 | 14 | docs/reference/gamelogic.md 558–585 — rating efficiency and storage |
| 4 | 200 | 16 | docs/reference/gamelogic.md 558–585 — rating efficiency and storage |
| 5 | 250 | 20 | docs/reference/gamelogic.md 558–585 — rating efficiency and storage |
| 6 | 300 | 24 | docs/reference/gamelogic.md 558–585 — rating efficiency and storage |
| 7 | 360 | 30 | docs/reference/gamelogic.md 558–585 — rating efficiency and storage |
| 8 | 430 | 35 | docs/reference/gamelogic.md 558–585 — rating efficiency and storage |
| 9 | 500 | 40 | docs/reference/gamelogic.md 558–585 — rating efficiency and storage |

The storage multiplier is registered but inactive: the native base capacity and
type factor are missing, so M1 preserves the normalized product×size×3-day capacity.

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

## 3 — Product catalog and demand

| Key | Value | Units | Reference |
|---|---|---|---|
| `capacity_value_per_day` | 60000 **provisional** | usd of goods / job / day at base price | design.md fill rule base_capacity = round(value / base_price); design.md says 20000, raised ×3 so the bread chain can meet town demand (PR #11) |
| `demand_per_people` | 1000 | people | Product catalog and demand — demand per 1000 population |
| `diffusion_corp_weight` | 8 | years / corporation | Product catalog and demand — technology diffusion |
| `diffusion_threshold` | 50 | years | Product catalog and demand — technology diffusion |
| `gnp_pc_ref` | 20000 **provisional** | $/capita (index 1.0) | design.md slice 3 call 2 — gnp_pc_index base |
| `nec_lux_base` | 0.6 **provisional** | multiplier | design.md slice 3 call 2 — demand |
| `nec_lux_hi` | 1.5 **provisional** | multiplier | design.md slice 3 call 2 — demand |
| `nec_lux_lo` | 0.3 **provisional** | multiplier | design.md slice 3 call 2 — demand |
| `nec_lux_luxury` | 0.05 **provisional** | multiplier / luxury point | design.md slice 3 call 2 — demand |
| `nec_lux_necessity` | 0.05 **provisional** | multiplier / necessity point | design.md slice 3 call 2 — demand |
| `obsolete_demand_factor` | 0.8 **provisional** | multiplier | design.md slice 3 call 2 — demand age |
| `score_jitter` | 4 | score points (±) | Product catalog and demand — initial score (±4) |
| `score_no_links` | 400 | score | Product catalog and demand; design.md slice 3 call 7 |
| `tech_jitter` | 4 | tech levels (±) | Product catalog and demand — technology (±4) |

## 4 — Firms

| Key | Value | Units | Reference |
|---|---|---|---|
| `link_bits` | 20 | links | design.md slice 4 call 1 — 3×3 neighbour grid |
| `media_staff` | 20 **provisional** | staff | design.md slice 4 call 5 — media payroll staff (4b) |
| `media_wage_mult` | 2 | multiplier | Firm daily cycle — media payroll |
| `size` | 1 **provisional** | size | design.md slice 4 — size 1 in M1 |
| `slots` | 9 | slots | Firm-to-job mapping — nine job slots |

## 4 — Jobs

| Key | Value | Units | Reference |
|---|---|---|---|
| `ad_budget_max` | 500000 | $ / month | Advertising — budget clamp |
| `ad_budget_min` | 50000 | $ / month | Advertising — budget clamp |
| `corp_training_budget_default` | 10 | training budget | decompiled training review (2026-11-06) |
| `crop_climate_slope` | -10 | yield / climate step | Crop Growing — yield |
| `crop_moisture_slope` | -10 | yield / moisture step | Crop Growing — yield |
| `crop_moisture_step` | 25 **provisional** | moisture points / step | design.md slice 4 — moisture distance in steps |
| `crop_soil_div` | 5 | divisor | Crop Growing — soil ÷ 5 |
| `crop_yield_base` | 20 | yield | Crop Growing — yield (× −10 + 20) |
| `extraction_rate` | 1 **provisional** | rate | design.md slice 4 call 7 — extraction |
| `freight_distance_value_divisor` | 100 | currency-distance divisor | decompiled FUN_000785f1 review (Esteban 2026-11-06) |
| `freight_floor_usd_per_unit` | 0.01 | USD per unit only if raw rate == 0 | decompiled FUN_000785f1 review (Esteban 2026-11-06) |
| `freight_multiplier` | 0.5 | multiplier | decompiled FUN_000785f1 review (Esteban 2026-11-06) |
| `import_quality` | 50 **provisional** | quality | design.md slice 4 call 7 — Seaport (Moderate) |
| `livestock_scalar` | 36500 | days | Livestock Raising — 36,500 |
| `mfg_skill_max` | 100 **provisional** | quality | design.md slice 4 — manufacturing skill = min(this, product tech level) until R&D lands |
| `purchase_every_days` | 5 | days | Purchasing — 5-day cycle |
| `purchase_order_mult` | 4 | multiplier | Purchasing — order size |
| `quality_base` | 30 | quality | Livestock Raising — quality target (rating − 1) × 5 + 30 (crop/extraction reuse it: our call) |
| `quality_per_rating` | 5 | quality / rating | Livestock Raising — quality target (rating − 1) × 5 + 30 (crop/extraction reuse it: our call) |
| `rating_max` | 9 | rating | Job daily cycle — rating 1..9 |
| `rating_min` | 1 | rating | Job daily cycle — rating 1..9 |
| `sales_mult_other` | 4 | multiplier | Sales — multiplier |
| `sales_mult_store` | 2 | multiplier | Sales — live-inventory multiplier |
| `train_weekday` | 2 | weekday | Job daily cycle — train on weekday 2 |
| `training_credit_budget_divisor` | 10 **provisional** | budget-value / divisor; budget10 neutral | docs/design.md slice 4 call 6 (PR22 d012404) — provisional neutral credit scaling |
| `training_credit_education` | 100 **provisional** | global fallback education; no native field recovered | docs/design.md slice 4 call 6 (PR22 d012404) — provisional neutral credit scaling |
| `training_credit_education_divisor` | 100 **provisional** | education / divisor; fallback100 neutral | docs/design.md slice 4 call 6 (PR22 d012404) — provisional neutral credit scaling |
| `training_expense_divisor` | 100 | USD divisor | decompiled training review (2026-11-06) |
| `wage_per_worker_month` | 2000 | usd / worker / month at labor cost 100 | Job daily cycle — post wages ((staff × 2000) / days-in-month × labor) / 100; design.md slice 4 call 5 |

## 5 — Product links and markets

| Key | Value | Units | Reference |
|---|---|---|---|
| `ad_brand_per_100k` | 1 **provisional** | brand points / $100k / month | design.md slice 5 call 8 |
| `brand_max` | 100 **provisional** | brand | design.md slice 5 call 8 |
| `brand_nudge` | 0.1 | brand points / sale | Product links — brand perception |
| `brand_start` | 0 **provisional** | brand | design.md slice 5 — new link brand |
| `oversupply_div` | 20 **provisional** | divisor | design.md slice 5 call 6 |
| `price_base` | 100 **provisional** | score | design.md slice 5 call 2 |
| `price_slope` | 50 **provisional** | score / price ratio | design.md slice 5 call 2 |
| `score_div` | 60 | divisor | Product links — score (/60) |
| `share_exponent` | 2 **provisional** | exponent | design.md slice 5 call 5 |
| `weight_max` | 100 | weight | Product links — weight clamp |
| `weight_nonfarm` | 50 | weight | Product links — weight (+50, non-farm per design.md call 4) |
| `weight_rate_mult` | 5 | weight / rate point | Product links — weight (× 5) |

## 4b — Research and projects

| Key | Value | Units | Reference |
|---|---|---|---|
| `days_per_project_month` | 30 **provisional** | days / month | design.md slice 4b project elapsed time |
| `manager_skill_divisor` | 2 **provisional** | divisor | design.md slice 4b manufacturing skill provisional |
| `max_technology` | 100 **provisional** | technology | design.md slice 4b completed sentinel |
| `tech_year_divisor` | 15 **provisional** | tech years / duration bucket | design.md slice 4b R&D duration formula |

## 4b — Software

| Key | Value | Units | Reference |
|---|---|---|---|
| `software_copy_cost_per_day` | 0 **provisional** | usd per copy-unit day | M1 no additional daily copy cost; wages already posted once daily |
| `software_copy_quality` | 50 **provisional** | quality | M1 provisional software initial quality |
| `software_gate_every_days` | 15 | days | gamelogic.md Software Production — gate check interval |
| `software_gate_max_age_days` | 151 | days | gamelogic.md Software Production — gate staleness threshold |
| `software_gate_no_revenue_months` | 5 | months | gamelogic.md Software Production — gate no-revenue window |
| `software_project_months` | 6 **provisional** | months | design.md slice 4b software one level project |

## 4b — Advertising and media

| Key | Value | Units | Reference |
|---|---|---|---|
| `ad_campaign_every_days` | 60 **provisional** | days | design.md slice 4b advertising campaign stagger |
| `ad_revenue_fraction` | 0.1 **provisional** | fraction of previous month revenue | design.md slice 4b provisional budget rate |
| `ad_tech_min_exclusive` | 14 **provisional** | tech level | design.md slice 4b no ads at tech <= 14 |
| `media_audience_adjust_rate` | 0.1 **provisional** | fraction / month | M1 provisional gradual audience adjustment |
| `media_audience_cap` | 100 **provisional** | audience | design.md slice 4b provisional audience |
| `media_audience_delta_divisor` | 200 | divisor | gamelogic.md Media firm economics — audience delta divisor |
| `media_audience_delta_offset` | 50 | subtracted from draw | gamelogic.md Media firm economics — audience delta offset |
| `media_audience_delta_range` | 101 | random draw range | gamelogic.md Media firm economics — audience delta range |
| `media_audience_min` | 10 **provisional** | audience | design.md slice 4b provisional audience |
| `media_audience_population_div` | 10000 **provisional** | people / audience point | design.md slice 4b provisional audience |
| `media_competition_steal_factor` | 0.5 | fraction | gamelogic.md Media firm economics — audience zero-sum steal |
| `media_government_max` | 39 **provisional** | audience | design.md slice 4b government audience |
| `media_high_audience_threshold` | 40 | audience | gamelogic.md Media firm economics — audience high threshold |
| `media_low_audience_threshold` | 15 | audience | gamelogic.md Media firm economics — audience low threshold |
| `media_market_cap` | 90 | audience | gamelogic.md Media firm economics — audience market soft-cap |
| `media_min_audience` | 5 | audience | gamelogic.md Advertising — media partner minimum audience |
| `media_min_revenue` | 10000 **provisional** | usd / month | design.md slice 4b media partner threshold |
| `media_reputation_boost_range` | 31 | random draw range | gamelogic.md Media firm economics — audience reputation boost range |
| `media_reputation_drift_offset` | 30 | subtracted from draw | gamelogic.md Media firm economics — audience reputation drift offset |
| `media_reputation_drift_range` | 61 | random draw range | gamelogic.md Media firm economics — audience reputation drift range |
| `media_reputation_max` | 100 | reputation | gamelogic.md Media firm economics — audience reputation ceiling |
| `media_reputation_min` | -100 | reputation | gamelogic.md Media firm economics — audience reputation floor |
| `media_revenue_audience_addend` | 2 | addend | gamelogic.md Media firm economics — organic revenue audience addend |
| `media_revenue_base_divisor` | 1000 | divisor | gamelogic.md Media firm economics — organic revenue base divisor |
| `media_revenue_floor` | 100 | usd / month | gamelogic.md Media firm economics — organic revenue floor |
| `media_revenue_seasonal_neutral` | 100 **provisional** | percentage | Provisional neutral seasonal factor |
| `media_revenue_town_divisor` | 20000 | divisor | gamelogic.md Media firm economics — organic revenue town divisor |

## 7 — Corporation financials

| Key | Value | Units | Reference |
|---|---|---|---|
| `interest_fall_chance` | 50 | 1-in-N per month | gamelogic.md Interest rates |
| `interest_rate_default` | 10 | percent | gamelogic.md Interest rates |
| `interest_rate_floor` | 1 | percent | gamelogic.md Interest rates |
| `interest_rate_step` | 0.5 | percentage points | gamelogic.md Interest rates |
| `interest_rise_chance` | 10 | 1-in-N per month | gamelogic.md Interest rates |
| `overdraft_spread` | 2 | percentage points | gamelogic.md Cash flow and daily finance |
| `weak_gnp_threshold` | 5 | gnp / 1000 | gamelogic.md Interest rates |

## 8 — Persons

| Key | Value | Units | Reference |
|---|---|---|---|
| `dormant_chance` | 0.5 | probability | gamelogic.md Competitor spawning |
| `dormant_year_threshold` | 10 | years | gamelogic.md Competitor spawning |
| `loyalty_base` | 25 | years | gamelogic.md Salary and retention |
| `max_competitors` | 12 | count | gamelogic.md Competitor spawning |
| `max_persons` | 15 | count | gamelogic.md Person system |
| `raise_penalty_max` | 60 | points | gamelogic.md Salary raise penalties |
| `raise_penalty_min` | 30 | points | gamelogic.md Salary raise penalties |
| `raise_wealth_ratio` | 1.1 | ratio | gamelogic.md January wealth comparison |
| `random_raise_base` | 150 | divisor | gamelogic.md Random salary trigger |
| `service_salary_factor` | 0.1 | per year | gamelogic.md Salary negotiation |
| `skill_level_step` | 20 | points per level | gamelogic.md Expertise skills |
| `skill_range` | 40 | points | gamelogic.md Expertise skills |
| `spawn_chance` | 0.333 | probability | gamelogic.md Competitor spawning |
| `spawn_first_day_gate` | 0.01 | probability | gamelogic.md Competitor spawning |
| `wealth_floor` | 1000000 | dollars | gamelogic.md Salary and retention |

## 9 — AI corporations

| Key | Value | Units | Reference |
|---|---|---|---|
| `ai_cash_reset` | 1000000000 | dollars | gamelogic.md Cash management |
| `bankruptcy_age_threshold` | 10 | years | gamelogic.md Bankruptcy check |
| `bankruptcy_value_threshold` | 100000 | dollars | gamelogic.md Bankruptcy check |
| `build_cooldown` | 30 | days | gamelogic.md Firm creation |
| `competitor_cap` | 10 | count | gamelogic.md NPC corporation spawning |
| `dormant_chance` | 0.5 | probability | gamelogic.md NPC corporation spawning |
| `dormant_year_threshold` | 10 | years | gamelogic.md NPC corporation spawning |
| `finance_interval` | 30 | days | gamelogic.md Decision schedule |
| `link_interval` | 15 | days | gamelogic.md Decision schedule |
| `max_competitors` | 12 | count | gamelogic.md NPC corporation spawning |
| `mode_transition_interval` | 200 | days | gamelogic.md Decision schedule |
| `random_build_chance` | 0.001 | probability | gamelogic.md Strategy parameter change |
| `spawn_chance` | 0.333 | probability | gamelogic.md NPC corporation spawning |
| `spawn_first_day_gate` | 0.01 | probability | gamelogic.md NPC corporation spawning |
| `starting_capital_low` | 3000000 | dollars | gamelogic.md NPC corporation spawning |
| `strategy_interval` | 15 | days | gamelogic.md Decision schedule |
| `survey_interval` | 30 | days | gamelogic.md Decision schedule |
| `template_cost_estimate` | 500000 | dollars | gamelogic.md Firm creation |
| `vertical_interval` | 60 | days | gamelogic.md Decision schedule |

## 10 — Stock market

| Key | Value | Units | Reference |
|---|---|---|---|
| `buyback_float_threshold` | 0.3 **provisional** | fraction | gamelogic.md AI stock trading |
| `buyback_fraction` | 0.1 **provisional** | fraction | gamelogic.md AI stock trading |
| `dilution_decay_rate` | 0.95 **provisional** | per-day | gamelogic.md Daily price movement |
| `dilution_issue_factor` | 0.5 **provisional** | multiplier | gamelogic.md Share issuance |
| `dividend_max_ratio` | 0.5 **provisional** | fraction | gamelogic.md Dividends |
| `dividend_min_payout` | 1000 **provisional** | dollars | gamelogic.md Dividends |
| `impact_factor` | 0.5 **provisional** | multiplier | gamelogic.md Price impact |
| `initial_price_per_share` | 10 **provisional** | dollars | gamelogic.md Share creation and ownership |
| `invest_max_fraction` | 0.05 **provisional** | fraction | gamelogic.md AI stock trading |
| `issuance_momentum_factor` | 0.5 **provisional** | multiplier | gamelogic.md Share issuance |
| `momentum_clamp` | 0.05 **provisional** | fraction | gamelogic.md Daily price movement |
| `momentum_down_step` | 0.001 **provisional** | fraction | gamelogic.md Daily price movement |
| `momentum_up_step` | 0.001 **provisional** | fraction | gamelogic.md Daily price movement |
| `spike_chance` | 0.005 | probability | gamelogic.md Daily price movement (1/200) |
| `spike_magnitude` | 0.15 **provisional** | fraction | gamelogic.md Daily price movement |
| `volume_decay_rate` | 0.95 **provisional** | per-day | gamelogic.md Daily price movement |
| `volume_trade_factor` | 0.1 **provisional** | multiplier | gamelogic.md Price impact |

## 11 — News system

| Key | Value | Units | Reference |
|---|---|---|---|
| `buffer_capacity` | 2000 | count | gamelogic.md: circular buffer holding up to 2000 items |

## 11 — Random events

| Key | Value | Units | Reference |
|---|---|---|---|
| `blackout_gate` | 0.5 | probability | gamelogic.md: 50pct chance of actually triggering |
| `blackout_max_loss` | 29 | units | gamelogic.md: loses up to 29 units of inventory |
| `breakthrough_progress_hi` | 60 | points | gamelogic.md: adds 20 to 60 progress points |
| `breakthrough_progress_lo` | 20 | points | gamelogic.md: adds 20 to 60 progress points |
| `destruction_gate` | 0.5 | probability | gamelogic.md: 50pct chance of actually triggering |
| `disease_divisor_hi` | 5 | ratio | gamelogic.md: dividing capacity by 2 to 5 |
| `disease_divisor_lo` | 2 | ratio | gamelogic.md: dividing capacity by 2 to 5 |
| `downturn_gate` | 0.2 | probability | gamelogic.md: 1-in-5 chance of actually triggering |
| `downturn_loss_hi` | 0.25 | ratio | gamelogic.md: 4 to 25 pct asset reduction |
| `downturn_loss_lo` | 0.04 | ratio | gamelogic.md: 4 to 25 pct asset reduction |
| `event_type_count` | 6 | count | gamelogic.md: six event types chosen with equal probability |
| `freq_high_denominator` | 50 | 1/day | gamelogic.md: 1-in-50 chance each day |
| `freq_low_denominator` | 200 | 1/day | gamelogic.md: 1-in-200 chance each day |
| `freq_medium_denominator` | 100 | 1/day | gamelogic.md: 1-in-100 chance each day |

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

| Climate | Label | Drift | Swing (±) | Units |
|---|---|---|---|---|
| 4 | Boom | -0.15 **provisional** | 0.3 | percentage points / month |
| 3 | Prosperous | -0.1 **provisional** | 0.2 | percentage points / month |
| 2 | Normal | 0 **provisional** | 0.1 | percentage points / month |
| 1 | Recession | 0.1 **provisional** | 0.2 | percentage points / month |
| 0 | Panic | 0.15 **provisional** | 0.3 | percentage points / month |

Drift: design.md slice 2 — unemployment drift. Swing: Towns and cities — unemployment random swing.

## Product classes

| Id | Code | Name | Durable | Quality decay base | Group | Reference |
|---|---|---|---|---|---|---|
| 1 | RAW | Raw Material | no | 0.98 **p** | 8 | Product catalog and demand — product classes |
| 2 | PLANT | Plant | no | 0.98 **p** | 2 | Product catalog and demand — product classes |
| 3 | PSEMI | Plant Products | no | 0.98 **p** | 8 | Product catalog and demand — product classes |
| 4 | LSTOCK | Livestock | no | 0.98 **p** | 4 | Product catalog and demand — product classes |
| 5 | LSEMI | Livestock Semi-products | no | 0.98 **p** | 3 | Product catalog and demand — product classes |
| 6 | SEMI | Semi-products | yes | 1 | 12 | Product catalog and demand — product classes |
| 7 | FOOD | Food | no | 0.98 **p** | 4 | Product catalog and demand — product classes |
| 8 | BEVERAGE | Beverage | no | 0.98 **p** | 4 | Product catalog and demand — product classes |
| 9 | LPRODUCT | Livestock Products | no | 0.98 **p** | 5 | Product catalog and demand — product classes |
| 10 | CHEMGOOD | Chemical Products | no | 0.98 **p** | 4 | Product catalog and demand — product classes |
| 11 | COSMETIC | Cosmetics | no | 0.98 **p** | 2 | Product catalog and demand — product classes |
| 12 | CIGAR | Cigarette | no | 0.98 **p** | 1 | Product catalog and demand — product classes |
| 13 | WEAR | Apparel, Footwear & Bag | yes | 1 | 7 | Product catalog and demand — product classes |
| 14 | FURN | Furniture | yes | 1 | 2 | Product catalog and demand — product classes |
| 15 | JEWELRY | Jewelry | yes | 1 | 1 | Product catalog and demand — product classes |
| 16 | WATCH | Watch | yes | 1 | 1 | Product catalog and demand — product classes |
| 17 | TOY | Toy | yes | 1 | 2 | Product catalog and demand — product classes |
| 18 | ELEAPP | Electronic Products | yes | 1 | 7 | Product catalog and demand — product classes |
| 19 | COMPUTER | Computer | yes | 1 | 5 | Product catalog and demand — product classes |
| 20 | AUTO | Automobile | yes | 1 | 2 | Product catalog and demand — product classes |

## Products — market

| Id | Name | Class | Kind | Unit | Price | Demand / 1000 / day | L | N | P% | Q% | B% | Import |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Aluminum | RAW | raw | lb | 1.3 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 2 | Chemical Minerals | RAW | raw | lb | 2 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 3 | Coal | RAW | raw | lb | 0.2 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 4 | Gold | RAW | raw | oz | 300 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 5 | Iron Ore | RAW | raw | lb | 0.3 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 6 | Oil | RAW | raw | barrel | 20 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 7 | Silica | RAW | raw | lb | 0.2 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 8 | Timber | RAW | raw | lb | 0.2 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 9 | Rubber Plant | PLANT | crop | lb | 0.3 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 10 | Sugar Cane | PLANT | crop | lb | 0.3 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 11 | Barley | PSEMI | crop | lb **p** | 0.1 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 12 | Cocoa | PSEMI | crop | lb **p** | 0.5 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 13 | Cotton | PSEMI | crop | lb **p** | 0.5 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 14 | Grapes | PSEMI | crop | lb **p** | 0.5 **p** | 7 | 1 **p** | 5 **p** | 45 | 45 | 10 | 1 **p** |
| 15 | Rubber | PSEMI | crop | lb **p** | 0.4 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 16 | Sugar | PSEMI | crop | lb **p** | 0.2 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 17 | Tobacco | PSEMI | crop | lb **p** | 1 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 18 | Wheat | PSEMI | crop | lb **p** | 0.1 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 19 | Cattle | LSTOCK | livestock | head **p** | 500 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 20 | Chicken | LSTOCK | livestock | head **p** | 5 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 21 | Pig | LSTOCK | livestock | head **p** | 150 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 22 | Sheep | LSTOCK | livestock | head **p** | 150 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** |
| 23 | Leather | LSEMI | semi | lb | 10 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 24 | Milk | LSEMI | semi | quart | 1 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 25 | Wool | LSEMI | semi | lb | 20 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 26 | Car Body | SEMI | semi | unit **p** | 5000 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 27 | CPU | SEMI | semi | unit **p** | 200 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 28 | Electronic Components | SEMI | semi | lb | 10 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 29 | Engine | SEMI | semi | unit **p** | 3000 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 30 | Flour | SEMI | semi | lb | 0.5 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 31 | Glass | SEMI | semi | lb | 1 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 32 | Paper | SEMI | semi | lb | 1 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 33 | Plastic | SEMI | semi | lb | 1 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 34 | Silicon | SEMI | semi | lb | 1 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 35 | Steel | SEMI | semi | lb | 1 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 36 | Textiles | SEMI | semi | lb | 10 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 37 | Wheel & Tire | SEMI | semi | unit **p** | 1000 | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 0 |
| 38 | Bread | FOOD | consumer | unit **p** | 1.5 | 10 | 1 | 7 | 35 | 35 | 30 | 0 |
| 39 | Chocolate Bar | FOOD | consumer | unit **p** | 1.5 | 8 | 1 | 6 | 35 | 35 | 30 | 0 |
| 40 | Cookies | FOOD | consumer | unit **p** | 4 | 3 | 1 | 5 | 35 | 35 | 30 | 0 |
| 41 | Ice Cream | FOOD | consumer | unit **p** | 1.5 | 10 | 1 | 5 | 35 | 35 | 30 | 0 |
| 42 | Beer | BEVERAGE | consumer | unit **p** | 2 | 10 | 1 | 5 | 30 | 30 | 40 | 0 |
| 43 | Bottled Milk | BEVERAGE | consumer | unit **p** | 2 | 10 | 1 | 5 | 35 | 35 | 30 | 0 |
| 44 | Cola | BEVERAGE | consumer | unit **p** | 1 | 30 | 1 | 5 | 30 | 20 | 50 | 0 |
| 45 | Wine | BEVERAGE | consumer | unit **p** | 20 | 1 | 1 | 3 | 20 | 30 | 50 | 0 |
| 46 | Eggs | LPRODUCT | consumer | unit **p** | 2 | 3.5 | 1 | 6 | 45 | 45 | 10 | 0 |
| 47 | Frozen Beef | LPRODUCT | consumer | unit **p** | 3 | 5 | 1 | 6 | 45 | 45 | 10 | 0 |
| 48 | Frozen Chicken | LPRODUCT | consumer | unit **p** | 3 | 5 | 1 | 6 | 45 | 45 | 10 | 0 |
| 49 | Frozen Pork | LPRODUCT | consumer | unit **p** | 3 | 3.5 | 1 | 6 | 45 | 45 | 10 | 0 |
| 50 | Frozen Lamb | LPRODUCT | consumer | unit **p** | 3 | 1 | 1 | 6 | 45 | 45 | 10 | 0 |
| 51 | Detergent | CHEMGOOD | consumer | unit **p** | 4 | 3 | 1 | 9 | 40 | 30 | 30 | 0 |
| 52 | Diaper | CHEMGOOD | consumer | unit **p** | 6 | 2 | 2 | 8 | 33 | 33 | 34 | 0 |
| 53 | Shampoo | CHEMGOOD | consumer | unit **p** | 4 | 6 | 1 | 8 | 30 | 30 | 40 | 0 |
| 54 | Toothpaste | CHEMGOOD | consumer | unit **p** | 3 | 6 | 1 | 9 | 25 | 25 | 50 | 0 |
| 55 | Eye Shadow | COSMETIC | consumer | unit **p** | 30 | 0.5 | 7 | 1 | 20 | 30 | 50 | 0 |
| 56 | Perfume | COSMETIC | consumer | unit **p** | 30 | 0.5 | 7 | 1 | 20 | 30 | 50 | 0 |
| 57 | Cigarettes | CIGAR | consumer | unit **p** | 3 | 7 | 5 | 5 | 25 | 15 | 60 | 0 |
| 58 | Leather Briefcase | WEAR | consumer | unit **p** | 200 | 0.04 | 7 | 4 | 30 | 35 | 35 | 0 |
| 59 | Leather Jacket | WEAR | consumer | unit **p** | 250 | 0.03 | 7 | 3 | 30 | 35 | 35 | 0 |
| 60 | Jeans | WEAR | consumer | unit **p** | 30 | 0.5 | 2 | 4 | 25 | 25 | 50 | 0 |
| 61 | Leather Shoes | WEAR | consumer | unit **p** | 50 | 0.25 | 2 | 4 | 30 | 30 | 40 | 0 |
| 62 | Socks | WEAR | consumer | unit **p** | 5 | 2 | 3 | 4 | 35 | 35 | 30 | 0 |
| 63 | Sweater | WEAR | consumer | unit **p** | 80 | 0.15 | 3 | 4 | 30 | 35 | 35 | 0 |
| 64 | Sport Shoes | WEAR | consumer | unit **p** | 50 | 0.3 | 3 | 4 | 25 | 25 | 50 | 0 |
| 65 | Bed | FURN | consumer | unit **p** | 350 | 0.05 | 3 | 5 | 35 | 40 | 25 | 0 |
| 66 | Sofa | FURN | consumer | unit **p** | 250 | 0.02 | 5 | 5 | 35 | 40 | 25 | 0 |
| 67 | Jewelry | JEWELRY | consumer | unit **p** | 600 | 0.05 | 9 | 1 | 45 | 45 | 10 | 0 |
| 68 | Watch | WATCH | consumer | unit **p** | 60 | 0.3 | 4 | 4 | 30 | 35 | 35 | 0 |
| 69 | Toy Train | TOY | consumer | unit **p** | 20 | 0.5 | 5 | 2 | 35 | 40 | 25 | 0 |
| 70 | Toy Bear | TOY | consumer | unit **p** | 20 | 0.5 | 5 | 2 | 35 | 40 | 25 | 0 |
| 71 | Air Conditioner | ELEAPP | consumer | unit **p** | 400 | 0.05 | 6 | 3 | 30 | 40 | 30 | 0 |
| 72 | Camera | ELEAPP | consumer | unit **p** | 150 | 0.1 | 5 | 3 | 30 | 40 | 30 | 0 |
| 73 | DVD Player | ELEAPP | consumer | unit **p** | 500 | 0.05 | 5 | 3 | 30 | 40 | 30 | 0 |
| 74 | Hi-fi | ELEAPP | consumer | unit **p** | 400 | 0.05 | 6 | 3 | 30 | 40 | 30 | 0 |
| 75 | Television | ELEAPP | consumer | unit **p** | 400 | 0.05 | 4 | 3 | 30 | 40 | 30 | 0 |
| 76 | Video Camera | ELEAPP | consumer | unit **p** | 800 | 0.025 | 8 | 1 | 30 | 40 | 30 | 0 |
| 77 | Video Recorder | ELEAPP | consumer | unit **p** | 400 | 0.05 | 6 | 3 | 30 | 40 | 30 | 0 |
| 78 | Desktop Computer | COMPUTER | consumer | unit **p** | 1500 | 0.05 | 7 | 2 | 35 | 35 | 30 | 1 |
| 79 | Internet-TV | COMPUTER | consumer | unit **p** | 600 | 0.06 | 5 | 4 | 35 | 35 | 30 | 0 |
| 80 | PDA | COMPUTER | consumer | unit **p** | 320 | 0.05 | 7 | 1 | 30 | 40 | 30 | 0 |
| 81 | VR Computer | COMPUTER | consumer | unit **p** | 1800 | 0.025 | 9 | 1 | 25 | 45 | 30 | 0 |
| 82 | Wrist Computer | COMPUTER | consumer | unit **p** | 900 | 0.03 | 9 | 1 | 25 | 45 | 30 | 0 |
| 83 | Car | AUTO | consumer | unit **p** | 20000 | 0.005 | 8 | 2 | 30 | 35 | 35 | 1 |
| 84 | Motorcycle | AUTO | consumer | unit **p** | 10000 | 0.002 | 7 | 2 | 30 | 35 | 35 | 1 |
| 85 | Software | ELEAPP | software | copy **p** | 100 **p** | 0.1 **p** | 0 **p** | 0 **p** | 30 **p** | 40 **p** | 30 **p** | 0 **p** |

Reference: Product catalog and demand — complete product catalog.

## Products — production

| Id | Code | Name | Base cost | Capacity / day | Tech importance | Base tech | Tech year (years) | Freight coefficient | SPENDING (freight $) | Plant month (0 = Jan) | Grow months | Climate | Moisture |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ALUMINUM **p** | Aluminum | 0.78 **p** | 46154 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 1.3 **p** | — | — | — | — |
| 2 | CHEMICAL **p** | Chemical Minerals | 1.2 **p** | 30000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 2 **p** | — | — | — | — |
| 3 | COAL **p** | Coal | 0.12 **p** | 300000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 0.2 **p** | — | — | — | — |
| 4 | GOLD **p** | Gold | 180 **p** | 200 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 300 **p** | — | — | — | — |
| 5 | IRONORE **p** | Iron Ore | 0.18 **p** | 200000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 0.3 **p** | — | — | — | — |
| 6 | OIL **p** | Oil | 12 **p** | 3000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 20 **p** | — | — | — | — |
| 7 | SILICA **p** | Silica | 0.12 **p** | 300000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 0.2 **p** | — | — | — | — |
| 8 | TIMBER **p** | Timber | 0.12 **p** | 300000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 0.2 **p** | — | — | — | — |
| 9 | RUBBERPL **p** | Rubber Plant | 0.18 **p** | 200000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 0.3 **p** | 3 **p** | 5 **p** | 2 **p** | 50 **p** |
| 10 | SUGARCAN **p** | Sugar Cane | 0.18 **p** | 200000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 0.3 **p** | 3 **p** | 5 **p** | 2 **p** | 50 **p** |
| 11 | BARLEY **p** | Barley | 0.06 **p** | 600000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 0.1 **p** | 3 **p** | 5 **p** | 2 **p** | 50 **p** |
| 12 | COCOA **p** | Cocoa | 0.3 **p** | 120000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 0.5 **p** | 3 **p** | 5 **p** | 2 **p** | 50 **p** |
| 13 | COTTON **p** | Cotton | 0.3 **p** | 120000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 0.5 **p** | 3 **p** | 5 **p** | 2 **p** | 50 **p** |
| 14 | GRAPES **p** | Grapes | 0.3 **p** | 120000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 0.5 **p** | 3 **p** | 5 **p** | 2 **p** | 50 **p** |
| 15 | RUBBER **p** | Rubber | 0.24 **p** | 150000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 0.4 **p** | 3 **p** | 5 **p** | 2 **p** | 50 **p** |
| 16 | SUGAR **p** | Sugar | 0.12 **p** | 300000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 0.2 **p** | 3 **p** | 5 **p** | 2 **p** | 50 **p** |
| 17 | TOBACCO **p** | Tobacco | 0.6 **p** | 60000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** | 3 **p** | 5 **p** | 2 **p** | 50 **p** |
| 18 | WHEAT **p** | Wheat | 0.06 **p** | 600000 **p** | 3 **p** | 0 **p** | 0 **p** | 70 | 0.3 | 3 **p** | 5 **p** | 2 **p** | 50 **p** |
| 19 | CATTLE **p** | Cattle | 300 **p** | 120 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 500 **p** | — | — | — | — |
| 20 | CHICKEN **p** | Chicken | 3 **p** | 12000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 5 **p** | — | — | — | — |
| 21 | PIG **p** | Pig | 90 **p** | 400 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 150 **p** | — | — | — | — |
| 22 | SHEEP **p** | Sheep | 90 **p** | 400 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 150 **p** | — | — | — | — |
| 23 | LEATHER **p** | Leather | 6 **p** | 6000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 10 **p** | — | — | — | — |
| 24 | MILK **p** | Milk | 0.6 **p** | 60000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 1 **p** | — | — | — | — |
| 25 | WOOL **p** | Wool | 12 **p** | 3000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 20 **p** | — | — | — | — |
| 26 | CARBODY **p** | Car Body | 3000 **p** | 12 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 5000 **p** | — | — | — | — |
| 27 | CPU **p** | CPU | 120 **p** | 300 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 200 **p** | — | — | — | — |
| 28 | ELECTRON **p** | Electronic Components | 6 **p** | 6000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 10 **p** | — | — | — | — |
| 29 | ENGINE **p** | Engine | 1800 **p** | 20 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 3000 **p** | — | — | — | — |
| 30 | FLOUR **p** | Flour | 0.3 **p** | 120000 **p** | 6 **p** | 20 **p** | 15 **p** | 70 | 0.5 | — | — | — | — |
| 31 | GLASS **p** | Glass | 0.6 **p** | 60000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 1 **p** | — | — | — | — |
| 32 | PAPER **p** | Paper | 0.6 **p** | 60000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 1 **p** | — | — | — | — |
| 33 | PLASTIC **p** | Plastic | 0.6 **p** | 60000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 1 **p** | — | — | — | — |
| 34 | SILICON **p** | Silicon | 0.6 **p** | 60000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 1 **p** | — | — | — | — |
| 35 | STEEL **p** | Steel | 0.6 **p** | 60000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 1 **p** | — | — | — | — |
| 36 | TEXTILES **p** | Textiles | 6 **p** | 6000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 10 **p** | — | — | — | — |
| 37 | WHEELTIR **p** | Wheel & Tire | 600 **p** | 60 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 1000 **p** | — | — | — | — |
| 38 | BREAD **p** | Bread | 0.9 **p** | 40000 **p** | 3 **p** | 0 **p** | 0 **p** | 50 | 1.5 | — | — | — | — |
| 39 | CHOCOLAT **p** | Chocolate Bar | 0.9 **p** | 40000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 1.5 **p** | — | — | — | — |
| 40 | COOKIES **p** | Cookies | 2.4 **p** | 15000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 4 **p** | — | — | — | — |
| 41 | ICECREAM **p** | Ice Cream | 0.9 **p** | 40000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 1.5 **p** | — | — | — | — |
| 42 | BEER **p** | Beer | 1.2 **p** | 30000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 2 **p** | — | — | — | — |
| 43 | BOTTLEDM **p** | Bottled Milk | 1.2 **p** | 30000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 2 **p** | — | — | — | — |
| 44 | COLA **p** | Cola | 0.6 **p** | 60000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 1 **p** | — | — | — | — |
| 45 | WINE **p** | Wine | 12 **p** | 3000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 20 **p** | — | — | — | — |
| 46 | EGGS **p** | Eggs | 1.2 **p** | 30000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 2 **p** | — | — | — | — |
| 47 | FROZENBE **p** | Frozen Beef | 1.8 **p** | 20000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 3 **p** | — | — | — | — |
| 48 | FROZENCH **p** | Frozen Chicken | 1.8 **p** | 20000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 3 **p** | — | — | — | — |
| 49 | FROZENPO **p** | Frozen Pork | 1.8 **p** | 20000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 3 **p** | — | — | — | — |
| 50 | FROZENLA **p** | Frozen Lamb | 1.8 **p** | 20000 **p** | 3 **p** | 0 **p** | 0 **p** | 0 **p** | 3 **p** | — | — | — | — |
| 51 | DETERGEN **p** | Detergent | 2.4 **p** | 15000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 4 **p** | — | — | — | — |
| 52 | DIAPER **p** | Diaper | 3.6 **p** | 10000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 6 **p** | — | — | — | — |
| 53 | SHAMPOO **p** | Shampoo | 2.4 **p** | 15000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 4 **p** | — | — | — | — |
| 54 | TOOTHPAS **p** | Toothpaste | 1.8 **p** | 20000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 3 **p** | — | — | — | — |
| 55 | EYESHADO **p** | Eye Shadow | 18 **p** | 2000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 30 **p** | — | — | — | — |
| 56 | PERFUME **p** | Perfume | 18 **p** | 2000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 30 **p** | — | — | — | — |
| 57 | CIGARETT **p** | Cigarettes | 1.8 **p** | 20000 **p** | 3 **p** | 20 **p** | 0 **p** | 0 **p** | 3 **p** | — | — | — | — |
| 58 | LEATHERB **p** | Leather Briefcase | 120 **p** | 300 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 200 **p** | — | — | — | — |
| 59 | LEATHERJ **p** | Leather Jacket | 150 **p** | 240 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 250 **p** | — | — | — | — |
| 60 | JEANS **p** | Jeans | 18 **p** | 2000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 30 **p** | — | — | — | — |
| 61 | LEATHERS **p** | Leather Shoes | 30 **p** | 1200 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 50 **p** | — | — | — | — |
| 62 | SOCKS **p** | Socks | 3 **p** | 12000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 5 **p** | — | — | — | — |
| 63 | SWEATER **p** | Sweater | 48 **p** | 750 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 80 **p** | — | — | — | — |
| 64 | SPORTSHO **p** | Sport Shoes | 30 **p** | 1200 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 50 **p** | — | — | — | — |
| 65 | BED **p** | Bed | 210 **p** | 171 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 350 **p** | — | — | — | — |
| 66 | SOFA **p** | Sofa | 150 **p** | 240 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 250 **p** | — | — | — | — |
| 67 | JEWELRY **p** | Jewelry | 360 **p** | 100 **p** | 12 **p** | 20 **p** | 45 **p** | 0 **p** | 600 **p** | — | — | — | — |
| 68 | WATCH **p** | Watch | 36 **p** | 1000 **p** | 12 **p** | 20 **p** | 45 **p** | 0 **p** | 60 **p** | — | — | — | — |
| 69 | TOYTRAIN **p** | Toy Train | 12 **p** | 3000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 20 **p** | — | — | — | — |
| 70 | TOYBEAR **p** | Toy Bear | 12 **p** | 3000 **p** | 6 **p** | 20 **p** | 15 **p** | 0 **p** | 20 **p** | — | — | — | — |
| 71 | AIRCONDI **p** | Air Conditioner | 240 **p** | 150 **p** | 10 **p** | 20 **p** | 30 **p** | 0 **p** | 400 **p** | — | — | — | — |
| 72 | CAMERA **p** | Camera | 90 **p** | 400 **p** | 10 **p** | 20 **p** | 30 **p** | 0 **p** | 150 **p** | — | — | — | — |
| 73 | DVDPLAYE **p** | DVD Player | 300 **p** | 120 **p** | 10 **p** | 20 **p** | 30 **p** | 0 **p** | 500 **p** | — | — | — | — |
| 74 | HIFI **p** | Hi-fi | 240 **p** | 150 **p** | 10 **p** | 20 **p** | 30 **p** | 0 **p** | 400 **p** | — | — | — | — |
| 75 | TELEVISI **p** | Television | 240 **p** | 150 **p** | 10 **p** | 20 **p** | 30 **p** | 0 **p** | 400 **p** | — | — | — | — |
| 76 | VIDEOCAM **p** | Video Camera | 480 **p** | 75 **p** | 10 **p** | 20 **p** | 30 **p** | 0 **p** | 800 **p** | — | — | — | — |
| 77 | VIDEOREC **p** | Video Recorder | 240 **p** | 150 **p** | 10 **p** | 20 **p** | 30 **p** | 0 **p** | 400 **p** | — | — | — | — |
| 78 | DESKTOPC **p** | Desktop Computer | 900 **p** | 40 **p** | 10 **p** | 20 **p** | 30 **p** | 0 **p** | 1500 **p** | — | — | — | — |
| 79 | INTERNET **p** | Internet-TV | 360 **p** | 100 **p** | 10 **p** | 20 **p** | 30 **p** | 0 **p** | 600 **p** | — | — | — | — |
| 80 | PDA **p** | PDA | 192 **p** | 188 **p** | 10 **p** | 20 **p** | 30 **p** | 0 **p** | 320 **p** | — | — | — | — |
| 81 | VRCOMPUT **p** | VR Computer | 1080 **p** | 33 **p** | 10 **p** | 20 **p** | 30 **p** | 0 **p** | 1800 **p** | — | — | — | — |
| 82 | WRISTCOM **p** | Wrist Computer | 540 **p** | 67 **p** | 10 **p** | 20 **p** | 30 **p** | 0 **p** | 900 **p** | — | — | — | — |
| 83 | CAR **p** | Car | 12000 **p** | 3 **p** | 15 | 20 **p** | 60 **p** | 0 **p** | 20000 **p** | — | — | — | — |
| 84 | MOTORCYC **p** | Motorcycle | 6000 **p** | 6 **p** | 15 | 20 **p** | 60 **p** | 0 **p** | 10000 **p** | — | — | — | — |
| 85 | SOFTWARE | Software | 5 **p** | 1000 **p** | 0 **p** | 0 **p** | 0 **p** | 0 **p** | 100 **p** | — | — | — | — |

## Recipes

| Product | Output / cycle | Speed | Inputs (qty / cycle @ quality weight) | Skill |
|---|---|---|---|---|
| Car Body | 1 | 100% | Glass × 30 @ 15%; Plastic × 30 @ 15%; Steel × 600 @ 20% | 50% |
| CPU | 100 | 100% | Silicon × 1 @ 5% | 95% |
| Electronic Components | 3 | 400% | Chemical Minerals × 1 @ 10%; Silicon × 1 @ 10%; Steel × 1 @ 10% | 70% |
| Engine | 1 | 200% | Steel × 100 @ 20% | 80% |
| Flour | 1 | 100% | Wheat × 1 @ 70% | 30% |
| Glass | 1 | 100% | Silica × 1 @ 40% | 60% |
| Paper | 1 | 100% | Timber × 1 @ 50% | 50% |
| Plastic | 30 | 100% | Oil × 1 @ 35% | 65% |
| Silicon | 2 | 100% | Silica × 2 @ 40% | 60% |
| Steel | 2 | 100% | Coal × 1 @ 20%; Iron Ore × 1 @ 30% | 50% |
| Textiles | 1 | 100% | Cotton × 1 @ 50% | 50% |
| Wheel & Tire | 1 | 200% | Rubber × 20 @ 25%; Steel × 20 @ 25% | 50% |
| Bread | 10 | 100% | Flour × 9 @ 40% | 60% |
| Chocolate Bar | 10 | 100% | Cocoa × 1 @ 30%; Milk × 1 @ 20% | 50% |
| Cookies | 10 | 100% | Sugar × 1 @ 30%; Flour × 9 @ 10% | 60% |
| Ice Cream | 30 | 100% | Sugar × 1 @ 10%; Milk × 2 @ 30% | 60% |
| Beer | 17 | 100% | Aluminum × 1 @ 5%; Barley × 5 @ 40% | 55% |
| Bottled Milk | 8 | 100% | Milk × 2 @ 65%; Glass × 1 @ 5% | 30% |
| Cola | 17 | 100% | Aluminum × 1 @ 10%; Sugar × 5 @ 10% | 80% |
| Wine | 6 | 100% | Grapes × 5 @ 50%; Glass × 1 @ 5% | 45% |
| Detergent | 10 | 100% | Chemical Minerals × 3 @ 25%; Plastic × 1 @ 5% | 70% |
| Diaper | 6 | 100% | Cotton × 1 @ 15%; Paper × 1 @ 15% | 70% |
| Shampoo | 15 | 100% | Chemical Minerals × 3 @ 25%; Plastic × 1 @ 5% | 70% |
| Toothpaste | 20 | 100% | Chemical Minerals × 3 @ 25%; Plastic × 1 @ 5% | 70% |
| Eye Shadow | 10 | 100% | Chemical Minerals × 1 @ 25%; Plastic × 1 @ 5% | 70% |
| Perfume | 10 | 100% | Chemical Minerals × 1 @ 25%; Glass × 1 @ 5% | 70% |
| Cigarettes | 50 | 100% | Tobacco × 1 @ 40%; Paper × 1 @ 10% | 50% |
| Leather Briefcase | 6 | 100% | Leather × 5 @ 45%; Textiles × 1 @ 5% | 50% |
| Leather Jacket | 6 | 100% | Leather × 5 @ 45%; Textiles × 1 @ 5% | 50% |
| Jeans | 2 | 100% | Textiles × 1 @ 50% | 50% |
| Leather Shoes | 6 | 100% | Rubber × 1 @ 5%; Leather × 2 @ 45% | 50% |
| Socks | 20 | 100% | Wool × 1 @ 60% | 40% |
| Sweater | 2 | 100% | Wool × 1 @ 50% | 50% |
| Sport Shoes | 6 | 100% | Cotton × 1 @ 5%; Rubber × 1 @ 5%; Leather × 1 @ 30% | 60% |
| Bed | 1 | 100% | Timber × 100 @ 50% | 50% |
| Sofa | 1 | 100% | Timber × 30 @ 20%; Cotton × 5 @ 10%; Leather × 5 @ 30% | 40% |
| Jewelry | 1 | 100% | Gold × 1 @ 70% | 30% |
| Watch | 50 | 100% | Glass × 1 @ 10%; Steel × 1 @ 10% | 80% |
| Toy Train | 4 | 100% | Plastic × 1 @ 10%; Steel × 1 @ 10% | 80% |
| Toy Bear | 15 | 100% | Cotton × 2 @ 10%; Textiles × 1 @ 30% | 60% |
| Air Conditioner | 1 | 100% | Electronic Components × 1 @ 20%; Plastic × 3 @ 5%; Steel × 6 @ 5% | 70% |
| Camera | 6 | 100% | Electronic Components × 1 @ 20%; Glass × 1 @ 5%; Plastic × 1 @ 5% | 70% |
| DVD Player | 2 | 100% | CPU × 2 @ 30%; Electronic Components × 1 @ 15%; Plastic × 1 @ 5% | 50% |
| Hi-fi | 1 | 100% | Electronic Components × 2 @ 20%; Plastic × 3 @ 5%; Steel × 3 @ 5% | 70% |
| Television | 1 | 100% | Electronic Components × 3 @ 20%; Glass × 2 @ 5%; Plastic × 2 @ 5% | 70% |
| Video Camera | 6 | 100% | Electronic Components × 1 @ 20%; Glass × 1 @ 5%; Plastic × 1 @ 5% | 70% |
| Video Recorder | 1 | 100% | Electronic Components × 1 @ 20%; Plastic × 1 @ 5%; Steel × 1 @ 5% | 70% |
| Desktop Computer | 1 | 200% | CPU × 1 @ 40%; Electronic Components × 1 @ 15%; Steel × 1 @ 5% | 40% |
| Internet-TV | 1 | 100% | CPU × 1 @ 35%; Glass × 2 @ 5%; Plastic × 2 @ 5% | 55% |
| PDA | 5 | 100% | CPU × 5 @ 20%; Electronic Components × 1 @ 20%; Plastic × 2 @ 0% | 60% |
| VR Computer | 2 | 100% | CPU × 1 @ 30%; Glass × 2 @ 10% | 60% |
| Wrist Computer | 2 | 100% | CPU × 2 @ 40%; Electronic Components × 2 @ 15%; Plastic × 1 @ 5% | 40% |
| Car | 1 | 300% | Car Body × 1 @ 30%; Engine × 1 @ 30%; Wheel & Tire × 4 @ 10% | 30% |
| Motorcycle | 1 | 200% | Engine × 1 @ 30%; Steel × 10 @ 10%; Wheel & Tire × 2 @ 10% | 50% |

Reference: docs/recipes.md — 1STD.SET METHOD. Speed is a throughput multiplier (200% = twice the units per work cycle); skill is the share of output quality from manufacturing skill (100 − Σ input weights).

## R&D prerequisites

| Product | Requires first | Reference |
|---|---|---|
| DVD Player | Desktop Computer | docs/recipes.md — R&D prerequisites (ITEMPAE) |
| Video Camera | Camera | docs/recipes.md — R&D prerequisites (ITEMPAE) |
| Video Camera | Television | docs/recipes.md — R&D prerequisites (ITEMPAE) |
| Video Recorder | Television | docs/recipes.md — R&D prerequisites (ITEMPAE) |
| Desktop Computer | Television | docs/recipes.md — R&D prerequisites (ITEMPAE) |
| Internet-TV | Desktop Computer | docs/recipes.md — R&D prerequisites (ITEMPAE) |
| PDA | Desktop Computer | docs/recipes.md — R&D prerequisites (ITEMPAE) |
| VR Computer | Desktop Computer | docs/recipes.md — R&D prerequisites (ITEMPAE) |
| Wrist Computer | Desktop Computer | docs/recipes.md — R&D prerequisites (ITEMPAE) |

## Firm types

| Id | Name | Setup cost | Overhead / month | Max slots | Live inventory | Government | Units | Reference |
|---|---|---|---|---|---|---|---|---|
| 1 | Department Store | 1000000 | 100000 | 9 | yes | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 2 | Factory | 1500000 | 100000 | 9 | no | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 3 | R&D Center | 1500000 | 100000 | 9 | no | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 4 | Farm | 1000000 | 100000 | 9 | no | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 5 | Logging Camp | 1500000 | 100000 | 9 | no | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 6 | Mine | 5000000 | 300000 | 9 | no | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 7 | Oil Well | 5000000 | 300000 | 9 | no | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 8 | Software Developer | 100000 | 10000 | 9 | no | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 9 | Software Publisher | 1000000 | 100000 | 9 | no | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 10 | Restaurant | 2000000 | 100000 | 9 **p** | yes | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 11 | Television Station | 20000000 | 350000 | 0 | no | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 12 | Radio Station | 10000000 | 200000 | 0 | no | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 13 | Newspaper Publisher | 10000000 | 200000 | 0 | no | no **p** | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |
| 14 | Seaport | 0 | 0 | 0 **p** | no | no | usd (setup); usd_per_month (overhead) | Firm types; Firm-to-job mapping (live inventory: Sales) |

## Job types

| Id | Name | Staff | Setup cost | Training factor | Capacity mult | Units | Reference |
|---|---|---|---|---|---|---|---|
| 1 | Crop Growing | 16 | 100000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 2 | Livestock Raising | 16 | 100000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 3 | Livestock Processing | 16 | 100000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 4 | Logging | 24 | 100000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 5 | Inventory | 1 | 50000 | 10 **p** | 3 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 6 | Private Labelling | 6 | 100000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 7 | Manufacturing | 24 | 300000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 8 | Mining | 24 | 1000000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 9 | Oil Extraction | 24 | 1000000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 10 | Purchasing | 4 | 50000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 11 | Research & Development | 12 | 500000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 12 | Sales | 8 | 100000 | 10 **p** | 3 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 13 | Software Development | 8 | 50000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 14 | Software Production | 4 | 100000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 15 | Advertising | 1 | 5000 | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | Job types; cap_mult design.md slice 4 call 4 |
| 16 | Import | 0 **p** | 0 **p** | 10 **p** | 1 **p** | staff; usd (setup); daily-credit input (role unresolved); × base_capacity | design.md slice 4 — Seaport ImportJob |

## Jobs allowed per firm type

| Firm type | Job type | Reference |
|---|---|---|
| Department Store | Inventory | Firm-to-job mapping |
| Department Store | Private Labelling | Firm-to-job mapping |
| Department Store | Purchasing | Firm-to-job mapping |
| Department Store | Sales | Firm-to-job mapping |
| Department Store | Advertising | Firm-to-job mapping |
| Factory | Inventory | Firm-to-job mapping |
| Factory | Private Labelling | Firm-to-job mapping |
| Factory | Manufacturing | Firm-to-job mapping |
| Factory | Purchasing | Firm-to-job mapping |
| Factory | Sales | Firm-to-job mapping |
| Factory | Advertising | Firm-to-job mapping |
| R&D Center | Research & Development | Firm-to-job mapping |
| Farm | Crop Growing | Firm-to-job mapping |
| Farm | Livestock Raising | Firm-to-job mapping |
| Farm | Livestock Processing | Firm-to-job mapping |
| Farm | Inventory | Firm-to-job mapping |
| Farm | Sales | Firm-to-job mapping |
| Farm | Advertising | Firm-to-job mapping |
| Logging Camp | Logging | Firm-to-job mapping |
| Logging Camp | Inventory | Firm-to-job mapping |
| Logging Camp | Sales | Firm-to-job mapping |
| Mine | Inventory | Firm-to-job mapping |
| Mine | Mining | Firm-to-job mapping |
| Mine | Sales | Firm-to-job mapping |
| Oil Well | Inventory | Firm-to-job mapping |
| Oil Well | Oil Extraction | Firm-to-job mapping |
| Oil Well | Sales | Firm-to-job mapping |
| Software Developer | Software Development | Firm-to-job mapping |
| Software Publisher | Sales | Firm-to-job mapping |
| Software Publisher | Software Production | Firm-to-job mapping |
| Software Publisher | Advertising | Firm-to-job mapping |
| Restaurant | Purchasing **provisional** | Firm-to-job mapping — Restaurant as Department Store variant; Seaport ImportJob (design.md) |
| Restaurant | Sales **provisional** | Firm-to-job mapping — Restaurant as Department Store variant; Seaport ImportJob (design.md) |
| Seaport | Import **provisional** | Firm-to-job mapping — Restaurant as Department Store variant; Seaport ImportJob (design.md) |
