"""Bounded immutable crop result commits and readers, before farm custody."""
from bisect import bisect_left, bisect_right
from copy import deepcopy
import fcntl
from hashlib import sha256
import json
from math import fsum
import os
from pathlib import Path
import shutil
import stat
from uuid import uuid4

from . import crop_cycle_stream_execution as engine
from . import crop_cycle_input_stream as inputs
from . import crop_startup_artifact as samples
from . import thermal_run_store as json_store

VERSION = 'crop-cycle-artifact-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
DEPENDENCY_SHA256 = {k:sha256(Path(m.__file__).read_bytes()).hexdigest() for k,m in (
    ('startup_artifact',samples),('legacy_artifact',samples.legacy_artifact),('canonical_json',json_store))}
LIMITS = {'page_bytes':2*1024*1024,'page_records':128,'delta_bytes':8*1024*1024,
          'pages_per_commit':16,'metadata_bytes':128*1024,'root_bytes':2*1024*1024,
          'commits':16384,'directory_bytes':512*1024*1024,'files':65536}
_canonical = engine._canonical
_hash = engine._hash
physical = engine.physical


class CycleArtifactRejected(ValueError):
    """No published/replayable artifact for this identity, position or resource."""


def _need(condition,reason):
    if not condition:raise CycleArtifactRejected(reason)


def _json(raw):
    try:return inputs._json(raw)
    except inputs.CycleInputRejected as exc:raise CycleArtifactRejected('ARTIFACT_HOLD: invalid UTF-8 JSON') from exc


def _read(fd,name,limit):
    try:return inputs._read(fd,name,limit)
    except inputs.CycleInputRejected as exc:raise CycleArtifactRejected('STORAGE_HOLD: bounded regular artifact file required') from exc


def _blob(fd,digest,limit):
    _need(inputs._digest(digest),'ARTIFACT_HOLD: blob SHA required')
    raw = _read(fd,digest+'.json',limit)
    _need(sha256(raw).hexdigest()==digest,'HASH_HOLD: artifact blob mismatch')
    value = _json(raw)
    _need(_canonical(value)==raw,'ARTIFACT_HOLD: canonical blob required')
    return value,len(raw)


def _pins(context,notice_raw):
    try:engine._require_context(context)
    except engine.CycleStreamExecutionRejected as exc:
        raise CycleArtifactRejected('CONTEXT_HOLD: valid open execution context required') from exc
    _need(type(notice_raw) is bytes and sha256(notice_raw).hexdigest()==samples.NOTICE_SHA256,
          'NOTICE_HOLD: exact research notice required')
    _need(CODE_SHA256==sha256(Path(__file__).read_bytes()).hexdigest()
          and DEPENDENCY_SHA256=={k:sha256(Path(m.__file__).read_bytes()).hexdigest() for k,m in (
              ('startup_artifact',samples),('legacy_artifact',samples.legacy_artifact),('canonical_json',json_store))},
          'CODE_HOLD: artifact reader code mismatch')


def _header(context,notice_raw):
    _pins(context,notice_raw)
    return {'schema_version':VERSION,'scope':'software_research_only','manifest':context.manifest,
            'initial_checkpoint':engine.start(context),'notice_raw_utf8':notice_raw.decode(),
            'artifact_code_sha256':CODE_SHA256,'dependency_sha256':DEPENDENCY_SHA256,'limits':LIMITS}


def _budget(value):
    _need(type(value) is dict and set(value)=={'max_steps','max_transitions'}
          and type(value['max_steps']) is int and 1<=value['max_steps']<=10000
          and type(value['max_transitions']) is int and 1<=value['max_transitions']<=128,
          'RESOURCE_HOLD: bounded artifact chunk budget required')


def _vector(sample):
    return samples._state(sample['state'])+[
        samples._quantity(sample['cumulative'][k],physical.FLUX_UNITS[k]) for k in physical.FLUX]


def _position(context,at):
    """Return an original boundary or its following interval, in one grid page."""
    previous = [p.previous or '' for p in context.index]
    page = max(0,bisect_left(previous,at)-1)
    first = page*inputs.BLOCK_RECORDS
    rows = [engine._boundary(context,i) for i in range(first,min(first+inputs.BLOCK_RECORDS,context.boundary_count))]
    index = bisect_left([r['at'] for r in rows],at)
    if index == len(rows):
        _need(first+index<context.boundary_count,'ARTIFACT_HOLD: time beyond original grid')
        return first+index,engine._boundary(context,first+index)
    return first+index,rows[index]


def _sample(context,value,event_carbon,event_number):
    index,row = _position(context,value['at'])
    _need(row['at']==value['at'] and row['output'],'ARTIFACT_HOLD: sample is not an original output')
    events = row['positions']['events'];active = min(row['positions']['segments'],context.segment_count-1)
    samples._sample(value,context.seed,row['steps']+events,context.growth_profile)
    y = _vector(value);at = physical._utc(value['at']);physical._guard(y,at,'artifact')
    _need(_canonical(physical._state(y))==_canonical(value['state']),'ARTIFACT_HOLD: normalized float64 state required')
    _need(y[4].hex()==engine._evaluator(context,active).clock(y,at,0,'artifact')[4].hex(),
          'ARTIFACT_HOLD: exact original clock mismatch')
    _need(y[115]==event_carbon and y[116]==event_number,'ARTIFACT_HOLD: event cumulative mismatch')


def _event(context,value,index):
    _need(type(value) is dict and set(value)=={'at','input_id','before','after','removed'},'ARTIFACT_HOLD: closed event required')
    original = context.reader.record('events',index)
    _need(value['at']==original['at'] and value['input_id']==original['removals']['input_id'],
          'ARTIFACT_HOLD: original event identity mismatch')
    before = samples._state(value['before'])+[0.0]*16;at = physical._utc(value['at'])
    physical._guard(before,at,'artifact-event')
    _need(_canonical(physical._state(before))==_canonical(value['before']),'ARTIFACT_HOLD: normalized event state required')
    boundary_index,row = _position(context,value['at'])
    active = min(row['positions']['segments'],context.segment_count-1)
    evaluator = engine._evaluator(context,active)
    _need(before[4].hex()==evaluator.clock(before,at,0,'artifact-event')[4].hex(),'ARTIFACT_HOLD: event clock mismatch')
    after,removed = evaluator.remove_event(before,original,at);physical._guard(after,at,'artifact-event')
    _need(_canonical(value['after'])==_canonical(physical._state(after)) and _canonical(value['removed'])==_canonical(removed),
          'ARTIFACT_HOLD: original removal amount/after mismatch')
    return after[115],after[116]


def _confirmed_checkpoint(context,old,meta,records,prefixes):
    value = meta['last_confirmed']
    if value is None:
        _need(old['phase']=='initial-ready' and meta['steps']==0 and not any(records.values()),
              'ARTIFACT_HOLD: empty confirmed past mismatch')
        return None
    _need(type(value) is dict and type(value.get('phase')) is str,'ARTIFACT_HOLD: confirmed phase required')
    at = value['at'];index,row = _position(context,at);phase = value['phase']
    _need(phase in ('step-end','boundary','boundary-after-event'),'ARTIFACT_HOLD: confirmed phase mismatch')
    cursor = index if phase=='step-end' else index+1
    _need(phase=='step-end' or row['at']==at,'ARTIFACT_HOLD: confirmed boundary mismatch')
    previous = engine._boundary(context,cursor-1)
    active = min(previous['positions']['segments'],context.segment_count-1)
    cp = deepcopy(old)
    cp.update(y=_vector(value),at=at,steps=meta['steps'],event_count=old['event_cursor']+len(records['events']),
              event_cursor=old['event_cursor']+len(records['events']),output_cursor=old['output_cursor']+len(records['samples']),
              boundary_cursor=cursor,active_segment=active,sequence=meta['steps']+cursor,
              phase='step-end' if phase=='step-end' else 'boundary-committed',
              clock=engine._clock_record(context,active),parent_sha256=old['checkpoint_sha256'],**prefixes)
    engine._seal(cp);engine.checkpoint_bytes(context,cp)
    _need(_canonical(engine._confirmed(context,cp))==_canonical(value),'ARTIFACT_HOLD: confirmed state/diagnostics mismatch')
    return cp


def _validate_delta(context,old,meta,records,budget):
    _budget(budget);_need(type(meta) is dict,'ARTIFACT_HOLD: result object required')
    held = meta.get('status')=='hold'
    keys = {'status','scope','steps','planned_steps','output_start','event_start','checkpoint'}
    _need(type(meta) is dict and set(meta)==keys|({'hold','last_confirmed'} if held else set())
          and meta['status'] in ('yielded','completed','hold') and meta['scope']=='software_research_only'
          and all(type(meta[k]) is int for k in ('steps','planned_steps','output_start','event_start'))
          and meta['output_start']==old['output_cursor'] and meta['event_start']==old['event_cursor']
          and type(meta['steps']) is int and old['steps']<=meta['steps']<=old['steps']+budget['max_steps']
          and meta['planned_steps']==context.planned_steps,'ARTIFACT_HOLD: execution delta position mismatch')
    _need(all(type(v) is list and len(v)<=budget['max_transitions'] for v in records.values()),
          'RESOURCE_HOLD: bounded delta records required')
    prefixes = {'output_prefix_sha256':old['output_prefix_sha256'],'event_prefix_sha256':old['event_prefix_sha256'],
                'output_cursor':old['output_cursor'],'event_cursor':old['event_cursor']}
    event_totals = [];carbon = old['y'][115];number = old['y'][116]
    for i,event in enumerate(records['events']):
        c,n = _event(context,event,old['event_cursor']+i)
        # Preserve the original fsum order, including individual removal terms.
        removed = event['removed']
        carbon = fsum((carbon,removed['leaf']['value'],removed['stem_root']['value'],
                       *(q['value'] for q in removed['fruit_carbohydrate'])))
        number = fsum((number,*(q['value'] for q in removed['fruit_number'])))
        event_totals.append((carbon,number))
        engine.short._prefix(prefixes,'event_prefix_sha256','event_cursor',event)
    event_at = [e['at'] for e in records['events']]
    for i,value in enumerate(records['samples']):
        _need(value['at']==context.reader.record('outputs',old['output_cursor']+i),
              'ARTIFACT_HOLD: original output prefix mismatch')
        count = bisect_right(event_at,value['at'])
        c,n = event_totals[count-1] if count else (old['y'][115],old['y'][116])
        _sample(context,value,c,n)
        if count and event_at[count-1]==value['at']:
            _need(_canonical(value['state'])==_canonical(records['events'][count-1]['after']),
                  'ARTIFACT_HOLD: event/output state mismatch')
        engine.short._prefix(prefixes,'output_prefix_sha256','output_cursor',value)
    hashes = {k:v for k,v in prefixes.items() if k.endswith('sha256')}
    if held:
        _need(meta['checkpoint'] is None,'ARTIFACT_HOLD: failed trial checkpoint forbidden')
        hold = meta['hold']
        _need(type(hold) is dict and set(hold)=={'at','phase','reason'}
              and type(hold['phase']) is str and 0<len(hold['phase'])<=128
              and type(hold['reason']) is str and 0<len(hold['reason'])<=1024,'ARTIFACT_HOLD: closed hold required')
        at = json_store._time(hold['at'])
        _need(hold['at']==physical._stamp(at) and physical._utc(context.start_at)<=at
              <=physical._utc(context.reader.manifest['period']['end']),'ARTIFACT_HOLD: hold time mismatch')
        cp = _confirmed_checkpoint(context,old,meta,records,hashes)
        _need(cp is None or physical._utc(cp['at'])<=at,'ARTIFACT_HOLD: hold before confirmed past')
        _need(all(physical._utc(v['at'])<at for v in records['samples']), 'ARTIFACT_HOLD: sample at failed trial')
    else:
        cp = meta['checkpoint'];engine.checkpoint_bytes(context,cp)
        _need(cp['parent_sha256']==old['checkpoint_sha256'] and cp['steps']==meta['steps']
              and 1<=cp['sequence']-old['sequence']<=budget['max_transitions']
              and ((cp['boundary_cursor']==context.boundary_count)==(meta['status']=='completed')),
              'ARTIFACT_HOLD: checkpoint progression/status mismatch')
    if cp is not None:
        _need(all(cp[k]==v for k,v in prefixes.items()) and cp['y'][115]==carbon and cp['y'][116]==number,
              'ARTIFACT_HOLD: checkpoint delta prefix/cumulative mismatch')
        if records['samples'] and records['samples'][-1]['at']==cp['at']:
            _need(_canonical(_vector(records['samples'][-1]))==_canonical(cp['y']),
                  'ARTIFACT_HOLD: final output/checkpoint vector mismatch')
    return cp


def _wrap_validation(fn,*args):
    try:return fn(*args)
    except CycleArtifactRejected:raise
    except (ValueError,TypeError,KeyError,IndexError,OverflowError,RecursionError,physical._EvaluationHold) as exc:
        raise CycleArtifactRejected('ARTIFACT_HOLD: invalid result identity/shape/position/ledger') from exc


class _Files:
    def __init__(self,directory):
        self._fd=None;self._lock=None;self._page_cache=None;self._seen=set();self._referenced_bytes=8192
        try:self._fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        except OSError as exc:raise CycleArtifactRejected('STORAGE_HOLD: artifact directory unavailable') from exc
    @property
    def closed(self):return self._fd is None
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def close(self):
        if self._lock is not None:os.close(self._lock);self._lock=None
        if self._fd is not None:os.close(self._fd);self._fd=None
        self._page_cache=None
    def _open(self):_need(not self.closed,'STORAGE_HOLD: artifact handle closed')
    def _blob(self,digest,limit):
        value,size=_blob(self._fd,digest,limit)
        if digest not in self._seen:
            self._seen.add(digest);self._referenced_bytes+=size
            _need(self._referenced_bytes<=LIMITS['directory_bytes'] and len(self._seen)<=LIMITS['files'],
                  'RESOURCE_HOLD: referenced artifact budget exceeded')
        return value,size
    def _head(self):
        self._open();raw=_read(self._fd,'HEAD',8192);value=_json(raw)
        _need(_canonical(value)==raw and type(value) is dict and set(value)=={
            'version','header_sha256','latest_commit_sha256','commit_count','artifact_sha256'}
            and value['version']==VERSION and inputs._digest(value['header_sha256'])
            and type(value['commit_count']) is int and 0<=value['commit_count']<=LIMITS['commits']
            and (value['latest_commit_sha256'] is None if value['commit_count']==0 else inputs._digest(value['latest_commit_sha256']))
            and (value['artifact_sha256'] is None or inputs._digest(value['artifact_sha256'])),
            'ARTIFACT_HOLD: closed HEAD required')
        return value,sha256(raw).hexdigest()
    def _records(self,descriptors):
        records=[];total=0
        _need(type(descriptors) is list and len(descriptors)<=LIMITS['pages_per_commit'],'RESOURCE_HOLD: bounded page list required')
        for descriptor in descriptors:
            _need(type(descriptor) is dict and set(descriptor)=={'sha256','count','first_at','last_at'},
                  'ARTIFACT_HOLD: closed page descriptor required')
            values,size=self._blob(descriptor['sha256'],LIMITS['page_bytes']);total+=size
            _need(type(values) is list and type(descriptor['count']) is int
                  and 1<=len(values)==descriptor['count']<=LIMITS['page_records']
                  and values[0]['at']==descriptor['first_at'] and values[-1]['at']==descriptor['last_at'],
                  'ARTIFACT_HOLD: exact page records/index required')
            records.extend(values)
            _need(len(records)<=128 and total<=LIMITS['delta_bytes'],'RESOURCE_HOLD: delta window exceeded')
        return records,total
    def _load_prefix(self,context,notice,head):
        header,_=self._blob(head['header_sha256'],LIMITS['metadata_bytes'])
        _need(_canonical(header)==_canonical(_header(context,notice)),'ARTIFACT_HOLD: original header/context/code/notice mismatch')
        hashes=[];digest=head['latest_commit_sha256']
        for sequence in range(head['commit_count'],0,-1):
            chunk,_=self._blob(digest,LIMITS['metadata_bytes'])
            _need(type(chunk) is dict and set(chunk)=={'version','header_sha256','sequence','parent_commit_sha256',
                'input_checkpoint_sha256','budget','result','pages'} and chunk['version']==VERSION
                and chunk['header_sha256']==head['header_sha256'] and type(chunk['sequence']) is int and chunk['sequence']==sequence,
                'ARTIFACT_HOLD: original commit chain mismatch')
            hashes.append(digest);digest=chunk['parent_commit_sha256']
        _need(digest is None,'ARTIFACT_HOLD: commit chain not rooted')
        hashes.reverse();cp=header['initial_checkpoint'];summary=None;index={'samples':[],'events':[]};counts={'samples':0,'events':0}
        for i,digest in enumerate(hashes):
            chunk,_=self._blob(digest,LIMITS['metadata_bytes'])
            _need(cp is not None and chunk['input_checkpoint_sha256']==cp['checkpoint_sha256']
                  and type(chunk['pages']) is dict and set(chunk['pages'])==set(index),'ARTIFACT_HOLD: commit checkpoint/page identity mismatch')
            records={};size=0;pages=0
            for kind in index:
                records[kind],n=self._records(chunk['pages'][kind]);size+=n;pages+=len(chunk['pages'][kind])
                for descriptor in chunk['pages'][kind]:
                    index[kind].append({'start':counts[kind],**descriptor});counts[kind]+=descriptor['count']
            _need(size<=LIMITS['delta_bytes'] and pages<=LIMITS['pages_per_commit'],'RESOURCE_HOLD: complete delta budget exceeded')
            previous=cp;meta=chunk['result']
            validated=_wrap_validation(_validate_delta,context,previous,meta,records,chunk['budget'])
            _need(i==len(hashes)-1 or meta['status']=='yielded','ARTIFACT_HOLD: premature terminal commit')
            cp=meta['checkpoint'];summary=deepcopy(meta)
        return hashes,cp,summary,index,counts


class ArtifactWriter(_Files):
    def _acquire(self):
        try:
            self._lock=os.open('.writer-lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK,0o600,dir_fd=self._fd)
            _need(stat.S_ISREG(os.fstat(self._lock).st_mode) and os.fstat(self._lock).st_size==0,'STORAGE_HOLD: regular empty writer lock required')
            fcntl.flock(self._lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:raise CycleArtifactRejected('STORAGE_HOLD: exclusive writer unavailable') from exc
    def _usage(self):
        size=0;names=os.listdir(self._fd)
        _need(len(names)<=LIMITS['files'],'RESOURCE_HOLD: artifact file count exceeded')
        for name in names:
            value=os.stat(name,dir_fd=self._fd,follow_symlinks=False)
            _need(stat.S_ISREG(value.st_mode),'STORAGE_HOLD: regular owned artifact files required');size+=value.st_size
        _need(size<=LIMITS['directory_bytes'],'RESOURCE_HOLD: directory byte budget exceeded')
        return size,len(names)
    def _put(self,raw,limit):
        _need(len(raw)<=limit,'RESOURCE_HOLD: artifact blob too large')
        digest=sha256(raw).hexdigest();name=digest+'.json'
        try:
            value=_read(self._fd,name,limit)
            _need(value==raw,'HASH_HOLD: existing immutable blob changed');return digest
        except CycleArtifactRejected as exc:
            try:os.stat(name,dir_fd=self._fd,follow_symlinks=False)
            except FileNotFoundError:pass
            else:raise exc
        size,count=self._usage()
        _need(size+2*len(raw)<=LIMITS['directory_bytes'] and count+2<=LIMITS['files'],'RESOURCE_HOLD: directory budget exceeded')
        temporary='.blob-'+uuid4().hex+'.tmp';fd=None
        try:
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self._fd)
            with os.fdopen(fd,'wb') as handle:
                fd=None;handle.write(raw);handle.flush();os.fchmod(handle.fileno(),0o400);os.fsync(handle.fileno())
            os.link(temporary,name,src_dir_fd=self._fd,dst_dir_fd=self._fd,follow_symlinks=False)
            os.fsync(self._fd)
        finally:
            if fd is not None:os.close(fd)
            try:os.unlink(temporary,dir_fd=self._fd)
            except FileNotFoundError:pass
        return digest
    def _publish_head(self,head):
        raw=_canonical(head);temporary='.head-'+uuid4().hex+'.tmp';fd=None
        _need(len(raw)<=8192,'RESOURCE_HOLD: HEAD too large')
        size,count=self._usage()
        _need(size+len(raw)<=LIMITS['directory_bytes'] and count+1<=LIMITS['files'],'RESOURCE_HOLD: HEAD budget exceeded')
        try:
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self._fd)
            with os.fdopen(fd,'wb') as handle:
                fd=None;handle.write(raw);handle.flush();os.fchmod(handle.fileno(),0o400);os.fsync(handle.fileno())
            os.replace(temporary,'HEAD',src_dir_fd=self._fd,dst_dir_fd=self._fd);os.fsync(self._fd)
        finally:
            if fd is not None:os.close(fd)
            try:os.unlink(temporary,dir_fd=self._fd)
            except FileNotFoundError:pass
        self._head_value=head;self.head_sha256=sha256(raw).hexdigest()
    def _pages(self,records):
        result=[];batch=[]
        def flush():
            raw=_canonical(batch);digest=self._put(raw,LIMITS['page_bytes'])
            result.append({'sha256':digest,'count':len(batch),'first_at':batch[0]['at'],'last_at':batch[-1]['at']})
        for record in records:
            _need(len(_canonical([record]))<=LIMITS['page_bytes']-4096,'RESOURCE_HOLD: single record too large')
            if batch and (len(batch)==128 or len(_canonical(batch+[record]))>LIMITS['page_bytes']):flush();batch=[]
            batch.append(record)
        if batch:flush()
        return result
    def advance(self,budget):
        self._open();_budget(budget);_pins(self.context,self.notice)
        _need(self._summary is None or self._summary['status']=='yielded','ARTIFACT_HOLD: already terminal')
        _need(len(self._hashes)<LIMITS['commits'],'RESOURCE_HOLD: commit budget exceeded')
        head,head_hash=self._head();_need(head_hash==self.head_sha256,'ARTIFACT_HOLD: changed HEAD')
        self._usage()
        result=engine.advance_chunk(self.context,self._checkpoint,budget)
        _need(result['manifest']==self.context.manifest,'ARTIFACT_HOLD: execution manifest mismatch')
        records={k:result[k] for k in ('samples','events')}
        _need(sum(len(_canonical(v)) for v in records.values())<=LIMITS['delta_bytes'],'RESOURCE_HOLD: delta bytes exceeded')
        meta={k:v for k,v in result.items() if k not in ('manifest','samples','events')}
        _wrap_validation(_validate_delta,self.context,self._checkpoint,meta,records,budget)
        pages={k:self._pages(v) for k,v in records.items()}
        _need(sum(map(len,pages.values()))<=LIMITS['pages_per_commit'],'RESOURCE_HOLD: page count exceeded')
        chunk={'version':VERSION,'header_sha256':head['header_sha256'],'sequence':len(self._hashes)+1,
               'parent_commit_sha256':head['latest_commit_sha256'],'input_checkpoint_sha256':self._checkpoint['checkpoint_sha256'],
               'budget':dict(budget),'result':meta,'pages':pages}
        digest=self._put(_canonical(chunk),LIMITS['metadata_bytes'])
        try:self._publish_head({**head,'latest_commit_sha256':digest,'commit_count':len(self._hashes)+1})
        except BaseException:self.close();raise
        self._hashes.append(digest);self._checkpoint=result['checkpoint'];self._summary=meta
        return {'status':result['status'],'head_sha256':self.head_sha256,'commit_count':len(self._hashes),'steps':result['steps']}
    def finalize(self):
        self._open();_pins(self.context,self.notice)
        _need(self._summary is not None and self._summary['status'] in ('completed','hold'),'ARTIFACT_HOLD: terminal result required')
        head,head_hash=self._head();_need(head_hash==self.head_sha256,'ARTIFACT_HOLD: changed HEAD')
        root={'version':VERSION,'header_sha256':head['header_sha256'],'commits':self._hashes,'status':self._summary['status']}
        digest=self._put(_canonical(root),LIMITS['root_bytes'])
        try:self._publish_head({**head,'artifact_sha256':digest})
        except BaseException:self.close();raise
        return {'artifact_sha256':digest,'artifact_id':VERSION+':'+digest,'head_sha256':self.head_sha256,
                'status':self._summary['status'],'steps':self._summary['steps'],'commit_count':len(self._hashes)}


def create_writer(directory,context,*,notice_raw):
    header=_header(context,notice_raw);directory=Path(directory)
    try:directory.mkdir(mode=0o700)
    except OSError as exc:raise CycleArtifactRejected('STORAGE_HOLD: new artifact directory required') from exc
    writer=None
    try:
        writer=ArtifactWriter(directory);writer._acquire();writer.context=context;writer.notice=notice_raw
        digest=writer._put(_canonical(header),LIMITS['metadata_bytes'])
        writer._publish_head({'version':VERSION,'header_sha256':digest,'latest_commit_sha256':None,'commit_count':0,'artifact_sha256':None})
        writer._hashes=[];writer._checkpoint=header['initial_checkpoint'];writer._summary=None
        return writer
    except BaseException:
        if writer is not None:writer.close()
        shutil.rmtree(directory);raise


def open_writer(directory,expected_head_sha256,context,*,notice_raw):
    _pins(context,notice_raw);writer=ArtifactWriter(directory)
    try:
        writer._acquire();head,actual=writer._head()
        _need(inputs._digest(expected_head_sha256) and actual==expected_head_sha256,'HASH_HOLD: original HEAD required')
        writer._usage()
        hashes,cp,summary,_,_=_wrap_validation(writer._load_prefix,context,notice_raw,head)
        if head['artifact_sha256'] is not None:
            published,_=writer._blob(head['artifact_sha256'],LIMITS['root_bytes'])
            _need(summary is not None and summary['status'] in ('completed','hold')
                  and _canonical(published)==_canonical({'version':VERSION,'header_sha256':head['header_sha256'],
                      'commits':hashes,'status':summary['status']}),'ARTIFACT_HOLD: published root mismatch')
        writer.context=context;writer.notice=notice_raw;writer._head_value=head;writer.head_sha256=actual
        writer._hashes=hashes;writer._checkpoint=cp;writer._summary=summary
        return writer
    except BaseException:writer.close();raise


class ArtifactReader(_Files):
    @property
    def summary(self):
        self._open();return deepcopy(self._summary_value)
    def page(self,kind,start=0,limit=None):
        self._open();maximum=64 if kind=='samples' else 8
        limit=maximum if limit is None else limit
        _need(kind in self._index and type(start) is int and 0<=start<=self._counts[kind]
              and type(limit) is int and 1<=limit<=maximum,'RESOURCE_HOLD: bounded page position/limit required')
        rows=[];index=self._index[kind];starts=[d['start'] for d in index];position=start;self._page_cache=None
        while position<min(start+limit,self._counts[kind]):
            block=bisect_right(starts,position)-1;descriptor=index[block]
            if self._page_cache is None or self._page_cache[0]!=descriptor['sha256']:
                values,size=self._blob(descriptor['sha256'],LIMITS['page_bytes'])
                self._page_cache=(descriptor['sha256'],values)
            values=self._page_cache[1]
            value=values[position-descriptor['start']]
            candidate={'kind':kind,'start':start,'next':position+1,'total':self._counts[kind],'records':rows+[value]}
            if len(_canonical(candidate))>LIMITS['page_bytes']:
                _need(bool(rows),'RESOURCE_HOLD: replay record too large');break
            rows.append(value);position+=1
        return {'kind':kind,'start':start,'next':position,'total':self._counts[kind],'records':deepcopy(rows)}


def open_artifact(directory,expected_artifact_sha256,context,*,notice_raw):
    _pins(context,notice_raw);reader=ArtifactReader(directory)
    try:
        head,_=reader._head()
        _need(head['artifact_sha256']==expected_artifact_sha256,'ARTIFACT_HOLD: root not atomically published')
        root,_=reader._blob(expected_artifact_sha256,LIMITS['root_bytes'])
        _need(type(root) is dict and set(root)=={'version','header_sha256','commits','status'}
              and root['version']==VERSION and root['header_sha256']==head['header_sha256']
              and type(root['commits']) is list and 1<=len(root['commits'])<=LIMITS['commits']
              and root['status'] in ('completed','hold'),'ARTIFACT_HOLD: closed terminal root required')
        hashes,cp,summary,index,counts=_wrap_validation(reader._load_prefix,context,notice_raw,head)
        _need(root['commits']==hashes and summary['status']==root['status'],'ARTIFACT_HOLD: terminal root/index mismatch')
        reader._index=index;reader._counts=counts
        reader._summary_value={'artifact_id':VERSION+':'+expected_artifact_sha256,'artifact_sha256':expected_artifact_sha256,
            'scope':'software_research_only','manifest':context.manifest,'notice_raw_utf8':notice_raw.decode(),
            'commit_count':len(hashes),'counts':counts,**summary}
        return reader
    except BaseException:reader.close();raise
