import { defineConfig } from 'vite';
import { resolve } from 'node:path';

export default defineConfig({base:'./',build:{outDir:'dist-crop-appearance',
  rolldownOptions:{input:resolve(import.meta.dirname,'crop-appearance.html')}},
  server:{host:'127.0.0.1',port:5175,strictPort:true,
    fs:{strict:true,allow:[process.cwd()],deny:['.env','.env.*','**/*.pem','**/*.key','**/.git/**']}},
  preview:{host:'127.0.0.1',port:4175,strictPort:true}});
