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

  constructor(firms: FirmInfo[], frames: Record<string, Texture>) {
    this.layer.addChild(this.firmSprites, this.flagSprites);
    for (const firm of [...firms].sort((a, b) => a.y - b.y || a.x - b.x)) {
      const body = new Sprite(frames[FIRM_SPRITES[firm.type]] ?? Texture.EMPTY);
      body.position.set(firm.x * TILE_PX, firm.y * TILE_PX);
      this.firmSprites.addChild(body);
      const sprites = [body];
      if (firm.owner !== null) {
        const flag = new Sprite(frames[flagFrame(firm.owner)] ?? Texture.EMPTY);
        flag.position.set(firm.x * TILE_PX + FLAG_DX, firm.y * TILE_PX + FLAG_DY);
        this.flagSprites.addChild(flag);
        sprites.push(flag);
      }
      this.items.push({ firm, sprites });
    }
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
