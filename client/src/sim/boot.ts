import type { Json } from "./protocol.ts";
import type { PyApi } from "./engine.ts";

/** The parts of a Pyodide instance boot uses (typed loosely so the npm types aren't needed). */
export interface PyodideLike {
  loadPackage(names: string[]): Promise<unknown>;
  unpackArchive(buffer: Uint8Array, format: string, options: { extractDir: string }): void;
  runPython(code: string): unknown;
  globals: { get(name: string): unknown };
}

export type Progress = (stage: string, done: number, total: number) => void;

const GLUE = `
import json, sys
sys.path.insert(0, "/home/pyodide/sim")
from capitalism.api import Api

_api = Api.new_game(**json.loads(_setup_json))

def _tick(days, read_since):
    return json.dumps(_api.tick(int(days), int(read_since)))

def _status(read_since):
    return json.dumps(_api.status(int(read_since)))

def _query(kind, args):
    return json.dumps(_api.query(kind, json.loads(args)))

def _command(kind, args):
    return json.dumps(_api.command(kind, json.loads(args)))
`;

/**
 * Same steps as web/smoke.mjs: load pydantic, unpack capitalism.zip into
 * /home/pyodide/sim, then create the game through `capitalism.api.Api.new_game(**setup)`.
 */
export async function bootSim(py: PyodideLike, zip: Uint8Array, setup: Json, progress: Progress = () => {}): Promise<PyApi> {
  progress("Loading Python packages", 2, 4);
  await py.loadPackage(["pydantic"]);
  progress("Unpacking the sim", 3, 4);
  py.unpackArchive(zip, "zip", { extractDir: "/home/pyodide/sim" });
  progress("Creating the world", 4, 4);
  py.runPython(`_setup_json = ${JSON.stringify(JSON.stringify(setup))}`);
  py.runPython(GLUE);
  const fn = (name: string) => py.globals.get(name) as (...a: unknown[]) => string;
  const tick = fn("_tick");
  const status = fn("_status");
  const query = fn("_query");
  const command = fn("_command");
  return {
    tick: (days, readSince) => tick(days, readSince),
    status: (readSince) => status(readSince),
    query: (kind, args) => query(kind, args),
    command: (kind, args) => command(kind, args),
  };
}
