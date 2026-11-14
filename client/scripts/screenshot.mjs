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
  // #254 News feed: a live game run until it has news (toast shot when an important item lands),
  // then Menu > News (phone) or N (desktop).
  { name: "m2-news-phone.png", w: 390, h: 844, dpr: 3, url: "?events=3&seed=3", news: "menu", toast: "m2-news-toast-phone.png" },
  { name: "m2-news-desktop.png", w: 1280, h: 800, dpr: 1, url: "?events=3&seed=3", news: "key" },
];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
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
    await new Promise((r) => setTimeout(r, 500));
    if (s.news) await runForNews(page, s);
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
