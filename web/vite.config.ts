import { defineConfig } from 'vitest/config';
import { Agent } from 'node:https';
import { readFileSync } from 'node:fs';
import { authoredJobId, authoredRunId, authoredResponses } from './e2e/authored-thermal-fixture.ts';
import { cropReferenceResponse,cropReferenceSelection,cropHoldReferenceResponse,cropHoldReferenceSelection } from './demo/crop-reference.ts';

const upstream = process.env.OSSF_WEB_API_ORIGIN;
const certificate = process.env.OSSF_WEB_TLS_CERT;
const privateKey = process.env.OSSF_WEB_TLS_KEY;
const demo = process.env.OSSF_WEB_DEMO === '1';
if (demo && (upstream || certificate || privateKey)) {
  throw new Error('Synthetic 3D demo cannot connect to an operator API or TLS runtime');
}
if (!!certificate !== !!privateKey || upstream && (!certificate || !privateKey)) {
  throw new Error('Browser HTTPS certificate and key required for API proxy');
}
const https = certificate && privateKey ? {cert:readFileSync(certificate),key:readFileSync(privateKey)} : undefined;
let proxy;
if (upstream) {
  const url = new URL(upstream);
  if (url.protocol !== 'https:' || !['127.0.0.1','localhost','[::1]'].includes(url.hostname)
    || url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
    throw new Error('Loopback HTTPS API origin required');
  }
  const ca = process.env.OSSF_WEB_API_CA;
  proxy = {'^/v1(?:/|$)':{target:url.origin,changeOrigin:true,secure:true,
    agent:new Agent(ca ? {ca:readFileSync(ca)} : {})}};
}
export default defineConfig({
  plugins:demo ? [{name:'local-synthetic-3d-demo',apply:'serve',configureServer(server) {
    const fixture=authoredResponses();
    const crops=[{selection:cropReferenceSelection,value:cropReferenceResponse()},
      {selection:cropHoldReferenceSelection,value:cropHoldReferenceResponse()}];
    const run='/v1/authored-runs/'+encodeURIComponent(authoredRunId);
    server.middlewares.use((request,response,next)=>{
      const url=new URL(request.url ?? '/', 'http://127.0.0.1'),path=url.pathname;
      if (!path.startsWith('/v1/')) return next();
      response.setHeader('Cache-Control','no-store');
      response.setHeader('Content-Type','application/json; charset=utf-8');
      if (request.method !== 'GET' || request.headers.authorization !== 'Bearer synthetic-demo-token-only') {
        response.statusCode=403;
        response.end(JSON.stringify({error:{code:'forbidden',message:'Synthetic demo request denied'}}));
        return;
      }
      const crop=crops.find(({selection})=>path==='/v1/crop-research-results/'+encodeURIComponent(selection.result_id) && [...url.searchParams].length===4 &&
        (['scenario_id','scenario_revision','registration_sha256','crop_id'] as const)
        .every(key=>url.searchParams.getAll(key).length===1 && url.searchParams.get(key)===selection[key]));
      const value=crop?crop.value:path===`/v1/jobs/${authoredJobId}/authored-run` || path===run ? fixture.summary
        : path===run+'/series' ? fixture.series : null;
      response.statusCode=value===null ? 404 : 200;
      response.end(JSON.stringify(value ?? {error:{code:'not_found',message:'Synthetic demo record unavailable'}}));
    });
  }}] : [],
  test:{include:['src/**/*.test.ts','src/**/*.test.tsx']},
  server:{host:'127.0.0.1',port:5173,strictPort:true,proxy,https,
    fs:{strict:true,allow:[process.cwd()],deny:['.env','.env.*','**/*.pem','**/*.key','**/.git/**']}},
  preview:{host:'127.0.0.1',port:4173,strictPort:true},
});
