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
  // #250 town-name plates over the sample map (towns from the map's town table).
  { name: "m2-map-plates-desktop.png", w: 1280, h: 800, dpr: 1, q: "x=203&y=146" },
  { name: "m2-map-plates-phone.png", w: 390, h: 844, dpr: 3, q: "x=206&y=144" },
  // #336 review: a tap on a plate selects the tile under it (plate goes see-through); a long
  // press on the plate opens the town card.
  { name: "m2-map-plates-tile-phone.png", w: 390, h: 844, dpr: 3, q: "x=206&y=144", plate: "tap" },
  { name: "m2-map-plates-town-phone.png", w: 390, h: 844, dpr: 3, q: "x=206&y=144", plate: "long" },
  // #178 chart style: profit crossing zero (April tip shown), a single point, a share price.
  { name: "m2-chart-demo.png", w: 1024, h: 230, dpr: 1, url: "?chart=demo" },
  // #254 News feed: a live game run until it has news (toast shot when an important item lands),
  // then Menu > News (phone) or N (desktop).
  { name: "m2-news-phone.png", w: 390, h: 844, dpr: 3, url: "?events=3&seed=3", news: "menu", toast: "m2-news-toast-phone.png" },
  { name: "m2-news-desktop.png", w: 1280, h: 800, dpr: 1, url: "?events=3&seed=3", news: "key" },
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
/** Builds a few firms in a live game with events on, steps it three years and shoots the toasts. */
async function runForNews(page, s) {
  await page.waitForFunction(() => !/Loading Python|Creating the world/.test(document.body.innerText), { timeout: 120000 });
  await page.evaluate(() => {
    const builds = [[4, 222, 150], [4, 226, 150], [3, 222, 166], [1, 205, 165]];
    for (const [firm_type, x, y] of builds) window.__sim.command("build_firm", { firm_type, x, y });
    window.__sim.step(1100);
  });
  await page.waitForSelector(".toast.tap", { timeout: 60000 });
  await sleep(300);
  if (s.toast) writeFileSync(new URL(s.toast, out), await page.screenshot());
  await page.evaluate(() => window.__sim.setSpeed(0));
  await sleep(600);
  await page.evaluate(() => document.querySelectorAll(".toast").forEach((t) => t.remove()));
  if (s.news === "key") await page.keyboard.press("n");
  else {
    await page.click(".menu-btn");
    await sleep(300);
    await page.evaluate(() => [...document.querySelectorAll(".panel button")].find((b) => /News/.test(b.textContent)).click());
  }
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
    // The sample map draws before the sim boots; wait for its loading overlay to clear.
    await new Promise((r) => setTimeout(r, 3000));
    await page
      .waitForFunction(() => !/Loading Python|Creating the world/.test(document.body.innerText), { timeout: 35000 })
      .catch(() => {});
    await new Promise((r) => setTimeout(r, 500));
    if (s.news) await runForNews(page, s);
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
