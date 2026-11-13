import { describe, expect, it } from "vitest";
import { DAYS_PER_SEC, MAX_POST_EVERY, dayDelayMs, shouldPost } from "../src/sim/clock";
import { Engine, type PyApi, type Timer } from "../src/sim/engine";
import { SimClient, type WorkerPort } from "../src/sim/client";
import type { CmdResult, TickInfo, UiMsg, WorkerMsg } from "../src/sim/protocol";

/** A stand-in for capitalism.api.Api: commands queue and apply at the next tick. */
class FakeApi implements PyApi {
  day = 0;
  cash = 1000;
  private nextId = 1;
  private queue: { id: number; kind: string; args: Record<string, unknown> }[] = [];
  status() {
    return JSON.stringify({ day_serial: this.day, year: 1990, month: 1, day: this.day + 1, cash: this.cash, unread_important: 0 });
  }
  tick(days: number) {
    const results: CmdResult[] = this.queue.map((c) =>
      c.args.x === -1 ? { id: c.id, ok: false, error: "You can't build on that tile." } : { id: c.id, ok: true, result: { firm: 0 } },
    );
    this.queue = [];
    this.day += days;
    return JSON.stringify({ ...JSON.parse(this.status()), results });
  }
  query(kind: string) {
    if (kind === "boom") throw new Error("Traceback...\nKeyError: 'boom'");
    return JSON.stringify({ kind, day: this.day });
  }
  command(kind: string, args: string) {
    if (kind !== "build_firm") throw new Error(`Traceback...\nKeyError: "unknown command '${kind}'"`);
    const id = this.nextId++;
    this.queue.push({ id, kind, args: JSON.parse(args) });
    return JSON.stringify({ id });
  }
}

/** Manual clock: advance() runs due timers in order. */
class FakeTimer implements Timer {
  t = 0;
  private jobs: { at: number; fn: () => void; id: number }[] = [];
  private seq = 0;
  /** Simulated cost of each now() call, so max-speed slices end. */
  step = 0;
  now() {
    this.t += this.step;
    return this.t;
  }
  set(fn: () => void, ms: number) {
    const id = ++this.seq;
    this.jobs.push({ at: this.t + ms, fn, id });
    return id;
  }
  clear(h: unknown) {
    this.jobs = this.jobs.filter((j) => j.id !== h);
  }
  advance(ms: number) {
    const end = this.t + ms;
    for (;;) {
      this.jobs.sort((a, b) => a.at - b.at || a.id - b.id);
      const j = this.jobs[0];
      if (!j || j.at > end) break;
      this.jobs.shift();
      this.t = Math.max(this.t, j.at);
      j.fn();
    }
    this.t = end;
  }
}

const ticks = (out: WorkerMsg[]) => out.filter((m): m is { type: "tick"; tick: TickInfo } => m.type === "tick").map((m) => m.tick);

describe("clock", () => {
  it("maps speeds to day delays", () => {
    expect(dayDelayMs(0)).toBe(Infinity);
    expect(dayDelayMs(1)).toBe(1000 / DAYS_PER_SEC[1]);
    expect(dayDelayMs(4)).toBe(0);
  });
  it("posts every day below max, every Nth day at max", () => {
    expect(shouldPost(3, 1, false)).toBe(true);
    expect(shouldPost(4, MAX_POST_EVERY - 1, false)).toBe(false);
    expect(shouldPost(4, MAX_POST_EVERY, false)).toBe(true);
    expect(shouldPost(4, 1, true)).toBe(true);
  });
});

describe("engine pacing", () => {
  it("runs the target days per second at each speed", () => {
    for (const speed of [1, 2, 3] as const) {
      const api = new FakeApi();
      const timer = new FakeTimer();
      const out: WorkerMsg[] = [];
      const e = new Engine(api, (m) => out.push(m), timer);
      e.setSpeed(speed);
      timer.advance(5000);
      expect(api.day).toBe(5 * DAYS_PER_SEC[speed]);
      // One posted tick per day (a speed change posts nothing; pausing does).
      expect(ticks(out).length).toBe(api.day);
      expect(ticks(out).every((t) => t.speed === speed)).toBe(true);
    }
  });

  it("pause stops the date", () => {
    const api = new FakeApi();
    const timer = new FakeTimer();
    const out: WorkerMsg[] = [];
    const e = new Engine(api, (m) => out.push(m), timer);
    e.setSpeed(1);
    timer.advance(3000);
    e.setSpeed(0);
    const day = api.day;
    timer.advance(10_000);
    expect(api.day).toBe(day);
    expect(ticks(out).at(-1)!.speed).toBe(0);
  });

  it("max speed posts only every Nth day", () => {
    const api = new FakeApi();
    const timer = new FakeTimer();
    timer.step = 1; // every now() costs 1 ms, so each slice ends
    const out: WorkerMsg[] = [];
    const e = new Engine(api, (m) => out.push(m), timer);
    e.setSpeed(4);
    timer.advance(200);
    e.setSpeed(0);
    const posted = ticks(out).filter((t) => t.speed === 4);
    expect(api.day).toBeGreaterThan(MAX_POST_EVERY * 3);
    expect(posted.length).toBe(Math.floor(api.day / MAX_POST_EVERY));
    expect(posted.every((t) => t.day_serial % MAX_POST_EVERY === 0)).toBe(true);
  });
});

describe("command queue", () => {
  it("applies commands at the next day and maps results to client ids", () => {
    const api = new FakeApi();
    const timer = new FakeTimer();
    const out: WorkerMsg[] = [];
    const e = new Engine(api, (m) => out.push(m), timer);
    e.handleMsg({ type: "cmd", id: 41, kind: "build_firm", args: { x: 3 } });
    e.handleMsg({ type: "cmd", id: 42, kind: "build_firm", args: { x: -1 } });
    expect(ticks(out)).toEqual([]); // nothing applied while paused
    e.handleMsg({ type: "step", days: 1 });
    const [t] = ticks(out);
    expect(t.day_serial).toBe(1);
    expect(t.results).toEqual([
      { id: 41, ok: true, result: { firm: 0 } },
      { id: 42, ok: false, error: "You can't build on that tile." },
    ]);
  });

  it("at max speed a result is posted on the day it applies", () => {
    const api = new FakeApi();
    const timer = new FakeTimer();
    timer.step = 1;
    const out: WorkerMsg[] = [];
    const e = new Engine(api, (m) => out.push(m), timer);
    e.handleMsg({ type: "cmd", id: 7, kind: "build_firm", args: { x: 1 } });
    e.setSpeed(4);
    timer.advance(1);
    expect(ticks(out)[0].day_serial).toBe(1);
    expect(ticks(out)[0].results[0].id).toBe(7);
  });

  it("an unknown command fails at once; a query error comes back as a result", () => {
    const out: WorkerMsg[] = [];
    const e = new Engine(new FakeApi(), (m) => out.push(m), new FakeTimer());
    e.handleMsg({ type: "cmd", id: 5, kind: "nope", args: {} });
    expect(ticks(out)[0].results[0]).toMatchObject({ id: 5, ok: false });
    e.handleMsg({ type: "query", id: 6, kind: "boom", args: {} });
    expect(out.at(-1)).toEqual({ type: "query_result", id: 6, ok: false, error: "KeyError: 'boom'" });
  });

  it("a Python error during a day stops the clock and posts the traceback", () => {
    const api = new FakeApi();
    api.tick = () => {
      throw new Error("Traceback (most recent call last):\n  ...\nZeroDivisionError: division by zero");
    };
    const timer = new FakeTimer();
    const out: WorkerMsg[] = [];
    const e = new Engine(api, (m) => out.push(m), timer);
    e.setSpeed(1);
    timer.advance(5000);
    expect(out).toHaveLength(1);
    expect(out[0]).toMatchObject({ type: "error", message: "ZeroDivisionError: division by zero" });
  });
});

describe("SimClient with a fake worker", () => {
  /** Runs an Engine on the "worker side" of a fake port pair. */
  function pair() {
    const api = new FakeApi();
    const timer = new FakeTimer();
    let engine: Engine | null = null;
    const sent: UiMsg[] = [];
    const port: WorkerPort = {
      onmessage: null,
      postMessage(data: string) {
        const msg = JSON.parse(data) as UiMsg;
        sent.push(msg);
        const reply = (m: WorkerMsg) => port.onmessage?.({ data: JSON.stringify(m) });
        if (msg.type === "init") {
          engine = new Engine(api, reply, timer);
          reply({ type: "ready", status: engine.status() });
        } else engine!.handleMsg(msg);
      },
    };
    const client = new SimClient(port, { seed: 1 }, "capitalism.zip");
    return { api, timer, client, sent };
  }

  it("sends one JSON string per message, tracks pending commands and speed", async () => {
    const { timer, client, sent } = pair();
    const ready = await client.ready;
    expect(ready.day_serial).toBe(0);
    expect(sent[0]).toEqual({ type: "init", setup: { seed: 1 }, zipUrl: "capitalism.zip" });

    const results: CmdResult[] = [];
    client.onCmdResult = (r) => results.push(r);
    const ok = client.command("build_firm", { x: 2 });
    const bad = client.command("build_firm", { x: -1 });
    expect([...client.pending]).toEqual([ok, bad]);

    let last: TickInfo | null = null;
    client.onTick = (t) => (last = t);
    client.setSpeed(2);
    timer.advance(1000);
    expect(last!.day_serial).toBe(DAYS_PER_SEC[2]);
    expect(last!.speed).toBe(2);
    expect(client.pending.size).toBe(0);
    expect(results.map((r) => [r.id, r.ok])).toEqual([
      [ok, true],
      [bad, false],
    ]);
    expect(await client.query("firm", { firm: 0 })).toEqual({ kind: "firm", day: 3 });
    await expect(client.query("boom")).rejects.toThrow("KeyError");
  });
});
