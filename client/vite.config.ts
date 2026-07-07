import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The API endpoints exposed by the FastAPI server.
const API_ROUTES = ["/scan", "/remediate", "/egress-status", "/audit", "/health", "/eval-report"];

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // In dev, proxy API calls to the FastAPI server so the client can use
    // same-origin relative paths (which also works in prod when FastAPI
    // serves the built bundle).
    proxy: Object.fromEntries(
      API_ROUTES.map((route) => [
        route,
        { target: "http://localhost:8000", changeOrigin: true },
      ]),
    ),
  },
  build: {
    // Build straight into where FastAPI serves the bundle from.
    outDir: "../server/app/ui/static",
    emptyOutDir: true,
  },
});
