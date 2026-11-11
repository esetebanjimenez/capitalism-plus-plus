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
  { name: "m2-map-desktop.png", w: 1280, h: 800, dpr: 1, q: "x=147&y=39&zoom=1" },
  { name: "m2-map-phone.png", w: 390, h: 844, dpr: 3, q: "x=186&y=76&zoom=3" },
];
const stats = {};
try {
  for (const s of shots) {
    const page = await browser.newPage();
    page.on("pageerror", (e) => console.error(s.name, e.message));
    await page.setViewport({ width: s.w, height: s.h, deviceScaleFactor: s.dpr });
    await page.goto(`http://localhost:4173/?${s.q}`);
    await page.waitForFunction(() => /ready|failed/.test(document.title), { timeout: 30000 });
    await new Promise((r) => setTimeout(r, 500));
    stats[s.name] = await page.evaluate(() => window.__cppStats);
    writeFileSync(new URL(s.name, out), await page.screenshot());
    await page.close();
  }
} finally {
  await browser.close();
  server.kill();
}
console.log(JSON.stringify(stats));
