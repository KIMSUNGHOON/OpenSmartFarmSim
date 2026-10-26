import {it,expect} from 'vitest';
import {COMPLETE_CROP_FIXTURE as F} from './completeCropReplayFixture';
import {readCompleteCropLocation,completeCropURL} from './completeCropReplayLocation';
import type {CompleteCropScenario} from './completeCropReplay';

it.each(Object.keys(F.scenarios)as CompleteCropScenario[])('restores same artifact and exact frame after navigation: %s',s=>{
 for(const i of [0,20,F.scenarios[s].frames-1]){
  const url=completeCropURL('http://localhost:5180/complete-crop-replay.html',s,i)!;
  expect(readCompleteCropLocation(new URL(url).search)).toEqual({scenario:s,index:i});
 }
});
it.each(['-1','01','69','1.5','NaN','1e1','+1','9999999999999999999',''])('rejects invalid index %s',i=>{
 expect(readCompleteCropLocation(`?scenario=initial-0&artifact=${F.scenarios['initial-0'].artifact_sha256}&frame=${i}`)).toEqual({scenario:'initial-0',index:0});
});
it.each(['?scenario=unknown&frame=2','?scenario=initial-1&scenario=initial-0&frame=2',
 `?scenario=initial-0&artifact=${'0'.repeat(64)}&frame=2`,
 `?scenario=initial-0&artifact=${F.scenarios['initial-0'].artifact_sha256}&frame=2&frame=3`])('rejects ambiguous or different source: %s',q=>{
 expect(readCompleteCropLocation(q).index).toBe(0);
});
it.each(['file:///tmp/x','javascript:alert(1)','http://user:pass@localhost/','not a URL'])('does not write unsafe URL %s',href=>{
 expect(completeCropURL(href,'initial-0',0)).toBeNull();
});
