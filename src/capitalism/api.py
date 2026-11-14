"""M2 facade over the sim (docs/m2-facade-contract.md).

`Api.query(kind, args)` returns a JSON-ready snapshot and never changes state.
`Api.command(kind, args)` queues a command and returns `{"id": n}`; `Api.tick()`
applies queued commands in order, then advances the sim, and reports each result
as `{"id", "ok", "result"}` or `{"id", "ok": False, "error"}`. All commands act as
the player (corp 0). The facade adds no game rule: wrappers only set existing state.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable
from typing import Any

from . import stock as stk
from .firms import FIRM_CLASSES, Firm, MediaFirm, decode_links, edge_bit
from .goals import GoalConfig, check_goals, compute_difficulty_rating, compute_final_score
from .jobs import JOB_CLASSES, Job, Manufacturing, ProjectJob, Sales, product_freight_rate
from .links import Link
from .news import NewsCategory
from .plans import PlanLibrary, apply_plan, capture
from .sim import Sim
from .tables import FIRM_TYPES, JOB_TYPES
from .town import Town
from .world import TileCategory

PLAYER = 0
Json = dict[str, Any]
MAP_HISTORY = 64  # map_rev steps whose tile changes `map_objects` can still return


class CommandError(Exception):
    """A check the sim already makes failed; the message is shown to the player."""


def _num(v: float) -> float | None:
    """JSON has no inf or nan."""
    return v if math.isfinite(v) else None


def _ledger(led) -> Json:
    return {
        "cash": led.cash,
        "month": list(led.month),
        "last_month": list(led.last_month),
        "year": list(led.year),
    }


class Api:
    def __init__(self, sim: Sim) -> None:
        self.sim = sim
        self.plans = PlanLibrary()
        self._next_id = 1
        self._queue: list[tuple[int, str, Json]] = []
        if not sim.economy.corps:
            raise ValueError("the player corporation (corp 0) must exist")
        # Facade-side map revision (not sim state): a cheap signature of firms and town
        # levels is compared on each status/map read; when it moves, one pass over the
        # tiles records which ones changed.
        self.map_rev = 0
        self._map_sig = self._map_signature()
        self._map_tiles = self._tile_snapshot()
        self._map_changes: list[tuple[int, dict[int, tuple[int, int, int]]]] = []

    @classmethod
    def new_game(
        cls,
        player: str = "Player",
        setup: Json | None = None,
        goals: Json | None = None,
        **sim_kwargs: Any,
    ) -> Api:
        """A fresh sim with the player as corp 0.

        `setup` overrides `SetupOptions` fields (validated); `goals` sets `GoalConfig`
        targets in their own units (money goals in $ millions). Neither adds a rule.
        """
        sim = Sim(**sim_kwargs)
        if setup:
            fixed = {"seed", "start_year", "detailed_cities", "target_cities"} & set(setup)
            if fixed:
                raise ValueError(f"pass {sorted(fixed)} as Sim arguments, not setup")
            merged = {**sim.setup.model_dump(), **setup}
            sim.setup = type(sim.setup).model_validate(merged)
            sim.apply_setup()
        for name, value in (goals or {}).items():
            if name not in GoalConfig.__slots__:
                raise ValueError(f"unknown goal {name!r}")
            setattr(sim.goal_config, name, value)
        sim.economy.add_corp(player)
        return cls(sim)

    # --- shortcuts ---------------------------------------------------------

    @property
    def eco(self):
        return self.sim.economy

    @property
    def player(self):
        return self.eco.corps[PLAYER]

    def _firm(self, fid: int) -> Firm:
        firms = self.eco.firms
        if not 0 <= fid < len(firms) or firms[fid] is None:
            raise CommandError("That firm no longer exists.")
        return firms[fid]

    def _own_firm(self, fid: int) -> Firm:
        f = self._firm(fid)
        if f.owner is not self.player:
            raise CommandError("You don't own that firm.")
        return f

    def _job(self, fid: int, slot: int) -> Job:
        f = self._firm(fid)
        if not 0 <= slot < len(f.slots) or f.slots[slot] is None:
            raise CommandError("That slot is empty.")
        return f.slots[slot]

    def _town(self, tid: int) -> Town:
        for t in self.sim.towns:
            if t.id == tid:
                return t
        raise CommandError("That town no longer exists.")

    def _link(self, lid: int) -> Link:
        links = self.eco.market.links
        if not 0 <= lid < len(links) or links[lid] is None:
            raise CommandError("That link no longer exists.")
        return links[lid]

    def _stock(self, cid: int):
        st = self.eco.stocks[cid] if 0 <= cid < len(self.eco.stocks) else None
        if st is None:
            raise CommandError("That corporation has no stock.")
        return st

    def nearest_town(self, x: int, y: int) -> Town:
        return min(self.sim.towns, key=lambda t: ((t.x - x) ** 2 + (t.y - y) ** 2, t.id))

    # --- protocol ----------------------------------------------------------

    def query(self, kind: str, args: Json | None = None) -> Json:
        fn = QUERIES.get(kind)
        if fn is None:
            raise KeyError(f"unknown query {kind!r}")
        return fn(self, **(args or {}))

    def command(self, kind: str, args: Json | None = None) -> Json:
        if kind not in COMMANDS:
            raise KeyError(f"unknown command {kind!r}")
        cid = self._next_id
        self._next_id += 1
        self._queue.append((cid, kind, dict(args or {})))
        return {"id": cid}

    def apply_pending(self) -> list[Json]:
        out: list[Json] = []
        queue, self._queue = self._queue, []
        for cid, kind, args in queue:
            try:
                out.append({"id": cid, "ok": True, "result": COMMANDS[kind](self, **args)})
            except (CommandError, ValueError, NotImplementedError) as e:
                out.append({"id": cid, "ok": False, "error": str(e)})
            self.sync_map()  # a build and demolish in one batch still counts
        return out

    # --- map revision ------------------------------------------------------

    def _map_signature(self) -> tuple:
        firms = tuple((f.id, f.x, f.y) for f in self.eco.firms if f is not None)
        towns = tuple((t.id, t.level) for t in self.sim.towns)
        return firms, towns

    def _town_kinds(self) -> list[int]:
        """Native town tile kind per tile (rural 0x3000-0x3007, urban 0x3008-0x300c), else 0.
        A firm tile reports the town kind it stands on."""
        firms = self.eco.firms
        out = []
        for t in self.sim.world.tiles:
            if t.kind == TileCategory.FIRM:
                f = firms[t.ref] if 0 <= t.ref < len(firms) else None
                out.append(f.place_kind if f is not None and f.place_town >= 0 else 0)
            else:
                out.append(t.town_kind)
        return out

    def _tile_snapshot(self) -> list[tuple[int, int, int]]:
        return [
            (int(t.kind), t.ref, tk)
            for t, tk in zip(self.sim.world.tiles, self._town_kinds(), strict=True)
        ]

    def sync_map(self) -> int:
        """Bump `map_rev` if a firm was built or removed or a town changed level
        (which is when `spread_town` repaints tiles). Cheap when nothing moved."""
        sig = self._map_signature()
        if sig == self._map_sig:
            return self.map_rev
        self._map_sig = sig
        tiles = self._tile_snapshot()
        changed = {i: t for i, (t, old) in enumerate(zip(tiles, self._map_tiles)) if t != old}
        self._map_tiles = tiles
        self.map_rev += 1
        self._map_changes.append((self.map_rev, changed))
        del self._map_changes[:-MAP_HISTORY]
        return self.map_rev

    def tick(self, days: int = 1, read_since: int = -1) -> Json:
        """Apply queued commands, advance `days`, and return the per-tick status."""
        results = self.apply_pending()
        self.sim.advance_days(days)
        return {**self.status(read_since), "results": results}

    def status(self, read_since: int = -1) -> Json:
        unread = sum(1 for n in self.eco.news_log if n.important and n.day_serial > read_since)
        return {
            "day_serial": self.sim.calendar.day_serial,
            "year": self.sim.calendar.year,
            "month": self.sim.calendar.month,
            "day": self.sim.calendar.day,
            "cash": self.player.ledger.cash,
            "unread_important": unread,
            "map_rev": self.sync_map(),
        }

    # --- queries -----------------------------------------------------------

    def q_map(self) -> Json:
        w = self.sim.world
        return {
            "width": w.width,
            "height": w.height,
            "kind": [int(t.kind) for t in w.tiles],
            "ref": [t.ref for t in w.tiles],
            "town_kind": self._town_kinds(),
            "climate": [int(t.climate) for t in w.tiles],
            **self._map_objects(),
        }

    def q_map_objects(self, since: int = -1) -> Json:
        """Towns and firms plus the tiles changed since map_rev `since`, as
        `changes: [[index, kind, ref, town_kind], ...]`. When `since` is older than the kept
        history (or -1), `changes` is null and `kind` / `ref` hold the whole map."""
        objs = self._map_objects()
        rev = objs["map_rev"]
        oldest = self._map_changes[0][0] if self._map_changes else rev + 1
        if since == rev or (0 <= since < rev and since >= oldest - 1):
            merged: dict[int, tuple[int, int, int]] = {}
            for r, changed in self._map_changes:
                if r > since:
                    merged.update(changed)
            objs["changes"] = [[i, *v] for i, v in sorted(merged.items())]
        else:
            objs["changes"] = None
            tiles = self.sim.world.tiles
            objs["kind"] = [int(t.kind) for t in tiles]
            objs["ref"] = [t.ref for t in tiles]
            objs["town_kind"] = self._town_kinds()
        return objs

    def _map_objects(self) -> Json:
        return {
            "map_rev": self.sync_map(),
            "towns": [
                {
                    "id": t.id,
                    "name": t.name,
                    "x": t.x,
                    "y": t.y,
                    "level": t.level,
                }
                for t in self.sim.towns
            ],
            "firms": [
                {
                    "id": f.id,
                    "x": f.x,
                    "y": f.y,
                    "type_id": f.type_id,
                    "owner": None if f.owner is None else f.owner.id,
                }
                for f in self.eco.firms
                if f is not None
            ],
        }

    def q_overlay(self, layer: str) -> Json:
        w = self.sim.world
        if layer == "ownership":
            values = [
                {"firm": f.id, "owner": None if f.owner is None else f.owner.id}
                for f in self.eco.firms
                if f is not None
            ]
            owners = [v["owner"] for v in values if v["owner"] is not None]
            return {
                "layer": layer,
                "values": values,
                "min": min(owners, default=0),
                "max": max(owners, default=0),
            }
        if layer == "land_value":
            vals = [w.land_value(i % w.width, i // w.width) for i in range(len(w.tiles))]
        elif layer in ("soil", "rainfall", "climate"):
            vals = [int(getattr(t, layer)) for t in w.tiles]
        else:
            raise KeyError(f"unknown overlay {layer!r}")
        return {"layer": layer, "values": vals, "min": min(vals), "max": max(vals)}

    def q_tile(self, x: int, y: int) -> Json:
        w = self.sim.world
        if not (0 <= x < w.width and 0 <= y < w.height):
            raise KeyError("tile off the map")
        t = w.tile_at(x, y)
        return {
            "x": x,
            "y": y,
            "kind": int(t.kind),
            "town_kind": self._town_kinds()[y * w.width + x],
            "soil": t.soil,
            "rainfall": t.rainfall,
            "moisture": t.moisture,
            "climate": t.climate,
            "land_value": w.land_value(x, y),
            "can_build": w.can_build(x, y),
            "town": self.nearest_town(x, y).id,
        }

    def q_build_options(self, x: int, y: int) -> Json:
        cash = self.player.ledger.cash
        land = float(self.sim.world.land_value(x, y))
        rows = []
        for tid in sorted(FIRM_CLASSES):
            row = FIRM_TYPES[tid]
            if row.government or not row.player_buildable:
                continue
            cost = row.setup_cost + land  # B1/B3: setup + land; short cash refuses the build
            rows.append(
                {
                    "type_id": tid,
                    "name": row.name,
                    "setup_cost": row.setup_cost,
                    "land_value": land,
                    "build_cost": cost,
                    "overhead_month": row.overhead_month,
                    "affordable": cash >= cost,
                    "shortfall": max(0.0, cost - cash),
                }
            )
        return {"x": x, "y": y, "can_build": self.sim.world.can_build(x, y), "options": rows}

    def q_town(self, id: int) -> Json:
        t = self._town(id)
        return {
            "id": t.id,
            "name": t.name,
            "level": t.level,
            "population": t.population,
            "gnp": t.gnp,
            "per_capita_gnp": t.per_capita_gnp,
            "unemployment": t.unemployment,
            "labor_cost": t.labor_cost,
            "labor_quality": t.labor_quality,
            "consumer_spending": t.consumer_spending,
            "climate": int(t.climate),
            "pop_ring": list(t.pop_ring),
            "gnp_level_ring": list(t.gnp_level_ring),
            **self._town_history(t),
        }

    @staticmethod
    def _town_history(t: Town) -> Json:
        """Month-ordered series for the town card charts (#255, #280): oldest to newest, only
        recorded months, at most 12. The growth series are month-on-month percent changes,
        one shorter (the first month has no previous one); null when the earlier value is 0."""
        slots = t.history_slots()
        pop = [t.pop_ring[i] for i in slots]
        gnp = [t.gnp_month_ring[i] for i in slots]

        def growth(xs: list[float]) -> list[float | None]:
            return [(b / a - 1.0) * 100.0 if a else None for a, b in itertools.pairwise(xs)]

        return {
            "pop_history": pop,
            "gnp_level_history": gnp,
            "pop_growth_pct": growth(pop),
            "gnp_level_growth_pct": growth(gnp),
        }

    def q_town_market(self, id: int) -> Json:
        t = self._town(id)
        rows = []
        for (tid, _pid), tm in sorted(self.eco.market.towns.items()):
            if tid != t.id:
                continue
            total = sum(x.quantity for x in tm.links) or 0.0
            for x in tm.links:
                s = x.seller
                rows.append(
                    {
                        "link": x.id,
                        "product": tm.product.id,
                        "firm": s.firm.id,
                        "corp": None if s.firm.owner is None else s.firm.owner.id,
                        "price": x.price,
                        "quality": s.quality,
                        "brand": x.brand,
                        "share": x.quantity / total if total else 0.0,
                    }
                )
        return {"id": t.id, "links": rows}

    def _slot(self, j: Job | None) -> Json | None:
        if j is None:
            return None
        return {
            "job_type": j.type_id,
            "product": None if j.product is None else j.product.id,
            "rating": j.rating,
            "stock": j.stock,
            "capacity": j.capacity,
        }

    def q_firm(self, id: int) -> Json:
        f = self._firm(id)
        slots = [self._slot(j) for j in f.slots] + [None] * (9 - len(f.slots))
        out = {
            "id": f.id,
            "type_id": f.type_id,
            "name": f.row.name,
            "town": f.town.id,
            "owner": None if f.owner is None else f.owner.id,
            "x": f.x,
            "y": f.y,
            "land_value": f.land_value,
            "created_serial": f.created_serial,
            "max_slots": f.row.max_slots,
            "allowed_jobs": sorted(f.allowed_jobs),
            "slots": slots[:9],
            "edges": [list(e) for e in decode_links(f.links)],
            "ledger": _ledger(f.ledger),
        }
        if isinstance(f, MediaFirm):
            out["audience"] = getattr(f, "audience", 0)
            out["reputation"] = getattr(f, "reputation", 0)
            out["revenue_month"] = list(getattr(f, "revenue_month", []))
        return out

    def q_job(self, firm: int, slot: int) -> Json:
        j = self._job(firm, slot)
        out = {
            "firm": firm,
            "slot": slot,
            "job_type": j.type_id,
            "product": None if j.product is None else j.product.id,
            "rating": j.rating,
            "train_credits": j.train_credits,
            "train_threshold": max(1, j.rating) * 900.0,
            "train_progress": j.train_progress,
            "staff": j.staff,
            "stock": j.stock,
            "capacity": j.capacity,
            "quality": j.quality,
            "unit_cost": j.unit_cost,
            "price": j.price,
            "is_selling": isinstance(j, Sales),
        }
        if isinstance(j, Manufacturing) and j.product is not None:
            recipe = self.eco.catalog.recipe(j.product)
            ins = []
            for src in j.sources():
                ins.append({"product": src.product.id, "in_stock": src.stock})
            out["inputs"] = ins
            out["recipe"] = None if recipe is None else recipe.model_dump(mode="json")
        if isinstance(j, ProjectJob) and j.project is not None:
            p = j.project
            out["project"] = {
                "product": p.product.id,
                "elapsed_days": p.elapsed_days,
                "started": p.started,
                "completed": p.completed,
                "paused": p.paused,
            }
        return out

    def q_job_options(self, firm: int, slot: int) -> Json:
        f = self._firm(firm)
        products = [p.id for p in self.eco.catalog.products if p.state.available]
        rows = [
            {
                "job_type": jt,
                "name": JOB_TYPES[jt].name,
                "staff": JOB_TYPES[jt].staff,
                "setup_cost": JOB_TYPES[jt].setup_cost,
                # M1 has no job -> product table yet; the sim checks on add_job.
                "products": products,
            }
            for jt in sorted(f.allowed_jobs)
            if jt in JOB_CLASSES
        ]
        return {"firm": firm, "slot": slot, "options": rows}

    def _link_row(self, x: Link, side: str) -> Json:
        other = x.buyer if side == "selling" else x.seller
        row: Json = {
            "link": x.id,
            "product": None if x.seller.product is None else x.seller.product.id,
            "price": x.price,
            "quantity": x.quantity,
            "score": x.score,
            "brand": x.brand,
            "units_month": list(x.units_month),
            "money_month": list(x.money_month),
        }
        if x.consumer:
            row["consumers"] = other.town.id
        else:
            row["firm"] = other.firm.id
            row["slot"] = other.slot
            row["town"] = other.firm.town.id
        return row

    def q_firm_links(self, id: int) -> Json:
        f = self._firm(id)
        buying, selling = [], []
        for x in self.eco.market.live_links():
            if x.seller.firm is f:
                selling.append(self._link_row(x, "selling"))
            if not x.consumer and x.buyer.firm is f:
                buying.append(self._link_row(x, "buying"))
        return {"id": id, "buying": buying, "selling": selling}

    def q_suppliers(self, firm: int, slot: int) -> Json:
        buyer = self._job(firm, slot)
        if buyer.product is None:
            return {"firm": firm, "slot": slot, "suppliers": []}
        rows = []
        for f in self.eco.firms:
            if f is None or f is buyer.firm:
                continue
            for j in f.jobs():
                if isinstance(j, Sales) and j.product is buyer.product:
                    freight = product_freight_rate(j.product, f, buyer.firm)
                    rows.append(
                        {
                            "firm": f.id,
                            "slot": j.slot,
                            "corp": None if f.owner is None else f.owner.id,
                            "town": f.town.id,
                            "price": j.price,
                            "freight": freight,
                            "delivered_cost": j.price + freight,
                            "quality": j.quality,
                        }
                    )
        rows.sort(key=lambda r: (r["delivered_cost"], -r["quality"], r["firm"]))
        return {"firm": firm, "slot": slot, "suppliers": rows}

    def q_corp(self, id: int) -> Json:
        c = self.eco.corps[id]
        firms = self.eco.firms
        out = {
            "id": c.id,
            "name": c.name,
            "revenue": c.revenue,
            "operating_expenses": c.operating_expenses,
            "operating_profit": c.operating_profit,
            "other_profit": c.other_profit,
            "net_profit": c.net_profit,
            "ledger": _ledger(c.ledger),
            "by_firm": [
                {"firm": f.id, "ledger": _ledger(f.ledger)}
                for f in firms
                if f is not None and f.owner is c
            ],
            "stock_assets": c.stock_assets,
            "total_assets": c.total_assets(firms),
            "liabilities": c.liabilities,
            "net_worth": c.net_worth(firms),
            "credit_limit": c.credit_limit(firms),
            "interest_rate": self.eco.interest_rate,
            "month_history": {k: list(v) for k, v in c.month_history.items()},
            "year_history": {k: list(v) for k, v in c.year_history.items()},
        }
        if c.id == PLAYER:
            out |= {
                "technology": {str(k): v for k, v in c.technology.items()},
                "training_budget": c.training_budget,
                "brand_strategy": c.brand_strategy,
                "dividend_ratio": c.dividend_ratio,
                "dividend_auto": c.dividend_auto,
            }
        return out

    def _earnings(self, cid: int) -> float:
        return self.eco.corps[cid].net_profit

    def q_stocks(self) -> Json:
        rows = []
        for st in self.eco.stocks:
            if st is None:
                continue
            held = st.holdings_corps[PLAYER]
            rows.append(
                {
                    "corp": st.corp_id,
                    "name": self.eco.corps[st.corp_id].name,
                    "price": st.price,
                    "pe_ratio": _num(st.pe_ratio(self._earnings(st.corp_id))),
                    "owned_pct": 100.0 * held / st.total_shares,
                    "holding_value": held * st.price,
                }
            )
        return {"stocks": rows}

    def q_stock(self, corp: int) -> Json:
        st = self._stock(corp)
        holders = []
        for cid, n in enumerate(st.holdings_corps):
            if n:
                holders.append(
                    {"kind": "corp", "id": cid, "name": self.eco.corps[cid].name, "shares": n}
                )
        for pid, n in enumerate(st.holdings_persons):
            if n:
                p = self.eco.persons[pid] if pid < len(self.eco.persons) else None
                holders.append(
                    {"kind": "person", "id": pid, "name": getattr(p, "name", ""), "shares": n}
                )
        for h in holders:
            h["pct"] = 100.0 * h["shares"] / st.total_shares
            h["value"] = h["shares"] * st.price
        divs = st.dividend_history[-1:] or [0.0]
        return {
            "corp": corp,
            "price": st.price,
            "pe_ratio": _num(st.pe_ratio(self._earnings(corp))),
            "daily_prices": list(st.daily_prices),
            "monthly_prices": list(st.monthly_prices),
            "yearly_prices": list(st.yearly_prices),
            "total_shares": st.total_shares,
            "public_float": st.public_float,
            "dividend_yield": _num(st.dividend_yield(divs[0])),
            "shareholders": holders,
        }

    def q_trade_quote(self, corp: int, side: str, shares: int) -> Json:
        st = self._stock(corp)
        held = st.holdings_corps[PLAYER]
        if side == "buy":
            hi = st.public_float
        elif side == "sell":
            hi = held
        elif side == "issue":
            if corp != PLAYER:
                raise KeyError("only your own corporation can issue shares")
            hi = st.total_shares  # the UX caps it further; M1 has no issue limit yet
        else:
            raise KeyError(f"unknown side {side!r}")
        n = max(0, min(int(shares), hi))
        impact = stk.price_impact(n, st.total_shares, st.price)
        if side == "buy":
            amount, after = (st.price + impact / 2) * n, held + n
            total = st.total_shares
        elif side == "sell":
            amount, after = max(0.10, st.price - impact / 2) * n, held - n
            total = st.total_shares
        else:
            amount, after, total, impact = n * st.price, held, st.total_shares + n, 0.0
        return {
            "corp": corp,
            "side": side,
            "shares": n,
            "amount": amount,
            "price_impact": impact,
            "owned_pct_after": 100.0 * after / total,
            "min": 0,
            "max": hi,
        }

    def q_news(
        self, corp: int | None = None, category: int | None = None, since: int | None = None
    ) -> Json:
        rows = []
        for n in reversed(self.eco.news_log.items):
            if corp is not None and n.corp_id != corp:
                continue
            if category is not None and int(n.category) != category:
                continue
            if since is not None and n.day_serial <= since:
                continue
            rows.append(
                {
                    "day_serial": n.day_serial,
                    "category": int(n.category),
                    "category_name": NewsCategory(n.category).name.title(),
                    "corp_id": n.corp_id,
                    "news_type": int(n.news_type),
                    "details": {
                        k: v
                        for k, v in n.details.items()
                        if isinstance(v, (int, float, str, bool)) or v is None
                    },
                    "important": n.important,
                    "headline": n.news_type.name.replace("_", " ").capitalize(),
                }
            )
        return {"news": rows}

    def q_goals(self) -> Json:
        sim = self.sim
        cfg = sim.goal_checker.goals
        _, res = check_goals(cfg, self.eco, PLAYER)
        rows = [
            {"name": k, "target": t, "current": c, "met": m}
            for k, (t, c, m) in res.items()
            if t > 0
        ]
        years = sim.year - sim.start_year
        p = self.player
        score = compute_final_score(
            sim.setup,
            p.ledger.cash,
            p.net_worth(self.eco.firms),
            0,
            0,
            max(1, years),
            sim.goal_checker.result.name == "VICTORY",
        )
        return {
            "result": int(sim.goal_checker.result),
            "result_name": sim.goal_checker.result.name,
            "goals": rows,
            "years_played": years,
            "year_limit": sim.setup.year_limit,
            "seed": sim.seed,
            "difficulty": compute_difficulty_rating(sim.setup),
            "score": score,
        }

    def q_plans(self, firm_type: int) -> Json:
        folder = self.plans.folder_for(firm_type)
        return {
            "plans": [
                {
                    "index": i,
                    "description": p.description,
                    "slots": [
                        {"job_type": s.job_type, "product_id": s.product_id} for s in p.slots
                    ],
                    "connection_mask": p.connection_mask,
                }
                for i, p in enumerate(folder.plans)
            ]
        }

    # --- commands ----------------------------------------------------------

    def c_build_firm(self, firm_type: int, x: int, y: int) -> Json:
        if firm_type not in FIRM_CLASSES or FIRM_TYPES[firm_type].government:
            raise CommandError("You can't build that firm type.")
        if not FIRM_TYPES[firm_type].player_buildable:
            raise CommandError(
                f"You can't build a {FIRM_TYPES[firm_type].name}; the world places them."
            )
        if not self.sim.world.can_build(x, y):
            raise CommandError("You can't build on that tile.")
        f = self.eco.build_firm(firm_type, self.player, x, y, self.nearest_town(x, y))
        return {"firm": f.id}

    def _drop_links(self, pred: Callable[[Link], bool]) -> None:
        for x in list(self.eco.market.live_links()):
            if pred(x):
                self._remove_link(x)

    def _remove_link(self, x: Link) -> None:
        self.eco.market.links[x.id] = None
        if x.consumer:
            x.buyer.links.remove(x)
        elif getattr(x.buyer, "supply", None) is x:
            x.buyer.supply = None

    def c_demolish_firm(self, firm: int) -> None:
        f = self._own_firm(firm)
        self._drop_links(lambda x: x.seller.firm is f or (not x.consumer and x.buyer.firm is f))
        self.eco.demolish_firm(f)

    def c_add_job(self, firm: int, slot: int, job_type: int, product: int | None = None) -> None:
        f = self._own_firm(firm)
        if job_type not in f.allowed_jobs:
            raise CommandError(f"A {f.row.name} can't hold that job.")
        prod = None
        if product is not None:
            prod = self.eco.catalog.by_id.get(product)
            if prod is None:
                raise CommandError("Unknown product.")
        f.add_job(slot, job_type, prod)

    def c_remove_job(self, firm: int, slot: int) -> None:
        f = self._own_firm(firm)
        j = self._job(firm, slot)
        self._drop_links(lambda x: x.seller is j or x.buyer is j)
        for a, b in decode_links(f.links):
            if slot in (a, b):
                f.links &= ~(1 << edge_bit(a, b))
        f.slots[slot] = None

    def c_link_slots(self, firm: int, a: int, b: int) -> None:
        f = self._own_firm(firm)
        try:
            f.link_slots(a, b)
        except (KeyError, ValueError) as e:
            raise CommandError("Those slots aren't neighbours.") from e

    def c_unlink_slots(self, firm: int, a: int, b: int) -> None:
        f = self._own_firm(firm)
        try:
            f.links &= ~(1 << edge_bit(a, b))
        except (KeyError, ValueError) as e:
            raise CommandError("Those slots aren't neighbours.") from e

    def c_set_price(self, firm: int, slot: int, price: float) -> None:
        self._own_firm(firm)
        if price < 0:
            raise CommandError("Price can't be negative.")
        self._job(firm, slot).price = float(price)

    def c_link_b2b(
        self, seller_firm: int, seller_slot: int, buyer_firm: int, buyer_slot: int
    ) -> Json:
        self._own_firm(buyer_firm)
        s = self._job(seller_firm, seller_slot)
        b = self._job(buyer_firm, buyer_slot)
        if s.product is None or s.product is not b.product:
            raise CommandError("Those jobs handle different products.")
        return {"link": self.eco.link_b2b(s, b).id}

    def c_link_consumer(self, firm: int, slot: int) -> Json:
        self._own_firm(firm)
        j = self._job(firm, slot)
        if j.product is None or (j.firm.town.id, j.product.id) not in self.eco.market.towns:
            raise CommandError("Consumers here don't buy that product.")
        return {"link": self.eco.link_consumer(j).id}

    def c_remove_link(self, link: int) -> None:
        x = self._link(link)
        mine = x.seller.firm.owner is self.player or (
            not x.consumer and x.buyer.firm.owner is self.player
        )
        if not mine:
            raise CommandError("That link isn't yours.")
        self._remove_link(x)

    def c_borrow(self, amount: float) -> None:
        p = self.player
        if amount > p.credit_limit(self.eco.firms):
            raise CommandError("That's over your credit limit.")
        p.borrow(float(amount))

    def c_repay(self, amount: float) -> Json:
        p = self.player
        before = p.liabilities
        p.repay(float(amount))
        return {"repaid": before - p.liabilities}

    def c_buy_shares(self, corp: int, shares: int) -> Json:
        self._stock(corp)
        return {"cost": self.eco.buy_stock(self.player, corp, int(shares))}

    def c_sell_shares(self, corp: int, shares: int) -> Json:
        self._stock(corp)
        return {"proceeds": self.eco.sell_stock(self.player, corp, int(shares))}

    def c_issue_shares(self, shares: int) -> Json:
        self._stock(PLAYER)
        return {"received": self.eco.issue_stock(self.player, int(shares))}

    def c_set_training_budget(self, amount: float) -> None:
        self.player.training_budget = amount

    def c_set_brand_strategy(self, strategy: int) -> None:
        self.player.brand_strategy = strategy

    def c_set_dividend(self, ratio: float, auto: bool) -> None:
        self.player.dividend_ratio = ratio
        self.player.dividend_auto = bool(auto)

    def c_capture_plan(self, firm: int, description: str = "") -> Json:
        f = self._own_firm(firm)
        plan = capture(f)
        plan.description = description
        return {"plan": self.plans.folder_for(f.type_id).add(plan)}

    def c_apply_plan(self, firm: int, plan: int) -> None:
        f = self._own_firm(firm)
        folder = self.plans.folder_for(f.type_id)
        if not 0 <= plan < len(folder.plans):
            raise CommandError("That plan no longer exists.")
        apply_plan(folder.plans[plan], f, self.eco)


QUERIES: dict[str, Callable[..., Json]] = {
    name[2:]: fn for name, fn in vars(Api).items() if name.startswith("q_")
}
COMMANDS: dict[str, Callable[..., Any]] = {
    name[2:]: fn for name, fn in vars(Api).items() if name.startswith("c_")
}
