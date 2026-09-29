import { defineConfig } from 'vitest/config';
import { Agent } from 'node:https';
import { readFileSync } from 'node:fs';

const upstream = process.env.OSSF_WEB_API_ORIGIN;
const certificate = process.env.OSSF_WEB_TLS_CERT;
const privateKey = process.env.OSSF_WEB_TLS_KEY;
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
  test:{include:['src/**/*.test.ts','src/**/*.test.tsx']},
  server:{host:'127.0.0.1',port:5173,strictPort:true,proxy,https,
    fs:{strict:true,allow:[process.cwd()],deny:['.env','.env.*','**/*.pem','**/*.key','**/.git/**']}},
  preview:{host:'127.0.0.1',port:4173,strictPort:true},
});
