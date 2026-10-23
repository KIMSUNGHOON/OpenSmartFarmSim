import {LEAF_APPEARANCE_FIXTURE as FIXTURE} from './leafAppearanceReplayFixture';

export function readAppearanceReplayIndex(search:string):number{
 const params=new URLSearchParams(search),frame=params.get('frame');
 if(params.getAll('artifact').length!==1||params.get('artifact')!==FIXTURE.artifact_sha256||params.getAll('frame').length!==1||
  frame===null||!/^(0|[1-9]\d?)$/.test(frame))return 0;
 const index=Number(frame);return index<FIXTURE.frames?index:0;
}

export function appearanceReplayURL(href:string,index:number):string|null{
 if(!Number.isSafeInteger(index)||index<0||index>=FIXTURE.frames)return null;
 const url=new URL(href);url.searchParams.set('artifact',FIXTURE.artifact_sha256);url.searchParams.set('frame',String(index));return url.href;
}
