// Self-hosts Pyodide for the site (#247): copies the core files from the pinned `pyodide`
// npm package into public/pyodide/ and downloads the wheels the sim needs (pydantic and
// its dependencies, from pyodide-lock.json), checking each wheel's sha256. Wheels already
// present with the right hash are kept, so repeat builds don't download again.
// Usage: node scripts/fetch-pyodide.mjs   (runs before `npm run dev` and `npm run build`)
import { createHash } from "node:crypto";
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/** Top-level packages bootSim loads; their dependencies are added from the lock file. */
const PACKAGES = ["pydantic"];
const CORE = ["pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"];

const require = createRequire(import.meta.url);
const src = dirname(require.resolve("pyodide/package.json"));
const { version } = JSON.parse(readFileSync(join(src, "package.json"), "utf8"));
const out = fileURLToPath(new URL("../public/pyodide/", import.meta.url));
mkdirSync(out, { recursive: true });

for (const f of CORE) copyFileSync(join(src, f), join(out, f));

const lock = JSON.parse(readFileSync(join(src, "pyodide-lock.json"), "utf8"));
const want = new Set();
const visit = (name) => {
  const key = name.toLowerCase().replace(/[._]/g, "-");
  if (want.has(key)) return;
  const pkg = lock.packages[key];
  if (!pkg) throw new Error(`${name} is not in pyodide-lock.json ${version}`);
  want.add(key);
  for (const d of pkg.depends ?? []) visit(d);
};
PACKAGES.forEach(visit);

const sha256 = (buf) => createHash("sha256").update(buf).digest("hex");
const cdn = `https://cdn.jsdelivr.net/pyodide/v${version}/full/`;
let fetched = 0;
for (const key of [...want].sort()) {
  const { file_name: file, sha256: hash } = lock.packages[key];
  const dest = join(out, file);
  if (existsSync(dest) && sha256(readFileSync(dest)) === hash) continue;
  const r = await fetch(cdn + file);
  if (!r.ok) throw new Error(`${cdn + file}: HTTP ${r.status}`);
  const buf = Buffer.from(await r.arrayBuffer());
  if (sha256(buf) !== hash) throw new Error(`${file}: sha256 does not match pyodide-lock.json`);
  writeFileSync(dest, buf);
  fetched++;
}
console.log(`pyodide ${version}: core + ${want.size} wheels (${[...want].join(", ")}) in public/pyodide/, ${fetched} downloaded`);
