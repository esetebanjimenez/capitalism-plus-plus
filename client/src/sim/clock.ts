import type { Speed } from "./protocol.ts";

/**
 * Target game days per second for each speed (docs/m2-ux-spec.md "Default state").
 * Provisional client values: the native speeds are not traced, and M1 left speed to
 * the frontend. Max runs as fast as it can.
 */
export const DAYS_PER_SEC: Record<Speed, number> = { 0: 0, 1: 1, 2: 3, 3: 8, 4: Infinity };

/** At max speed the worker posts a tick only every Nth day (or when a command result is due). */
export const MAX_POST_EVERY = 7;

/** At max speed, run days for at most this long before yielding to incoming messages. */
export const MAX_SLICE_MS = 30;

/** Milliseconds between days at a speed; 0 for max, Infinity when paused. */
export function dayDelayMs(speed: Speed): number {
  const dps = DAYS_PER_SEC[speed];
  if (dps === 0) return Infinity;
  return Number.isFinite(dps) ? 1000 / dps : 0;
}

/** Whether a day should be posted: every day below max, every Nth day at max. */
export function shouldPost(speed: Speed, daysSincePost: number, hasResults: boolean): boolean {
  return speed !== 4 || hasResults || daysSincePost >= MAX_POST_EVERY;
}
