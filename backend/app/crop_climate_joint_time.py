"""Exact UTC labels for accepted elapsed-grid results; no numerical replay."""
from dataclasses import dataclass,field
from datetime import datetime,timedelta,timezone
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import re

from . import crop_climate_joint_continuation as continuation

VERSION='joint-crop-climate-time-binding-research-v1'
TIME_RULE='UTC_POSIX_integer_microseconds_decimal_step_v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_RESULT_BYTES=8*1024**2
_TOKEN=object()
_STAMP=re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})',re.ASCII)


class TimeBindingRejected(ValueError):
    """Unsupported time representation or mixed calculation identity."""


def _need(condition,reason):
    if not condition:raise TimeBindingRejected(reason)


def _origin(value,program):
    _need(type(value) is dict and set(value)=={'input_id','origin','start_at','precision'},'ORIGIN_HOLD: closed origin')
    _need(type(value['input_id']) is str and 1<=len(value['input_id'])<=200 and value['input_id'].strip()==value['input_id'],
        'ORIGIN_HOLD: input ID')
    _need(value['origin'] in ('synthetic','reference_calculation') and value['origin']==program['scenario']['origin']
        and value['precision']=='microsecond','ORIGIN_HOLD: scope/precision')
    stamp=value['start_at']
    _need(type(stamp) is str and _STAMP.fullmatch(stamp) and not stamp.endswith('-00:00'),
        'ORIGIN_HOLD: explicit supported RFC3339 offset and at most six fractional digits')
    if not stamp.endswith('Z'):
        _need(int(stamp[-5:-3])<24 and int(stamp[-2:])<60,'ORIGIN_HOLD: offset hours/minutes')
    try:return datetime.fromisoformat(stamp.replace('Z','+00:00')).astimezone(timezone.utc)
    except (ValueError,OverflowError) as exc:raise TimeBindingRejected('ORIGIN_HOLD: date/offset/range') from exc


def _stamp(start,step_us,index):
    try:return (start+timedelta(microseconds=step_us*index)).isoformat(timespec='microseconds').replace('+00:00','Z')
    except OverflowError as exc:raise TimeBindingRejected('RANGE_HOLD: UTC year 1..9999') from exc


def _manifest(context,origin):
    try:program,_=continuation._context(context)
    except continuation.ContinuationRejected as exc:raise TimeBindingRejected('CONTEXT_HOLD: '+str(exc)) from exc
    start=_origin(origin,program);step_decimal=str(program['step_seconds']);step=Fraction(step_decimal)*1_000_000
    _need(step.denominator==1 and step>0,'PRECISION_HOLD: exact integer microsecond step required')
    step_us=step.numerator
    return {'version':VERSION,'time_rule':TIME_RULE,'time_code_sha256':CODE_SHA256,'context_sha256':context.root_sha256,
        'origin':origin,'start_utc':_stamp(start,step_us,0),'end_utc':_stamp(start,step_us,program['step_count']),
        'step_seconds_decimal':step_decimal,'step_microseconds':step_us,'step_count':program['step_count'],
        'scope':'software_research_only','G0_G4':'not_assessed'}


@dataclass(frozen=True)
class Binding:
    _manifest:bytes=field(repr=False)
    sha256:str
    _context:continuation.Context=field(repr=False)
    _token:object=field(repr=False)

    @property
    def manifest(self):return json.loads(self._manifest)


def prepare_binding(context,*,origin):
    raw=continuation._canonical(_manifest(context,origin))
    return Binding(raw,sha256(raw).hexdigest(),context,_TOKEN)


def _binding(binding,expected_sha256=None):
    _need(type(binding) is Binding and binding._token is _TOKEN and type(binding._manifest) is bytes
        and len(binding._manifest)<=16384,'BINDING_HOLD: prepared bounded binding required')
    if expected_sha256 is not None:
        _need(continuation._digest(expected_sha256) and expected_sha256==binding.sha256,'BINDING_HOLD: trusted binding SHA')
    try:
        manifest=binding.manifest
        _need(sha256(binding._manifest).hexdigest()==binding.sha256
            and continuation._canonical(_manifest(binding._context,manifest['origin']))==binding._manifest,
            'BINDING_HOLD: changed time/context/origin identity')
    except (ValueError,TypeError,KeyError,AttributeError) as exc:raise TimeBindingRejected('BINDING_HOLD: '+str(exc)) from exc
    return manifest,binding._context.program


def at_index(binding,index):
    manifest,_=_binding(binding)
    return _at(manifest,index)


def _at(manifest,index):
    _need(type(index) is int and 0<=index<=manifest['step_count'],'INDEX_HOLD: original integer grid index')
    return _stamp(datetime.fromisoformat(manifest['start_utc'].replace('Z','+00:00')),manifest['step_microseconds'],index)


def _point(manifest,record,program):
    _need(type(record) is dict and 'step_index' in record and 'elapsed_seconds' in record,'SOURCE_HOLD: timed record')
    index=record['step_index'];at=_at(manifest,index)
    _need(type(record['elapsed_seconds']) is float and record['elapsed_seconds']==index*program['step_seconds'],
        'SOURCE_HOLD: original binary64 elapsed required')
    return {'step_index':index,'at':at}


def _checkpoint(binding,checkpoint,manifest,program):
    try:raw=continuation.checkpoint_bytes(binding._context,checkpoint)
    except continuation.ContinuationRejected as exc:raise TimeBindingRejected('SOURCE_HOLD: '+str(exc)) from exc
    value=json.loads(raw);n=value['next_index'];point=_point(manifest,value['last_confirmed'],program)
    _need(type(n) is int and 0<=n<=program['step_count']+1 and point['step_index']==max(0,n-1),
        'SOURCE_HOLD: checkpoint position')
    for kind,indices in (('output',program['output_steps']),('event',[e['step_index'] for e in program['events']])):
        _need(type(value[kind+'_cursor']) is int and value[kind+'_cursor']==sum(i<n for i in indices)
            and continuation._digest(value[kind+'_prefix_sha256']),'SOURCE_HOLD: checkpoint cursor/prefix')
    return value,point


def _result(binding,payload):
    payload={'version':VERSION,'binding_sha256':binding.sha256,'scope':'software_research_only','G0_G4':'not_assessed',**payload}
    raw=continuation._canonical(payload)
    _need(len(raw)+84<=MAX_RESULT_BYTES,'RESOURCE_HOLD: bound result byte limit')
    return {**payload,'result_sha256':sha256(raw).hexdigest()}


def bind_checkpoint(binding,checkpoint,*,expected_binding_sha256):
    _need(continuation._digest(expected_binding_sha256),'BINDING_HOLD: trusted binding SHA required')
    manifest,program=_binding(binding,expected_binding_sha256);value,point=_checkpoint(binding,checkpoint,manifest,program)
    return _result(binding,{'source_checkpoint_sha256':checkpoint.sha256,'source':value,'time':{**point,'next_index':value['next_index']}})


def _source(context,chunk):
    _need(type(chunk) is dict,'SOURCE_HOLD: chunk dictionary required')
    pack=dict(chunk);cp=pack.get('checkpoint')
    if cp is not None:
        try:raw=continuation.checkpoint_bytes(context,cp)
        except continuation.ContinuationRejected as exc:raise TimeBindingRejected('SOURCE_HOLD: '+str(exc)) from exc
        pack['checkpoint']={'sha256':cp.sha256,'value':json.loads(raw)}
    try:raw=continuation._canonical(pack)
    except (ValueError,TypeError,RecursionError) as exc:raise TimeBindingRejected('SOURCE_HOLD: canonical finite JSON required') from exc
    _need(len(raw)<=MAX_RESULT_BYTES,'RESOURCE_HOLD: source chunk byte limit')
    return json.loads(raw),sha256(raw).hexdigest()


def source_chunk_sha256(context,chunk):
    """Producer-side transport digest; the digest does not authenticate custody."""
    return _source(context,chunk)[1]


def bind_chunk(binding,before_checkpoint,chunk,*,expected_chunk_sha256,expected_binding_sha256):
    _need(continuation._digest(expected_binding_sha256),'BINDING_HOLD: trusted binding SHA required')
    manifest,program=_binding(binding,expected_binding_sha256)
    before,_=_checkpoint(binding,before_checkpoint,manifest,program)
    source,digest=_source(binding._context,chunk)
    _need(continuation._digest(expected_chunk_sha256) and digest==expected_chunk_sha256,'SOURCE_HOLD: trusted chunk SHA required')
    keys={'status','scope','claim_scope','G0_G4','manifest','context_sha256','steps','planned_steps','output_start','event_start',
        'samples','events','last_confirmed','checkpoint','hold','confirmed_numerical_rhs_evaluations','checkpoint_validation_rhs_evaluations'}
    _need(set(source)==keys and source['status'] in ('yielded','completed','hold')
        and source['scope']=='software_research_only' and source['claim_scope']=='synthetic_joint_crop_climate_continuation_only'
        and source['G0_G4']=='not_assessed' and source['context_sha256']==binding._context.root_sha256
        and continuation._canonical(source['manifest'])==binding._context._manifest,'SOURCE_HOLD: closed matching source identity')
    begin=before['next_index'];count=program['step_count']
    _need(begin<=count and type(source['planned_steps']) is int and source['planned_steps']==count,'SOURCE_HOLD: source period')
    for kind in ('output','event'):
        _need(type(source[kind+'_start']) is int and source[kind+'_start']==before[kind+'_cursor'],
            'SOURCE_HOLD: source/before cursor mismatch')
    held=source['status']=='hold';cp=chunk['checkpoint'];hold=source['hold']
    if held:
        _need(cp is None and type(hold) is dict and set(hold)=={'step_index','elapsed_seconds','phase','reason'}
            and hold['phase'] in ('initial','interval','global-step-balance','event','global-event-balance')
            and type(hold['reason']) is str and 0<len(hold['reason'])<=4096,'SOURCE_HOLD: explicit failed boundary')
        hold_point=_point(manifest,hold,program);end=hold['step_index'];after=None
    else:
        _need(hold is None and cp is not None,'SOURCE_HOLD: checkpoint/hold status')
        after,_=_checkpoint(binding,cp,manifest,program);end=after['next_index'];hold_point=None
        _need((source['status']=='completed')==(end==count+1),'SOURCE_HOLD: completion position')
    _need(type(end) is int and begin<=end<=min(begin+continuation.MAX_CHUNK_BOUNDARIES,count+1)
        and (held or end>begin) and (not held or end<min(begin+continuation.MAX_CHUNK_BOUNDARIES,count+1)),
        'SOURCE_HOLD: bounded original boundary range')
    times={}
    for key,kind,indices in (('samples','output',program['output_steps']),('events','event',[e['step_index'] for e in program['events']])):
        rows=source[key]
        _need(type(rows) is list and len(rows)<=continuation.MAX_CHUNK_BOUNDARIES,'SOURCE_HOLD: bounded rows')
        points=[_point(manifest,row,program) for row in rows]
        _need([p['step_index'] for p in points]==[i for i in indices if begin<=i<end],
            'SOURCE_HOLD: missing/extra/out-of-order boundary records')
        prefix=before[kind+'_prefix_sha256']
        for row in rows:prefix=continuation._prefix(prefix,row)
        if after is not None:
            _need(after[kind+'_cursor']==before[kind+'_cursor']+len(rows) and after[kind+'_prefix_sha256']==prefix,
                'SOURCE_HOLD: changed prefix/cursor')
        times[key]=points
    last=source['last_confirmed'];point=_point(manifest,last,program)
    expected_last=end if held and hold['phase'] in ('event','global-event-balance') else max(0,end-1)
    _need(point['step_index']==expected_last and type(source['steps']) is int and source['steps']==expected_last,
        'SOURCE_HOLD: last confirmed position')
    if after is not None:
        _need(continuation._canonical(after['last_confirmed'])==continuation._canonical(last),'SOURCE_HOLD: checkpoint/last mismatch')
    steps=expected_last-max(0,begin-1)
    _need(type(source['confirmed_numerical_rhs_evaluations']) is int
        and source['confirmed_numerical_rhs_evaluations']==5*steps+2*len(source['events'])
        and type(source['checkpoint_validation_rhs_evaluations']) is int and source['checkpoint_validation_rhs_evaluations']==1,
        'SOURCE_HOLD: confirmed call accounting')
    times.update(last_confirmed=point,hold=hold_point)
    return _result(binding,{'source_chunk_sha256':digest,'before_checkpoint_sha256':before_checkpoint.sha256,'source':source,'times':times})
