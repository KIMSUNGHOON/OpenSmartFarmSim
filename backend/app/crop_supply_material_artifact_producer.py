"""Publish a genuine selected material lineage; never copy unrelated store files."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from . import crop_supply_material_owner as model
from . import crop_supply_material_artifact_reader as reader
from .crop_morphology_artifact_io import MorphologyBlobStore,_need

CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


def _before_geometry(s):
    seed=s.parent.math_basis['seed'];value=s.point['before_dense'];y=value['state'];n=len(seed['program']['leaves']);h=len(seed['organs']['internodes'])
    size=seed['state_layout']['original_prefix_length'];branch=value['pending_branch_transfers_exact'];life=value['pending_lifetime_transfers_exact'];result={}
    for kind,rows,offset,unit in [('leaf',seed['organs']['leaves'],106+n,'m2'),('internode',seed['organs']['internodes'],size+h,'m')]:
        for i,node in enumerate(rows):
            key=f'{kind}_{i}';potential=model.x(branch[key+'_potential'],unit);realized=model.x(branch[key+'_realized'],unit)
            lp=model.x(life[key+'_potential'],unit);lr=model.x(life[key+'_realized'],unit)
            if kind=='leaf':
                curve=seed['program']['leaves'][i]['curve'];area=model.base.books.source.stock.short.old.leaf_area._area_at
                now=area(Fraction(y[106+i]),curve)['value'];before=area(Fraction(seed['initial_sample']['state'][106+i]),curve)['value']
            else:
                def length(age):return model.base.books.resume.bound.length.calculate_internode_length_point(inputs={
                    'input_id':node['compartment_id'],'origin':'synthetic','thermal_age_basis':'since_internode_emergence',
                    'age_exact':model.q(Fraction(age),'degC_day'),'curve':node['curve']})['length']['value']
                now=length(y[size+i]);before=length(seed['initial_sample']['state'][size+i])
            result[key]={name:model.q(v,unit)for name,v in [('potential_exact',potential),('realized_exact',realized),('deficit_exact',potential-realized),
                ('lifetime_potential_exact',lp),('lifetime_realized_exact',lr),('lifetime_deficit_exact',lp-lr),
                ('canonical_gap_exact',Fraction(y[offset+i])-Fraction(now)),('canonical_potential_difference_exact',Fraction(now)-Fraction(before)-potential)]}
    return result


def produce_material_artifact(directory,access,*,handle):
    _need(type(handle)is model.Handle and handle._token is model._TOKEN,'CONTEXT_HOLD: genuine selected material handle required')
    target=Path(directory)
    ws=handle._workspace;f=ws.forcing_workspace;b=f.source_workspace
    parents=[Path(v).resolve()for v in [ws.archive_directory,f.archive_directory,b.archive_directory,b.source_directory]]
    resolved=target.resolve()
    _need(target.is_absolute()and not target.is_symlink()and target.absolute()==resolved
        and all(resolved!=p and p not in resolved.parents and resolved not in p.parents for p in parents),
        'STORAGE_HOLD: separate nonsymlink material artifact output required')
    with model._session(handle._definition,ws)as s:
        cursor,current=model._restore(s,handle.cursor_sha256)
        _need(model.raw(current,model.base.CURRENT_MAX)==handle._current and model.raw(cursor,model.base.CURRENT_MAX)==handle._cursor
            and model.raw(s.basis)==handle._basis,'CONTEXT_HOLD: unchanged actual material handle bytes required')
        pins=reader._pins();_need(pins['backend/app/crop_supply_material_artifact_producer.py']==CODE_SHA256,
            'CODE_HOLD: current loaded material producer required')
        original=s.parent.origin
        selected={'original':{h:raw for h,(raw,_)in original.source_witnesses.items()}}
        for kind,session in [('base',original),('forcing',s.parent),('material',s)]:
            selected[kind]={h:session.archive.get(h,maximum=reader.MAX)for h in session.archive_witnesses}
        _need(all(sha256(raw).hexdigest()==h for blobs in selected.values()for h,raw in blobs.items()),'HASH_HOLD: original source bytes required')
        before_geometry=_before_geometry(s)
        model._check(s)
        with MorphologyBlobStore(target,access,write=True)as out:
            groups={}
            for kind,blobs in selected.items():
                groups[kind]=[]
                for h,raw in sorted(blobs.items()):
                    _need(len(raw)<=reader.MAX,'CAPACITY_HOLD: bounded individual replay blob required')
                    _need(out.put(raw,maximum=reader.MAX)==h,'HASH_HOLD: original raw source identity required')
                    groups[kind].append({'sha256':h,'bytes':len(raw)})
            source={'original_root':{'sha256':original.definition['source']['artifact_sha256'],'bytes':len(reader.raw(original.manifest))},
                'source_frame_index':original.definition['source']['frame_index'],'base':deepcopy(s.parent.definition['source']),
                'forcing':deepcopy(s.definition['source']),'material':{'definition_sha256':s.definition_ref,'cursor_sha256':handle.cursor_sha256}}
            manifest={**reader.FLAGS,'code_sha256':pins,'source':source,'blob_groups':groups,'before_geometry_diagnostics':before_geometry,
                'effective_rights':deepcopy(s.rights),'window':{},'terminal':{},'frames':[],
                'notice':deepcopy(original.manifest['root_inputs']['license_notice'])}
            def obj(h,kind):
                _need(h in selected[kind],'SOURCE_HOLD: exact selected source closure required')
                return reader.legacy._parse(selected[kind][h],reader.MAX)
            chains,bases,point,rights=reader._graph(manifest,obj,original.manifest)
            frames=reader._frames(manifest,chains,bases,point,s.parent.definition)
            manifest['frames']=[reader.frame_descriptor(v)for v in frames]
            manifest['window']={'source_event_id':point['source_event']['source_event_id'],'first_at':deepcopy(frames[0]['at']),
                'last_at':deepcopy(frames[-1]['at']),'covers_whole_season':False,'selection':'one_adopted_material_and_confirmed_remainder'}
            manifest['terminal']={'status':'completed'if current['phase']=='declared_end'else'confirmed_prefix','hold':None,'scope':'declared_synthetic_forcing_plan_only'}
            raw=reader.raw(manifest);_need(len(raw)<=reader.MAX,'CAPACITY_HOLD: bounded material artifact root required')
            root=sha256(raw).hexdigest();_,_,raws=reader._load(out,root,unpublished_raw=raw)
            model._check(s);reader._fence(out,manifest,raws)
            _need(model.raw(current,model.base.CURRENT_MAX)==handle._current and model.raw(cursor,model.base.CURRENT_MAX)==handle._cursor,
                'CONTEXT_HOLD: source handle changed during production')
            result=out.put(raw,maximum=reader.MAX);reader.legacy._read(out,result,raws);reader._fence(out,manifest,raws);model._check(s)
            return result
