// Node runner for the Pyodide smoke test. Usage (from the repo root):
//   python scripts/pyodide_bundle.py && npm install --prefix web && node web/smoke.mjs
import { readFile } from "node:fs/promises";
import { loadPyodide } from "pyodide";

const here = new URL(".", import.meta.url);
const bundle = await readFile(new URL("capitalism.zip", here));
const smoke = await readFile(new URL("smoke.py", here), "utf8");

const pyodide = await loadPyodide();
await pyodide.loadPackage(["pydantic"]);
pyodide.unpackArchive(new Uint8Array(bundle), "zip", { extractDir: "/home/pyodide/sim" });
pyodide.runPython("import sys; sys.path.insert(0, '/home/pyodide/sim')");
const result = await pyodide.runPythonAsync(smoke);
console.log(`PASS ${result}`);
