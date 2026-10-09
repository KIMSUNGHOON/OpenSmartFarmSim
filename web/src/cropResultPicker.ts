import {ApiError,need} from './api-validation';
import type {createApi} from './api';
import type {AuthoredFarmSummary,AuthoredFarmPage,AuthoredFarmCursor} from './authored-farm-api';
import type {CropFarmSelection,RegisteredCropSelection} from './cropFarmSelection';
import type {CropCatalogKind,CropCatalogPage,CropCatalogCursor} from './cropResultCatalog';
import type {StoredCropSelection} from './SelectedCropReplay';

export type CropResultPickerApi=Pick<ReturnType<typeof createApi>,
  'authoredFarmCatalog'|'authoredFarm'|'cropFarmSelection'|'cropResultCatalog'>;
export type CropResultPickerState=Readonly<{
  phase:'idle'|'loading'|'ready'|'error'|'disposed';work:'farms'|'crops'|'results'|null;
  farms:AuthoredFarmPage|null;farm:AuthoredFarmSummary|null;crops:CropFarmSelection|null;
  crop:RegisteredCropSelection|null;kind:CropCatalogKind;page:CropCatalogPage|null;
  farm_page:number;result_page:number;selection:StoredCropSelection|null;error:ApiError|null;
}>;
export function emptyCropResultPicker(kind:CropCatalogKind='calculation_cycle_v1'):CropResultPickerState{
  return {phase:'idle',work:null,farms:null,farm:null,crops:null,crop:null,kind,page:null,
    farm_page:0,result_page:0,selection:null,error:null};
}
function registration(farm:AuthoredFarmSummary){
  return {scenario_id:farm.scenario_id,scenario_revision:farm.scenario_revision,registration_sha256:farm.scenario_sha256};
}
export function createCropResultPicker(api:CropResultPickerApi|null,changed:(state:CropResultPickerState)=>void){
  let state=emptyCropResultPicker(),disposed=false,generation=0;
  let pending:Promise<void>=Promise.resolve(),controller:AbortController|null=null;
  let farmCursors:(AuthoredFarmCursor|undefined)[]=[undefined],resultCursors:(CropCatalogCursor|null)[]=[null];
  function publish(value:CropResultPickerState){state=value;changed(state);}
  function run(seed:CropResultPickerState,work:NonNullable<CropResultPickerState['work']>,
    load:(client:CropResultPickerApi,signal:AbortSignal)=>Promise<CropResultPickerState>,commit=()=>{}){
    need(!disposed&&api);const client=api,version=++generation;controller?.abort();
    const owned=new AbortController();controller=owned;
    const current=()=>!disposed&&version===generation&&!owned.signal.aborted;
    const previous=pending;
    state={...seed,phase:'loading',work,page:null,selection:null,error:null};
    const task=previous.catch(()=>{}).then(async()=>{
      if(!current())return;
      try{
        const value=await load(client,owned.signal);if(!current())return;
        commit();publish({...value,phase:'ready',work:null,selection:null,error:null});
      }catch(error){if(current())publish({...emptyCropResultPicker(seed.kind),phase:'error',
        error:error instanceof ApiError?error:new ApiError('network_unresolved')});}
      finally{if(version===generation)controller=null;}
    });
    pending=task;changed(state);return task;
  }
  function farms(direction:'refresh'|'previous'|'next'){
    const index=direction==='refresh'?0:state.farm_page+(direction==='next'?1:-1);
    need(index>=0&&(direction==='refresh'||state.farms));
    const cursor=direction==='next'?state.farms!.next_cursor:direction==='previous'?farmCursors[index]:undefined;
    need(direction!=='next'||cursor!==null);
    const cursors=direction==='refresh'?[undefined]:direction==='next'?
      [...farmCursors.slice(0,index),cursor??undefined]:farmCursors;
    const seed=emptyCropResultPicker(state.kind);
    return run(seed,'farms',async client=>({...seed,farms:await client.authoredFarmCatalog(cursor??undefined),farm_page:index}),
      ()=>{farmCursors=cursors;resultCursors=[null];});
  }
  function results(crop:RegisteredCropSelection,kind:CropCatalogKind,index:number,cursor:CropCatalogCursor|null,
    cursors:(CropCatalogCursor|null)[]){
    need(state.farm&&state.crops);
    const farm=state.farm,seed={...state,kind,crop,page:null,selection:null,result_page:index};
    const lookup={...registration(farm),crop_id:crop.crop_id};
    return run(seed,'results',async(client,signal)=>({...seed,
      page:await client.cropResultCatalog({kind,farm:lookup,limit:10,before:cursor},signal)}),()=>{resultCursors=cursors;});
  }
  return {
    snapshot:()=>state,
    refreshFarms:()=>farms('refresh'),previousFarms:()=>farms('previous'),nextFarms:()=>farms('next'),
    chooseFarm(jobId:string){
      const item=state.farms?.items.find(row=>row.intent_job.job_id===jobId);need(item);
      const seed={...state,farm:null,crops:null,crop:null,page:null,selection:null,result_page:0};
      return run(seed,'crops',async(client,signal)=>{
        const farm=await client.authoredFarm(item.scenario_id,item.scenario_revision);
        if(signal.aborted)throw new ApiError('request_canceled');
        need(farm.scenario_sha256===item.scenario_sha256);
        const crops=await client.cropFarmSelection(registration(farm),signal);
        return {...seed,farm,crops};
      },()=>{resultCursors=[null];});
    },
    chooseCrop(cropId:string){
      const crop=state.crops?.items.find(row=>row.crop_id===cropId);need(crop);
      return results(crop,state.kind,0,null,[null]);
    },
    setKind(kind:CropCatalogKind){
      need(!disposed&&(kind==='calculation_cycle_v1'||kind==='harvest_v1'));
      need(state.work!=='farms'&&state.work!=='crops');
      if(kind===state.kind)return Promise.resolve();
      if(state.crop)return results(state.crop,kind,0,null,[null]);
      publish({...state,kind,page:null,selection:null});return Promise.resolve();
    },
    refreshResults(){
      need(state.crop);return results(state.crop,state.kind,state.result_page,resultCursors[state.result_page]??null,resultCursors);
    },
    nextResults(){
      need(state.crop&&state.page&&state.page.next_cursor);
      const index=state.result_page+1,cursor=state.page.next_cursor;
      return results(state.crop,state.kind,index,cursor,[...resultCursors.slice(0,index),cursor]);
    },
    previousResults(){
      need(state.crop&&state.result_page>0);const index=state.result_page-1;
      return results(state.crop,state.kind,index,resultCursors[index]??null,resultCursors);
    },
    select(resultId:string){
      need(!disposed&&state.phase==='ready'&&state.page);
      if(state.selection?.result_id===resultId)return;
      const page=state.page;let selection:StoredCropSelection;
      if(page.kind==='calculation_cycle_v1'){
        const item=page.items.find(row=>row.result_id===resultId);need(item);
        selection={kind:page.kind,farm:{...page.farm},result_id:item.result_id};
      }else{
        const item=page.items.find(row=>row.result_id===resultId);need(item);
        selection={kind:page.kind,farm:{...page.farm},result_id:item.result_id,parent_result_id:item.parent_result_id};
      }
      publish({...state,selection});
    },
    cancel(){
      if(disposed)return;generation++;controller?.abort();controller=null;
      publish({...state,phase:'idle',work:null,page:null,selection:null,error:null});
    },
    dispose(){disposed=true;generation++;controller?.abort();controller=null;state={...emptyCropResultPicker(state.kind),phase:'disposed'};},
  };
}
