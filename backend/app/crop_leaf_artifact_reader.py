"""Compute-free typed projection of explicitly trusted synthetic leaf artifacts."""
from fractions import Fraction
from hashlib import sha256
from math import gcd
import re

from .crop_morphology_artifact_io import MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import FLAGS, _canonical, _closed, _hash, _id, _utc, _quantity, _parse
from .crop_rational_morphology_artifact_reader import (
    SOURCE_PATHS as STEM_SOURCE_PATHS, _load_manifest as _stem_manifest,
    read_rational_morphology_frame, read_rational_morphology_manifest,
)


MAX = 2*1024**2
MODEL_VERSIONS = {'rate':'leaf-logistic-thermal-area-rate-research-v1',
    'change':'leaf-logistic-area-change-research-v1','point':'leaf-logistic-canonical-area-point-research-v1',
    'area':'leaf-logistic-canonical-area-state-research-v1','clock':'leaf-rational-air-thermal-clock-research-v1',
    'leaf_state':'leaf-rational-air-area-state-research-v1','inventory':'declared-leaf-inventory-research-v1'}
DISPLAY_POLICY = {'version':'stored-leaf-m2-authored-blade-triangles-v1','surface':'one_sided_authored_leaflet_triangles',
    'petiole_rachis_area_excluded':True,'placement':'declared_attachment_upper_end_authored_angles_v1',
    'length_width_shape':'authored_uniform_scale_not_cultivar_prediction','leaf_count':'declared_initial_only'}
SOURCE_PATHS = tuple(dict.fromkeys((*STEM_SOURCE_PATHS,*(f'backend/app/{name}.py' for name in (
    'crop_leaf_expansion','crop_leaf_area_change','crop_leaf_area','crop_rational_leaf_area','crop_leaf_inventory',
    'crop_leaf_artifact_reader','crop_leaf_artifact_producer')))))
ROOT_CONSTANTS = {'schema_version':'leaf-area-research-artifact-v1',**FLAGS,'status':'completed_software_fixture',
    'time_kind':'synthetic_model_clock_not_observation','parameter_scope':'synthetic_software_fixture_only',
    'model_versions':MODEL_VERSIONS,'display_policy':DISPLAY_POLICY}
ROOT_FIELDS = set(ROOT_CONSTANTS)|{'program_sha256','program_bytes','program_rights','stem_artifact_sha256',
    'stem_program_sha256','time_origin_utc','initial_at_elapsed_seconds_exact','declared_leaves',
    'code_sha256','initial_state_sha256','terminal_state_sha256','samples'}
CLOCK_KEYS = {'origin','age_basis','temperature_basis','leaf_id','time_origin_utc','emerged_elapsed_seconds_exact',
              'at_elapsed_seconds_exact','base_temperature','age_exact'}


def _digest(value):
    return sha256(_canonical(value)).hexdigest()


def _exact(q,unit):
    _closed(q,{'numerator','denominator','unit'});_need(q['unit']==unit,'UNIT_HOLD: exact quantity unit mismatch')
    for key in ('numerator','denominator'):
        _need(type(q[key]) is str and re.fullmatch(r'0|[1-9][0-9]{0,1023}',q[key]),'FORMAT_HOLD: canonical exact quantity required')
    n,d=int(q['numerator']),int(q['denominator'])
    _need(d>0 and gcd(n,d)==1,'FORMAT_HOLD: reduced exact quantity required');return Fraction(n,d)


def _clock(c):
    _closed(c,CLOCK_KEYS);_need(c['origin']=='synthetic' and c['age_basis']=='since_leaf_emergence'
        and c['temperature_basis']=='indoor_air_piecewise_constant','SCOPE_HOLD: explicit synthetic leaf clock required')
    _id(c['leaf_id']);_utc(c['time_origin_utc']);_quantity(c['base_temperature'],'degC')
    birth,at=(_exact(c[k],'s') for k in ('emerged_elapsed_seconds_exact','at_elapsed_seconds_exact'))
    age=_exact(c['age_exact'],'degC_day')
    _need(birth<=at and (birth!=at or age==0),'TIME_HOLD: leaf emergence mismatch')


def _curve(c):
    _closed(c,{'profile_id','origin','values'});_id(c['profile_id']);_need(c['origin']=='synthetic','SCOPE_HOLD: synthetic leaf curve required')
    units={'maximum_area':'m2','steepness':'1/degC_day','inflection_age':'degC_day'};_closed(c['values'],units)
    normalized={}
    for name,unit in units.items():
        q=c['values'][name];_quantity(q,unit,positive=name!='inflection_age')
        _need(q['value']>=0,'FORMAT_HOLD: nonnegative curve quantity required')
        normalized[name]={'value':float(q['value']),'unit':unit}
    curve={**c,'values':normalized}
    return _digest({'rate_model_version':MODEL_VERSIONS['rate'],'curve':curve})


def _rights(r):
    grants={'ownership_asserted','access','store','use','transform','display'}
    _closed(r,grants|{'declaration_id','revision','declared_at_utc','redistribute'})
    _id(r['declaration_id']);_id(r['revision']);_utc(r['declared_at_utc'])
    _need(all(r[k] is True for k in grants) and type(r['redistribute']) is bool,'RIGHTS_HOLD: explicit owned synthetic rights required')


def _program(p):
    _closed(p,{'schema_version','origin','program_id','rights','stem','initialization','display_policy'})
    _need(p['schema_version']=='leaf-software-program-v1' and p['origin']=='synthetic'
          and p['display_policy']==DISPLAY_POLICY,'SCOPE_HOLD: supported leaf research program required')
    _id(p['program_id']);_rights(p['rights']);_closed(p['stem'],{'artifact_sha256','program_sha256'})
    for value in p['stem'].values():_hash(value)
    initial=p['initialization'];_closed(initial,{'input_id','time_origin_utc','at_elapsed_seconds_exact','leaves'})
    _id(initial['input_id']);_utc(initial['time_origin_utc']);_exact(initial['at_elapsed_seconds_exact'],'s')
    _need(type(initial['leaves']) is list and 1<=len(initial['leaves'])<=512,'CAPACITY_HOLD: bounded declared leaf input required')
    declarations=[];seen=set()
    for item in initial['leaves']:
        _closed(item,{'attachment_internode_id','initialization'});_id(item['attachment_internode_id']);q=item['initialization']
        _closed(q,{'input_id','clock_state','curve','normalization','initial_area'});_id(q['input_id']);_clock(q['clock_state'])
        _need(q['normalization']=='zero_lower_asymptote_sigmoid_v1','MODEL_HOLD: explicit leaf normalization required')
        _quantity(q['initial_area'],'m2',positive=True);curve_sha=_curve(q['curve']);clock=q['clock_state']
        _need(clock['time_origin_utc']==initial['time_origin_utc'] and clock['at_elapsed_seconds_exact']==initial['at_elapsed_seconds_exact']
              and clock['leaf_id'] not in seen,'STATE_HOLD: input leaf scope or identity mismatch');seen.add(clock['leaf_id'])
        declarations.append({'leaf_id':clock['leaf_id'],'attachment_internode_id':item['attachment_internode_id'],
            'emerged_elapsed_seconds_exact':clock['emerged_elapsed_seconds_exact'],'curve_sha256':curve_sha})
    return {'time_origin_utc':initial['time_origin_utc'],'initial_at_elapsed_seconds_exact':initial['at_elapsed_seconds_exact'],
            'declared_leaves':declarations}


def _load(store,root_sha):
    m=_parse(store.get(root_sha,maximum=MAX),MAX);_closed(m,ROOT_FIELDS)
    _need(all(m[k]==v for k,v in ROOT_CONSTANTS.items()),'MODEL_HOLD: unsupported leaf artifact')
    _closed(m['code_sha256'],SOURCE_PATHS)
    for value in m['code_sha256'].values():_hash(value)
    raw=store.get(m['program_sha256'],maximum=MAX);_need(type(m['program_bytes']) is int and len(raw)==m['program_bytes'],'HASH_HOLD: leaf program bytes mismatch')
    p=_parse(raw,MAX);meta=_program(p)
    _need(m['program_rights']==p['rights'] and all(m[k]==v for k,v in meta.items()),'HASH_HOLD: original leaf input mismatch')
    _need(m['stem_artifact_sha256']==p['stem']['artifact_sha256'] and m['stem_program_sha256']==p['stem']['program_sha256'],
          'HASH_HOLD: stem reference mismatch')
    stem=_stem_manifest(store,m['stem_artifact_sha256'])
    _need(stem['program_sha256']==m['stem_program_sha256'],'HASH_HOLD: original stem input mismatch')
    _hash(m['initial_state_sha256']);previous=m['initial_state_sha256'];samples=m['samples']
    _need(type(samples) is list and len(samples)==len(stem['samples']),'FORMAT_HOLD: complete leaf samples required')
    for i,(d,s) in enumerate(zip(samples,stem['samples'],strict=True)):
        _closed(d,{'index','at','result_sha256','result_bytes','payload_sha256','payload_bytes','input_state_sha256',
                   'state_sha256','input_sha256','stem_result_sha256'})
        _need(type(d['index']) is int and d['index']==i and d['at']==s['at'] and d['stem_result_sha256']==s['result_sha256']
              and d['input_state_sha256']==previous,'HASH_HOLD: leaf/stem sample chain mismatch')
        for key in ('result_bytes','payload_bytes'):_need(type(d[key]) is int and 0<d[key]<=MAX,'CAPACITY_HOLD: bounded leaf result required')
        for key in ('result_sha256','payload_sha256','input_state_sha256','state_sha256','input_sha256','stem_result_sha256'):_hash(d[key])
        previous=d['state_sha256']
    _need(m['terminal_state_sha256']==previous,'HASH_HOLD: terminal leaf state mismatch')
    return m,p


def _frame_payload(r,stem,index,p):
    meta=_program(p);_closed(r,{'model_version',*FLAGS,'input_sha256','state','tracked_leaf_count','tracked_leaf_area',
                               'leaf_area_changes','tracked_area_change'})
    _need(r['model_version']==MODEL_VERSIONS['inventory'] and all(r[k]==v for k,v in FLAGS.items()),'MODEL_HOLD: supported stored leaf result required')
    _hash(r['input_sha256']);s=r['state'];_closed(s,{'model_version','origin','time_origin_utc','at_elapsed_seconds_exact','initial_inventory','leaves'})
    delta=_utc(stem['at'])-_utc(meta['time_origin_utc']);elapsed=delta.days*86400+delta.seconds
    _need(s['model_version']==MODEL_VERSIONS['inventory'] and s['origin']=='synthetic' and s['time_origin_utc']==meta['time_origin_utc']
          and _exact(s['at_elapsed_seconds_exact'],'s')==elapsed and stem.get('time_origin_utc')==meta['time_origin_utc'],
          'TIME_HOLD: same leaf/stem model UTC required')
    initial=s['initial_inventory'];_closed(initial,{'at_elapsed_seconds_exact','leaf_attachments'})
    refs=[{k:d[k] for k in ('leaf_id','attachment_internode_id')} for d in meta['declared_leaves']]
    _need(initial['at_elapsed_seconds_exact']==meta['initial_at_elapsed_seconds_exact'] and initial['leaf_attachments']==refs,
          'STATE_HOLD: original declared inventory mismatch')
    _need(type(s['leaves']) is list and len(s['leaves'])==len(refs) and type(r['tracked_leaf_count']) is int
          and r['tracked_leaf_count']==len(refs),'FORMAT_HOLD: original leaf count required')
    stem_ids={n['internode_id'] for n in stem['internodes']};leaves=[]
    for item,declared,source in zip(s['leaves'],meta['declared_leaves'],p['initialization']['leaves'],strict=True):
        _closed(item,{'attachment_internode_id','state'});n=item['state'];_closed(n,{'model_version','clock_state','area_state','clock_anchor'})
        _need(n['model_version']==MODEL_VERSIONS['leaf_state'],'MODEL_HOLD: supported rational leaf state required')
        c=n['clock_state'];a=n['area_state'];anchor_clock=n['clock_anchor'];_clock(c);_clock(anchor_clock)
        _closed(a,{'model_version','origin','thermal_age_basis','normalization','leaf_id','curve','curve_sha256','age_exact','area','anchor'})
        _need(a['model_version']==MODEL_VERSIONS['area'] and a['origin']=='synthetic' and a['thermal_age_basis']=='since_leaf_emergence'
              and a['normalization']=='zero_lower_asymptote_sigmoid_v1','MODEL_HOLD: supported canonical leaf area required')
        _need(item['attachment_internode_id']==declared['attachment_internode_id'] and item['attachment_internode_id'] in stem_ids
              and c['leaf_id']==a['leaf_id']==declared['leaf_id'] and c['time_origin_utc']==meta['time_origin_utc']
              and c['at_elapsed_seconds_exact']==s['at_elapsed_seconds_exact'] and c['emerged_elapsed_seconds_exact']==declared['emerged_elapsed_seconds_exact']
              and c['age_exact']==a['age_exact'],'STATE_HOLD: leaf/stem identity or clock mismatch')
        _exact(a['age_exact'],'degC_day');_quantity(a['area'],'m2',positive=True)
        _need(_curve(a['curve'])==a['curve_sha256']==declared['curve_sha256'] and a['area']['value']<=a['curve']['values']['maximum_area']['value'],
              'HASH_HOLD: original leaf curve required')
        anchor=a['anchor'];_closed(anchor,{'leaf_id','age_exact','curve_sha256','requested_area','canonical_area'})
        _quantity(anchor['requested_area'],'m2',positive=True);_quantity(anchor['canonical_area'],'m2',positive=True)
        _need(anchor['leaf_id']==a['leaf_id'] and anchor['curve_sha256']==a['curve_sha256']
              and anchor['age_exact']==anchor_clock['age_exact'] and anchor['requested_area']==source['initialization']['initial_area']
              and _exact(anchor['age_exact'],'degC_day')<=_exact(a['age_exact'],'degC_day'),'STATE_HOLD: initial leaf area receipt mismatch')
        constants=CLOCK_KEYS-{'at_elapsed_seconds_exact','age_exact'}
        _need(all(c[k]==anchor_clock[k] for k in constants) and anchor_clock==source['initialization']['clock_state'],
              'STATE_HOLD: original initial leaf clock required')
        leaves.append({**declared,'age_exact':a['age_exact'],'area':a['area']})
    _quantity(r['tracked_leaf_area'],'m2',positive=True);_quantity(r['tracked_area_change'],'m2')
    _need(r['tracked_area_change']['value']>=0 and type(r['leaf_area_changes']) is list and len(r['leaf_area_changes'])==len(leaves),
          'FORMAT_HOLD: bounded stored leaf changes required')
    for item,d in zip(r['leaf_area_changes'],leaves,strict=True):
        _closed(item,{'leaf_id','area_change'});_need(item['leaf_id']==d['leaf_id'],'STATE_HOLD: leaf change identity mismatch')
        _quantity(item['area_change'],'m2');_need(item['area_change']['value']>=0,'FORMAT_HOLD: nonnegative stored leaf change required')
    return {'schema_version':'leaf-area-replay-frame-v1',**FLAGS,'result_sha256':_digest(r),'input_sha256':r['input_sha256'],
        'index':index,'at':stem['at'],'time_origin_utc':meta['time_origin_utc'],'tracked_leaf_count':r['tracked_leaf_count'],
        'tracked_leaf_area':r['tracked_leaf_area'],'leaves':leaves,'stem':stem}


def read_leaf_area_manifest(directory,access,root_sha256):
    with MorphologyBlobStore(directory,access) as store:return _load(store,root_sha256)[0]


def read_leaf_area_frame(directory,access,root_sha256,*,index):
    with MorphologyBlobStore(directory,access) as store:
        m,p=_load(store,root_sha256);_need(type(index) is int and 0<=index<len(m['samples']),'INDEX_HOLD: bounded explicit leaf frame required')
        d=m['samples'][index];raw=store.get(d['result_sha256'],maximum=MAX);r=_parse(raw,MAX)
        _need(len(raw)==d['result_bytes'] and _canonical(r)==raw and r.get('input_sha256')==d['input_sha256']
              and _digest(r.get('state'))==d['state_sha256'],'HASH_HOLD: original leaf result required')
        stem=read_rational_morphology_frame(directory,access,m['stem_artifact_sha256'],index=index)
        expected=_frame_payload(r,stem,index,p);raw=store.get(d['payload_sha256'],maximum=MAX);payload=_parse(raw,MAX)
        _need(len(raw)==d['payload_bytes'] and _canonical(payload)==raw and payload==expected,'HASH_HOLD: original leaf projection required')
        return {'artifact_sha256':root_sha256,**payload}
