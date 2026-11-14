import uiJson from "../../../art/atlas/ui_atlas.json";
import ui1xUrl from "../../../art/atlas/ui_atlas.png?url";
import ui2xUrl from "../../../art/atlas/ui_atlas_2x.png?url";
import terrainJson from "../../../art/atlas/terrain_atlas.json";
import terrainUrl from "../../../art/atlas/terrain_atlas.png?url";
import terrain64Json from "../../../art/atlas/terrain_atlas_64.json";
import terrain64Url from "../../../art/atlas/terrain_atlas_64.png?url";
import { nineSliceCss } from "./layout";

interface UiFrame {
  x: number;
  y: number;
  w: number;
  h: number;
  slice?: number[];
}

/**
 * Loads the UI parts sheet (art/atlas/ui_atlas*, 2x sheet on 2x and 3x screens) and turns
 * each frame into a CSS class: `.ui-<name>` as a nine-slice border image for frames with a
 * `slice`, otherwise a fixed-size background. Text stays live HTML on top.
 */
export async function loadUiAtlas(resolution: number): Promise<void> {
  const scale = resolution >= 2 ? 2 : 1;
  const img = new Image();
  img.src = scale === 2 ? ui2xUrl : ui1xUrl;
  await img.decode();
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d")!;
  const rules: string[] = [];
  for (const [name, f] of Object.entries(uiJson.frames as Record<string, UiFrame>)) {
    canvas.width = f.w * scale;
    canvas.height = f.h * scale;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, f.x * scale, f.y * scale, f.w * scale, f.h * scale, 0, 0, f.w * scale, f.h * scale);
    const url = canvas.toDataURL("image/png");
    rules.push(
      f.slice
        ? `.ui-${name}{${nineSliceCss(url, f.slice, scale)}}`
        : `.ui-${name}{background:url(${url}) 0 0/${f.w}px ${f.h}px no-repeat;width:${f.w}px;height:${f.h}px;}`,
    );
  }
  const style = document.createElement("style");
  style.textContent = rules.join("\n");
  document.head.appendChild(style);
}

/**
 * Firm-type icons for panels (art/README "Firm-type icons and goal tick (#176)"): the map's
 * `firm_*` sprites as `.firm-<frame>` CSS classes in a 32 pt cell, from the 64 px sheet on
 * 2x and 3x screens so they stay pixel-native.
 */
export async function loadFirmIcons(resolution: number): Promise<void> {
  const big = resolution >= 2;
  const json = (big ? terrain64Json : terrainJson) as { frames: Record<string, UiFrame> };
  const img = new Image();
  img.src = big ? terrain64Url : terrainUrl;
  await img.decode();
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d")!;
  const rules: string[] = [];
  for (const [name, f] of Object.entries(json.frames)) {
    if (!name.startsWith("firm_")) continue;
    canvas.width = f.w;
    canvas.height = f.h;
    ctx.clearRect(0, 0, f.w, f.h);
    ctx.drawImage(img, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
    rules.push(`.firm-${name}{background:url(${canvas.toDataURL("image/png")}) 0 0/32px 32px no-repeat;}`);
  }
  const style = document.createElement("style");
  style.textContent = rules.join("\n");
  document.head.appendChild(style);
}
