"""The M2 facade: JSON-only queries, queued commands answered on the next tick."""

from __future__ import annotations

import json

from capitalism.api import COMMANDS, QUERIES, Api, town_footprint
from capitalism.scenario import bread_town, find_site

STORE, FACTORY = 1, 2
MANUFACTURING, PURCHASING, SALES = 7, 10, 12


def make_api() -> Api:
    sim, _ = bread_town(1)
    sim.economy.add_corp("Player")
    return Api(sim)


def run(api: Api, kind: str, **args):
    cid = api.command(kind, args)["id"]
    (res,) = [r for r in api.tick()["results"] if r["id"] == cid]
    return res


def roundtrip(obj):
    return json.loads(json.dumps(obj, allow_nan=False))


def test_contract_names():
    assert set(QUERIES) == {
        "map",
        "map_objects",
        "overlay",
        "tile",
        "build_options",
        "town",
        "town_market",
        "firm",
        "job",
        "job_options",
        "firm_links",
        "suppliers",
        "corp",
        "stocks",
        "stock",
        "trade_quote",
        "news",
        "goals",
        "plans",
    }
    assert set(COMMANDS) == {
        "build_firm",
        "demolish_firm",
        "add_job",
        "remove_job",
        "link_slots",
        "unlink_slots",
        "set_price",
        "link_b2b",
        "link_consumer",
        "remove_link",
        "borrow",
        "repay",
        "buy_shares",
        "sell_shares",
        "issue_shares",
        "set_training_budget",
        "set_brand_strategy",
        "set_dividend",
        "capture_plan",
        "apply_plan",
    }


def test_command_is_queued_until_tick():
    api = make_api()
    x, y = find_site(api.sim, api.sim.towns[0])
    day = api.sim.calendar.day_serial
    assert api.command("build_firm", {"firm_type": FACTORY, "x": x, "y": y}) == {"id": 1}
    assert not any(f for f in api.eco.firms if f is not None)
    out = api.tick()
    assert out["day_serial"] == day + 1
    assert out["results"][0]["ok"] and out["results"][0]["result"]["firm"] >= 0


def test_failed_checks_answer_with_reason():
    api = make_api()
    res = run(api, "build_firm", firm_type=FACTORY, x=-5, y=-5)
    assert res["ok"] is False and res["error"]
    assert run(api, "demolish_firm", firm=99)["error"] == "That firm no longer exists."


def test_queries_are_json_and_do_not_change_state():
    api = make_api()
    town = api.sim.towns[0]
    x, y = find_site(api.sim, town)
    fid = run(api, "build_firm", firm_type=FACTORY, x=x, y=y)["result"]["firm"]
    assert run(
        api,
        "add_job",
        firm=fid,
        slot=1,
        job_type=MANUFACTURING,
        product=api.eco.catalog["Flour"].id,
    )["ok"]
    before = api.sim.state_hash()
    calls = [
        ("map", {}),
        ("map_objects", {"since": -1}),
        ("map_objects", {"since": 0}),
        ("overlay", {"layer": "land_value"}),
        ("overlay", {"layer": "ownership"}),
        ("tile", {"x": x, "y": y}),
        ("build_options", {"x": x, "y": y}),
        ("town", {"id": town.id}),
        ("town_market", {"id": town.id}),
        ("firm", {"id": fid}),
        ("job", {"firm": fid, "slot": 1}),
        ("job_options", {"firm": fid, "slot": 0}),
        ("firm_links", {"id": fid}),
        ("suppliers", {"firm": fid, "slot": 1}),
        ("corp", {"id": 0}),
        ("stocks", {}),
        ("stock", {"corp": 0}),
        ("trade_quote", {"corp": 0, "side": "issue", "shares": 1000}),
        ("news", {}),
        ("goals", {}),
        ("plans", {"firm_type": FACTORY}),
    ]
    for kind, args in calls:
        roundtrip(api.query(kind, args))
    assert api.sim.state_hash() == before
    firm = api.query("firm", {"id": fid})
    assert len(firm["slots"]) == 9 and firm["slots"][1]["job_type"] == MANUFACTURING


def test_wrappers_set_existing_state():
    api = make_api()
    town = api.sim.towns[0]
    cat = api.eco.catalog
    x, y = find_site(api.sim, town)
    fid = run(api, "build_firm", firm_type=FACTORY, x=x, y=y)["result"]["firm"]
    run(api, "add_job", firm=fid, slot=0, job_type=MANUFACTURING, product=cat["Flour"].id)
    run(api, "add_job", firm=fid, slot=1, job_type=SALES, product=cat["Flour"].id)
    assert run(api, "link_slots", firm=fid, a=0, b=1)["ok"]
    assert api.query("firm", {"id": fid})["edges"] == [[0, 1]]
    assert run(api, "unlink_slots", firm=fid, a=0, b=1)["ok"]
    assert api.query("firm", {"id": fid})["edges"] == []
    assert run(api, "set_price", firm=fid, slot=1, price=12.5)["ok"]
    assert api.eco.firms[fid].slots[1].price == 12.5
    assert run(api, "remove_job", firm=fid, slot=1)["ok"]
    assert api.eco.firms[fid].slots[1] is None
    assert run(api, "set_training_budget", amount=20)["ok"]
    assert run(api, "set_dividend", ratio=0.3, auto=False)["ok"]
    assert api.player.training_budget == 20 and api.player.dividend_ratio == 0.3
    assert run(api, "demolish_firm", firm=fid)["ok"]
    assert api.eco.firms[fid] is None
    assert api.sim.world.can_build(x, y)


def test_b2b_and_consumer_links_and_removal():
    api = make_api()
    town = api.sim.towns[0]
    cat = api.eco.catalog
    sim = api.sim
    x, y = find_site(sim, town)
    a = run(api, "build_firm", firm_type=FACTORY, x=x, y=y)["result"]["firm"]
    run(api, "add_job", firm=a, slot=0, job_type=SALES, product=cat["Bread"].id)
    x2, y2 = find_site(sim, town)
    b = run(api, "build_firm", firm_type=STORE, x=x2, y=y2)["result"]["firm"]
    run(api, "add_job", firm=b, slot=0, job_type=PURCHASING, product=cat["Bread"].id)
    run(api, "add_job", firm=b, slot=1, job_type=SALES, product=cat["Bread"].id)
    link = run(api, "link_b2b", seller_firm=a, seller_slot=0, buyer_firm=b, buyer_slot=0)
    assert link["ok"], link
    sups = api.query("suppliers", {"firm": b, "slot": 0})["suppliers"]
    assert [s["firm"] for s in sups] == [a]
    cons = run(api, "link_consumer", firm=b, slot=1)
    assert cons["ok"], cons
    links = api.query("firm_links", {"id": b})
    assert len(links["buying"]) == 1
    assert links["selling"][0]["consumers"] == api.eco.firms[b].town.id
    assert run(api, "remove_link", link=link["result"]["link"])["ok"]
    assert api.eco.firms[b].slots[0].supply is None


def test_finance_and_shares():
    api = make_api()
    p = api.player
    limit = p.credit_limit(api.eco.firms)
    if limit > 0:
        assert run(api, "borrow", amount=limit / 2)["ok"]
        assert run(api, "repay", amount=limit)["result"]["repaid"] > 0
    assert run(api, "borrow", amount=limit + 1e12)["ok"] is False
    got = run(api, "issue_shares", shares=1000)["result"]["received"]
    assert got > 0  # cash moves in the sim once the share-cash fix lands


def test_unread_important_counts_since_serial():
    api = make_api()
    out = api.tick(read_since=10**9)
    assert out["unread_important"] == 0


def test_map_rev_moves_on_build_and_level_up_only():
    api = make_api()
    before = api.sim.state_hash()
    rev0 = api.status()["map_rev"]
    api.query("map_objects", {"since": rev0})
    assert api.sim.state_hash() == before
    town = api.sim.towns[0]
    x, y = find_site(api.sim, town)
    fid = run(api, "build_firm", firm_type=STORE, x=x, y=y)["result"]["firm"]
    rev1 = api.status()["map_rev"]
    assert rev1 > rev0
    w = api.sim.world.width
    objs = api.query("map_objects", {"since": rev0})
    assert [y * w + x, int(api.sim.world.tile_at(x, y).kind), fid] in objs["changes"]
    assert "kind" not in objs
    # A quiet day: no build, no level change.
    levels = [t.level for t in api.sim.towns]
    assert api.tick()["map_rev"] == rev1
    assert [t.level for t in api.sim.towns] == levels
    assert api.query("map_objects", {"since": rev1})["changes"] == []
    # Forced level-up repaints through spread_town.
    town.level += 1
    api.sim.world.spread_town(town, api.sim.rng)
    rev2 = api.status()["map_rev"]
    assert rev2 > rev1
    changes = api.query("map_objects", {"since": rev1})["changes"]
    assert changes and all(k == int(api.sim.world.tiles[i].kind) for i, k, _ in changes)
    # Demolish moves it again.
    assert run(api, "demolish_firm", firm=fid)["ok"]
    assert api.status()["map_rev"] > rev2


def test_map_objects_full_when_since_is_unknown():
    api = make_api()
    full = api.query("map_objects", {"since": -1})
    m = api.query("map")
    assert full["changes"] is None
    assert full["kind"] == m["kind"] and full["ref"] == m["ref"]


def test_map_objects_matches_map():
    api = make_api()
    x, y = find_site(api.sim, api.sim.towns[0])
    run(api, "build_firm", firm_type=STORE, x=x, y=y)
    m, o = api.query("map"), api.query("map_objects", {"since": api.status()["map_rev"]})
    assert o["towns"] == m["towns"] and o["firms"] == m["firms"]
    assert o["map_rev"] == m["map_rev"]
    assert all({"radius", "block_level"} <= set(t) for t in m["towns"])


def test_town_footprint_for_levels_1_to_8():
    rows = [town_footprint(lv) for lv in range(1, 9)]
    assert all(set(r) == {"radius", "block_level"} for r in rows)
    assert rows[6] == rows[7] == town_footprint(6)  # past the table: its top row
