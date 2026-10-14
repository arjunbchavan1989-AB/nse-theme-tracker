import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({plugins:[react()],root:"client",base:"./",build:{outDir:"../dist/public",emptyOutDir:true,rollupOptions:{output:{manualChunks(id){
 if(!id.includes("/node_modules/"))return;
 if(/\/(react|react-dom|react-is|scheduler)\//.test(id))return "react";
 if(/\/(recharts|recharts-scale|d3-[^/]+|victory-vendor|decimal.js-light|lodash)\//.test(id))return "charts";
}}}}});
