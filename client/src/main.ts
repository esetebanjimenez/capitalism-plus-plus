import { Application, Assets, Container, Rectangle, Texture } from "pixi.js";
import atlasUrl from "../../art/atlas/terrain_atlas.png?url";
import atlasJson from "../../art/atlas/terrain_atlas.json";
import { ChunkCache } from "./chunks";
import { FirmLayer } from "./firms";
import { TILE_PX, View, clampView, stepZoom } from "./chunkmath";
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

  const base: Texture = await Assets.load({ src: atlasUrl, data: { scaleMode: "nearest" } });
  base.source.scaleMode = "nearest";
  const atlas = atlasJson as AtlasJson;
  const frames: Record<string, Texture> = {};
  for (const [name, f] of Object.entries(atlas.frames)) {
    frames[name] = new Texture({ source: base.source, frame: new Rectangle(f.x, f.y, f.w, f.h) });
  }

  const map = parseMap(await (await fetch("./sample-map.bin")).arrayBuffer());
  const chunks = new ChunkCache(app.renderer, map, frames, Number(params.get("margin") ?? 8) * TILE_PX);
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
      mb: +(chunks.bytes / 2 ** 20).toFixed(0),
      baked: chunks.baked,
      firms: firms.visibleCount,
    };
    hud.textContent = `zoom ${stats.zoom}x · ${stats.tilesAcross} tiles across · ${stats.chunks} chunks (${stats.mb} MB) · baked ${stats.baked} · ${stats.firms} firms`;
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
  document.title = "Capitalism++ map ready";
}

boot().catch((err) => {
  document.title = "Capitalism++ map failed";
  document.getElementById("hud")!.textContent = String(err);
  throw err;
});
