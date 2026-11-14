// Boot check for the built site (#247): serves dist/ with `vite preview`, opens it in
// headless Chrome, waits for the live sim's map, runs the game at top speed and exits 0
// once 10 in-game days have passed. Any boot error, sim error or timeout exits 1.
// Usage: npm run build && npm run boot-check   (CHROME=/path/to/chrome, default /usr/bin/google-chrome)
import { spawn } from "node:child_process";
import puppeteer from "puppeteer-core";

const PORT = 4175;
const DAYS = 10;
const BOOT_MS = 180_000;
const RUN_MS = 120_000;

const server = spawn("npx", ["vite", "preview", "--port", String(PORT), "--strictPort"], { stdio: "ignore" });
await new Promise((r) => setTimeout(r, 2500));
const browser = await puppeteer.launch({
  executablePath: process.env.CHROME ?? "/usr/bin/google-chrome",
  args: ["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
});
let failed = false;
try {
  const page = await browser.newPage();
  const offsite = new Set();
  page.on("pageerror", (e) => console.error("page error:", e.message));
  page.on("response", (r) => r.status() >= 400 && console.error(`HTTP ${r.status()}: ${r.url()}`));
  page.on("request", (r) => {
    const u = new URL(r.url());
    if (u.hostname !== "localhost" && !u.protocol.startsWith("data") && !u.protocol.startsWith("blob")) offsite.add(u.href);
  });
  const t0 = Date.now();
  await page.goto(`http://localhost:${PORT}/`);
  await page.waitForFunction(() => /ready|failed/.test(document.title), { timeout: BOOT_MS });
  const title = await page.title();
  if (!/map ready/.test(title)) throw new Error(`boot failed: ${title}: ${await page.$eval("body", (b) => b.innerText.slice(0, 2000))}`);
  console.log(`booted in ${((Date.now() - t0) / 1000).toFixed(1)} s`);

  const days = await page.evaluate(
    (want, ms) =>
      new Promise((resolve, reject) => {
        const sim = window.__sim;
        const date = (t) => Date.UTC(t.year, t.month - 1, t.day) / 86_400_000;
        const start = date(sim.last);
        const prev = sim.onTick;
        const prevErr = sim.onError;
        const timer = setTimeout(() => reject(new Error(`only ${date(sim.last) - start} days in ${ms} ms`)), ms);
        sim.onError = (message, tb) => {
          prevErr(message, tb);
          reject(new Error(`sim error: ${message}\n${tb}`));
        };
        sim.onTick = (t) => {
          prev(t);
          if (date(t) - start >= want) {
            clearTimeout(timer);
            sim.setSpeed(0);
            resolve(date(t) - start);
          }
        };
        sim.setSpeed(4);
      }),
    DAYS,
    RUN_MS,
  );
  console.log(`sim ran ${days} days`);
  if (offsite.size) throw new Error(`the site fetched from other hosts: ${[...offsite].join(", ")}`);
} catch (e) {
  failed = true;
  console.error(String(e?.stack ?? e));
} finally {
  await browser.close();
  server.kill();
}
process.exit(failed ? 1 : 0);
