// Compares terrain renderers in headless Chrome: memory and frame time at phone and desktop sizes.
// Usage: npm run build && npm run bench   (CHROME=/path/to/chrome, default /usr/bin/google-chrome)
// Chrome runs WebGL on SwiftShader (CPU), so frame times are relative, not phone GPU times.
import { spawn } from "node:child_process";
import puppeteer from "puppeteer-core";

const server = spawn("npx", ["vite", "preview", "--port", "4174", "--strictPort"], { stdio: "ignore" });
await new Promise((r) => setTimeout(r, 2500));
const browser = await puppeteer.launch({
  executablePath: process.env.CHROME ?? "/usr/bin/google-chrome",
  args: [
    "--no-sandbox",
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist",
    "--enable-precise-memory-info",
  ],
});
const views = {
  phone: { w: 390, h: 844, dpr: 3, q: "x=183&y=68" },
  desktop: { w: 1920, h: 1080, dpr: 1, q: "x=150&y=100" },
};
const variants = {
  "default (direct, sheet by zoom, 16-tile chunks)": "",
  "baked 32px, 32-tile chunks": "mode=baked&art=32&chunk=32",
  "baked 64px, 32-tile chunks": "mode=baked&art=64&chunk=32",
  "baked 64px, 16-tile chunks": "mode=baked&art=64&chunk=16",
  "direct 64px, 16-tile chunks": "mode=direct&art=64&chunk=16",
  "direct 32px, 16-tile chunks": "mode=direct&art=32&chunk=16",
};
const rows = [];
try {
  for (const [vname, v] of Object.entries(views)) {
    for (const [name, q] of Object.entries(variants)) {
      const page = await browser.newPage();
      page.on("pageerror", (e) => console.error(name, e.message));
      await page.setViewport({ width: v.w, height: v.h, deviceScaleFactor: v.dpr });
      await page.goto(`http://localhost:4174/?${v.q}&${q}`);
      await page.waitForFunction(() => /ready|failed/.test(document.title), { timeout: 60000 });
      await page.evaluate(() => window.__bench(60, 16)); // warm-up: shaders, buffers, first chunks
      const still = await page.evaluate(() => window.__bench(60, 0));
      const pan = await page.evaluate(() => window.__bench(120, 16));
      const s = await page.evaluate(() => window.__cppStats);
      rows.push({
        view: vname,
        variant: name,
        chunks: s.chunks,
        sprites: s.sprites,
        gpuMb: s.mb,
        gl: pan.gl,
        stillMedMs: still.medianMs,
        panMedMs: pan.medianMs,
        panAvgMs: pan.avgMs,
        panP95Ms: pan.p95Ms,
        panMaxMs: pan.maxMs,
        jsHeapMb: pan.jsHeapMb,
      });
      await page.close();
    }
  }
} finally {
  await browser.close();
  server.kill();
}
console.table(rows);
console.log(JSON.stringify(rows));
