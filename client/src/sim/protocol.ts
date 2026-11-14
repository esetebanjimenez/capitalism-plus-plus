// Messages between the main thread and the sim worker (docs/m2-frontend-plan.md
// "Sim to UI API", docs/m2-facade-contract.md "Conventions"). Each message crosses
// postMessage as one JSON string.

/** 0 = paused, 1–3 = the three speeds, 4 = max. */
export type Speed = 0 | 1 | 2 | 3 | 4;

export type Json = Record<string, unknown>;

export interface CmdResult {
  id: number;
  ok: boolean;
  result?: unknown;
  error?: string;
}

export interface TickInfo {
  day_serial: number;
  year: number;
  month: number;
  day: number;
  cash: number;
  speed: Speed;
  unread_important: number;
  /** Bumps when firms or town tiles change; the map then asks `map_objects` (#248). */
  map_rev: number;
  results: CmdResult[];
}

export type UiMsg =
  | { type: "init"; setup: Json; zipUrl: string }
  | { type: "speed"; speed: Speed }
  | { type: "step"; days: number }
  | { type: "read_news"; day_serial: number }
  | { type: "cmd"; id: number; kind: string; args: Json }
  | { type: "query"; id: number; kind: string; args: Json };

export type WorkerMsg =
  | { type: "progress"; stage: string; done: number; total: number }
  | { type: "ready"; status: TickInfo }
  | { type: "tick"; tick: TickInfo }
  | { type: "query_result"; id: number; ok: boolean; data?: unknown; error?: string }
  | { type: "error"; message: string; traceback: string };
