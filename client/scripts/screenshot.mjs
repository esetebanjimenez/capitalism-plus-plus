// Renders the sample map in headless Chrome and writes PNG screenshots to docs/art/.
// Usage: npm run build && npm run screenshot   (CHROME=/path/to/chrome, default /usr/bin/google-chrome)
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import puppeteer from "puppeteer-core";

const out = new URL("../../docs/art/", import.meta.url);
mkdirSync(out, { recursive: true });
const server = spawn("npx", ["vite", "preview", "--port", "4173", "--strictPort"], { stdio: "ignore" });
await new Promise((r) => setTimeout(r, 2500));
const browser = await puppeteer.launch({
  executablePath: process.env.CHROME ?? "/usr/bin/google-chrome",
  args: ["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
});
const shots = [
  { name: "m2-map-desktop.png", w: 1280, h: 800, dpr: 1, q: "x=190&y=138" },
  { name: "m2-map-phone.png", w: 390, h: 844, dpr: 3, q: "x=183&y=68" },
  { name: "m2-map-phone-64-direct.png", w: 390, h: 844, dpr: 2, q: "x=176&y=62" },
  { name: "m2-map-phone-firms.png", w: 390, h: 844, dpr: 3, q: "x=201&y=140" },
  // Panel shell: a tap (CSS px) opens the tile card or firm panel.
  { name: "m2-ui-phone-tile.png", w: 390, h: 844, dpr: 3, q: "x=201&y=140", tap: [80, 560] },
  { name: "m2-ui-phone-firm.png", w: 390, h: 844, dpr: 3, q: "x=201&y=140", tap: [144, 272] },
  { name: "m2-ui-desktop-firm.png", w: 1280, h: 800, dpr: 1, q: "x=190&y=138", tap: [496, 336] },
  // #250 town-name plates over the sample map (towns from the map's town table).
  { name: "m2-map-plates-desktop.png", w: 1280, h: 800, dpr: 1, q: "x=203&y=146" },
  { name: "m2-map-plates-phone.png", w: 390, h: 844, dpr: 3, q: "x=206&y=144" },
  // #336 review: a tap on a plate selects the tile under it (plate goes see-through); a long
  // press on the plate opens the town card.
  { name: "m2-map-plates-tile-phone.png", w: 390, h: 844, dpr: 3, q: "x=206&y=144", plate: "tap" },
  { name: "m2-map-plates-town-phone.png", w: 390, h: 844, dpr: 3, q: "x=206&y=144", plate: "long" },
  // #178 chart style: profit crossing zero (April tip shown), a single point, a share price.
  { name: "m2-chart-demo.png", w: 1024, h: 230, dpr: 1, url: "?chart=demo" },
];
const stats = {};
try {
  for (const s of shots) {
    const page = await browser.newPage();
    page.on("pageerror", (e) => console.error(s.name, e.message));
    await page.setViewport({ width: s.w, height: s.h, deviceScaleFactor: s.dpr });
    await page.goto(`http://localhost:4173/${s.url ?? `?map=sample&${s.q}`}`); // fixed map, not a live game
    await page.waitForFunction(() => /ready|failed/.test(document.title), { timeout: 30000 });
    // The sample map draws before the sim boots; wait for its loading overlay to clear.
    await new Promise((r) => setTimeout(r, 3000));
    await page
      .waitForFunction(() => !/Loading Python|Creating the world/.test(document.body.innerText), { timeout: 35000 })
      .catch(() => {});
    await new Promise((r) => setTimeout(r, 500));
    if (s.plate) {
      // The middle of the plate nearest the screen centre.
      const at = await page.evaluate(() => {
        const rs = [...document.querySelectorAll(".plate:not([hidden])")].map((p) => p.getBoundingClientRect());
        const d = (r) => Math.hypot(r.x + r.width / 2 - innerWidth / 2, r.y + r.height / 2 - innerHeight / 2);
        const r = rs.sort((a, b) => d(a) - d(b))[0];
        return [r.x + r.width / 2, r.y + r.height / 2];
      });
      await page.evaluate(([x, y, long]) => window.__tap(x, y, long), [...at, s.plate === "long"]);
      await new Promise((r) => setTimeout(r, 800));
    }
    if (s.tap) {
      await page.evaluate(([x, y]) => window.__tap(x, y), s.tap);
      await new Promise((r) => setTimeout(r, 600));
    }
    stats[s.name] = await page.evaluate(() => window.__cppStats);
    writeFileSync(new URL(s.name, out), await page.screenshot());
    await page.close();
  }
} finally {
  await browser.close();
  server.kill();
}
console.log(JSON.stringify(stats));
