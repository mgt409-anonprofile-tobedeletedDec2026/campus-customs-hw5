import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dashboard calls the FastAPI backend directly at http://localhost:8000
// (see src/api.ts). The backend allows this page's origin, http://localhost:5173.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
});
