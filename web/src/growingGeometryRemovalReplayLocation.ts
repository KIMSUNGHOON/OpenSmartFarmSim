import {GROWING_GEOMETRY_REMOVAL_FIXTURE as FIXTURE} from './growingGeometryRemovalReplayFixture';
import type {GrowingGeometryRemovalScenario} from './growingGeometryRemovalReplay';

export function readGrowingRemovalReplayLocation(search:string):{scenario:GrowingGeometryRemovalScenario;index:number}{
 const p=new URLSearchParams(search),candidate=p.get('scenario');
 const scenario=p.getAll('scenario').length===1&&candidate!==null&&Object.hasOwn(FIXTURE.scenarios,candidate)?candidate as GrowingGeometryRemovalScenario:'case-0-remove-1';
 const frame=p.get('frame');
 const valid=p.getAll('artifact').length===1&&p.get('artifact')===FIXTURE.scenarios[scenario].artifact_sha256&&p.getAll('frame').length===1&&frame!==null&&/^(0|[1-9]\d?)$/.test(frame)&&Number(frame)<FIXTURE.scenarios[scenario].frames;
 return {scenario,index:valid?Number(frame):0};
}

export function growingRemovalReplayURL(href:string,scenario:GrowingGeometryRemovalScenario,index:number):string|null{
 if(!Object.hasOwn(FIXTURE.scenarios,scenario)||!Number.isSafeInteger(index)||index<0||index>=FIXTURE.scenarios[scenario].frames)return null;
 try{const url=new URL(href);if(!['http:','https:'].includes(url.protocol)||url.username||url.password)return null;
  url.searchParams.set('scenario',scenario);url.searchParams.set('artifact',FIXTURE.scenarios[scenario].artifact_sha256);url.searchParams.set('frame',String(index));return url.href;
 }catch{return null;}
}
