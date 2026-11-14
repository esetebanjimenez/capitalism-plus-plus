import { Container, Sprite, Texture } from "pixi.js";
import { TILE_PX, View } from "./chunkmath";
import { FirmInfo } from "./mapdata";

/** Atlas sprite per firm_types.id (art/README.md firm sprite names). */
export const FIRM_SPRITES: Record<number, string> = {
  1: "firm_department_store",
  2: "firm_factory",
  3: "firm_rnd_center",
  4: "firm_farm",
  5: "firm_logging_camp",
  6: "firm_mine",
  7: "firm_oil_well",
  8: "firm_software_developer",
  9: "firm_software_publisher",
  10: "firm_restaurant",
  11: "firm_television_station",
  12: "firm_radio_station",
  13: "firm_newspaper_publisher",
  14: "firm_seaport",
};

/** Display names, firm_types.name per id (DB); the capitalism.api facade will supply them. */
export const FIRM_NAMES: Record<number, string> = {
  1: "Department Store",
  2: "Factory",
  3: "R&D Center",
  4: "Farm",
  5: "Logging Camp",
  6: "Mine",
  7: "Oil Well",
  8: "Software Developer",
  9: "Software Publisher",
  10: "Restaurant",
  11: "Television Station",
  12: "Radio Station",
  13: "Newspaper Publisher",
  14: "Seaport",
};

/** Owner flag offset from the tile's top-left (art/README.md): it pokes 4 px above the tile. */
export const FLAG_DX = 24;
export const FLAG_DY = -4;

export const flagFrame = (owner: number) => `flag_${String(owner % 12).padStart(2, "0")}`;

/**
 * Firms and owner flags, drawn above the baked terrain so they can change
 * without re-baking chunks and so flags are never clipped at a chunk edge.
 * Flags sit in their own layer above every firm, which also covers the row above.
 */
export class FirmLayer {
  readonly layer = new Container();
  private readonly firmSprites = new Container();
  private readonly flagSprites = new Container();
  private readonly items: { firm: FirmInfo; sprites: Sprite[] }[] = [];
  private frames?: Record<string, Texture>;

  /**
   * `texelsPerArtPx` says how many atlas texels a frame uses per 32 px art pixel
   * (2 for frames from the 64 px sheet), so every sprite keeps its 32-unit layout size.
   */
  constructor(
    firms: FirmInfo[],
    frames: Record<string, Texture>,
    private texelsPerArtPx: (t: Texture) => number = () => 1,
  ) {
    this.layer.addChild(this.firmSprites, this.flagSprites);
    this.frames = frames;
    this.setFirms(firms);
  }

  /** Replace the firm list: sprites for firms that left are destroyed, new ones added. */
  setFirms(firms: FirmInfo[]): void {
    const key = (f: FirmInfo) => `${f.id}:${f.x}:${f.y}:${f.type}:${f.owner}`;
    const want = new Set(firms.map(key));
    for (let i = this.items.length - 1; i >= 0; i--) {
      if (want.has(key(this.items[i].firm))) continue;
      for (const s of this.items[i].sprites) s.destroy();
      this.items.splice(i, 1);
    }
    const have = new Set(this.items.map((it) => key(it.firm)));
    for (const firm of firms) {
      if (have.has(key(firm))) continue;
      const body = new Sprite();
      body.position.set(firm.x * TILE_PX, firm.y * TILE_PX);
      this.firmSprites.addChild(body);
      const sprites = [body];
      if (firm.owner !== null) {
        const flag = new Sprite();
        flag.position.set(firm.x * TILE_PX + FLAG_DX, firm.y * TILE_PX + FLAG_DY);
        this.flagSprites.addChild(flag);
        sprites.push(flag);
      }
      this.items.push({ firm, sprites });
      this.texture(firm, sprites);
    }
    // Draw order: rows top to bottom so a firm overlaps the one above it.
    const order = (a: Sprite, b: Sprite) => a.y - b.y || a.x - b.x;
    this.firmSprites.children.sort((a, b) => order(a as Sprite, b as Sprite));
  }

  private texture(firm: FirmInfo, sprites: Sprite[]): void {
    const frames = this.frames ?? {};
    const names = [FIRM_SPRITES[firm.type], firm.owner !== null ? flagFrame(firm.owner) : ""];
    sprites.forEach((s, i) => {
      const tex = frames[names[i]] ?? Texture.EMPTY;
      s.texture = tex;
      s.scale.set(1 / this.texelsPerArtPx(tex));
    });
  }

  /** Point every sprite at `frames`; missing frames draw nothing. */
  setFrames(frames: Record<string, Texture>, texelsPerArtPx: (t: Texture) => number = this.texelsPerArtPx): void {
    if (frames === this.frames) return;
    this.frames = frames;
    this.texelsPerArtPx = texelsPerArtPx;
    for (const { firm, sprites } of this.items) this.texture(firm, sprites);
  }

  get count(): number {
    return this.items.length;
  }

  /** Hide firms more than a tile outside the view so the batch stays small. */
  update(v: View): void {
    const x0 = v.x - TILE_PX;
    const y0 = v.y - TILE_PX;
    const x1 = v.x + v.w / v.zoom + TILE_PX;
    const y1 = v.y + v.h / v.zoom + TILE_PX;
    for (const { firm, sprites } of this.items) {
      const px = firm.x * TILE_PX;
      const py = firm.y * TILE_PX;
      const on = px >= x0 && px <= x1 && py >= y0 && py <= y1;
      for (const s of sprites) s.visible = on;
    }
  }

  get visibleCount(): number {
    return this.items.filter((i) => i.sprites[0].visible).length;
  }
}
