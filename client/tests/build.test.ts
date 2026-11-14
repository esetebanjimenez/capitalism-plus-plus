// @vitest-environment happy-dom
import { describe, expect, it, vi } from "vitest";
import { BuildOptionsJson, buildConfirm, buildPanel, cost, needsConfirm } from "../src/ui/build";

const row = (type_id: number, name: string, setup: number, overhead: number, cash: number, land = 500_000) => ({
  type_id,
  name,
  setup_cost: setup,
  land_value: land,
  build_cost: setup + land,
  overhead_month: overhead,
  affordable: cash >= setup + land,
  shortfall: Math.max(0, setup + land - cash),
});

// Example cash and land value as in docs/art/m2-build-menu-preview.png; costs from capitalism.db.
const CASH = 4_812_300;
const FIXTURE: BuildOptionsJson = {
  x: 12,
  y: 40,
  can_build: true,
  options: [
    row(1, "Department Store", 1_000_000, 100_000, CASH),
    row(6, "Mine", 5_000_000, 300_000, CASH),
    row(11, "Television Station", 20_000_000, 350_000, CASH),
  ],
};

describe("build panel (#252, ux-spec Build menu)", () => {
  it("renders one row per option with sprite, cost and overhead", () => {
    const p = buildPanel(FIXTURE, CASH, () => {});
    const rows = [...p.body.querySelectorAll<HTMLButtonElement>(".build-row")];
    expect(p.key).toBe("build");
    expect(p.height).toBe("half");
    expect(rows.map((r) => r.querySelector(".build-name")!.textContent)).toEqual(["Department Store", "Mine", "Television Station"]);
    expect(rows[0].querySelector(".firm-icon")!.className).toContain("firm-firm_department_store");
    expect(rows[0].querySelector(".build-cost")!.textContent).toBe("$1.5M");
    expect(rows[0].querySelector(".build-overhead")!.textContent).toBe("$100k/month");
  });

  it("disables unaffordable rows, greys their sprite and shows the shortfall in red", () => {
    const pick = vi.fn();
    const p = buildPanel(FIXTURE, CASH, pick);
    const [store, mine, tv] = [...p.body.querySelectorAll<HTMLButtonElement>(".build-row")];
    expect([store.disabled, mine.disabled, tv.disabled]).toEqual([false, true, true]);
    expect(store.classList.contains("unaffordable")).toBe(false);
    expect(mine.classList.contains("unaffordable")).toBe(true);
    expect(store.querySelector(".build-short")).toBeNull();
    expect(mine.querySelector(".build-short")!.textContent).toBe("short $687.7k");
    expect(tv.querySelector(".build-short")!.textContent).toBe("short $15.7M");
    mine.click();
    expect(pick).not.toHaveBeenCalled();
    store.click();
    expect(pick).toHaveBeenCalledWith(FIXTURE.options[0]);
  });

  it("disables every row on a tile you can't build on", () => {
    const p = buildPanel({ ...FIXTURE, can_build: false }, CASH, () => {});
    expect([...p.body.querySelectorAll<HTMLButtonElement>(".build-row")].every((r) => r.disabled)).toBe(true);
    expect(p.body.querySelector(".build-note")).not.toBeNull();
  });

  it("asks first when the build spends more than 10% of cash", () => {
    expect(needsConfirm(1_500_000, CASH)).toBe(true);
    expect(needsConfirm(400_000, CASH)).toBe(false);
    expect(needsConfirm(481_230, CASH)).toBe(false);
    const ok = vi.fn();
    const c = buildConfirm(FIXTURE.options[0], CASH, ok, () => {});
    expect(c.title).toBe("Build a Department Store?");
    expect(c.body.textContent).toContain("31% of your cash");
    (c.actions![0] as HTMLButtonElement).click();
    expect(ok).toHaveBeenCalledOnce();
    expect(cost(600_000)).toBe("$600k");
  });
});
