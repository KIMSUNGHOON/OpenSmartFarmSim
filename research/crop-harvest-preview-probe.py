"""Bounded actual proxy reads; original wire and custody comparisons, no calculation."""
from hashlib import sha256
import argparse
import http.client
import importlib.util
import json
import os
from pathlib import Path
import time
from urllib.parse import urlencode, urlsplit

ROOT=Path(__file__).resolve().parents[1]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def request(origin,target,token):
    address=urlsplit(origin);assert address.scheme=='http' and address.hostname in ('localhost','127.0.0.1')
    client=http.client.HTTPConnection(address.hostname,address.port,timeout=30);raw=bytearray();start=time.monotonic()
    try:
        client.request('GET',target,headers={'Authorization':'Bearer '+token,'Connection':'close'})
        response=client.getresponse()
        while True:
            remaining=30-(time.monotonic()-start);assert remaining>0
            if client.sock is not None:client.sock.settimeout(remaining)
            chunk=response.read1(min(65536,2*1024**2+1-len(raw)));raw.extend(chunk)
            assert len(raw)<=2*1024**2
            if not chunk or response.isclosed():break
        assert time.monotonic()-start<30
        return {'status':response.status,'raw':bytes(raw),'seconds':time.monotonic()-start,
            'headers':{k.lower():v for k,v in response.getheaders()}}
    finally:client.close()


def run(directory,origin,output,*,full=True):
    directory=Path(directory);output=Path(output);output.mkdir(mode=0o700)
    access=json.loads((directory/'access.private.json').read_bytes())
    saved_raw=(directory/'original-checked-manifest.private.json').read_bytes()
    ready=json.loads((directory/'ready.private.json').read_bytes());assert sha256(saved_raw).hexdigest()==ready['source_manifest_sha256']
    saved=json.loads(saved_raw);farm={k:v for k,v in access['crop'].items() if k!='result_id'}
    assert access['harvest_result_id']==saved['original_record']['result_id']
    cost=module('owned_preview_probe_cost',ROOT/'research/crop-harvest-api-cost.py')
    cost.load_storage(ROOT,sha256((ROOT/'research/crop-harvest-storage-preservation.py').read_bytes()).hexdigest())
    from app import crop_harvest_current_query as current, api_crop_harvest_replay as public
    check=module('owned_preview_probe_reconcile',ROOT/'research/crop-harvest-http-reconciliation.py')
    reference=json.loads((ROOT/'research/artifacts/crop-harvest-full-view-reference-20261009.json').read_bytes())
    old_cost=json.loads((ROOT/'research/artifacts/crop-harvest-current-read-cost-reference-20261009.json').read_bytes())
    # Expected growth bytes are from the already accepted original DB/App run.
    expected={(r['endpoint'],r['view'],r.get('offset')):r for r in reference['browser_network'] if r['complete'] and r['status']==200}
    codes={'query_version':current.VERSION,'query_code_sha256':current.CODE_SHA256,
        'query_dependency_sha256':current.DEPENDENCY_SHA256,'projection_code_sha256':public.CODE_SHA256}
    responses=[];data={};initial=json.loads((directory/'live.private.json').read_bytes())
    assert initial['active_requests']==0 and initial['guarded_math_publication_calls']==0
    def get(endpoint,label,*,offset=None,subject='owner',status=200):
        query=dict(farm)
        if endpoint=='harvest':target=check.target(saved,farm,label)
        else:
            if label=='samples':query.update(view='samples',offset=offset,limit=7)
            target='/v1/crop-cycle-calculation-research-results/'+access['crop']['result_id']+'?'+urlencode(query)
        index=json.loads((directory/'live.private.json').read_bytes())['response_count']
        result=request(origin,target,access['tokens'][subject]);assert result['status']==status
        deadline=time.monotonic()+5
        while True:
            live=json.loads((directory/'live.private.json').read_bytes())
            if live['response_count']>index and live['active_requests']==0:break
            assert time.monotonic()<deadline;time.sleep(.05)
        assert live['response_count']==index+1
        emitted=live['responses'][-1]
        assert emitted['status']==status and emitted['complete'] and emitted['bytes']==len(result['raw'])
        assert emitted['body_sha256']==sha256(result['raw']).hexdigest() and result['headers']['cache-control']=='no-store'
        observation={'endpoint':endpoint,'label':label,'offset':offset,'subject':subject,'status':status,
            'seconds':result['seconds'],'bytes':len(result['raw']),'sha256':sha256(result['raw']).hexdigest()}
        if status==200:
            if endpoint=='harvest':
                observation['original_values']=check.reconcile(saved,farm,codes,label,
                    emission={**emitted,'sha256':emitted['body_sha256']},**result)
            else:
                previous=expected[('crop',label,str(offset) if offset is not None else None)]
                assert previous['body_sha256']==observation['sha256'] and previous['bytes']==observation['bytes']
            value=json.loads(result['raw'])
            if endpoint=='crop' and label=='summary':data['summary']=value
            elif endpoint=='crop' and offset==0:data['samples']=value['page']['records']
            elif endpoint=='harvest' and label=='first':data['rows']=value['page']['records'][:3]
        responses.append(observation)
    get('crop','summary');get('harvest','summary')
    if full:
        get('crop','samples',offset=0);get('crop','samples',offset=47808)
        get('harvest','first');get('harvest','last')
        get('harvest','summary',subject='denied',status=403);get('harvest','summary',subject='foreign',status=404)
        data['harvest_result_id']=access['harvest_result_id']
        cost.operator_file(output/'browser-data.private.json',json.dumps(data,sort_keys=True).encode())
    before=len(os.listdir(f"/proc/{ready['service_pid']}/fd"))
    page=request(origin,'/',access['token']);assert page['status']==200
    asset_source=json.loads((directory/'web-pins.private.json').read_bytes())
    assert sha256(page['raw']).hexdigest()==asset_source['assets']['index.html']
    assert json.loads((directory/'live.private.json').read_bytes())['guarded_math_publication_calls']==0
    assert len(os.listdir(f"/proc/{ready['service_pid']}/fd"))==before
    result={'accepted':True,'origin':origin,'same_original_full_growth_and_harvest':True,'responses':responses,
        'frontend_index_original_bytes':True,'service_FD_before_after':[before,before],
        'guarded_math_publication_calls':0,'G0_G4':'not_assessed','realtime_U3':False}
    cost.operator_file(output/'probe.private.json',json.dumps(result,sort_keys=True).encode())
    print(json.dumps({'accepted':True,'origin':origin,'response_count':len(responses),'frontend_status':200}),flush=True)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--service-directory',required=True);p.add_argument('--origin',required=True)
    p.add_argument('--output',required=True);p.add_argument('--short',action='store_true');args=p.parse_args()
    run(args.service_directory,args.origin,args.output,full=not args.short)


if __name__=='__main__':main()
