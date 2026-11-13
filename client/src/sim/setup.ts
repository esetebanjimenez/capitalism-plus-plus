/**
 * M2 TEST SETUP (#278, #290). Esteban accepted this for M2 testability only; the release
 * switches back to the original's defaults (no goals, no year limit), tracked in #291.
 * This is the one place to change it. Passed as keyword arguments to
 * `capitalism.api.Api.new_game`.
 */
export type GameSetup = {
  seed: number;
  setup?: Record<string, number | boolean>;
  goals?: Record<string, number>;
};

/** Fixed seed for tests and the CI boot. */
export const TEST_SEED = 1;

export function m2TestSetup(seed: number = TEST_SEED): GameSetup {
  return {
    seed,
    setup: { competitors: 3, year_limit: 0 }, // untimed, so the 7-day rival check (#241) runs
    // Tuning numbers, not native values. Money goals are in $ millions.
    goals: { corp_net_worth: 50, num_product_types: 3 },
  };
}

/** A new random seed for each new game (shown on the Goals screen via the `goals` query). */
export function randomSeed(): number {
  const a = new Uint32Array(1);
  crypto.getRandomValues(a);
  return a[0] & 0x7fffffff;
}

/** Setup with the fixed test seed, for tests and the CI boot. */
export const DEFAULT_SETUP: GameSetup = m2TestSetup();
