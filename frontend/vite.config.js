import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, /api/* is proxied to the locally running FastAPI backend
// (uvicorn api.main:app --port 8000). In the Docker image, nginx does the
// same proxying. Same-origin in both modes -> no CORS changes needed in
// the Phase 2 backend.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
