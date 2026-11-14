"""The M2 facade: JSON-only queries, queued commands answered on the next tick."""

from __future__ import annotations

import json

import pytest

from capitalism.api import COMMANDS, QUERIES, Api
from capitalism.news import NewsItem, NewsType
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
    assert [y * w + x, int(api.sim.world.tile_at(x, y).kind), fid, 0] in objs["changes"]
    assert "kind" not in objs
    # A quiet day: no build, no level change.
    levels = [t.level for t in api.sim.towns]
    assert api.tick()["map_rev"] == rev1
    assert [t.level for t in api.sim.towns] == levels
    assert api.query("map_objects", {"since": rev1})["changes"] == []
    # Forced level-up repaints through spread_town.
    town.level += 1
    api.sim.world.spread_town(town, api.sim.rng, api.eco.firms)
    rev2 = api.status()["map_rev"]
    assert rev2 > rev1
    changes = api.query("map_objects", {"since": rev1})["changes"]
    assert changes and all(k == int(api.sim.world.tiles[i].kind) for i, k, _, _ in changes)
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
    assert all(set(t) == {"id", "name", "x", "y", "level"} for t in m["towns"])


def test_map_has_climate_and_town_kinds():
    api = make_api()
    m = api.query("map")
    n = m["width"] * m["height"]
    assert len(m["climate"]) == len(m["town_kind"]) == n
    assert set(m["climate"]) <= set(range(5))
    kinds = {k for k in m["town_kind"] if k}
    assert kinds and all(0x3000 <= k <= 0x300C for k in kinds)


def test_new_game_setup_and_goals():
    api = Api.new_game(
        seed=7,
        setup={"competitors": 3, "year_limit": 0},
        goals={"corp_net_worth": 50, "num_product_types": 3},
    )
    assert api.sim.setup.competitors == 3 and api.sim.setup.year_limit == 0
    g = api.query("goals")
    assert g["seed"] == 7 and g["year_limit"] == 0
    assert {r["name"]: r["target"] for r in g["goals"]} == {
        "corp_net_worth": 50,
        "num_product_types": 3,
    }
    assert api.sim.goal_checker.goals.has_any_goal
    for bad in ({"setup": {"seed": 2}}, {"setup": {"competitors": 99}}, {"goals": {"nope": 1}}):
        try:
            Api.new_game(**bad)
        except ValueError:
            continue
        raise AssertionError(bad)


def _news(api: Api, item) -> dict:
    api.eco.news_log.post(item)
    return api.query("news", {})["news"][0]


def test_news_headlines_name_the_corp_firm_and_product():
    """ux-spec section 4: one item of each event type the sim emits today (#253)."""
    api = make_api()
    corp = api.player
    town = api.sim.towns[0]
    x, y = find_site(api.sim, town)
    fid = run(api, "build_firm", firm_type=FACTORY, x=x, y=y)["result"]["firm"]
    day = api.sim.calendar.day_serial
    flour = api.eco.catalog["Flour"]

    row = _news(
        api, NewsItem(NewsType.LIVESTOCK_DISEASE, day, corp.id, {"divisor": 2, "farms_affected": 1})
    )
    assert corp.name in row["headline"] and row["corp_name"] == corp.name and row["corp"] == corp.id
    row = _news(
        api,
        NewsItem(NewsType.BUILDING_DESTROYED, day, corp.id, {"firm_id": 999, "firm_type": FACTORY}),
    )
    assert (
        row["headline"] == f"A Factory owned by {corp.name} was destroyed" and row["firm"] is None
    )
    row = _news(api, NewsItem(NewsType.BUILDING_DESTROYED, day, corp.id, {"firm_id": fid}))
    assert "Factory" in row["headline"] and row["firm"] == fid
    row = _news(api, NewsItem(NewsType.CROP_FAILURE, day, corp.id, {"farms_affected": 2}))
    assert row["headline"] == f"Crops failed on {corp.name}'s farms"
    row = _news(
        api,
        NewsItem(
            NewsType.RND_BREAKTHROUGH, day, corp.id, {"progress_added": 5, "product": "Flour"}
        ),
    )
    assert row["headline"] == f"{corp.name} made a research breakthrough on Flour"
    assert row["product"] == flour.id
    row = _news(api, NewsItem(NewsType.INVENTORY_LOSS, day, corp.id, {"total_loss": 12.0}))
    assert corp.name in row["headline"] and "12" not in row["headline"]
    row = _news(
        api,
        NewsItem(NewsType.ECONOMIC_DOWNTURN, day, -1, {"loss_fraction": 0.1, "total_loss": 5.0}),
    )
    assert row["headline"] == "An economic downturn cut corporate cash"
    assert row["corp"] is None and row["corp_name"] is None
    roundtrip(api.query("news", {}))


@pytest.mark.parametrize("news_type", list(NewsType))
def test_every_news_type_has_a_headline(news_type):
    from capitalism.news_text import PLACEHOLDERS, fields
    from capitalism.tables import NEWS_HEADLINES

    row = NEWS_HEADLINES[int(news_type)]
    assert row.name == news_type.name
    assert fields(row.template) <= PLACEHOLDERS
    api = make_api()
    out = _news(api, NewsItem(news_type, api.sim.calendar.day_serial, api.player.id, {}))
    text = out["headline"]
    assert text and text[0].isupper() and "{" not in text and not any(ch.isdigit() for ch in text)
    if "{corp}" in row.template:
        assert api.player.name in text


def test_build_options_leave_out_the_seaport():
    """ux-spec "Build menu": the 14 firm types minus Seaport (#251)."""
    api = make_api()
    x, y = find_site(api.sim, api.sim.towns[0])
    ids = {o["type_id"] for o in api.query("build_options", {"x": x, "y": y})["options"]}
    assert 14 not in ids
    assert ids == set(range(1, 14))
    res = run(api, "build_firm", firm_type=14, x=x, y=y)
    assert res["ok"] is False and "Seaport" in res["error"]
    assert not any(f for f in api.eco.firms if f is not None and f.x == x and f.y == y)
