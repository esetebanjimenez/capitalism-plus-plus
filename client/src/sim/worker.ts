/// <reference lib="webworker" />
// The sim's module worker (docs/m2-frontend-plan.md "Sim in a Web Worker"). The main
// thread never loads Pyodide; it talks to this file through client.ts.
import { bootSim, type PyodideLike } from "./boot.ts";
import { Engine, errorMsg } from "./engine.ts";
import type { UiMsg, WorkerMsg } from "./protocol.ts";

// Pyodide is self-hosted next to the site (client/public/pyodide/, written by
// scripts/fetch-pyodide.mjs at the version pinned in package.json), not loaded from a CDN.

const scope = self as unknown as DedicatedWorkerGlobalScope;
const post = (msg: WorkerMsg) => scope.postMessage(JSON.stringify(msg));
let engine: Engine | null = null;
const early: UiMsg[] = [];

async function init(setup: Record<string, unknown>, zipUrl: string, indexURL: string) {
  post({ type: "progress", stage: "Loading Python", done: 0, total: 4 });
  const [mod, zip] = await Promise.all([
    import(/* @vite-ignore */ `${indexURL}pyodide.mjs`) as Promise<{ loadPyodide(o: { indexURL: string }): Promise<PyodideLike> }>,
    fetch(zipUrl).then((r) => {
      if (!r.ok) throw new Error(`Couldn't load ${zipUrl}: HTTP ${r.status}`);
      return r.arrayBuffer();
    }),
  ]);
  const py = await mod.loadPyodide({ indexURL });
  post({ type: "progress", stage: "Python ready", done: 1, total: 4 });
  const api = await bootSim(py, new Uint8Array(zip), setup, (stage, done, total) => post({ type: "progress", stage, done, total }));
  engine = new Engine(api, post);
  post({ type: "ready", status: engine.status() });
  for (const m of early.splice(0)) engine.handleMsg(m);
}

scope.onmessage = (e: MessageEvent<string>) => {
  const msg = JSON.parse(e.data) as UiMsg;
  if (msg.type === "init") {
    init(msg.setup, msg.zipUrl, msg.pyodideUrl).catch((err) => post(errorMsg(err)));
  } else if (engine) {
    engine.handleMsg(msg);
  } else {
    early.push(msg);
  }
};
