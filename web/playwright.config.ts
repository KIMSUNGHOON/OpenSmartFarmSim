import { defineConfig } from '@playwright/test';
const port=Number(process.env.OSSF_TEST_WEB_PORT ?? '5173');
if(!Number.isSafeInteger(port) || port<1024 || port>65535)throw new Error('invalid browser test port');
export default defineConfig({
  testDir:'e2e',fullyParallel:false,workers:1,retries:0,
  use:{baseURL:'http://127.0.0.1:'+port,browserName:'chromium',trace:'off',video:'off',
    launchOptions:{args:['--enable-unsafe-swiftshader']}},
  webServer:{command:'npm run dev -- --host 127.0.0.1 --port '+port+' --strictPort',
    url:'http://127.0.0.1:'+port,reuseExistingServer:false},
});
