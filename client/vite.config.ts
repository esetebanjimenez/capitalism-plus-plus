import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  server: { fs: { allow: [".."] } },
  build: { target: "es2022", assetsInlineLimit: 0 },
  // The sim worker (src/sim/worker.ts) is a module worker.
  worker: { format: "es" },
});
