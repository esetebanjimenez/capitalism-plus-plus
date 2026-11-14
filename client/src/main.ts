import { Application, Assets, Container, Rectangle, Sprite, Texture } from "pixi.js";
import atlasUrl from "../../art/atlas/terrain_atlas.png?url";
import atlasJson from "../../art/atlas/terrain_atlas.json";
import atlas64Url from "../../art/atlas/terrain_atlas_64.png?url";
import atlas64Json from "../../art/atlas/terrain_atlas_64.json";
import marksUrl from "../../art/atlas/marks_atlas.png?url";
import marksJson from "../../art/atlas/marks_atlas.json";
import marks64Url from "../../art/atlas/marks_atlas_64.png?url";
import marks64Json from "../../art/atlas/marks_atlas_64.json";
import { ChunkCache, TerrainOptions } from "./chunks";
import { FIRM_NAMES, FirmLayer } from "./firms";
import { CHUNK_TILES, STANDARD_STEP, TILE_PX, View, clampView, makeView, sheetFor } from "./chunkmath";
import { MapData, MapJson, MapObjectsJson, applyMapObjects, mapFromJson, parseMap } from "./mapdata";
import { loadUiAtlas } from "./ui/atlas";
import { showChartDemo } from "./ui/chartdemo";
import { TileJson, firmCard, menuPanel, sampleTile, tileCard, townCard } from "./ui/cards";
import { CorpJson, ReportState, companyReport } from "./ui/company";
import { showCompanyDemo } from "./ui/companydemo";
import { Pick, isDesktop, panToShow, pickAt, visibleMapRect } from "./ui/layout";
import { LoadingOverlay, showSimError } from "./ui/overlay";
import { Shell } from "./ui/shell";
import { SimClient, type WorkerPort } from "./sim/client";
import type { Speed } from "./sim/protocol";
import { m2TestSetup, randomSeed } from "./sim/setup";

interface AtlasJson {
  tile: number;
  frames: Record<string, { x: number; y: number; w: number; h: number }>;
}

async function boot() {
  const params = new URLSearchParams(location.search);
  if (params.get("chart") === "demo") {
    await showChartDemo(Math.max(1, Math.round(devicePixelRatio)));
    document.title = "Capitalism++ chart ready";
    return;
  }
  if (params.get("company") === "demo") {
    await showCompanyDemo(Math.max(1, Math.round(devicePixelRatio)), params.get("firm") === "1", params);
    document.title = "Capitalism++ company ready";
    return;
  }
  const app = new Application();
  const resolution = Math.max(1, Math.round(devicePixelRatio));
  await app.init({
    resizeTo: window,
    background: "#10131a",
    antialias: false,
    resolution,
    autoDensity: true,
    preference: "webgl",
  });
  document.getElementById("map")!.appendChild(app.canvas);

  // Art sheet: by default the 64 px sheet once a tile spans 64+ canvas px, else the 32 px
  // sheet (sheetFor). ?art=32 or ?art=64 forces one. Frames missing from the 64 px sheet
  // fall back to their 32 px versions (same frame names).
  const artParam = params.get("art");
  const forced = artParam === "32" ? 32 : artParam === "64" ? 64 : null;
  const terrain: TerrainOptions = {
    // Default: tiles drawn straight from the atlas (about 4 MB of GPU memory with both
    // sheets, against about 100 MB of baked 64 px chunks on a 3x phone). ?mode=baked compares.
    mode: params.get("mode") === "baked" ? "baked" : "direct",
    chunkTiles: Number(params.get("chunk") ?? (params.get("mode") === "baked" ? CHUNK_TILES : 16)),
    artScale: 1,
    marginPx: Number(params.get("margin") ?? 8) * TILE_PX,
  };
  let atlasBytes = 0;
  const loadAtlas = async (url: string, json: AtlasJson, into: Record<string, Texture>) => {
    const base: Texture = await Assets.load({ src: url, data: { scaleMode: "nearest" } });
    base.source.scaleMode = "nearest";
    atlasBytes += base.source.pixelWidth * base.source.pixelHeight * 4;
    for (const [name, f] of Object.entries(json.frames)) {
      into[name] = new Texture({ source: base.source, frame: new Rectangle(f.x, f.y, f.w, f.h) });
    }
    return base.source;
  };
  const frames32: Record<string, Texture> = {};
  await loadAtlas(atlasUrl, atlasJson as AtlasJson, frames32);
  await loadAtlas(marksUrl, marksJson as AtlasJson, frames32);
  const frames64: Record<string, Texture> = { ...frames32 };
  const source64 = await loadAtlas(atlas64Url, atlas64Json as AtlasJson, frames64);
  const marks64 = await loadAtlas(marks64Url, marks64Json as AtlasJson, frames64);
  const texels = (t: Texture) => (t.source === source64 || t.source === marks64 ? 2 : 1);
  const sheets = { 32: frames32, 64: frames64 } as const;

  // Panels (docs/m2-ux-spec.md): status pill, menu button, one panel at a time.
  await loadUiAtlas(resolution);
  const shell = new Shell(document.body);
  const sim = startSim(shell);
  // The live sim's map by default; ?map=sample draws the static sample map instead
  // (tests, `npm run bench` and the screenshot script, which need a fixed map).
  const sample = params.get("map") === "sample";
  const map: MapData = sample
    ? parseMap(await (await fetch("./sample-map.bin")).arrayBuffer())
    : (await sim.ready, mapFromJson(await sim.query<MapJson>("map")));
  const home = map.towns[0] ?? { x: 100, y: 99 };
  const chunks = new ChunkCache(app.renderer, map, frames32, terrain);
  const firms = new FirmLayer(map.firms, frames32, texels);
  const world = new Container();
  // Selection outline (marks atlas `sel_tile`, art PR #70) on the chosen tile.
  const selection = new Sprite(frames32.sel_tile);
  selection.visible = false;
  world.addChild(chunks.layer, firms.layer, selection);
  app.stage.addChild(world);

  const screen = () => ({ w: app.screen.width * resolution, h: app.screen.height * resolution });
  let view: View = makeView(
    Number(params.get("x") ?? home.x) * TILE_PX,
    Number(params.get("y") ?? home.y) * TILE_PX,
    0,
    0,
    STANDARD_STEP,
    resolution,
  );
  let art: 32 | 64 = 32;

  const hud = document.getElementById("hud")!;
  hud.hidden = params.get("hud") !== "1"; // renderer stats, for device checks: ?hud=1
  const hudInfo = document.createElement("span");
  const hudPerf = document.createElement("span");
  hud.replaceChildren(hudInfo, document.createElement("br"), hudPerf);

  // On-screen frame time for real-device checks: average frame interval over the last
  // 60 frames (capped by the screen's refresh rate) and the CPU time of the render call.
  const frameMs: number[] = [];
  const renderMs: number[] = [];
  const push = (a: number[], v: number) => (a.push(v), a.length > 60 && a.shift());
  const avg = (a: number[]) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
  const render = app.render.bind(app);
  app.render = () => {
    const t0 = performance.now();
    render();
    push(renderMs, performance.now() - t0);
  };
  app.ticker.add((t) => push(frameMs, t.deltaMS));
  setInterval(() => {
    const f = avg(frameMs);
    hudPerf.textContent = `${f.toFixed(1)} ms/frame (${f ? Math.round(1000 / f) : 0} fps) · render ${avg(renderMs).toFixed(1)} ms · ${devicePixelRatio}× screen`;
  }, 500);
  const apply = () => {
    view = clampView({ ...view, ...screen() }, map.width, map.height);
    art = forced ?? sheetFor(view.zoom);
    chunks.setFrames(sheets[art], art / TILE_PX);
    firms.setFrames(sheets[art], texels);
    chunks.update(view);
    firms.update(view);
    selection.texture = sheets[art].sel_tile;
    selection.scale.set(1 / texels(selection.texture));
    const s = view.zoom / resolution;
    world.scale.set(s);
    world.position.set(-view.x * s, -view.y * s);
    const stats = {
      zoom: view.step,
      pxPerArtPx: view.zoom,
      tilesAcross: +(view.w / view.zoom / TILE_PX).toFixed(1),
      chunks: chunks.count,
      mode: terrain.mode,
      art,
      chunkTiles: terrain.chunkTiles,
      mb: +((chunks.bytes + atlasBytes) / 2 ** 20).toFixed(1),
      sprites: chunks.sprites,
      baked: chunks.baked,
      firms: firms.visibleCount,
    };
    hudInfo.textContent = `${stats.mode} ${art} px · ${view.zoom}x · ${stats.tilesAcross} tiles across · ${stats.chunks} chunks · ${stats.mb} MB GPU · ${stats.firms} firms`;
    (window as unknown as { __cppStats: typeof stats }).__cppStats = stats;
  };

  if (sample && map.info) shell.setStatus(map.info.year, map.info.month, map.info.day, map.info.cash);

  // Live map (#249): when map_rev moves, fetch the changes and rebuild only the chunks
  // and firm sprites they touch. One request at a time; a newer rev is caught next tick.
  let fetching = false;
  const refreshMap = async () => {
    if (fetching) return;
    fetching = true;
    try {
      const o = await sim.query<MapObjectsJson>("map_objects", { since: map.rev });
      const delta = applyMapObjects(map, o);
      chunks.invalidate(delta.tiles);
      if (delta.firms) firms.setFirms(map.firms);
      apply();
    } finally {
      fetching = false;
    }
  };
  if (!sample) {
    const onTick = sim.onTick;
    sim.onTick = (t) => {
      onTick(t);
      if (t.map_rev !== map.rev) void refreshMap();
    };
  }
  // Company report (#257): Menu > Company or C on desktop; refreshes each month while open.
  let report: ReportState = { tab: "Income", byFirm: false };
  const firmById = (id: number) => map.firms.find((f) => f.id === id);
  let today = { year: 1990, month: 1 };
  const showCompany = async () => {
    const corp = await sim.query<CorpJson>("corp", { id: 0 });
    shell.open(
      companyReport(corp, report, {
        today,
        chartWidth: isDesktop(window.innerWidth) ? 352 : Math.min(480, window.innerWidth - 48),
        firmLabel: (id) => `${FIRM_NAMES[firmById(id)?.type ?? -1] ?? "Firm"} #${id}`,
        onFirm: (id) => {
          const f = firmById(id);
          if (f) select({ kind: "firm", firm: f });
        },
        onState: (s) => ((report = s), void showCompany()),
      }),
    );
  };
  let reportMonth = -1;
  const onTickReport = sim.onTick;
  sim.onTick = (t) => {
    onTickReport(t);
    today = { year: t.year, month: t.month };
    const month = t.year * 12 + t.month;
    if (month !== reportMonth && reportMonth >= 0 && shell.current?.key === "company") void showCompany();
    reportMonth = month;
  };
  window.addEventListener("keydown", (e) => {
    const t = e.target as HTMLElement | null;
    if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA")) return;
    if ((e.key === "c" || e.key === "C") && isDesktop(window.innerWidth) && !e.metaKey && !e.ctrlKey) void showCompany();
  });
  shell.onMenu = () =>
    shell.open(
      menuPanel((name) => (name === "Company" ? void showCompany() : (shell.close(), shell.toast(`${name} comes in a later PR.`)))),
    );
  let selected: { x: number; y: number } | null = null;
  const ptPerWorld = () => view.zoom / resolution;
  const showSelection = () => {
    const open = shell.current && selected && !shell.current.key.startsWith("menu");
    selection.visible = Boolean(open);
    if (open) selection.position.set(selected!.x * TILE_PX, selected!.y * TILE_PX);
  };
  shell.onLayout = (h) => {
    if (h && selected && shell.current?.key !== "menu") {
      const rect = visibleMapRect(window.innerWidth, window.innerHeight, h);
      const [dx, dy] = panToShow(view, selected.x, selected.y, rect, ptPerWorld());
      if (dx || dy) view = { ...view, x: view.x + dx, y: view.y + dy };
    }
    if (!h) selected = null;
    showSelection();
    apply();
  };
  const select = (p: Pick) => {
    if (p.kind === "none") return shell.close();
    if (p.kind === "firm") {
      selected = { x: p.firm.x, y: p.firm.y };
      shell.open(firmCard(p.firm));
    } else if (p.kind === "town") {
      selected = { x: p.town.x, y: p.town.y };
      shell.open(townCard(p.town));
    } else {
      selected = { x: p.x, y: p.y };
      const onBuild = () => shell.toast("The build menu comes in a later PR.");
      const tile: Promise<TileJson> = sample ? Promise.resolve(sampleTile(map, p.x, p.y)) : sim.query<TileJson>("tile", { x: p.x, y: p.y });
      tile.then((t) => selected?.x === t.x && selected.y === t.y && shell.open(tileCard(t, onBuild)));
    }
  };

  // Pan with one pointer or the mouse; a short press that barely moves is a tap.
  let drag: { id: number; x: number; y: number; x0: number; y0: number; t0: number } | null = null;
  app.canvas.addEventListener("pointerdown", (e) => {
    if (drag) return;
    app.canvas.setPointerCapture(e.pointerId);
    drag = { id: e.pointerId, x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY, t0: performance.now() };
  });
  app.canvas.addEventListener("pointermove", (e) => {
    if (!drag || drag.id !== e.pointerId) return;
    view = { ...view, x: view.x - ((e.clientX - drag.x) * resolution) / view.zoom, y: view.y - ((e.clientY - drag.y) * resolution) / view.zoom };
    drag = { ...drag, x: e.clientX, y: e.clientY };
    apply();
  });
  const up = (e: PointerEvent) => {
    if (drag?.id !== e.pointerId) return;
    const tap = Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) < 8 && performance.now() - drag.t0 < 500;
    drag = null;
    if (tap && e.type === "pointerup") {
      const s = resolution / view.zoom;
      select(pickAt(map, view.x + e.clientX * s, view.y + e.clientY * s, ptPerWorld()));
    }
  };
  app.canvas.addEventListener("pointerup", up);
  app.canvas.addEventListener("pointercancel", up);
  (window as unknown as { __tap: (x: number, y: number) => void }).__tap = (x, y) => {
    const s = resolution / view.zoom;
    select(pickAt(map, view.x + x * s, view.y + y * s, ptPerWorld()));
  };
  window.addEventListener("resize", apply);
  apply();

  // Benchmark hook for scripts/bench.mjs: pan `frames` frames by `step` art px and time
  // each update + render, including GPU work (a 1-pixel readback waits for it).
  (window as unknown as { __bench: unknown }).__bench = (frames: number, step: number) => {
    app.ticker.stop();
    const gl = (app.renderer as unknown as { gl?: WebGLRenderingContext }).gl;
    const px = new Uint8Array(4);
    const times: number[] = [];
    let dir = 1;
    for (let i = 0; i < frames; i++) {
      const t0 = performance.now();
      const before = view.x;
      view = { ...view, x: view.x + dir * step };
      apply();
      if (view.x === before) dir = -dir;
      app.renderer.render(app.stage);
      gl?.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); // waits for the GPU
      times.push(performance.now() - t0);
    }
    times.sort((a, b) => a - b);
    const mem = (performance as unknown as { memory?: { usedJSHeapSize: number } }).memory;
    return {
      avgMs: +(times.reduce((a, b) => a + b, 0) / frames).toFixed(2),
      medianMs: +times[Math.floor(frames / 2)].toFixed(2),
      gl: Boolean(gl),
      p95Ms: +times[Math.floor(frames * 0.95)].toFixed(2),
      maxMs: +times[frames - 1].toFixed(2),
      jsHeapMb: mem ? +(mem.usedJSHeapSize / 2 ** 20).toFixed(1) : null,
    };
  };
  document.title = "Capitalism++ map ready";
}

boot().catch((err) => {
  document.title = "Capitalism++ map failed";
  document.getElementById("hud")!.textContent = String(err);
  throw err;
});

/**
 * Boots the sim worker and wires the status pill, speed controls and keyboard to it
 * (docs/m2-ux-spec.md "Shared rules" and "Default state").
 */
function startSim(shell: Shell): SimClient {
  const loading = new LoadingOverlay();
  const worker = new Worker(new URL("./sim/worker.ts", import.meta.url), { type: "module" });
  const sim = new SimClient(worker as unknown as WorkerPort, m2TestSetup(randomSeed()), new URL("capitalism.zip", document.baseURI).href,
    new URL("pyodide/", document.baseURI).href,
  );
  (window as unknown as { __sim: SimClient }).__sim = sim;
  let resumeTo: Speed = 1;
  const setSpeed = (s: Speed) => {
    if (s !== 0) resumeTo = s;
    sim.setSpeed(s);
    shell.setSpeed(s);
  };
  sim.onProgress = (stage, done, total) => loading.set(stage, done, total);
  sim.onTick = (t) => {
    shell.setStatus(t.year, t.month, t.day, t.cash);
    shell.setSpeed(t.speed);
    shell.setBadge(t.unread_important);
  };
  sim.onCmdResult = (r) => {
    if (!r.ok) shell.toast(r.error ?? "That didn't work.", "error");
  };
  sim.onError = (message, traceback) => {
    loading.remove();
    showSimError(message, traceback);
  };
  sim.ready.then((t) => {
    loading.remove();
    sim.onTick(t);
    document.title = "Capitalism++";
  });
  shell.setSpeed(0);
  shell.onSpeed = () => setSpeed(sim.speed === 0 ? resumeTo : 0);
  shell.onSpeedPick = (s) => setSpeed(s);
  window.addEventListener("keydown", (e) => {
    const t = e.target as HTMLElement | null;
    if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
    if (e.key === " ") {
      e.preventDefault();
      shell.onSpeed();
    } else if (e.key >= "1" && e.key <= "4") {
      setSpeed(Number(e.key) as Speed);
    }
  });
  return sim;
}
