import {COMPLETE_CROP_FIXTURE as F} from './completeCropReplayFixture';
import {isCompleteCropScenario,type CompleteCropScenario} from './completeCropReplay';

export function readCompleteCropLocation(search:string):{scenario:CompleteCropScenario;index:number}{
 const p=new URLSearchParams(search),candidate=p.get('scenario');
 const scenario=p.getAll('scenario').length===1&&isCompleteCropScenario(candidate)?candidate:'initial-0',raw=p.get('frame');
 const valid=p.getAll('artifact').length===1&&p.get('artifact')===F.scenarios[scenario].artifact_sha256&&p.getAll('frame').length===1&&
  raw!==null&&/^(0|[1-9]\d{0,2})$/.test(raw)&&Number(raw)<F.scenarios[scenario].frames;
 return {scenario,index:valid?Number(raw):0};
}
export function completeCropURL(href:string,scenario:CompleteCropScenario,index:number):string|null{
 if(!isCompleteCropScenario(scenario)||!Number.isSafeInteger(index)||index<0||index>=F.scenarios[scenario].frames)return null;
 try{const url=new URL(href);if(!['http:','https:'].includes(url.protocol)||url.username||url.password)return null;
  url.searchParams.set('scenario',scenario);url.searchParams.set('artifact',F.scenarios[scenario].artifact_sha256);url.searchParams.set('frame',String(index));return url.href;
 }catch{return null;}
}
