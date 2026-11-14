import { describe, expect, it } from "vitest";
import { PALETTE, axisRange, chartLayout, crossesZero, nearestPoint, shortMoney, tipColour } from "../src/ui/chart";

describe("shortMoney", () => {
  it("formats the art/charts.json examples", () => {
    expect(shortMoney(950)).toBe("950");
    expect(shortMoney(12_500)).toBe("12.5k");
    expect(shortMoney(3_200_000)).toBe("3.2M");
    expect(shortMoney(1_100_000_000)).toBe("1.1B");
    expect(shortMoney(0)).toBe("0");
  });
  it("uses a minus sign for negatives", () => {
    expect(shortMoney(-60_000)).toBe("\u221260k");
    expect(shortMoney(-2_400_000_000)).toBe("\u22122.4B");
  });
  it("rolls over at unit edges and handles billions beyond 1000", () => {
    expect(shortMoney(999_960)).toBe("1M");
    expect(shortMoney(1_000)).toBe("1k");
    expect(shortMoney(2_500_000_000_000)).toBe("2500B");
    expect(shortMoney(18.5)).toBe("18.5");
  });
});

describe("axis", () => {
  it("detects a zero crossing", () => {
    expect(crossesZero(-1, 2)).toBe(true);
    expect(crossesZero(0, 2)).toBe(false);
    expect(crossesZero(1, 2)).toBe(false);
  });
  it("picks four round ticks covering the values", () => {
    expect(axisRange([-420e3, 1.2e6]).ticks).toEqual([-1e6, 0, 1e6, 2e6]);
    expect(axisRange([18.2, 20.3]).ticks).toEqual([18, 19, 20, 21]);
  });
  it("widens a single point to include zero, and an empty series to 0..1", () => {
    expect(axisRange([12.5e6]).ticks).toEqual([0, 5e6, 10e6, 15e6]);
    expect(axisRange([]).ticks).toEqual([0, 0.5, 1, 1.5]);
  });
});

describe("chartLayout", () => {
  it("draws a zero line only when the range crosses 0", () => {
    const l = chartLayout([{ label: "J", value: -5 }, { label: "F", value: 9 }], 300, 160);
    expect(l.zeroY).not.toBeNull();
    expect(l.ticks.filter((t) => t.zero)).toHaveLength(1);
    expect(chartLayout([{ label: "J", value: 5 }, { label: "F", value: 9 }], 300, 160).zeroY).toBeNull();
  });
  it("places a single point in the middle and handles empty series", () => {
    const one = chartLayout([{ label: "Jan", value: 7 }], 200, 160);
    expect(one.points).toHaveLength(1);
    expect(one.points[0].x).toBeCloseTo(one.plot.x + one.plot.w / 2);
    const none = chartLayout([], 200, 160);
    expect(none.points).toHaveLength(0);
    expect(nearestPoint(none, 50)).toBe(-1);
  });
  it("finds the nearest point to a tap", () => {
    const l = chartLayout([0, 1, 2, 3].map((v) => ({ label: String(v), value: v })), 300, 160);
    expect(nearestPoint(l, l.points[2].x + 3)).toBe(2);
  });
});

it("colours the tip green at or above 0 and red below", () => {
  expect(tipColour(0)).toBe(PALETTE.GREEN);
  expect(tipColour(5)).toBe(PALETTE.GREEN);
  expect(tipColour(-1)).toBe(PALETTE.RED);
});
