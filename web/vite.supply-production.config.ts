import {defineConfig} from 'vite';
import {resolve} from 'node:path';
export default defineConfig({base:'./',publicDir:false,build:{outDir:'dist-supply-production',minify:false,target:'es2022',
 rolldownOptions:{input:resolve(import.meta.dirname,'supply-production-replay.html')}},
 server:{host:'127.0.0.1',port:5182,strictPort:true,fs:{strict:true,allow:[process.cwd()],deny:['.env','.env.*','**/*.pem','**/*.key','**/.git/**']}},
 preview:{host:'127.0.0.1',port:4182,strictPort:true}});
