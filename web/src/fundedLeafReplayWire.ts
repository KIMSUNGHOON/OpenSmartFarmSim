import {sha256} from './morphologyReplay';
import {need} from './storedLeafReplayIO';

// Subtree hashes use original Python JSON bytes, including 2.0 versus 2.
function split(raw:string,shape:'{'|'['):Record<string,string>|string[]{
 need(raw.length>0&&raw.length<=2*1024**2);let at=0;
 const space=()=>{while(at<raw.length&&/[\x20\t\r\n]/.test(raw[at]!))at++;};
 const string=()=>{
  const start=at;need(raw[at++]==='"');let escaped=false;
  while(at<raw.length){const c=raw[at++]!;
   if(!escaped&&c==='"')return JSON.parse(raw.slice(start,at)) as string;
   if(!escaped&&c==='\\')escaped=true;else escaped=false;
  }
  throw Error('완전한 JSON 문자열이 필요합니다.');
 };
 function value(depth:number):Record<string,string>|string[]|undefined{
  need(depth<=64);space();const kind=raw[at];
  if(kind==='{'||kind==='['){
   at++;space();const result=kind==='{'?Object.create(null) as Record<string,string>:[] as string[];
   const end=kind==='{'?'}':']';if(raw[at]===end){at++;return result;}
   while(at<raw.length){
    let key='';if(kind==='{'){key=string();need(!Object.hasOwn(result,key));space();need(raw[at++]===':');space();}
    const start=at;value(depth+1);const text=raw.slice(start,at);
    if(Array.isArray(result))result.push(text);else result[key]=text;
    space();if(raw[at]===end){at++;return result;}
    need(raw[at++ ]===',');space();
   }
   throw Error('완전한 JSON 컨테이너가 필요합니다.');
  }
  if(kind==='"'){string();return;}
  const match=/^(?:-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null)/.exec(raw.slice(at));
  need(match);const parsed:unknown=JSON.parse(match[0]);need(typeof parsed!=='number'||Number.isFinite(parsed));at+=match[0].length;
 }
 space();need(raw[at]===shape);const result=value(0);space();need(at===raw.length&&result!==undefined);return result;
}
export function wireFields(raw:string):Record<string,string>{const q=split(raw,'{');need(!Array.isArray(q));return q;}
export function wireItems(raw:string):string[]{const q=split(raw,'[');need(Array.isArray(q));return q;}
export function wireHash(raw:string){return sha256(new TextEncoder().encode(raw));}
