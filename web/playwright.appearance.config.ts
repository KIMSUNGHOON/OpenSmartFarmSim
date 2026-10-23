import { defineConfig } from '@playwright/test';
import base from './playwright.config';

export default defineConfig({...base,testMatch:['tomato-appearance.spec.ts','morphology-replay.spec.ts','morphology-rational-replay.spec.ts','morphology-execution.spec.ts','leaf-area-replay.spec.ts','leaf-population-replay.spec.ts','leaf-appearance-replay.spec.ts'],
  use:{...base.use,baseURL:'http://127.0.0.1:4175'},
  webServer:{command:'npx --no-install vite preview --config vite.crop-appearance.config.ts',
    url:'http://127.0.0.1:4175/crop-appearance.html',reuseExistingServer:false}});
