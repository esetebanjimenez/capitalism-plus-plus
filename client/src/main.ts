import { Application, Assets, Container, Rectangle, Texture } from "pixi.js";
import atlasUrl from "../../art/atlas/terrain_atlas.png?url";
import atlasJson from "../../art/atlas/terrain_atlas.json";
import atlas64Url from "../../art/atlas/terrain_atlas_64.png?url";
import atlas64Json from "../../art/atlas/terrain_atlas_64.json";
import { ChunkCache, TerrainOptions } from "./chunks";
import { FirmLayer } from "./firms";
import { CHUNK_TILES, STANDARD_STEP, TILE_PX, View, clampView, makeView, sheetFor } from "./chunkmath";
import { parseMap } from "./mapdata";

interface AtlasJson {
  tile: number;
  frames: Record<string, { x: number; y: number; w: number; h: number }>;
}

async function boot() {
  const params = new URLSearchParams(location.search);
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
  const frames64: Record<string, Texture> = { ...frames32 };
  const source64 = await loadAtlas(atlas64Url, atlas64Json as AtlasJson, frames64);
  const texels = (t: Texture) => (t.source === source64 ? 2 : 1);
  const sheets = { 32: frames32, 64: frames64 } as const;

  const map = parseMap(await (await fetch("./sample-map.bin")).arrayBuffer());
  const chunks = new ChunkCache(app.renderer, map, frames32, terrain);
  const firms = new FirmLayer(map.firms, frames32, texels);
  const world = new Container();
  world.addChild(chunks.layer, firms.layer);
  app.stage.addChild(world);

  const screen = () => ({ w: app.screen.width * resolution, h: app.screen.height * resolution });
  let view: View = makeView(
    Number(params.get("x") ?? 100) * TILE_PX,
    Number(params.get("y") ?? 99) * TILE_PX,
    0,
    0,
    STANDARD_STEP,
    resolution,
  );
  let art: 32 | 64 = 32;

  const hud = document.getElementById("hud")!;
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

  // Pan with one pointer or the mouse. There is one map view (32 pt tiles), so no zoom input.
  let drag: { id: number; x: number; y: number } | null = null;
  app.canvas.addEventListener("pointerdown", (e) => {
    if (drag) return;
    app.canvas.setPointerCapture(e.pointerId);
    drag = { id: e.pointerId, x: e.clientX, y: e.clientY };
  });
  app.canvas.addEventListener("pointermove", (e) => {
    if (!drag || drag.id !== e.pointerId) return;
    view = { ...view, x: view.x - ((e.clientX - drag.x) * resolution) / view.zoom, y: view.y - ((e.clientY - drag.y) * resolution) / view.zoom };
    drag = { id: e.pointerId, x: e.clientX, y: e.clientY };
    apply();
  });
  const up = (e: PointerEvent) => {
    if (drag?.id === e.pointerId) drag = null;
  };
  app.canvas.addEventListener("pointerup", up);
  app.canvas.addEventListener("pointercancel", up);
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
