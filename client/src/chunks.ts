import { Container, Renderer, RenderTexture, Sprite, Texture } from "pixi.js";
import {
  CHUNK_BYTES,
  CHUNK_PX,
  CHUNK_TILES,
  MARGIN_PX,
  TILE_PX,
  View,
  chunkKey,
  neededChunks,
} from "./chunkmath";
import { MapData } from "./mapdata";
import { frameFor } from "./tiles";

/**
 * Terrain chunk cache. Each chunk is 32 x 32 tiles baked once into a 1024 px
 * render texture. Only chunks within 8 tiles of the screen are kept; the rest are
 * destroyed so GPU memory stays bounded at any map size.
 */
export class ChunkCache {
  readonly layer = new Container();
  private readonly live = new Map<string, { sprite: Sprite; tex: RenderTexture }>();
  baked = 0;

  constructor(
    private readonly renderer: Renderer,
    private readonly map: MapData,
    private readonly frames: Record<string, Texture>,
    private readonly marginPx = MARGIN_PX,
  ) {}

  get count(): number {
    return this.live.size;
  }

  get bytes(): number {
    return this.live.size * CHUNK_BYTES;
  }

  update(v: View): void {
    const want = new Set<string>();
    for (const [cx, cy] of neededChunks(v, this.map.width, this.map.height, this.marginPx)) {
      const key = chunkKey(cx, cy);
      want.add(key);
      if (!this.live.has(key)) this.live.set(key, this.bake(cx, cy));
    }
    for (const [key, c] of this.live) {
      if (want.has(key)) continue;
      c.sprite.destroy();
      c.tex.destroy(true);
      this.live.delete(key);
    }
  }

  private bake(cx: number, cy: number) {
    const tiles = new Container();
    const tx0 = cx * CHUNK_TILES;
    const ty0 = cy * CHUNK_TILES;
    for (let ty = 0; ty < CHUNK_TILES; ty++) {
      const y = ty0 + ty;
      if (y >= this.map.height) break;
      for (let tx = 0; tx < CHUNK_TILES; tx++) {
        const x = tx0 + tx;
        if (x >= this.map.width) break;
        const s = new Sprite(this.frames[frameFor(this.map, x, y)] ?? Texture.EMPTY);
        s.position.set(tx * TILE_PX, ty * TILE_PX);
        tiles.addChild(s);
      }
    }
    const tex = RenderTexture.create({ width: CHUNK_PX, height: CHUNK_PX, scaleMode: "nearest" });
    this.renderer.render({ container: tiles, target: tex, clear: true });
    tiles.destroy({ children: true });
    const sprite = new Sprite(tex);
    sprite.position.set(cx * CHUNK_PX, cy * CHUNK_PX);
    this.layer.addChild(sprite);
    this.baked++;
    return { sprite, tex };
  }
}
