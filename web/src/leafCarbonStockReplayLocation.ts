import {LEAF_CARBON_STOCK_FIXTURE as FIXTURE} from './leafCarbonStockReplayFixture';
import {isLeafCarbonStockScenario,type LeafCarbonStockScenario} from './leafCarbonStockReplay';

export function readLeafCarbonStockLocation(search:string):{scenario:LeafCarbonStockScenario;index:number}{
 const p=new URLSearchParams(search),candidate=p.get('scenario');
 const scenario=p.getAll('scenario').length===1&&isLeafCarbonStockScenario(candidate)?candidate:'warm-day-individual-stock';
 const frame=p.get('frame');
 const valid=p.getAll('artifact').length===1&&p.get('artifact')===FIXTURE.scenarios[scenario].artifact_sha256&&p.getAll('frame').length===1&&frame!==null&&/^(0|[1-9]\d?)$/.test(frame)&&Number(frame)<FIXTURE.scenarios[scenario].frames;
 return {scenario,index:valid?Number(frame):0};
}

export function leafCarbonStockURL(href:string,scenario:LeafCarbonStockScenario,index:number):string|null{
 if(!Object.hasOwn(FIXTURE.scenarios,scenario)||!Number.isSafeInteger(index)||index<0||index>=FIXTURE.scenarios[scenario].frames)return null;
 try{const url=new URL(href);if(!['http:','https:'].includes(url.protocol)||url.username||url.password)return null;
  url.searchParams.set('scenario',scenario);url.searchParams.set('artifact',FIXTURE.scenarios[scenario].artifact_sha256);url.searchParams.set('frame',String(index));return url.href;
 }catch{return null;}
}
