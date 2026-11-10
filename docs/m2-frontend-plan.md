# Milestone 2: frontend technical plan

Status: proposal for review. Docs only, no code in this PR.

M1 is the baseline. M2 puts a playable browser frontend on the headless
sim without changing sim rules. Real sim bugs found during M2 get their own
PR. Art direction needs Esteban's approval before any production art.

## Measured baseline

Numbers measured on main `6d30f9c` on the team box (x86 server CPU), so a
phone will be slower. The phone figures below are estimates, not
measurements, until we test on real devices.

| Scenario | Native CPython | Pyodide 314.0.7 in Node |
|---|---|---|
| Bread chain, 1 town, 4 firms, per sim year | 0.6 to 0.8 s (about 2 ms/day) | 2.0 to 2.7 s (about 5 to 7 ms/day) |
| 15 bread chains, 60 firms, per sim year | 4.9 s (about 13.5 ms/day) | not measured, expect about 3x native |
| `state_hash()` / `report()` | 0.1 ms / under 0.1 ms | 1.1 ms / 0.3 ms |
| Pyodide boot, then pydantic plus our bundle | n/a | 1.3 s, then 0.3 s |
| Node process memory after boot and 2 sim years | n/a | 284 MB RSS |

Download size, gzip -9: `pyodide.asm.wasm` 3.5 MB, `python_stdlib.zip`
2.5 MB, `pyodide.asm.mjs` 0.26 MB, pydantic wheels 1.75 MB, our
`capitalism.zip` 0.09 MB. About 8.2 MB on first load, cacheable after.

Profiling the 60-firm run: about 90% of the tick is `Job.work` in
`jobs.py`, which checks every recipe input once per production cycle
(`any(...)` inside `for _ in range(cycles)`). That is a loop that can be
computed in one step (cycles = min over inputs of stock // qty). It is a
performance fix, not a rule change, and goes in its own PR with the golden
tests and state hashes checked unchanged.

## Stack

- **Build:** Vite plus TypeScript, static output only. No server.
- **Map renderer: PixiJS v8 (WebGL2, falls back to WebGL1/Canvas).** The
  map is 240 x 198 tiles (47,520). Pixi batches sprites from one atlas,
  handles pan/zoom on a GPU transform, and works on mobile browsers.
  Terrain is static, so it is drawn once into chunk render textures
  (for example 32 x 32 tiles per chunk) and only firms, roads and overlays
  redraw. The reference has three zooms (standard sprites, 2x2 close-up
  attribute overlay, 1x1 far overview); the 1x1 and 2x2 views are just a
  pixel buffer from tile data uploaded as one texture.
  - Plain Canvas2D was considered. It is enough for the far and overlay
    views, but zoomed-out standard view with tens of thousands of sprites
    is slow on phones without the same chunk caching Pixi gives us.
  - Phaser and other engines bring a game loop, physics and scenes we
    don't need, since the sim owns the loop.
- **UI panels: DOM (HTML/CSS) over the canvas, with Preact.** Firm detail,
  income statements, product and stock tables and news are text and
  tables. DOM gives crisp text at any DPI, scrolling, and accessibility,
  and keeps the canvas for the map only.

## Sim in a Web Worker

The sim runs in one dedicated module worker. The main thread never loads
Pyodide.

1. Worker boots Pyodide, loads pydantic, unpacks `capitalism.zip` into
   `/home/pyodide/sim` (same steps as `web/smoke.mjs`), imports a new
   `capitalism.api` facade.
2. The worker owns the clock. Speed settings (M1 moved them to the
   frontend) are a target days-per-second. The worker advances one day,
   posts the update, and waits for the next slot. Pause stops the loop.
   At max speed it runs as fast as it can and only posts every Nth day.
3. Player commands are queued and applied at the start of the next day,
   never mid-day. Each command is logged with its day serial. Seed plus
   command log replays to the same `state_hash()`, which gives us save
   games, bug repros and a desync check for free.
4. The UI stays responsive because a long day never blocks the main
   thread. If a day overruns its slot the game just runs slower.

`capitalism.api` is new code that only reads sim state and calls existing
entry points (`build_firm`, `link_b2b`, `link_consumer`, and so on). It
adds no rules. It returns plain dicts and lists, serialized once with
`json.dumps` and parsed on the JS side, which avoids per-field proxy cost
across the Pyodide boundary.

## Sim to UI API

Messages are JSON over `postMessage`, except the map, which goes as
transferable typed arrays.

**UI to worker (commands and queries):**

| Message | Purpose |
|---|---|
| `init {seed, setup}` | New game; returns map, towns, catalog, player corp id |
| `load {seed, setup, commands}` | Replay a save |
| `speed {days_per_sec}` / `pause` / `step {days}` | Clock control |
| `cmd {id, type, args}` | Build firm, place/remove job, link, set price, loan, buy shares, and so on. Reply `cmd_result {id, ok, error}` after the day it was applied |
| `query {id, kind, ref}` | Read a view: firm detail, town, product market, corp statement, stock, news page. Reply `query_result {id, data}` |
| `subscribe {kind, ref}` / `unsubscribe` | Get the open panel's view pushed every day instead of polling |

**Worker to UI:**

| Message | Contents |
|---|---|
| `map` (once, on init) | `Uint8Array`s for tile kind, climate, height, soil, plus town list. Transferred, not copied |
| `day` (each posted day) | Date, player cash and headline numbers, dirty firms (built, removed, changed sprite state), new news items, results of subscribed views |
| `month` / `year` | Statement rollups for charts |
| `error` | Python traceback, shown in a debug overlay |

Snapshots stay small because the UI only gets what changed plus the
panels it has open, not the whole economy each day.

## Asset pipeline

- Source art lives in `art/` (PNG or Aseprite files) to the Artist's spec.
  Tile size, palette and sprite list wait on the approved art direction.
  Placeholder colored tiles until then.
- A build script packs sprites into one atlas (`atlas.png` plus a JSON
  frame map) with fixed padding to avoid bleeding. A small Pillow script
  in `scripts/` keeps it in Python like the rest of the repo; a
  TexturePacker-style tool is fine too.
- Pixel art renders with nearest-neighbor filtering, `image-rendering:
  pixelated`, and integer zoom steps only (1x, 2x, 3x, 4x of device
  pixels) so pixels stay square. UI text is DOM, not baked into sprites.
- Sprite ids map to sim data (firm type, product class) through a table in
  the SQLite DB or a JSON manifest, not hardcoded in TS.

## GitHub Pages deploy

- New workflow `pages.yml` on push to `main` (and manual dispatch):
  build `capitalism.zip`, `npm ci`, `vite build`, copy the Pyodide core
  files and the pydantic wheels from `node_modules/pyodide` into `dist/`,
  then `actions/upload-pages-artifact` and `actions/deploy-pages`.
- Self-host Pyodide in the site instead of the jsDelivr CDN, so a deploy
  is pinned and works if the CDN is slow or blocked. Pages serves gzip.
- Vite `base` set to the repo path (`/capitalism-plus-plus/`).
- PRs keep running `build` and `pyodide-smoke`; add a headless-browser
  check that the built site boots and advances 10 days.
- One-time setup by the repo owner: Settings, Pages, source "GitHub
  Actions".

## Mobile performance risks

1. **First load and startup.** About 8.2 MB gzipped and 1.6 s boot on a
   desktop-class CPU; a mid-range phone on mobile data could take several
   seconds or more. Mitigations: show a loading screen with progress,
   cache with a service worker, and consider dropping pydantic at runtime
   (1.75 MB, plus its validation cost) by loading DB rows into plain
   classes in the browser build.
2. **Tick cost.** Pyodide was about 3x slower than native in our test, and
   phones are slower again. At 60 firms native is 13.5 ms/day, so a phone
   could be well over 100 ms/day before the `Job.work` fix. A full game
   with AI competitors will have many more firms. Mitigations: the
   `Job.work` fix first, then profile a large AI-populated game, cap max
   speed on slow devices, and keep Pydantic off the per-tick path as
   `code-style.md` says.
3. **Memory.** 284 MB RSS in Node after boot. iOS Safari kills tabs that
   use too much memory. Measure in real mobile browsers early; keep one
   Pyodide instance and avoid holding old snapshots.
4. **Serialization.** Converting Python objects to JS per field is slow.
   One JSON string per message, typed arrays for the map, and diffs only.
5. **Render cost and battery.** Chunk-cached terrain, render only on change
   or camera move (not a fixed 60 fps), and throttle when the tab is
   hidden.
6. **Touch input.** Pan, pinch-zoom and tap-to-select need hit targets
   bigger than one tile at low zoom, so selection snaps to the nearest firm.

## Order of work

1. `Job.work` performance PR (sim, hashes unchanged).
2. Worker plus `capitalism.api` facade, with a Node test that drives it.
3. Pixi map with placeholder tiles, pan/zoom, far and overlay views.
4. Pages workflow, so every merge is playable at the Pages URL.
5. Commands for build and link, plus firm and town panels.
6. Real art once the direction is approved.
