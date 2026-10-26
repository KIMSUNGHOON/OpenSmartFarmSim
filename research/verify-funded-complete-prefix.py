"""Reconstruct actual branches and independently check every bound frame."""
from decimal import Decimal,localcontext
from datetime import datetime
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app import crop_funded_complete_prefix as model
from app.content_access import ContentAccess


def frac(v):return Fraction(int(v['numerator']),int(v['denominator']))


def flows(frame):
    cp=frame['evidence']['checkpoint']
    if cp is None:return frame['lifetime_integrated_transfers']
    return cp['lifetime_integrated_transfers']if frame['evidence']['kind']=='fractional_checkpoint'else cp['integrated_transfers']


def snapshot(frame):return frame['snapshot']if frame['evidence']['checkpoint']is None else frame['evidence']['checkpoint']['last_confirmed']


def independent(packet,context,stem_state,source_directory,programs,checkpoints,source_programs):
    data=context.value;F=Fraction.from_float;timeline=stem_state['timeline_state'];base=F(float(timeline['base_temperature']['value']))
    delta=datetime.fromisoformat(timeline['at'].replace('Z','+00:00'))-datetime.fromisoformat(timeline['started_at'].replace('Z','+00:00'))
    offset=Fraction(delta.days*86400+delta.seconds)
    birth=frac(data['records'][0]['at']);birth_air=F(data['base_lifetime_transfers']['indoor_air_temperature_time']['value'])
    ages=lengths=leaf_values=originals=0;maximum=0.;seen_before=0
    with localcontext()as dc:
        dc.prec=110;D=Decimal.from_float
        for i,frame in enumerate(packet['frames']):
            at=frac(frame['at']['elapsed_seconds_exact']);air=F(flows(frame)['indoor_air_temperature_time']['value'])
            assert frame['output_cursor']==i+1 and frame['at']['time_origin_utc']==timeline['at']
            expected=[frac(n['length_state']['clock_state']['age_exact'])+(air-base*at)/86400 for n in stem_state['internodes']]
            if at>=birth:expected.append((air-birth_air-base*(at-birth))/86400)
            assert frac(frame['shoot']['shoot_age_exact'])==frac(timeline['age_exact'])+(air-base*at)/86400;ages+=1
            for node,age in zip(frame['shoot']['internodes'],expected,strict=True):
                assert frac(node['age_exact'])==age;ages+=1
                values=node['curve']['values'];a=Decimal(age.numerator)/Decimal(age.denominator)
                x=D(float(values['steepness']['value']))*(a-D(float(values['inflection_age']['value'])))
                reference=D(float(values['maximum_length']['value']))/(1+(-x).exp())
                difference=float(abs(D(node['length']['value'])-reference)/reference);assert difference<=2e-15;maximum=max(maximum,difference);lengths+=1
            evidence=frame['evidence'];cp=evidence['checkpoint']
            if evidence['kind']=='original_funded_checkpoint':
                raw=(source_directory/evidence['checkpoint_sha256']).read_bytes();assert sha256(raw).hexdigest()==evidence['checkpoint_sha256']
                assert model.crop._canonical(cp)==raw and snapshot(frame)['state']==cp['last_confirmed']['state'];originals+=1
                program=source_programs[evidence['source_frame_index']]
            elif evidence['kind']=='checked_dense_candidate':
                assert cp is None and evidence['checkpoint_sha256']is None and snapshot(frame)['state']==data['source']['candidate']['dense_candidate']['state'];seen_before+=1
                assert evidence['candidate']==data['source']['candidate'];program=data['source']['program']
            else:
                assert evidence['kind']=='fractional_checkpoint'and sha256(model.crop._canonical(cp)).hexdigest()==evidence['checkpoint_sha256']
                assert cp==checkpoints[evidence['checkpoint_sha256']]and snapshot(frame)['state']==cp['last_confirmed']['state']
                program=programs[evidence['context_sha256']]
            n=len(frame['leaves']);y=snapshot(frame)['state'];assert len(y)==107+3*n
            assert frame['program_sha256']==model.binding._digest(program)
            parents={node['internode_id']:node for node in frame['shoot']['internodes']}
            for j,leaf in enumerate(frame['leaves']):
                assert leaf['leaf_id']==program['leaves'][j]['leaf_id']and leaf['curve_sha256']==model.binding._digest(program['leaves'][j]['curve'])
                assert all(type(v)is float for v in (y[107+j],y[107+n+j],y[107+2*n+j]));leaf_values+=3
                assert leaf['attachment_internode_id']in parents
                leaf_birth=Fraction(0)if leaf['birth_at_elapsed_seconds_exact']is None else frac(leaf['birth_at_elapsed_seconds_exact'])
                assert frac(parents[leaf['attachment_internode_id']]['development_birth_seconds_exact'])<=offset+leaf_birth<=offset+at
    assert seen_before==1 and frac(packet['frames'][-1]['at']['elapsed_seconds_exact'])==F(data['original']['grid_step_seconds'])*data['original']['grid_step_count']
    return {'exact_shoot_and_node_ages':ages,'Decimal110_lengths':lengths,'leaf_state_values':leaf_values,'original_CP_bytes':originals,'CP_less_dense_before':seen_before,'maximum_length_relative_difference':maximum}


def verify(source,previous,output,mode):
    source,previous,output=Path(source),Path(previous),Path(output)
    raw=(ROOT/'fixtures/crop-funded-complete-prefix-fixtures-v1.json').read_bytes();qa=json.loads(raw);assert mode in qa['modes']
    assert all(qa['rights'][k]is True for k in ['use','display','redistribute'])
    old_raw=(ROOT/qa['previous_evidence_path']).read_bytes();assert sha256(old_raw).hexdigest()==qa['previous_evidence_sha256'];accepted=json.loads(old_raw)
    expected=accepted['fresh']['output_file_sha256'];assert sha256((previous/'index.json').read_bytes()).hexdigest()==expected['index.json']
    index=json.loads((previous/'index.json').read_bytes());rows={(r['case_index'],r['label']):r for r in index['records']}
    spec=importlib.util.spec_from_file_location('old_binding_QA',ROOT/'research/verify-fractional-stem-bindings.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    declaration_raw=(ROOT/qa['initial_links_declaration_path']).read_bytes();assert sha256(declaration_raw).hexdigest()==qa['initial_links_declaration_sha256'];declaration=json.loads(declaration_raw)
    register=json.loads((source/'register.json').read_bytes());sm=json.loads((source/'stem'/register['stem_root_sha256']).read_bytes());state=json.loads((source/'stem'/sm['samples'][0]['result_sha256']).read_bytes())['state']
    access=ContentAccess(os.getuid(),os.getegid());output.mkdir(mode=0o750);results=[]
    for case in register['cases']:
        i=case['case_index'];directory=source/'leaves'/str(i)
        def restore(label):
            path=rows[(i,label)]['context_path'];data=(previous/path).read_bytes();assert sha256(data).hexdigest()==expected[path]
            return model.crop.restore_context(directory,source/'stem',access,raw_bytes=data,expected_sha256=expected[path])
        first=restore('initial');cp=model.crop.start(first);checkpoints=[cp]
        if mode=='additional':
            run=model.crop.advance_chunk(first,cp,1);assert run['hold']is None;checkpoints.append(run['checkpoint'])
            last_context=restore('additional');last_cp=model.crop.start(last_context);tail=[last_cp]
        else:last_context=first;tail=checkpoints
        horizon=Fraction.from_float(first.value['original']['grid_step_seconds'])*first.value['original']['grid_step_count']
        while frac(tail[-1].value['at']['elapsed_seconds_exact'])<horizon:
            run=model.crop.advance_chunk(last_context,tail[-1],1);assert run['hold']is None;tail.append(run['checkpoint'])
        segments=[{'context':first,'checkpoints':checkpoints,'initial_bindings':driver.initial_links(first,declaration)}]
        if mode=='additional':segments.append({'context':last_context,'checkpoints':tail,'initial_bindings':driver.initial_links(last_context,declaration)})
        packet=model.bind_complete_trajectory(segments);assert len(packet['frames'])==qa['expected_frames'][mode]
        with model.MorphologyBlobStore(directory,access)as store:
            manifest=model.crop._parse(store.get(case['leaf_root_sha256'],maximum=model.crop.birth.leaf.MAX),model.crop.birth.leaf.MAX)
            graph=model.crop.birth.leaf._graph(store,manifest);source_programs=[frame['program']for frame in graph[4]]
        programs={s['context'].sha256:s['context'].value['program']for s in segments}
        checkpoints={cp.sha256:cp.value for s in segments for cp in s['checkpoints']}
        metric=independent(packet,first,state,directory,programs,checkpoints,source_programs)
        old_row=rows[(i,'additional-final'if mode=='additional'else'final')];old_bytes=(previous/old_row['path']).read_bytes();assert sha256(old_bytes).hexdigest()==expected[old_row['path']]
        old_cp=json.loads(old_bytes)['checkpoint'];assert tail[-1].value==old_cp
        data=model.crop._canonical(packet);name=f'case-{i}-{mode}.json';(output/name).write_bytes(data)
        for j,segment in enumerate(segments):(output/f'case-{i}-segment-{j}-context.json').write_bytes(segment['context']._raw)
        results.append({'case_index':i,'mode':mode,'path':name,'sha256':sha256(data).hexdigest(),'bytes':len(data),'frames':len(packet['frames']),
            'current_checkpoint_RHS':packet['current_checkpoint_RHS_evaluations'],'sample_scalars':packet['sample_scalars'],'independent':metric,'previous_final_CP_bytes_equal':True})
    result={'scope':'software_research_only','G0_G4':'not_assessed','R2':'not_approved','mode':mode,'declaration_sha256':sha256(raw).hexdigest(),
        'records':results,'code_sha256':model._pins(),'known_512_hold':'unchanged','scientific_scope':'same synthetic first numerical threshold; stem C allocation/initial biology/subsequent emergence not validated'}
    (output/'index.json').write_bytes(model.crop._canonical(result));return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    for name in ['source','previous','output']:parser.add_argument(name,type=Path)
    parser.add_argument('mode',choices=['initial','additional']);args=parser.parse_args();print(json.dumps(verify(args.source,args.previous,args.output,args.mode),sort_keys=True))
