import {isLeafCarbonStockScenario} from './leafCarbonStockReplay';
import {expect,it} from 'vitest';
import {readLeafCarbonStockLocation,leafCarbonStockURL} from './leafCarbonStockReplayLocation';
import {LEAF_CARBON_STOCK_FIXTURE as F} from './leafCarbonStockReplayFixture';
it.each(Object.keys(F.scenarios))('restores a pinned scenario/frame: %s',name=>{
 if(!isLeafCarbonStockScenario(name))throw Error('scenario');const scenario=name,url=leafCarbonStockURL('http://localhost:5176/leaf-carbon-stock-replay.html',scenario,16);
 expect(url).not.toBeNull();expect(readLeafCarbonStockLocation(new URL(url!).search)).toEqual({scenario,index:16});
});
it.each(['','?scenario=other','?scenario=reverse-individual-stock&frame=1','?scenario=reverse-individual-stock&scenario=warm-day-individual-stock',
 '?scenario=warm-day-individual-stock&artifact=bad&frame=16',`?artifact=${F.scenarios['warm-day-individual-stock'].artifact_sha256}&frame=17`,
 `?artifact=${F.scenarios['warm-day-individual-stock'].artifact_sha256}&frame=01`,`?artifact=${F.scenarios['warm-day-individual-stock'].artifact_sha256}&frame=1&frame=2`])('rejects unbound frame selections %s',search=>{
 expect(readLeafCarbonStockLocation(search).index).toBe(0);
});
it.each([-1,17,NaN,Infinity,1.5])('refuses invalid output frame %s',index=>expect(leafCarbonStockURL('http://localhost:5176/leaf-carbon-stock-replay.html','warm-day-individual-stock',index)).toBeNull());

it.each(['file:///tmp/replay','https://user:pass@example.com/','not-a-url'])('rejects invalid replay URL %s',href=>{
 expect(leafCarbonStockURL(href,'warm-day-individual-stock',0)).toBeNull();
});
