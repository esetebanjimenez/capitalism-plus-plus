import type { CmdResult, Json, Speed, TickInfo, UiMsg, WorkerMsg } from "./protocol.ts";

/** What SimClient needs from a Worker; tests pass a fake. */
export interface WorkerPort {
  postMessage(data: string): void;
  onmessage: ((e: { data: string }) => void) | null;
}

/**
 * Main-thread wrapper around the sim worker. `command` returns an id at once, so the
 * caller can show the pending badge; `onCmdResult` fires when the worker has applied it
 * at the next day (docs/m2-facade-contract.md "Conventions").
 */
export class SimClient {
  /** Commands sent but not yet applied. */
  readonly pending = new Set<number>();
  speed: Speed = 0;
  last: TickInfo | null = null;
  readonly ready: Promise<TickInfo>;

  onTick: (t: TickInfo) => void = () => {};
  onCmdResult: (r: CmdResult) => void = () => {};
  onProgress: (stage: string, done: number, total: number) => void = () => {};
  onError: (message: string, traceback: string) => void = () => {};

  private nextId = 1;
  private readonly queries = new Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>();

  constructor(
    private readonly port: WorkerPort,
    setup: Json,
    zipUrl: string,
    /** Folder holding pyodide.mjs, the core files and the wheels (self-hosted, #247). */
    pyodideUrl = "pyodide/",
  ) {
    let resolveReady!: (t: TickInfo) => void;
    let rejectReady!: (e: Error) => void;
    this.ready = new Promise((res, rej) => ((resolveReady = res), (rejectReady = rej)));
    this.ready.catch(() => {});
    port.onmessage = (e) => {
      const msg = JSON.parse(e.data) as WorkerMsg;
      switch (msg.type) {
        case "progress":
          return this.onProgress(msg.stage, msg.done, msg.total);
        case "ready":
          this.last = msg.status;
          return resolveReady(msg.status);
        case "tick":
          return this.tick(msg.tick);
        case "query_result": {
          const q = this.queries.get(msg.id);
          this.queries.delete(msg.id);
          if (msg.ok) q?.resolve(msg.data);
          else q?.reject(new Error(msg.error));
          return;
        }
        case "error":
          rejectReady(new Error(msg.message));
          for (const q of this.queries.values()) q.reject(new Error(msg.message));
          this.queries.clear();
          return this.onError(msg.message, msg.traceback);
      }
    };
    this.send({ type: "init", setup, zipUrl, pyodideUrl });
  }

  private send(msg: UiMsg): void {
    this.port.postMessage(JSON.stringify(msg));
  }

  private tick(t: TickInfo): void {
    this.last = t;
    this.speed = t.speed;
    for (const r of t.results) {
      this.pending.delete(r.id);
      this.onCmdResult(r);
    }
    this.onTick(t);
  }

  query<T = unknown>(kind: string, args: Json = {}): Promise<T> {
    const id = this.nextId++;
    return new Promise<T>((resolve, reject) => {
      this.queries.set(id, { resolve: resolve as (v: unknown) => void, reject });
      this.send({ type: "query", id, kind, args });
    });
  }

  command(kind: string, args: Json = {}): number {
    const id = this.nextId++;
    this.pending.add(id);
    this.send({ type: "cmd", id, kind, args });
    return id;
  }

  setSpeed(speed: Speed): void {
    this.speed = speed;
    this.send({ type: "speed", speed });
  }

  step(days = 1): void {
    this.send({ type: "step", days });
  }

  markNewsRead(daySerial: number): void {
    this.send({ type: "read_news", day_serial: daySerial });
  }
}
