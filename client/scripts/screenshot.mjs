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
  // #252 build panel from a long press on empty land (live build_options; compare with
  // docs/art/m2-build-menu-preview.png).
  { name: "m2-build-panel-desktop.png", w: 1280, h: 800, dpr: 1, q: "x=203&y=146", tap: [700, 520], long: true, scan: true },
  { name: "m2-build-panel-phone.png", w: 390, h: 844, dpr: 3, q: "x=206&y=144", tap: [200, 120], long: true, scan: true,
    then: [
      { click: ".build-row:not(:disabled)", name: "m2-build-confirm-phone.png" },
      { click: ".btn[data-kind=primary]", run: true, name: "m2-build-done-phone.png" },
    ] },
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
    if (s.tap) {
      await page.evaluate(([x, y, long]) => window.__tap(x, y, long), [...s.tap, Boolean(s.long)]);
      await new Promise((r) => setTimeout(r, s.long ? 1500 : 600));
      // The sim's world isn't the sample map, so tap around until the sim says the tile is
      // buildable (the panel then has no "can't build" note).
      for (let i = 0; s.scan && i < 40; i++) {
        if (await page.evaluate(() => !document.querySelector(".build-note"))) break;
        const [x, y] = [s.tap[0] + ((i % 8) - 4) * 48, s.tap[1] + (Math.floor(i / 8) - 2) * 48];
        await page.evaluate(([x, y]) => window.__tap(x, y), [x, y]);
        await new Promise((r) => setTimeout(r, 700));
      }
    }
    stats[s.name] = await page.evaluate(() => window.__cppStats);
    writeFileSync(new URL(s.name, out), await page.screenshot());
    // Follow-up shots in the same page: click a selector, optionally run the sim, shoot.
    for (const step of s.then ?? []) {
      await page.click(step.click);
      if (step.run) await page.evaluate(() => window.__sim.setSpeed(1));
      await new Promise((r) => setTimeout(r, step.run ? 2500 : 600));
      writeFileSync(new URL(step.name, out), await page.screenshot());
    }
    await page.close();
  }
} finally {
  await browser.close();
  server.kill();
}
console.log(JSON.stringify(stats));
