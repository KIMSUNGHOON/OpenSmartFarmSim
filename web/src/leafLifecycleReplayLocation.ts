import {LEAF_LIFECYCLE_FIXTURE as FIXTURE} from './leafLifecycleReplayFixture';
import type {LeafLifecycleScenario} from './leafLifecycleReplay';

export function readLifecycleReplayLocation(search:string):{scenario:LeafLifecycleScenario;index:number}{
 const p=new URLSearchParams(search),candidate=p.get('scenario');
 const scenario=p.getAll('scenario').length===1&&(candidate==='no-removal'||candidate==='with-removal')?candidate:'with-removal';
 const frame=p.get('frame');
 const valid=p.getAll('artifact').length===1&&p.get('artifact')===FIXTURE.scenarios[scenario].artifact_sha256&&p.getAll('frame').length===1&&frame!==null&&/^(0|[1-9]\d?)$/.test(frame)&&Number(frame)<FIXTURE.frames;
 return {scenario,index:valid?Number(frame):0};
}

export function lifecycleReplayURL(href:string,scenario:LeafLifecycleScenario,index:number):string|null{
 if((scenario!=='no-removal'&&scenario!=='with-removal')||!Number.isSafeInteger(index)||index<0||index>=FIXTURE.frames)return null;
 const url=new URL(href);url.searchParams.set('scenario',scenario);url.searchParams.set('artifact',FIXTURE.scenarios[scenario].artifact_sha256);url.searchParams.set('frame',String(index));return url.href;
}
