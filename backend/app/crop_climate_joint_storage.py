"""Immutable confirmed joint crop/climate pages, before farm custody/API."""
from functools import wraps
from hashlib import sha256
import json
import os
from pathlib import Path

from . import crop_climate_joint_time as clock
from . import crop_cycle_artifact as files

continuation=clock.continuation
VERSION='joint-crop-climate-storage-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
LIMITS={'page_bytes':2*1024**2,'samples_per_page':64,'events_per_page':8,'metadata_bytes':128*1024,
    'context_bytes':3*1024**2,'root_bytes':2*1024**2,'commits':4097,'pages_per_commit':18,
    'directory_bytes':512*1024**2,'files':65536}
_SOURCES={'time':Path(clock.__file__),'continuation':Path(continuation.__file__),
    'driver':Path(continuation.driver.__file__),'short':Path(continuation.driver.short.__file__),
    'management':Path(continuation.driver.management.__file__),'rhs':Path(continuation.driver.joint.__file__),
    'file_store':Path(files.__file__),'file_input_io':Path(files.inputs.__file__),'file_json':Path(files.json_store.__file__),
    **{k:Path(__file__).with_name(k+'.py') for k in continuation.driver.joint.COMPONENT_CODE_SHA256},
    'notice':Path(__file__).resolve().parents[2]/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt'}
DEPENDENCY_SHA256={k:sha256(p.read_bytes()).hexdigest() for k,p in _SOURCES.items()}
_canonical=continuation._canonical
_hash=continuation._hash


class JointStorageHold(ValueError):
    """No readable/published result for this identity, bytes or position."""


def _need(condition,reason):
    if not condition:raise JointStorageHold(reason)


def _pins():
    _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256
        and DEPENDENCY_SHA256=={k:sha256(p.read_bytes()).hexdigest() for k,p in _SOURCES.items()},
        'CODE_HOLD: changed storage/model/file dependencies')


def _operation(fn):
    @wraps(fn)
    def run(self,*args,**kw):
        try:
            self._open();_pins();result=fn(self,*args,**kw);_pins();return result
        except BaseException as exc:
            self.close()
            if isinstance(exc,(files.CycleArtifactRejected,clock.TimeBindingRejected,continuation.ContinuationRejected,OSError,KeyError,TypeError,ValueError)):
                raise JointStorageHold(str(exc)) from exc
            raise
    return run


class _Files(files._Files):
    _acquire=files.ArtifactWriter._acquire
    _usage=files.ArtifactWriter._usage
    _put=files.ArtifactWriter._put
    _publish_head=files.ArtifactWriter._publish_head

    def _pages(self,kind,values,times):
        limit=LIMITS[kind+'_per_page'];descriptors=[];batch=[]
        def flush():
            raw=_canonical(batch);digest=self._put(raw,LIMITS['page_bytes'])
            descriptors.append({'sha256':digest,'count':len(batch),'first_at':batch[0]['time']['at'],'last_at':batch[-1]['time']['at']})
        _need(len(values)==len(times)<=128,'PAGE_HOLD: exact bounded values/time pairs')
        for value,point in zip(values,times,strict=True):
            record={'value':value,'time':point}
            _need(len(_canonical([record]))+1024<=LIMITS['page_bytes'],'RESOURCE_HOLD: single record byte limit')
            if batch and (len(batch)==limit or len(_canonical([*batch,record]))>LIMITS['page_bytes']):flush();batch=[]
            batch.append(record)
        if batch:flush()
        return descriptors

    def _records(self,kind,descriptors,manifest,program):
        _need(type(descriptors) is list and len(descriptors)<=LIMITS['pages_per_commit'],'PAGE_HOLD: bounded descriptors')
        values=[];times=[]
        for d in descriptors:
            _need(type(d) is dict and set(d)=={'sha256','count','first_at','last_at'},'PAGE_HOLD: closed descriptor')
            rows,_=self._blob(d['sha256'],LIMITS['page_bytes'])
            _need(type(rows) is list and type(d['count']) is int and 1<=len(rows)==d['count']<=LIMITS[kind+'_per_page'],
                'PAGE_HOLD: bounded exact row count')
            for row in rows:
                _need(type(row) is dict and set(row)=={'value','time'}
                    and row['time']==clock._point(manifest,row['value'],program),'PAGE_HOLD: original value/time pair')
                values.append(row['value']);times.append(row['time'])
            _need(rows[0]['time']['at']==d['first_at'] and rows[-1]['time']['at']==d['last_at'],'PAGE_HOLD: page time bounds')
        _need(len(values)<=128,'PAGE_HOLD: bounded commit records')
        return values,times

    def _head(self):
        raw=files._read(self._fd,'HEAD',8192);v=files._json(raw)
        _need(type(v) is dict and set(v)=={'version','header_sha256','latest_commit_sha256','commit_count','artifact_sha256'}
            and v['version']==VERSION and _canonical(v)==raw,'HEAD_HOLD: closed canonical HEAD')
        _need(continuation._digest(v['header_sha256']) and type(v['commit_count']) is int and 0<=v['commit_count']<=LIMITS['commits']
            and (v['latest_commit_sha256'] is None if v['commit_count']==0 else continuation._digest(v['latest_commit_sha256']))
            and (v['artifact_sha256'] is None or continuation._digest(v['artifact_sha256'])),'HEAD_HOLD: position/hashes')
        return v,sha256(raw).hexdigest()

    def _load_header(self,digest):
        h,_=self._blob(digest,LIMITS['metadata_bytes'])
        _need(type(h) is dict and set(h)=={'version','code_sha256','dependencies','limits','context_blob_sha256',
            'context_sha256','binding_sha256','binding','initial_checkpoint','notice_raw_utf8'} and h['version']==VERSION
            and h['code_sha256']==CODE_SHA256 and h['dependencies']==DEPENDENCY_SHA256 and h['limits']==LIMITS
            and h['notice_raw_utf8']==_SOURCES['notice'].read_bytes().decode(),'HEADER_HOLD: identity/code/limits/notice')
        context,_=self._blob(h['context_blob_sha256'],LIMITS['context_bytes'])
        _need(type(context) is dict and set(context)=={'program','manifest','initial_rhs','profiles'}
            and _hash(context['manifest'])==h['context_sha256']==h['binding']['context_sha256']
            and _hash(context['program'])==context['manifest']['program_sha256']
            and _hash(context['initial_rhs'])==context['manifest']['initial_rhs_sha256']
            and _hash(h['binding'])==h['binding_sha256'] and h['binding']['time_code_sha256']==clock.CODE_SHA256,
            'HEADER_HOLD: source context/binding hashes')
        profiles=context['profiles'];expected=context['manifest']['identity']['profile_sha256']
        _need(type(profiles) is dict and set(profiles)==set(expected)==set(continuation.PROFILE_NAMES),
            'HEADER_HOLD: exact source profiles')
        for name,raw in profiles.items():
            _need(type(raw) is str and sha256(raw.encode()).hexdigest()==expected[name],'HEADER_HOLD: original profile bytes')
        joint=continuation.driver.joint
        constructors=(joint.growth.ReferenceParameters,joint.fruit.ReferenceFruitCohortParameters,
            joint.ReferenceFruitTransportParameters,joint.exchange.ReferenceParameters)
        parsed=tuple(cls(profiles[name].encode()) for cls,name in zip(constructors,continuation.PROFILE_NAMES,strict=True))
        _need(_canonical(context['manifest']['identity'])==_canonical(continuation._identity(parsed)),
            'HEADER_HOLD: current model/profile/environment identity')
        cp=h['initial_checkpoint']
        _need(type(cp) is dict and set(cp)=={'sha256','value'} and _hash(cp['value'])==cp['sha256']
            and cp['value']['context_sha256']==h['context_sha256'] and cp['value']['next_index']==0,
            'HEADER_HOLD: original initial-ready checkpoint')
        return h,context

    def _load(self,head):
        h,context=self._load_header(head['header_sha256']);program=context['program'];manifest=h['binding']
        digests=[];digest=head['latest_commit_sha256']
        for sequence in range(head['commit_count'],0,-1):
            commit,_=self._blob(digest,LIMITS['metadata_bytes'])
            _need(type(commit) is dict and set(commit)=={'version','header_sha256','sequence','parent_commit_sha256',
                'before_checkpoint_sha256','source_chunk_sha256','result_sha256','source_meta','times_meta','pages'}
                and commit['version']==VERSION and commit['header_sha256']==head['header_sha256']
                and type(commit['sequence']) is int and commit['sequence']==sequence,'COMMIT_HOLD: rooted ordered chain')
            digests.append(digest);digest=commit['parent_commit_sha256']
        _need(digest is None,'COMMIT_HOLD: chain root');digests.reverse()
        cp=h['initial_checkpoint'];counts={'samples':0,'events':0};index={'samples':[],'events':[]};last=None;times=None
        for sequence,digest in enumerate(digests,1):
            commit,_=self._blob(digest,LIMITS['metadata_bytes'])
            _need(cp is not None and commit['before_checkpoint_sha256']==cp['sha256']
                and type(commit['pages']) is dict and set(commit['pages'])==set(index)
                and sum(len(v) for v in commit['pages'].values())<=LIMITS['pages_per_commit'],
                'COMMIT_HOLD: checkpoint/page identity')
            source=dict(commit['source_meta']);times=dict(commit['times_meta'])
            _need(not ({'samples','events'}&set(source)) and not ({'samples','events'}&set(times)),
                'COMMIT_HOLD: metadata excludes paged values')
            for kind in index:
                source[kind],times[kind]=self._records(kind,commit['pages'][kind],manifest,program)
                for descriptor in commit['pages'][kind]:
                    index[kind].append({'start':counts[kind],'commit_sha256':digest,**descriptor});counts[kind]+=descriptor['count']
            _need(_hash(source)==commit['source_chunk_sha256'],'HASH_HOLD: exact original chunk')
            payload={'version':clock.VERSION,'binding_sha256':h['binding_sha256'],'scope':'software_research_only','G0_G4':'not_assessed',
                'source_chunk_sha256':commit['source_chunk_sha256'],'before_checkpoint_sha256':cp['sha256'],'source':source,'times':times}
            _need(_hash(payload)==commit['result_sha256'] and source['context_sha256']==h['context_sha256']
                and _canonical(source['manifest'])==_canonical(context['manifest']) and source['status'] in ('yielded','completed','hold')
                and source['scope']=='software_research_only' and source['claim_scope']=='synthetic_joint_crop_climate_continuation_only'
                and source['G0_G4']=='not_assessed','HASH_HOLD: exact bound result/context/scope')
            for kind,cursor in (('samples','output'),('events','event')):
                _need(source[cursor+'_start']==cp['value'][cursor+'_cursor'],'COMMIT_HOLD: original cursor')
                prefix=cp['value'][cursor+'_prefix_sha256']
                for value in source[kind]:prefix=continuation._prefix(prefix,value)
                after=source['checkpoint']
                if after is not None:
                    _need(after['value'][cursor+'_prefix_sha256']==prefix and after['value'][cursor+'_cursor']==counts[kind],
                        'COMMIT_HOLD: original prefix/cursor')
            _need(times['last_confirmed']==clock._point(manifest,source['last_confirmed'],program)
                and times['hold']==(None if source['hold'] is None else clock._point(manifest,source['hold'],program)),
                'COMMIT_HOLD: confirmed/failed times')
            cp=source['checkpoint'];last=source
            if cp is not None:
                _need(_hash(cp['value'])==cp['sha256'] and _canonical(cp['value']['last_confirmed'])==_canonical(last['last_confirmed']),
                    'COMMIT_HOLD: raw checkpoint/confirmed state')
            _need(sequence==len(digests) or source['status']=='yielded','COMMIT_HOLD: premature terminal state')
        return h,context,digests,cp,last,times,index,counts

    def _check_head(self):
        head,digest=self._head();_need(digest==self.head_sha256,'HEAD_HOLD: stale or changed HEAD');return head


class ArtifactWriter(_Files):
    def _check(self):
        head=self._check_head();h,_=self._load_header(head['header_sha256'])
        clock._binding(self.binding,self.binding.sha256)
        _need(h['binding_sha256']==self.binding.sha256,'BINDING_HOLD: original writer binding required')
        stored=h['initial_checkpoint'] if head['commit_count']==0 else self._blob(
            head['latest_commit_sha256'],LIMITS['metadata_bytes'])[0]['source_meta']['checkpoint']
        supplied=None if self.checkpoint is None else {'sha256':self.checkpoint.sha256,
            'value':json.loads(continuation.checkpoint_bytes(self.binding._context,self.checkpoint))}
        _need(_canonical(supplied)==_canonical(stored),'CHECKPOINT_HOLD: original writer checkpoint required')
        return head

    @_operation
    def _create(self,binding,checkpoint):
        self._acquire();self._usage()
        try:os.stat('HEAD',dir_fd=self._fd,follow_symlinks=False)
        except FileNotFoundError:pass
        else:raise JointStorageHold('HEAD_HOLD: already initialized')
        clock._binding(binding,binding.sha256);ctx=binding._context
        initial=clock.bind_checkpoint(binding,checkpoint,expected_binding_sha256=binding.sha256)
        _need(initial['source']['next_index']==0,'CHECKPOINT_HOLD: initial-ready required')
        context={'program':ctx.program,'manifest':ctx.manifest,'initial_rhs':json.loads(ctx._first),
            'profiles':{k:p.raw_bytes.decode() for k,p in zip(continuation.PROFILE_NAMES,ctx._profiles,strict=True)}}
        context_sha=self._put(_canonical(context),LIMITS['context_bytes'])
        header={'version':VERSION,'code_sha256':CODE_SHA256,'dependencies':DEPENDENCY_SHA256,'limits':LIMITS,
            'context_blob_sha256':context_sha,'context_sha256':ctx.root_sha256,'binding_sha256':binding.sha256,
            'binding':binding.manifest,'initial_checkpoint':{'sha256':checkpoint.sha256,'value':checkpoint.value},
            'notice_raw_utf8':_SOURCES['notice'].read_bytes().decode()}
        header_sha=self._put(_canonical(header),LIMITS['metadata_bytes'])
        self.binding=binding;self.checkpoint=checkpoint;self._commits=[];self._counts={'samples':0,'events':0};self._last=None
        self._publish_head({'version':VERSION,'header_sha256':header_sha,'latest_commit_sha256':None,'commit_count':0,'artifact_sha256':None})
        return self

    @_operation
    def _resume(self,expected_head_sha256,binding,checkpoint):
        self._acquire();self._usage();head,digest=self._head()
        _need(continuation._digest(expected_head_sha256) and digest==expected_head_sha256 and head['artifact_sha256'] is None,
            'HEAD_HOLD: trusted unfinished HEAD required')
        h,_,commits,cp,last,_,_,counts=self._load(head)
        clock._binding(binding,binding.sha256)
        _need(h['binding_sha256']==binding.sha256,'BINDING_HOLD: original binding required')
        supplied=None if checkpoint is None else {'sha256':checkpoint.sha256,
            'value':json.loads(continuation.checkpoint_bytes(binding._context,checkpoint))}
        _need(_canonical(supplied)==_canonical(cp),'CHECKPOINT_HOLD: exact stored checkpoint required')
        self.binding=binding;self.checkpoint=checkpoint;self._commits=commits;self._counts=counts;self._last=last
        self._head_value=head;self.head_sha256=digest;return self

    @_operation
    def append(self,chunk,*,expected_chunk_sha256):
        head=self._check()
        _need(head['artifact_sha256'] is None and self.checkpoint is not None
            and (self._last is None or self._last['status']=='yielded') and head['commit_count']<LIMITS['commits'],
            'COMMIT_HOLD: no remaining append position')
        result=clock.bind_chunk(self.binding,self.checkpoint,chunk,expected_chunk_sha256=expected_chunk_sha256,
            expected_binding_sha256=self.binding.sha256)
        source=result['source'];times=result['times'];pages={}
        for kind in ('samples','events'):pages[kind]=self._pages(kind,source[kind],times[kind])
        _need(sum(map(len,pages.values()))<=LIMITS['pages_per_commit'],'RESOURCE_HOLD: commit page count')
        commit={'version':VERSION,'header_sha256':head['header_sha256'],'sequence':head['commit_count']+1,
            'parent_commit_sha256':head['latest_commit_sha256'],'before_checkpoint_sha256':self.checkpoint.sha256,
            'source_chunk_sha256':result['source_chunk_sha256'],'result_sha256':result['result_sha256'],
            'source_meta':{k:v for k,v in source.items() if k not in ('samples','events')},
            'times_meta':{k:v for k,v in times.items() if k not in ('samples','events')},'pages':pages}
        digest=self._put(_canonical(commit),LIMITS['metadata_bytes'])
        self._check();_pins()
        self._publish_head({**head,'latest_commit_sha256':digest,'commit_count':head['commit_count']+1})
        self.checkpoint=chunk['checkpoint'];self._commits.append(digest);self._last=source
        for kind in self._counts:self._counts[kind]+=len(source[kind])
        return {'head_sha256':self.head_sha256,'status':source['status'],'counts':dict(self._counts)}

    @_operation
    def finalize(self):
        head=self._check()
        _need(head['artifact_sha256'] is None and self._last is not None and self._last['status'] in ('completed','hold'),
            'ROOT_HOLD: terminal original result required')
        root={'version':VERSION,'header_sha256':head['header_sha256'],'commits':self._commits,
            'status':self._last['status'],'counts':self._counts,'final_checkpoint_sha256':None if self.checkpoint is None else self.checkpoint.sha256}
        digest=self._put(_canonical(root),LIMITS['root_bytes']);self._check();_pins()
        self._publish_head({**head,'artifact_sha256':digest});return digest


class ArtifactReader(_Files):
    @_operation
    def _load_root(self,expected_artifact_sha256):
        self._usage();head,head_sha=self._head()
        _need(continuation._digest(expected_artifact_sha256) and head['artifact_sha256']==expected_artifact_sha256,
            'ROOT_HOLD: trusted published root required')
        root,_=self._blob(expected_artifact_sha256,LIMITS['root_bytes'])
        h,context,commits,cp,last,times,index,counts=self._load(head)
        expected={'version':VERSION,'header_sha256':head['header_sha256'],'commits':commits,
            'status':None if last is None else last['status'],'counts':counts,'final_checkpoint_sha256':None if cp is None else cp['sha256']}
        _need(_canonical(root)==_canonical(expected) and root['status'] in ('completed','hold'),'ROOT_HOLD: exact complete terminal root')
        self.artifact_sha256=expected_artifact_sha256;self.head_sha256=head_sha;self._head_value=head
        self._header=h;self._context=context;self._index=index;self._counts=counts;self._last=last;self._times=times
        return self

    def _check(self):
        self._check_head();self._blob(self.artifact_sha256,LIMITS['root_bytes']);self._load_header(self._head_value['header_sha256'])

    @property
    @_operation
    def summary(self):
        self._check()
        value={'version':VERSION,'scope':'software_research_only','G0_G4':'not_assessed','artifact_sha256':self.artifact_sha256,
            'context_sha256':self._header['context_sha256'],'binding_sha256':self._header['binding_sha256'],
            'status':self._last['status'],'counts':self._counts,'checkpoint':self._last['checkpoint'],
            'last_confirmed':self._last['last_confirmed'],'hold':self._last['hold'],'times':self._times}
        result=json.loads(_canonical(value));self._check();return result

    @_operation
    def page(self,kind,*,start=0,limit=None):
        self._check();_need(kind in ('samples','events'),'PAGE_HOLD: known kind')
        maximum=LIMITS[kind+'_per_page'];limit=maximum if limit is None else limit
        _need(type(start) is int and 0<=start<=self._counts[kind] and type(limit) is int and 1<=limit<=maximum,
            'PAGE_HOLD: bounded integer range')
        records=[];end=min(self._counts[kind],start+limit)
        for d in self._index[kind]:
            if d['start']>=end or d['start']+d['count']<=start:continue
            self._blob(d['commit_sha256'],LIMITS['metadata_bytes'])
            descriptor={k:v for k,v in d.items() if k not in ('start','commit_sha256')}
            values,times=self._records(kind,[descriptor],self._header['binding'],self._context['program'])
            lo=max(0,start-d['start']);hi=min(d['count'],end-d['start'])
            records.extend({'value':values[i],'time':times[i]} for i in range(lo,hi))
        result={'version':VERSION,'artifact_sha256':self.artifact_sha256,'kind':kind,'start':start,'total':self._counts[kind],'records':records}
        _need(len(records)==end-start and len(_canonical(result))<=LIMITS['page_bytes'],'PAGE_HOLD: exact response count/byte limit')
        self._check();return result


def _factory(cls,directory,method,*args):
    handle=None
    try:handle=cls(directory);return getattr(handle,method)(*args)
    except BaseException as exc:
        if handle is not None:handle.close()
        if isinstance(exc,(files.CycleArtifactRejected,OSError)):raise JointStorageHold(str(exc)) from exc
        raise


def create_writer(directory,binding,initial_checkpoint):return _factory(ArtifactWriter,directory,'_create',binding,initial_checkpoint)
def open_writer(directory,expected_head_sha256,binding,checkpoint):return _factory(ArtifactWriter,directory,'_resume',expected_head_sha256,binding,checkpoint)
def open_artifact(directory,expected_artifact_sha256):return _factory(ArtifactReader,directory,'_load_root',expected_artifact_sha256)
