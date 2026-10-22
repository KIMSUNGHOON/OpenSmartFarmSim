export const STORED_LEAF_MAX_BYTES=2*1024**2;
export function need(c:unknown):asserts c{if(!c)throw Error('저장된 잎 면적의 원 파일·범위·무결성을 확인할 수 없습니다.');}
export function object(v:unknown):Record<string,unknown>{need(v!==null&&typeof v==='object'&&!Array.isArray(v));return v as Record<string,unknown>;}
export function closed(v:unknown,keys:string[]){const q=object(v);need(Object.keys(q).length===keys.length&&keys.every(k=>Object.hasOwn(q,k)));return q;}
export function digest(v:unknown):asserts v is string{need(typeof v==='string'&&/^[0-9a-f]{64}$/.test(v));}
export function id(v:unknown):asserts v is string{need(typeof v==='string'&&/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(v));}
export function utc(v:unknown):asserts v is string{need(typeof v==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(v)&&
  Number.isFinite(Date.parse(v))&&new Date(v).toISOString().replace('.000Z','Z')===v);}
export function integer(v:unknown,min:number,max:number):asserts v is number{need(typeof v==='number'&&Number.isSafeInteger(v)&&v>=min&&v<=max);}
export function flags(q:Record<string,unknown>){need(q.scope==='software_research_only'&&q.claim_scope==='synthetic_crop_math_only'&&q.gates==='not_assessed');}
export function exact(v:unknown,unit:'s'|'degC_day'){
  const q=closed(v,['numerator','denominator','unit']);need(q.unit===unit);
  for(const k of ['numerator','denominator'])need(typeof q[k]==='string'&&/^(0|[1-9][0-9]{0,1023})$/.test(q[k]));
  const n=BigInt(q.numerator as string),d=BigInt(q.denominator as string);need(d>0n);let x=n,y=d;
  while(y){const r=x%y;x=y;y=r;}need(x===1n);return {n,d};
}
export function area(v:unknown){const q=closed(v,['value','unit']);need(q.unit==='m2'&&typeof q.value==='number'&&Number.isFinite(q.value)&&q.value>0);}
export function constants(v:unknown,expected:Record<string,unknown>){const q=closed(v,Object.keys(expected));need(Object.entries(expected).every(([k,value])=>q[k]===value));}
export function rights(v:unknown){const q=closed(v,['access','declaration_id','declared_at_utc','display','ownership_asserted','redistribute','revision','store','transform','use']);
  for(const k of ['access','display','ownership_asserted','redistribute','store','transform','use'])need(q[k]===true);
  id(q.declaration_id);id(q.revision);utc(q.declared_at_utc);}
export async function readStoredLeafFile(directory:string,name:string,signal:AbortSignal){
  const response=await fetch(directory+name,{signal,cache:'no-store',redirect:'error',credentials:'omit'});need(response.ok&&response.body);
  const reader=response.body.getReader(),chunks:Uint8Array[]=[];let size=0;
  try{while(true){const value=await reader.read();if(value.done)break;size+=value.value.byteLength;need(size<=STORED_LEAF_MAX_BYTES);chunks.push(value.value);}}
  catch(error){await reader.cancel();throw error;}
  finally{reader.releaseLock();}
  const raw=new Uint8Array(size);let offset=0;for(const part of chunks){raw.set(part,offset);offset+=part.length;}return raw;
}
export function parse(raw:Uint8Array){return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)) as unknown;}
