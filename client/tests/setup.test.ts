import { describe, expect, it } from "vitest";
import { DEFAULT_SETUP, TEST_SEED, devSetup, m2TestSetup, randomSeed } from "../src/sim/setup";

describe("M2 test setup (#290)", () => {
  it("is untimed with 3 competitors and the two goals", () => {
    expect(m2TestSetup(42)).toEqual({
      seed: 42,
      setup: { competitors: 3, year_limit: 0 },
      goals: { corp_net_worth: 50, num_product_types: 3 },
    });
  });
  it("tests and CI use the fixed seed", () => {
    expect(DEFAULT_SETUP.seed).toBe(TEST_SEED);
  });
  it("random seeds are non-negative 31-bit ints", () => {
    for (let i = 0; i < 20; i++) {
      const s = randomSeed();
      expect(Number.isInteger(s) && s >= 0 && s < 2 ** 31).toBe(true);
    }
  });
});

describe("dev URL options", () => {
  it("fixes the seed and sets the event frequency only when asked", () => {
    expect(devSetup("?seed=3&events=3")).toEqual({ ...m2TestSetup(3), setup: { ...m2TestSetup(3).setup, event_frequency: 3 } });
    const plain = devSetup("");
    expect(plain.setup).toEqual(m2TestSetup().setup);
    expect(devSetup("?events=9&seed=-1").setup).toEqual(m2TestSetup().setup);
  });
});
