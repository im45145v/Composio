import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Bind IPv4 explicitly. On this machine "localhost" is ::1, so a page opened at
    // 127.0.0.1 would otherwise load from cache and then fail every /api request.
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        timeout: 0,
        configure: (proxy) => {
          proxy.on("proxyRes", (proxyRes) => {
            const contentType = proxyRes.headers["content-type"];
            if (typeof contentType === "string" && contentType.includes("text/event-stream")) {
              proxyRes.headers["cache-control"] = "no-cache";
              proxyRes.headers["x-accel-buffering"] = "no";
            }
          });
        },
      },
    },
  },
});
