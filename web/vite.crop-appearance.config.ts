import { defineConfig } from 'vite';
import { resolve } from 'node:path';

export default defineConfig({base:'./',build:{outDir:'dist-crop-appearance',
  rolldownOptions:{input:{appearance:resolve(import.meta.dirname,'crop-appearance.html'),
    morphology:resolve(import.meta.dirname,'morphology-replay.html'),
    rationalMorphology:resolve(import.meta.dirname,'morphology-rational-replay.html'),
    morphologyExecution:resolve(import.meta.dirname,'morphology-execution.html'),
    leafArea:resolve(import.meta.dirname,'leaf-area-replay.html'),
    leafPopulation:resolve(import.meta.dirname,'leaf-population-replay.html'),
    leafAppearance:resolve(import.meta.dirname,'leaf-appearance-replay.html'),
    leafLifecycle:resolve(import.meta.dirname,'leaf-lifecycle-replay.html'),
    growingGeometry:resolve(import.meta.dirname,'growing-geometry-replay.html'),
    growingGeometryRemoval:resolve(import.meta.dirname,'growing-geometry-removal-replay.html'),
    leafCarbonStock:resolve(import.meta.dirname,'leaf-carbon-stock-replay.html'),
    completeCrop:resolve(import.meta.dirname,'complete-crop-replay.html'),
    leafLifecycleEmptyTest:resolve(import.meta.dirname,'e2e/leaf-lifecycle-empty-harness.html'),
    leafPopulationExecution:resolve(import.meta.dirname,'leaf-population-execution.html'),
    leafAppearanceExecution:resolve(import.meta.dirname,'leaf-appearance-execution.html')}}},
  server:{host:'127.0.0.1',port:5175,strictPort:true,
    fs:{strict:true,allow:[process.cwd()],deny:['.env','.env.*','**/*.pem','**/*.key','**/.git/**']}},
  preview:{host:'127.0.0.1',port:4175,strictPort:true}});
