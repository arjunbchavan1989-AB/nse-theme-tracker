import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({plugins:[react()],root:"client",base:"./",build:{outDir:"../dist/public",emptyOutDir:true,rollupOptions:{output:{manualChunks:{react:["react","react-dom"],charts:["recharts"]}}}}});
