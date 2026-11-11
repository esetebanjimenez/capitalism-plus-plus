import { Container, Renderer, RenderTexture, Sprite, Texture } from "pixi.js";
import { CHUNK_TILES, MARGIN_PX, TILE_PX, View, chunkBytes, chunkKey, neededChunks } from "./chunkmath";
import { MapData } from "./mapdata";
import { frameFor } from "./tiles";

/** Terrain renderer options: baked chunk textures or tiles drawn straight from the atlas. */
export interface TerrainOptions {
  mode: "baked" | "direct";
  chunkTiles: number;
  /** Atlas texels per art pixel: 1 for the 32 px set, 2 for the 64 px set. */
  artScale: number;
  marginPx: number;
}

export const DEFAULT_TERRAIN: TerrainOptions = {
  mode: "baked",
  chunkTiles: CHUNK_TILES,
  artScale: 1,
  marginPx: MARGIN_PX,
};

interface Live {
  node: Container;
  tex?: RenderTexture;
  sprites: number;
}

/**
 * Terrain chunk cache. Chunks within the margin of the screen are kept; the rest are
 * destroyed so memory stays bounded at any map size.
 *
 * - baked: each chunk is painted once into a render texture (chunkTiles x 32 art px,
 *   times artScale texels), then drawn as one sprite. GPU memory grows with chunk area.
 * - direct: each chunk is a container of tile sprites drawn from the atlas every frame.
 *   GPU memory is the atlas only; Pixi batches the sprites because they share one texture.
 */
export class ChunkCache {
  readonly layer = new Container();
  private readonly live = new Map<string, Live>();
  baked = 0;

  constructor(
    private readonly renderer: Renderer,
    private readonly map: MapData,
    private frames: Record<string, Texture>,
    readonly opts: TerrainOptions = DEFAULT_TERRAIN,
  ) {}

  /** Swap the art sheet (e.g. on a zoom change); every chunk is rebuilt on the next update. */
  setFrames(frames: Record<string, Texture>, artScale: number): void {
    if (frames === this.frames && artScale === this.opts.artScale) return;
    this.frames = frames;
    this.opts.artScale = artScale;
    for (const c of this.live.values()) {
      c.node.destroy({ children: true });
      c.tex?.destroy(true);
    }
    this.live.clear();
  }

  get count(): number {
    return this.live.size;
  }

  /** GPU bytes held by baked chunk textures (0 in direct mode). */
  get bytes(): number {
    return this.opts.mode === "baked" ? this.live.size * chunkBytes(this.opts.chunkTiles, this.opts.artScale) : 0;
  }

  get sprites(): number {
    let n = 0;
    for (const c of this.live.values()) n += c.sprites;
    return n;
  }

  update(v: View): void {
    const want = new Set<string>();
    const { chunkTiles, marginPx } = this.opts;
    for (const [cx, cy] of neededChunks(v, this.map.width, this.map.height, marginPx, chunkTiles)) {
      const key = chunkKey(cx, cy);
      want.add(key);
      if (!this.live.has(key)) this.live.set(key, this.build(cx, cy));
    }
    for (const [key, c] of this.live) {
      if (want.has(key)) continue;
      c.node.destroy({ children: true });
      c.tex?.destroy(true);
      this.live.delete(key);
    }
  }

  private tiles(cx: number, cy: number): Container {
    const n = this.opts.chunkTiles;
    const tiles = new Container();
    const tx0 = cx * n;
    const ty0 = cy * n;
    for (let ty = 0; ty < n; ty++) {
      const y = ty0 + ty;
      if (y >= this.map.height) break;
      for (let tx = 0; tx < n; tx++) {
        const x = tx0 + tx;
        if (x >= this.map.width) break;
        const s = new Sprite(this.frames[frameFor(this.map, x, y)] ?? Texture.EMPTY);
        s.position.set(tx * TILE_PX, ty * TILE_PX);
        s.width = TILE_PX;
        s.height = TILE_PX;
        tiles.addChild(s);
      }
    }
    return tiles;
  }

  private build(cx: number, cy: number): Live {
    const px = this.opts.chunkTiles * TILE_PX;
    const tiles = this.tiles(cx, cy);
    if (this.opts.mode === "direct") {
      tiles.position.set(cx * px, cy * px);
      this.layer.addChild(tiles);
      return { node: tiles, sprites: tiles.children.length };
    }
    const tex = RenderTexture.create({
      width: px,
      height: px,
      resolution: this.opts.artScale,
      scaleMode: "nearest",
    });
    this.renderer.render({ container: tiles, target: tex, clear: true });
    tiles.destroy({ children: true });
    const sprite = new Sprite(tex);
    sprite.position.set(cx * px, cy * px);
    this.layer.addChild(sprite);
    this.baked++;
    return { node: sprite, tex, sprites: 1 };
  }
}
