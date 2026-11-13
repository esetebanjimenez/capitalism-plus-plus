import { MAX_SLICE_MS, dayDelayMs, shouldPost } from "./clock.ts";
import type { CmdResult, Speed, TickInfo, UiMsg, WorkerMsg } from "./protocol.ts";

/** The facade as the worker sees it: JSON strings in and out (boot.ts wraps Pyodide). */
export interface PyApi {
  tick(days: number, readSince: number): string;
  status(readSince: number): string;
  query(kind: string, argsJson: string): string;
  command(kind: string, argsJson: string): string;
}

export interface Timer {
  now(): number;
  set(fn: () => void, ms: number): unknown;
  clear(handle: unknown): void;
}

export const realTimer: Timer = {
  now: () => performance.now(),
  set: (fn, ms) => setTimeout(fn, ms),
  clear: (h) => clearTimeout(h as ReturnType<typeof setTimeout>),
};

/** A Python exception crossing into JS (Pyodide's PythonError carries the traceback in message). */
export function errorMsg(err: unknown): { type: "error"; message: string; traceback: string } {
  const e = err as { message?: string; type?: string };
  const tb = String(e?.message ?? err);
  const last = tb.trim().split("\n").pop() ?? tb;
  return { type: "error", message: last, traceback: tb };
}

/**
 * The worker side of the sim: owns the clock, queues commands into `Api` (which applies
 * them at the start of the next day), and posts a tick per posted day. Pure logic with an
 * injectable timer so tests can drive it without a worker or Pyodide.
 */
export class Engine {
  speed: Speed = 0;
  private readSince = -1;
  private handle: unknown = null;
  private due = 0;
  private sincePost = 0;
  private held: CmdResult[] = [];
  private dead = false;
  /** Facade command id -> client command id. */
  private readonly ids = new Map<number, number>();

  private readonly api: PyApi;
  private readonly post: (msg: WorkerMsg) => void;
  private readonly timer: Timer;

  // Plain fields, not constructor parameter properties: Node's type stripping (used by
  // web/worker-smoke.mjs) only accepts erasable TypeScript.
  constructor(api: PyApi, post: (msg: WorkerMsg) => void, timer: Timer = realTimer) {
    this.api = api;
    this.post = post;
    this.timer = timer;
  }

  status(): TickInfo {
    return { ...JSON.parse(this.api.status(this.readSince)), speed: this.speed, results: [] };
  }

  handleMsg(msg: UiMsg): void {
    if (this.dead) return;
    try {
      switch (msg.type) {
        case "speed":
          return this.setSpeed(msg.speed);
        case "step":
          for (let i = 0; i < msg.days; i++) this.day(true);
          return;
        case "read_news":
          this.readSince = msg.day_serial;
          return;
        case "cmd":
          return this.command(msg.id, msg.kind, msg.args);
        case "query":
          return this.query(msg.id, msg.kind, msg.args);
      }
    } catch (err) {
      this.fail(err);
    }
  }

  setSpeed(speed: Speed): void {
    this.speed = speed;
    if (this.handle !== null) this.timer.clear(this.handle);
    this.handle = null;
    this.sincePost = 0;
    if (speed === 0) {
      this.post({ type: "tick", tick: { ...this.status(), results: this.takeHeld() } });
      return;
    }
    this.due = this.timer.now() + dayDelayMs(speed);
    this.schedule();
  }

  private command(id: number, kind: string, args: unknown): void {
    try {
      const { id: apiId } = JSON.parse(this.api.command(kind, JSON.stringify(args ?? {})));
      this.ids.set(apiId, id);
    } catch (err) {
      // Unknown command kind: a client bug, reported as a failed result straight away.
      this.held.push({ id, ok: false, error: errorMsg(err).message });
      if (this.speed === 0) this.post({ type: "tick", tick: { ...this.status(), results: this.takeHeld() } });
    }
  }

  private query(id: number, kind: string, args: unknown): void {
    try {
      this.post({ type: "query_result", id, ok: true, data: JSON.parse(this.api.query(kind, JSON.stringify(args ?? {}))) });
    } catch (err) {
      this.post({ type: "query_result", id, ok: false, error: errorMsg(err).message });
    }
  }

  private takeHeld(): CmdResult[] {
    const h = this.held;
    this.held = [];
    return h;
  }

  /** Advance one day; post it if due. Returns whether it posted. */
  private day(forcePost = false): boolean {
    const t = JSON.parse(this.api.tick(1, this.readSince)) as TickInfo;
    const results = t.results.map((r) => ({ ...r, id: this.ids.get(r.id) ?? -r.id }));
    for (const r of t.results) this.ids.delete(r.id);
    this.held.push(...results);
    this.sincePost++;
    if (forcePost || shouldPost(this.speed, this.sincePost, this.held.length > 0)) {
      this.post({ type: "tick", tick: { ...t, speed: this.speed, results: this.takeHeld() } });
      this.sincePost = 0;
      return true;
    }
    return false;
  }

  private schedule(): void {
    if (this.speed === 0 || this.dead) return;
    const wait = this.speed === 4 ? 0 : Math.max(0, this.due - this.timer.now());
    this.handle = this.timer.set(() => this.run(), wait);
  }

  private run(): void {
    this.handle = null;
    try {
      if (this.speed === 4) {
        const start = this.timer.now();
        do this.day();
        while (this.timer.now() - start < MAX_SLICE_MS && this.speed === 4);
      } else {
        this.day();
        const delay = dayDelayMs(this.speed);
        // A day that overran its slot just makes the game run slower; no catch-up burst.
        this.due = Math.max(this.due + delay, this.timer.now());
      }
    } catch (err) {
      return this.fail(err);
    }
    this.schedule();
  }

  private fail(err: unknown): void {
    this.dead = true;
    if (this.handle !== null) this.timer.clear(this.handle);
    this.handle = null;
    this.post(errorMsg(err));
  }
}
