import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir:'e2e',fullyParallel:false,workers:1,retries:0,
  use:{baseURL:'http://127.0.0.1:5173',browserName:'chromium',trace:'off',video:'off',
    launchOptions:{args:['--enable-unsafe-swiftshader']}},
  webServer:{command:'npm run dev',url:'http://127.0.0.1:5173',reuseExistingServer:false},
});
