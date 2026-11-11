import { Application, Assets, Container, Rectangle, Texture } from "pixi.js";
import atlasUrl from "../../art/atlas/terrain_atlas.png?url";
import atlasJson from "../../art/atlas/terrain_atlas.json";
import atlas64Url from "../../art/atlas/terrain_atlas_64.png?url";
import atlas64Json from "../../art/atlas/terrain_atlas_64.json";
import { ChunkCache, TerrainOptions } from "./chunks";
import { FirmLayer } from "./firms";
import { CHUNK_TILES, TILE_PX, View, clampView, stepZoom } from "./chunkmath";
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

  // ?art=64 draws terrain from the 64 px set (frames it lacks fall back to the 32 px set).
  const art = params.get("art") === "64" ? 64 : 32;
  const terrain: TerrainOptions = {
    mode: params.get("mode") === "direct" ? "direct" : "baked",
    chunkTiles: Number(params.get("chunk") ?? CHUNK_TILES),
    artScale: art / TILE_PX,
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
  };
  const frames: Record<string, Texture> = {};
  await loadAtlas(atlasUrl, atlasJson as AtlasJson, frames);
  const terrainFrames: Record<string, Texture> = { ...frames };
  if (art === 64) await loadAtlas(atlas64Url, atlas64Json as AtlasJson, terrainFrames);

  const map = parseMap(await (await fetch("./sample-map.bin")).arrayBuffer());
  const chunks = new ChunkCache(app.renderer, map, terrainFrames, terrain);
  const firms = new FirmLayer(map.firms, frames);
  const world = new Container();
  world.addChild(chunks.layer, firms.layer);
  app.stage.addChild(world);

  const screen = () => ({ w: app.screen.width * resolution, h: app.screen.height * resolution });
  let view: View = {
    x: Number(params.get("x") ?? 100) * TILE_PX,
    y: Number(params.get("y") ?? 99) * TILE_PX,
    zoom: Math.max(1, Math.min(3, Math.round(Number(params.get("zoom") ?? 1)))),
    ...screen(),
  };

  const hud = document.getElementById("hud")!;
  const apply = () => {
    view = clampView({ ...view, ...screen() }, map.width, map.height);
    chunks.update(view);
    firms.update(view);
    const s = view.zoom / resolution;
    world.scale.set(s);
    world.position.set(-view.x * s, -view.y * s);
    const stats = {
      zoom: view.zoom,
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
    hud.textContent = `${stats.mode} ${art} px · zoom ${stats.zoom}x · ${stats.tilesAcross} tiles across · ${stats.chunks} chunks · ${stats.mb} MB GPU · ${stats.firms} firms`;
    (window as unknown as { __cppStats: typeof stats }).__cppStats = stats;
  };

  // Pan with one pointer; zoom with the wheel, pinch or the buttons, in whole-number steps.
  const pointers = new Map<number, { x: number; y: number }>();
  let pinchStart = 0;
  app.canvas.addEventListener("pointerdown", (e) => {
    app.canvas.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointers.size === 2) pinchStart = pinchDistance();
  });
  app.canvas.addEventListener("pointermove", (e) => {
    const p = pointers.get(e.pointerId);
    if (!p) return;
    if (pointers.size === 1) {
      view = { ...view, x: view.x - ((e.clientX - p.x) * resolution) / view.zoom, y: view.y - ((e.clientY - p.y) * resolution) / view.zoom };
      apply();
    }
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointers.size === 2 && pinchStart) {
      const d = pinchDistance();
      if (d / pinchStart > 1.4 || d / pinchStart < 0.7) {
        view = stepZoom(view, d > pinchStart ? 1 : -1);
        pinchStart = d;
        apply();
      }
    }
  });
  const up = (e: PointerEvent) => {
    pointers.delete(e.pointerId);
    if (pointers.size < 2) pinchStart = 0;
  };
  app.canvas.addEventListener("pointerup", up);
  app.canvas.addEventListener("pointercancel", up);
  function pinchDistance() {
    const [a, b] = [...pointers.values()];
    return Math.hypot(a.x - b.x, a.y - b.y);
  }
  app.canvas.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      view = stepZoom(view, e.deltaY < 0 ? 1 : -1, e.clientX * resolution, e.clientY * resolution);
      apply();
    },
    { passive: false },
  );
  document.getElementById("zoom-in")!.onclick = () => ((view = stepZoom(view, 1)), apply());
  document.getElementById("zoom-out")!.onclick = () => ((view = stepZoom(view, -1)), apply());
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
