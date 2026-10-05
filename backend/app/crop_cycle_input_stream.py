"""Bounded content-addressed input pages for synthetic crop research programs."""
from bisect import bisect_right
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat

from . import crop_plant_startup_integration as physical

VERSION='crop-cycle-input-packet-v1'
CURSOR_VERSION='crop-cycle-input-cursor-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
KINDS=('segments','events','anchors','outputs')
BLOCK_RECORDS=128
MAX_RECORDS=131072
MAX_BLOCK_BYTES=2*1024*1024
MAX_ROOT_BYTES=1024*1024
MAX_PACKET_BYTES=512*1024*1024
MAX_CURSOR_BYTES=65536


class CycleInputRejected(ValueError):
    """Invalid or unsupported input; no crop calculation or adoption performed."""


def _need(condition,reason):
    if not condition:raise CycleInputRejected(reason)


def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def _hash(value):return sha256(_canonical(value)).hexdigest()
def _digest(value):return type(value) is str and re.fullmatch(r'[0-9a-f]{64}',value) is not None
def _fraction(value):return {'numerator':str(value.numerator),'denominator':str(value.denominator)}


def _json(raw):
    def pairs(items):
        result={}
        for key,value in items:
            _need(key not in result,'INPUT_HOLD: duplicate JSON key');result[key]=value
        return result
    def constant(value):raise CycleInputRejected('INPUT_HOLD: nonfinite JSON constant')
    try:return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
    except (ValueError,UnicodeDecodeError,RecursionError) as exc:
        raise CycleInputRejected('INPUT_HOLD: invalid UTF-8 JSON') from exc


def _profiles(growth_profile,cohort_profile,transport_profile):
    _need(type(growth_profile) is physical.plant.ReferenceParameters
          and type(cohort_profile) is physical.fruit.ReferenceFruitCohortParameters
          and type(transport_profile) is physical.transport.ReferenceFruitTransportParameters,
          'PROFILE_HOLD: exact pinned profiles required')
    return {k:p.sha256 for k,p in (('growth_profile',growth_profile),
        ('cohort_profile',cohort_profile),('transport_profile',transport_profile))}


def _block(raw,scalars,arrays=None):
    value=physical.legacy._block(raw,scalars,arrays)
    _need(value['origin']=='synthetic','SOURCE_HOLD: only synthetic software inputs supported')
    return value


def _normalise(kind,raw):
    try:
        if kind=='initial_state':return _block(raw,physical.legacy.coupled.PLANT_UNITS,physical.ARRAY_UNITS)
        if kind in ('anchors','outputs'):
            physical._utc(raw);return raw
        if kind=='events':
            _need(type(raw) is dict and set(raw)=={'at','removals'},'INPUT_HOLD: closed event required')
            physical._utc(raw['at'])
            return {'at':raw['at'],'removals':_block(raw['removals'],
                {'leaf':physical.plant.MASS_UNIT,'stem_root':physical.plant.MASS_UNIT},{'fruit_fraction':'1'})}
        _need(kind=='segments' and type(raw) is dict and set(raw)=={
            'start','end','forcing','removals','fruit_entry','relative_growth_rate'},'INPUT_HOLD: closed segment required')
        begin,end=physical._utc(raw['start']),physical._utc(raw['end'])
        _need(begin<end,'TIME_HOLD: nonpositive segment')
        return {'start':raw['start'],'end':raw['end'],
            'forcing':_block(raw['forcing'],physical.plant.FORCING_UNITS),
            'removals':_block(raw['removals'],physical.legacy.coupled.REMOVAL_UNITS),
            'fruit_entry':_block(raw['fruit_entry'],physical.legacy.coupled.ENTRY_UNITS),
            'relative_growth_rate':_block(raw['relative_growth_rate'],{}, {'fruit_relative_growth_rate':'1/s'})}
    except physical.legacy.PlantCohortIntegrationHold as exc:
        raise CycleInputRejected(str(exc)) from exc


def _time(kind,record):return record['end'] if kind=='segments' else record['at'] if kind=='events' else record
def _slope(segment,seconds):return Fraction.from_float(segment['forcing']['values']['canopy_temperature']['value'])/Fraction.from_float(seconds)
def _chain(previous,record):return _hash({'previous':previous,'record':record})


def _solver(raw):
    _need(type(raw) is dict and set(raw)=={'method','max_step_seconds','max_steps','roundoff_rule'}
          and raw['method']=='rk4-fixed-v1' and raw['roundoff_rule']=='64-ulp-per-operation-v1',
          'SOLVER_HOLD: pinned closed solver required')
    _need(type(raw['max_step_seconds']) is int and 1<=raw['max_step_seconds']<=3600
          and type(raw['max_steps']) is int and 1<=raw['max_steps']<=40000000,
          'RESOURCE_HOLD: bounded integer solver budgets required')
    return dict(raw)


def write_input_packet(directory,*,initial_state,segments,events,anchors,outputs,solver,
                       growth_profile,cohort_profile,transport_profile,program_id):
    profiles=_profiles(growth_profile,cohort_profile,transport_profile)
    initial=_normalise('initial_state',initial_state);solver=_solver(solver)
    _need(type(program_id) is str and 0<len(program_id)<=256 and bool(program_id.strip()),'INPUT_HOLD: bounded program ID required')
    directory=Path(directory)
    try:directory.mkdir(mode=0o700)
    except OSError as exc:raise CycleInputRejected('STORAGE_HOLD: new packet directory required') from exc
    written=set();packet_bytes=0;clock=Fraction.from_float(initial['values']['temperature_sum']['value'])
    period={};streams={}
    def put(raw,name):
        nonlocal packet_bytes
        if name not in written:
            packet_bytes+=len(raw);_need(packet_bytes<=MAX_PACKET_BYTES,'RESOURCE_HOLD: packet exceeds byte limit')
            with (directory/name).open('xb') as handle:handle.write(raw)
            written.add(name)
    try:
        for kind,records in (('segments',segments),('events',events),('anchors',anchors),('outputs',outputs)):
            try:iterator=iter(records)
            except TypeError as exc:raise CycleInputRejected('INPUT_HOLD: iterable stream required') from exc
            count=0;blocks=[];batch=[];chain=_hash([]);prefix=None
            def flush():
                raw=_canonical(batch);_need(len(raw)<=MAX_BLOCK_BYTES,'RESOURCE_HOLD: input block too large')
                digest=sha256(raw).hexdigest();put(raw,digest+'.json')
                descriptor={'sha256':digest,'start_index':count-len(batch),'count':len(batch),
                    'first_at':_time(kind,batch[0]),'last_at':_time(kind,batch[-1])}
                if kind=='segments':descriptor['clock_prefix']=_fraction(prefix)
                blocks.append(descriptor)
            for record in iterator:
                _need(count<MAX_RECORDS,'RESOURCE_HOLD: input record count exceeded')
                value=_normalise(kind,record)
                if kind=='segments':
                    if not batch:prefix=clock
                    if count==0:period['start']=value['start']
                    period['end']=value['end']
                    clock+=_slope(value,growth_profile.values['seconds_per_day'])*int((physical._utc(value['end'])-physical._utc(value['start'])).total_seconds())
                chain=_chain(chain,value);batch.append(value);count+=1
                if len(batch)==BLOCK_RECORDS:flush();batch=[]
            if batch:flush()
            streams[kind]={'count':count,'record_chain_sha256':chain,'blocks':blocks}
        root={'version':VERSION,'scope':'software_research_only','program_id':program_id,'initial_state':initial,
            'profile_sha256':profiles,'normalization_sha256':{'input_stream':CODE_SHA256,'legacy_helpers':physical.CODE_HASHES['legacy_helpers']},
            'python_version':platform.python_version(),'solver':solver,'period':period,'streams':streams}
        raw=_canonical(root);_need(len(raw)<=MAX_ROOT_BYTES,'RESOURCE_HOLD: input root too large')
        put(raw,'root.json');root_hash=sha256(raw).hexdigest()
        with open_input_packet(directory,root_hash,growth_profile=growth_profile,
                cohort_profile=cohort_profile,transport_profile=transport_profile) as reader:
            plan=reader.plan
        return {'root_sha256':root_hash,'calculation_sha256':reader.calculation_sha256,'packet_bytes':packet_bytes,'plan':plan}
    except BaseException:
        shutil.rmtree(directory)
        raise


def _read(directory_fd,name,limit):
    descriptor=None
    try:
        descriptor=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory_fd)
        status=os.fstat(descriptor)
        _need(stat.S_ISREG(status.st_mode) and status.st_size<=limit,'RESOURCE_HOLD: bounded regular input file required')
        with os.fdopen(descriptor,'rb') as handle:
            descriptor=None;raw=handle.read(limit+1)
        _need(len(raw)<=limit,'RESOURCE_HOLD: input file grew beyond limit')
        return raw
    except OSError as exc:raise CycleInputRejected('STORAGE_HOLD: input file unavailable') from exc
    finally:
        if descriptor is not None:os.close(descriptor)


def open_input_packet(directory,expected_root_sha256,*,growth_profile,cohort_profile,transport_profile):
    return InputPacket(directory,expected_root_sha256,growth_profile,cohort_profile,transport_profile)


class InputPacket:
    def __init__(self,directory,expected_root_sha256,growth_profile,cohort_profile,transport_profile):
        self._fd=None;self._cache={};self._seen=set();self._referenced_bytes=0
        hashes=_profiles(growth_profile,cohort_profile,transport_profile)
        _need(_digest(expected_root_sha256),'INPUT_HOLD: expected root hash required')
        try:
            self._fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            raw=_read(self._fd,'root.json',MAX_ROOT_BYTES)
            _need(sha256(raw).hexdigest()==expected_root_sha256,'HASH_HOLD: input root mismatch')
            self._root=_json(raw);self._raw=raw;self.root_sha256=expected_root_sha256
            self._referenced_bytes=len(raw);self._seconds=growth_profile.values['seconds_per_day']
            self._validate_root(hashes)
            calculation={**self._root,'streams':{k:v for k,v in self._root['streams'].items() if k!='outputs'}}
            self.calculation_sha256=_hash(calculation)
            self._preflight()
        except OSError as exc:
            self.close();raise CycleInputRejected('STORAGE_HOLD: input directory unavailable') from exc
        except BaseException:
            self.close();raise

    @property
    def closed(self):return self._fd is None
    @property
    def manifest(self):return _json(self._raw)
    @property
    def plan(self):return deepcopy(self._plan)
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def close(self):
        if self._fd is not None:os.close(self._fd);self._fd=None
        self._cache.clear()

    def _validate_root(self,profiles):
        root=self._root
        _need(type(root) is dict and set(root)=={'version','scope','program_id','initial_state','profile_sha256',
            'normalization_sha256','python_version','solver','period','streams'},'INPUT_HOLD: closed root required')
        _need(root['version']==VERSION and root['scope']=='software_research_only','SOURCE_HOLD: unsupported input scope/version')
        _need(type(root['program_id']) is str and 0<len(root['program_id'])<=256 and bool(root['program_id'].strip()),'INPUT_HOLD: bounded program ID required')
        _need(root['profile_sha256']==profiles and root['normalization_sha256']=={
            'input_stream':CODE_SHA256,'legacy_helpers':physical.CODE_HASHES['legacy_helpers']}
            and root['python_version']==platform.python_version(),'PROFILE_HOLD: profile/code/environment mismatch')
        _need(_canonical(_normalise('initial_state',root['initial_state']))==_canonical(root['initial_state']),
              'INPUT_HOLD: normalized initial state required')
        _solver(root['solver'])
        _need(type(root['period']) is dict and set(root['period'])=={'start','end'},'TIME_HOLD: exact period required')
        try:self._begin,self._end=(physical._utc(root['period'][k]) for k in ('start','end'))
        except physical.legacy.PlantCohortIntegrationHold as exc:raise CycleInputRejected(str(exc)) from exc
        _need(self._begin<self._end and (self._end-self._begin).total_seconds()<=366*86400,'RESOURCE_HOLD: period exceeds research range')
        _need(type(root['streams']) is dict and set(root['streams'])==set(KINDS),'INPUT_HOLD: four closed streams required')
        for kind,stream in root['streams'].items():
            _need(type(stream) is dict and set(stream)=={'count','record_chain_sha256','blocks'}
                and type(stream['count']) is int and 0<=stream['count']<=MAX_RECORDS and _digest(stream['record_chain_sha256']),
                'RESOURCE_HOLD: bounded stream descriptor required')
            blocks=stream['blocks'];count=stream['count']
            _need(type(blocks) is list and len(blocks)==(count+BLOCK_RECORDS-1)//BLOCK_RECORDS,'RESOURCE_HOLD: exact block count required')
            for i,block in enumerate(blocks):
                fields={'sha256','start_index','count','first_at','last_at'}|({'clock_prefix'} if kind=='segments' else set())
                _need(type(block) is dict and set(block)==fields and _digest(block['sha256'])
                    and type(block['start_index']) is int and block['start_index']==i*BLOCK_RECORDS
                    and type(block['count']) is int and block['count']==min(BLOCK_RECORDS,count-i*BLOCK_RECORDS),
                    'INPUT_HOLD: exact closed block index required')
                for k in ('first_at','last_at'):_normalise('anchors',block[k])
            if kind=='segments':_need(count>=1,'INPUT_HOLD: forcing required')
            if kind=='anchors':_need(count>=2,'INPUT_HOLD: anchor endpoints required')

    def _load(self,kind,block_index):
        _need(not self.closed,'STORAGE_HOLD: input reader closed')
        cached=self._cache.get(kind)
        if cached is not None and cached[0]==block_index:return cached[1]
        block=self._root['streams'][kind]['blocks'][block_index]
        raw=_read(self._fd,block['sha256']+'.json',MAX_BLOCK_BYTES)
        _need(sha256(raw).hexdigest()==block['sha256'],'HASH_HOLD: input block mismatch')
        if block['sha256'] not in self._seen:
            self._seen.add(block['sha256']);self._referenced_bytes+=len(raw)
            _need(self._referenced_bytes<=MAX_PACKET_BYTES,'RESOURCE_HOLD: packet exceeds byte limit')
        records=_json(raw)
        _need(type(records) is list and len(records)==block['count'],'INPUT_HOLD: exact record block required')
        normalized=[_normalise(kind,v) for v in records]
        _need(_canonical(normalized)==raw,'INPUT_HOLD: canonical normalized record block required')
        _need(block['first_at']==_time(kind,normalized[0]) and block['last_at']==_time(kind,normalized[-1]),
            'TIME_HOLD: block index timestamps mismatch')
        self._cache[kind]=(block_index,normalized)
        return normalized

    def _iter(self,kind):
        chain=_hash([])
        for i in range(len(self._root['streams'][kind]['blocks'])):
            for record in self._load(kind,i):
                chain=_chain(chain,record);yield record
        _need(chain==self._root['streams'][kind]['record_chain_sha256'],'HASH_HOLD: whole record chain mismatch')

    def _preflight(self):
        total=Fraction.from_float(self._root['initial_state']['values']['temperature_sum']['value']);previous=self._begin
        for i,segment in enumerate(self._iter('segments')):
            if i%BLOCK_RECORDS==0:
                block=self._root['streams']['segments']['blocks'][i//BLOCK_RECORDS]
                _need(block['clock_prefix']==_fraction(total),'CLOCK_HOLD: original exact prefix mismatch')
            begin,end=physical._utc(segment['start']),physical._utc(segment['end'])
            _need(begin==previous and end<=self._end,'TIME_HOLD: forcing gap/overlap/period mismatch')
            total+=_slope(segment,self._seconds)*int((end-begin).total_seconds());previous=end
        _need(previous==self._end,'TIME_HOLD: forcing does not cover period')
        for kind in ('events','anchors','outputs'):
            previous=None;first=None
            for record in self._iter(kind):
                at=physical._utc(_time(kind,record))
                _need(self._begin<=at<=self._end and (previous is None or previous<at),'TIME_HOLD: unordered/duplicate/external record')
                if first is None:first=at
                previous=at
            if kind=='anchors':_need(first==self._begin and previous==self._end,'TIME_HOLD: anchor endpoints required')
        steps=0;count=0;previous=None;h=self._root['solver']['max_step_seconds']
        for record in self._boundaries():
            at=physical._utc(record['at'])
            if previous is not None:steps+=(int((at-previous).total_seconds())+h-1)//h
            previous=at;count+=1
        _need(steps<=self._root['solver']['max_steps'],'RESOURCE_HOLD: original planned steps exceed budget')
        self._plan={'planned_steps':steps,'boundaries':count,'counts':{k:v['count'] for k,v in self._root['streams'].items()},
                    'packet_referenced_bytes':self._referenced_bytes}

    def _record(self,kind,index):
        count=self._root['streams'][kind]['count']
        return self._load(kind,index//BLOCK_RECORDS)[index%BLOCK_RECORDS] if index<count else None

    def record(self,kind,index):
        _need(kind in KINDS and type(index) is int and 0<=index<self._root['streams'][kind]['count'],
            'INPUT_HOLD: record index out of range')
        return deepcopy(self._record(kind,index))

    def segment(self,index):
        value=self.record('segments',index);block_index=index//BLOCK_RECORDS
        block=self._root['streams']['segments']['blocks'][block_index]
        prefix=block['clock_prefix'];total=Fraction(int(prefix['numerator']),int(prefix['denominator']))
        for earlier in self._load('segments',block_index)[:index%BLOCK_RECORDS]:
            total+=_slope(earlier,self._seconds)*int((physical._utc(earlier['end'])-physical._utc(earlier['start'])).total_seconds())
        return {'segment':value,'clock':{'start':value['start'],'prefix':_fraction(total),'slope':_fraction(_slope(value,self._seconds))}}

    def _next_boundary(self,positions):
        records={k:self._record(k,positions[k]) for k in KINDS}
        pending=[_time(k,v) for k,v in records.items() if k!='outputs' and v is not None]
        if not pending:return None
        at=min(pending);selected={k:v is not None and _time(k,v)==at for k,v in records.items()}
        output=records['outputs']
        _need(output is None or output>=at,'TIME_HOLD: output is not a calculation anchor')
        _need(not selected['outputs'] or selected['anchors'],'TIME_HOLD: output is not a calculation anchor')
        for kind in KINDS:
            if selected[kind]:positions[kind]+=1
        return {'at':at,'forcing_end':selected['segments'],'anchor':selected['anchors'],
                'event':deepcopy(records['events']) if selected['events'] else None,'output':selected['outputs']}

    def _boundaries(self):
        positions={k:0 for k in KINDS}
        while True:
            value=self._next_boundary(positions)
            if value is None:break
            yield value
        _need(positions['outputs']==self._root['streams']['outputs']['count'],'TIME_HOLD: output left outside anchors')

    def _count_through(self,kind,at):
        stream=self._root['streams'][kind];blocks=stream['blocks']
        completed=bisect_right([b['last_at'] for b in blocks],at)
        count=min(completed*BLOCK_RECORDS,stream['count'])
        if completed<len(blocks):count+=sum(_time(kind,v)<=at for v in self._load(kind,completed))
        return count

    def _validate_cursor(self,cursor):
        _need(not self.closed,'STORAGE_HOLD: input reader closed')
        _need(type(cursor) is dict and set(cursor)=={'version','root_sha256','positions','last_at','cursor_sha256'},
            'CURSOR_HOLD: closed input cursor required')
        try:
            _need(len(_canonical(cursor))<=MAX_CURSOR_BYTES,'RESOURCE_HOLD: cursor too large')
            _need(cursor['cursor_sha256']==_hash({k:v for k,v in cursor.items() if k!='cursor_sha256'}),
                'CURSOR_HOLD: cursor hash mismatch')
            _need(cursor['version']==CURSOR_VERSION and cursor['root_sha256']==self.root_sha256,'CURSOR_HOLD: root/version mismatch')
            positions=cursor['positions']
            _need(type(positions) is dict and set(positions)==set(KINDS) and all(
                type(v) is int and 0<=v<=self._root['streams'][k]['count'] for k,v in positions.items()),
                'CURSOR_HOLD: bounded integer positions required')
            if cursor['last_at'] is None:
                _need(all(v==0 for v in positions.values()),'CURSOR_HOLD: initial positions mismatch')
                return
            at=physical._utc(cursor['last_at'])
            _need(self._begin<=at<=self._end,'CURSOR_HOLD: external position')
            _need(all(v==self._count_through(k,cursor['last_at']) for k,v in positions.items()),'CURSOR_HOLD: original prefix mismatch')
            previous=[_time(k,self._record(k,positions[k]-1)) for k in KINDS if k!='outputs' and positions[k]>0]
            _need(previous and max(previous)==cursor['last_at'],'CURSOR_HOLD: not an original boundary')
        except CycleInputRejected:raise
        except (ValueError,TypeError,OverflowError,RecursionError) as exc:
            raise CycleInputRejected('CURSOR_HOLD: invalid input cursor') from exc

    def cursor_bytes(self,cursor):
        self._validate_cursor(cursor)
        return _canonical(cursor)

    def restore_cursor(self,raw_bytes):
        _need(type(raw_bytes) is bytes and len(raw_bytes)<=MAX_CURSOR_BYTES,'RESOURCE_HOLD: bounded cursor bytes required')
        cursor=_json(raw_bytes);self._validate_cursor(cursor)
        return cursor

    def boundary_page(self,cursor=None,limit=BLOCK_RECORDS):
        _need(not self.closed,'STORAGE_HOLD: input reader closed')
        _need(type(limit) is int and 1<=limit<=BLOCK_RECORDS,'RESOURCE_HOLD: bounded integer boundary page required')
        if cursor is None:
            positions={k:0 for k in KINDS};last=None
        else:
            self._validate_cursor(cursor);positions=dict(cursor['positions']);last=cursor['last_at']
        rows=[]
        for _ in range(limit):
            value=self._next_boundary(positions)
            if value is None:break
            rows.append(value);last=value['at']
        complete=all(positions[k]==self._root['streams'][k]['count'] for k in KINDS)
        next_cursor={'version':CURSOR_VERSION,'root_sha256':self.root_sha256,'positions':positions,'last_at':last}
        next_cursor['cursor_sha256']=_hash(next_cursor)
        return {'boundaries':rows,'cursor':next_cursor,'complete':complete}
