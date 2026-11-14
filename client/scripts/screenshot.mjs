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
  // #178 chart style: profit crossing zero (April tip shown), a single point, a share price.
  { name: "m2-chart-demo.png", w: 1024, h: 230, dpr: 1, url: "?chart=demo" },
  // #258 Company Charts tab with fixed demo data (operating profit crosses zero; a tapped point).
  { name: "m2-company-charts-phone.png", w: 390, h: 844, dpr: 3, url: "?company=demo&tab=Charts", chartTap: [1, 0.55] },
  { name: "m2-company-charts-years-phone.png", w: 390, h: 844, dpr: 3, url: "?company=demo&tab=Charts&range=years" },
  // Desktop over a live game: four firms, 13 months run, then C and the Charts tab.
  { name: "m2-company-charts-desktop.png", w: 1280, h: 800, dpr: 1, url: "", live: "charts" },
];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function runForCharts(page) {
  await page.waitForFunction(() => !/Loading Python|Creating the world/.test(document.body.innerText), { timeout: 120000 });
  // The live world is random, so look up buildable tiles around the first town.
  await page.evaluate(async () => {
    const sim = window.__sim;
    const { towns } = await sim.query("map", {});
    const t = towns[0];
    const spots = [];
    for (let r = 6; r < 30 && spots.length < 4; r += 2)
      for (const [dx, dy] of [[r, 0], [-r, 0], [0, r], [0, -r], [r, r], [-r, -r]]) {
        if (spots.length >= 4) break;
        const tile = await sim.query("tile", { x: t.x + dx, y: t.y + dy });
        if (tile.can_build && !spots.some(([x, y]) => Math.abs(x - tile.x) < 4 && Math.abs(y - tile.y) < 4)) spots.push([tile.x, tile.y]);
      }
    [4, 4, 3, 1].forEach((firm_type, i) => spots[i] && sim.command("build_firm", { firm_type, x: spots[i][0], y: spots[i][1] }));
    sim.step(400);
  });
  await page.waitForFunction(() => /1991/.test(document.body.innerText), { timeout: 120000 });
  await page.evaluate(() => window.__sim.setSpeed(0));
  await sleep(800);
  await page.keyboard.press("c");
  await page.waitForSelector(".company .tab", { timeout: 30000 });
  await page.evaluate(() => Array.from(document.querySelectorAll(".company .tab")).find((b) => b.textContent === "Charts").click());
  await sleep(800);
}
const stats = {};
try {
  for (const s of shots) {
    const page = await browser.newPage();
    page.on("pageerror", (e) => console.error(s.name, e.message));
    await page.setViewport({ width: s.w, height: s.h, deviceScaleFactor: s.dpr });
    await page.goto(`http://localhost:4173/${s.url ?? `?map=sample&${s.q}`}`); // fixed map, not a live game
    await page.waitForFunction(() => /ready|failed/.test(document.title), { timeout: 30000 });
    await new Promise((r) => setTimeout(r, 500));
    if (s.tap) {
      await page.evaluate(([x, y]) => window.__tap(x, y), s.tap);
      await new Promise((r) => setTimeout(r, 600));
    }
    if (s.live === "charts") await runForCharts(page);
    if (s.live) await page.evaluate(() => document.querySelectorAll(".toast").forEach((t) => t.remove()));
    if (s.chartTap) {
      // Tap chart number chartTap[0] at a fraction of its width, to show the value tip.
      const [i, fx] = s.chartTap;
      const box = await (await page.$$(".chart"))[i].boundingBox();
      await page.mouse.click(box.x + box.width * fx, box.y + box.height / 2);
      await new Promise((r) => setTimeout(r, 200));
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
