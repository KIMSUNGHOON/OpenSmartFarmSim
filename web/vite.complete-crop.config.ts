import {defineConfig} from 'vite';
import {resolve} from 'node:path';

export default defineConfig({base:'./',build:{outDir:'dist-complete-crop',minify:false,target:'es2022',
 rolldownOptions:{input:{replay:resolve(import.meta.dirname,'complete-crop-replay.html'),appearance:resolve(import.meta.dirname,'crop-appearance.html')}}},
 server:{host:'127.0.0.1',port:5180,strictPort:true,
  fs:{strict:true,allow:[process.cwd()],deny:['.env','.env.*','**/*.pem','**/*.key','**/.git/**']}},
 preview:{host:'127.0.0.1',port:4180,strictPort:true}});
