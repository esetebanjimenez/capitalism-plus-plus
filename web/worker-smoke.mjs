// Drives the client's real sim-worker logic (client/src/sim/engine.ts + boot.ts) under the
// pinned Pyodide, without a browser: init, 10 days, one build_firm that succeeds and one
// that fails with a reason. Usage (from the repo root, Node 24 strips the TypeScript types):
//   python scripts/pyodide_bundle.py && npm install --prefix web && node web/worker-smoke.mjs
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { loadPyodide } from "pyodide";
import { bootSim } from "../client/src/sim/boot.ts";
import { Engine } from "../client/src/sim/engine.ts";
import { DEFAULT_SETUP } from "../client/src/sim/setup.ts";

const here = new URL(".", import.meta.url);
const zip = new Uint8Array(await readFile(new URL("capitalism.zip", here)));
const py = await loadPyodide();
const api = await bootSim(py, zip, DEFAULT_SETUP);

const out = [];
const engine = new Engine(api, (m) => out.push(m));
const ticks = () => out.filter((m) => m.type === "tick").map((m) => m.tick);
const status = engine.status();
assert.equal(status.day_serial >= 0, true);

engine.handleMsg({ type: "step", days: 10 });
assert.equal(ticks().length, 10);
assert.equal(ticks().at(-1).day_serial, status.day_serial + 10);

// A free tile next to the first town, found the same way the Python tests do.
const [x, y] = JSON.parse(
  py.runPython("import json\nfrom capitalism.scenario import find_site\njson.dumps(find_site(_api.sim, _api.sim.towns[0]))"),
);
engine.handleMsg({ type: "cmd", id: 1, kind: "build_firm", args: { firm_type: 4, x, y } });
engine.handleMsg({ type: "cmd", id: 2, kind: "build_firm", args: { firm_type: 4, x: -5, y: -5 } });
engine.handleMsg({ type: "step", days: 1 });
const { results } = ticks().at(-1);
assert.equal(results.length, 2);
assert.deepEqual(results[0].id, 1);
assert.equal(results[0].ok, true, JSON.stringify(results[0]));
assert.equal(results[1].id, 2);
assert.equal(results[1].ok, false);
assert.match(results[1].error, /can't build/);
assert.equal(out.some((m) => m.type === "error"), false);
console.log(`PASS worker day ${ticks().at(-1).day_serial}, built firm ${results[0].result.firm}, refused: ${results[1].error}`);
