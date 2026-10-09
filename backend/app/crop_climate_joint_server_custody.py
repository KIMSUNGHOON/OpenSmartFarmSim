"""Server signatures over original joint calculations and confirmed file HEADs."""
from contextlib import contextmanager
from hashlib import sha256
import hmac
import os
from pathlib import Path

from . import crop_climate_joint_farm_binding as farms
from . import crop_climate_joint_storage as storage

evidence=farms.evidence
clock=storage.clock
continuation=storage.continuation
files=evidence.files
VERSION='joint-crop-climate-server-custody-v1'
INTENT_VERSION='joint-crop-climate-server-intent-v1'
PROOF_VERSION='joint-crop-climate-server-head-v1'
SCOPE='synthetic_joint_crop_climate_math_only'
INTENT_DOMAIN=b'ossf-joint-crop-climate-server-intent-v1\0'
PROOF_DOMAIN=b'ossf-joint-crop-climate-server-head-v1\0'
IDENTITY_DOMAIN=b'ossf-joint-crop-climate-server-identity-v1\0'
LIMITS=dict(files.LIMITS)
_LIMITS_RAW=continuation._canonical(LIMITS)
_STORAGE_LIMITS_RAW=continuation._canonical(storage.LIMITS)
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES={'farm_binding':farms,'input_evidence':evidence,'storage':storage,'time':clock,
    'continuation':continuation,'secure_files':files,'directory_helper':files.job_store,
    'file_metadata':files.operator_config}
DEPENDENCY_SHA256={k:sha256(Path(m.__file__).read_bytes()).hexdigest() for k,m in _MODULES.items()}
_DEPENDENCY_RAW=continuation._canonical(DEPENDENCY_SHA256)
_CONFIG_RAW=continuation._canonical((VERSION,INTENT_VERSION,PROOF_VERSION,SCOPE,INTENT_DOMAIN.hex(),PROOF_DOMAIN.hex(),IDENTITY_DOMAIN.hex()))
_canonical=continuation._canonical
_digest=continuation._digest


class JointCustodyHold(ValueError):
    """No authenticated, currently permitted calculation history."""


class JointCustodyConflict(ValueError):
    """An existing study revision has different original request bytes."""


class JointCustodyPending(ValueError):
    """An owned calculation history is locked by another operation."""


def _need(condition):
    if not condition:raise JointCustodyHold('joint calculation custody unavailable')


def _hash(raw):return sha256(raw).hexdigest()


def _pins():
    _need(_hash(Path(__file__).read_bytes())==CODE_SHA256
        and {k:_hash(Path(m.__file__).read_bytes()) for k,m in _MODULES.items()}==DEPENDENCY_SHA256
        and _canonical(DEPENDENCY_SHA256)==_DEPENDENCY_RAW
        and _canonical((VERSION,INTENT_VERSION,PROOF_VERSION,SCOPE,INTENT_DOMAIN.hex(),PROOF_DOMAIN.hex(),IDENTITY_DOMAIN.hex()))==_CONFIG_RAW
        and _canonical(LIMITS)==_canonical(files.LIMITS)==_LIMITS_RAW
        and _canonical(storage.LIMITS)==_STORAGE_LIMITS_RAW)
    storage._pins();evidence._pins()


def _signed(payload,key,domain):
    return _canonical({'payload':payload,'hmac_sha256':hmac.new(key,domain+_canonical(payload),'sha256').hexdigest()})


def _checked(raw,key,domain,maximum):
    _need(type(raw) is bytes and 0<len(raw)<=maximum)
    value=files.inputs._json(raw)
    _need(type(value) is dict and set(value)=={'payload','hmac_sha256'} and _canonical(value)==raw
        and type(value['payload']) is dict and _digest(value['hmac_sha256'])
        and hmac.compare_digest(value['hmac_sha256'],hmac.new(key,domain+_canonical(value['payload']),'sha256').hexdigest()))
    return value['payload']


def _intent_id(tenant,request):
    return _hash(IDENTITY_DOMAIN+_canonical({'tenant_id':tenant,'study_id':request['study_id'],'revision':request['revision']}))


def _head(value):
    _need(type(value) is dict and set(value)=={'version','header_sha256','latest_commit_sha256','commit_count','artifact_sha256'}
        and value['version']==storage.VERSION and _digest(value['header_sha256'])
        and type(value['commit_count']) is int and 0<=value['commit_count']<=storage.LIMITS['commits']
        and (value['latest_commit_sha256'] is None if value['commit_count']==0 else _digest(value['latest_commit_sha256']))
        and (value['artifact_sha256'] is None or _digest(value['artifact_sha256'])))
    return _hash(_canonical(value))


class _Session:
    def __init__(self,owner,root,intent,proofs,artifact,identity,intent_raw,binding_raw,current):
        self.owner,self.root,self.intent,self.proofs,self.artifact=owner,root,intent,proofs,artifact
        self.identity,self.intent_raw,self.binding_raw,self.current=identity,intent_raw,binding_raw,current
        self.path='/proc/self/fd/'+str(intent)+'/artifact'
        self.intent_sha256=_hash(intent_raw);self.binding_sha256=_hash(binding_raw)

    def _guard(self):
        self.owner._binding();_need(self.current()==self.binding_raw)
        files._same_directory(self.root,self.identity,self.intent)
        files._same_directory(self.intent,'proofs',self.proofs)
        files._same_directory(self.intent,'artifact',self.artifact)
        _need(files._read(self.intent,'intent.json',LIMITS['intent_bytes'])==self.intent_raw)
        files._usage(self.root,'root')

    def _proof(self,head):
        digest=_head(head);raw=files._read(self.proofs,digest+'.json',LIMITS['proof_bytes'])
        p=_checked(raw,self.owner.integrity_key,PROOF_DOMAIN,LIMITS['proof_bytes'])
        _need(set(p)=={'version','intent_sha256','binding_sha256','head','parent','sequence','action'}
            and p['version']==PROOF_VERSION and p['intent_sha256']==self.intent_sha256
            and p['binding_sha256']==self.binding_sha256 and _canonical(p['head'])==_canonical(head)
            and type(p['sequence']) is int and 0<=p['sequence']<=storage.LIMITS['commits']+1
            and p['action'] in ('initialize','advance','finalize'))
        if p['sequence']==0:
            _need(p['parent'] is None and p['action']=='initialize' and head['commit_count']==0 and head['artifact_sha256'] is None)
        else:
            _need(type(p['parent']) is dict and set(p['parent'])=={'head_sha256','proof_sha256'}
                and all(_digest(v) for v in p['parent'].values()) and p['action']!='initialize')
        return p,_hash(raw)

    def _selected(self,head):
        p,digest=self._proof(head);selected=(p,digest)
        for _ in range(storage.LIMITS['commits']+2):
            if p['sequence']==0:return selected
            parent=p['parent'];raw=files._read(self.proofs,parent['head_sha256']+'.json',LIMITS['proof_bytes'])
            _need(_hash(raw)==parent['proof_sha256'])
            previous=_checked(raw,self.owner.integrity_key,PROOF_DOMAIN,LIMITS['proof_bytes'])
            _need(_head(previous['head'])==parent['head_sha256']);q,_=self._proof(previous['head'])
            _need(q['sequence']==p['sequence']-1 and q['head']['header_sha256']==head['header_sha256']
                and q['head']['artifact_sha256'] is None)
            if p['action']=='advance':
                _need(p['head']['commit_count']==q['head']['commit_count']+1 and p['head']['artifact_sha256'] is None)
            else:
                _need(p['action']=='finalize' and p['head']['commit_count']==q['head']['commit_count']
                    and p['head']['latest_commit_sha256']==q['head']['latest_commit_sha256'] and _digest(p['head']['artifact_sha256']))
            p=q
        raise JointCustodyHold('joint calculation custody unavailable')

    def _load(self):
        with storage._Files(self.path) as handle:
            head,digest=handle._head();self._selected(head)
            data=handle._load(head);header,context,commits,cp,last,times,index,counts=data
            bound=files.inputs._json(self.binding_raw)['input']
            _need(header['context_sha256']==bound['context_sha256'] and header['binding_sha256']==bound['time_binding_sha256'])
            if head['artifact_sha256'] is not None:
                with storage.open_artifact(self.path,head['artifact_sha256']) as reader:reader.summary
            return head,digest,data

    def _reserve(self,operation):
        extra,count={
            'initialize':(2*storage.LIMITS['context_bytes']+2*storage.LIMITS['metadata_bytes']+32768,12),
            'advance':(2*storage.LIMITS['pages_per_commit']*storage.LIMITS['page_bytes']+4*storage.LIMITS['metadata_bytes']+32768,44),
            'finalize':(2*storage.LIMITS['root_bytes']+32768,8),
            'proof':(2*LIMITS['proof_bytes']+16384,4)}[operation]
        for fd,kind,a,b in ((self.root,'root','root_bytes','root_files'),
                (self.intent,'intent','intent_directory_bytes','intent_files'),
                (self.proofs,'proofs','proof_directory_bytes','proof_files')):
            n,c=files._usage(fd,kind)
            _need(n+(extra if kind!='proofs' else 2*LIMITS['proof_bytes'])<=LIMITS[a] and c+count<=LIMITS[b])
        n,c=files._usage(self.artifact,'artifact')
        _need(n+extra<=storage.LIMITS['directory_bytes'] and c+count<=storage.LIMITS['files'])

    def _publish(self,writer,original,head):
        self._guard();new=_head(head)
        if files._exists(self.artifact,'HEAD'):
            old=files.inputs._json(files._read(self.artifact,'HEAD',8192));p,digest=self._selected(old)
            _need(_head(old)==writer.head_sha256 and old['artifact_sha256'] is None
                and head['header_sha256']==old['header_sha256'])
            action='finalize' if head['artifact_sha256'] is not None else 'advance'
            _need(head['commit_count']==old['commit_count']+int(action=='advance')
                and (action!='finalize' or head['latest_commit_sha256']==old['latest_commit_sha256']))
            parent={'head_sha256':writer.head_sha256,'proof_sha256':digest};sequence=p['sequence']+1
        else:
            _need(head['commit_count']==0 and head['artifact_sha256'] is None)
            action='initialize';parent=None;sequence=0
        p={'version':PROOF_VERSION,'intent_sha256':self.intent_sha256,'binding_sha256':self.binding_sha256,
            'head':head,'parent':parent,'sequence':sequence,'action':action}
        raw=_signed(p,self.owner.integrity_key,PROOF_DOMAIN)
        self._reserve('proof')
        files._immutable(self.proofs,new+'.json',raw,LIMITS['proof_bytes'],'.proof-')
        self._guard();original(head);self._guard()

    def progress(self):
        self._guard();head,digest,data=self._load();header,context,_,cp,last,times,_,counts=data
        _,proof=self._selected(head);size,count=files._usage(self.artifact,'artifact')
        value={'version':VERSION,'scope':SCOPE,'G0_G4':'not_assessed','intent_sha256':self.intent_sha256,
            'binding_sha256':self.binding_sha256,'source_sha256':files.inputs._json(self.binding_raw)['input']['source_sha256'],
            'context_sha256':header['context_sha256'],'time_binding_sha256':header['binding_sha256'],
            'custody_code_sha256':CODE_SHA256,'head_sha256':digest,'proof_sha256':proof,
            'header_sha256':head['header_sha256'],'artifact_sha256':head['artifact_sha256'],
            'status':'ready' if last is None else last['status'],'commit_count':head['commit_count'],
            'steps':0 if last is None else last['steps'],'planned_steps':context['program']['step_count'],
            'counts':counts,'checkpoint':cp,'last_confirmed':None if last is None else last['last_confirmed'],
            'hold':None if last is None else last['hold'],'times':times,'storage_bytes':size,'file_count':count}
        raw=_canonical(value);_need(len(raw)<=LIMITS['progress_bytes']);self._guard();return raw

    def advance(self,budget,prepare):
        self._guard();existing=files._exists(self.artifact,'HEAD')
        data=None
        if existing:
            head,digest,data=self._load()
            if head['artifact_sha256'] is not None:return self.progress()
        binding=prepare();ctx=binding._context;self._guard()
        cp=continuation.start(ctx) if data is None else None if data[3] is None else continuation.restore_checkpoint(
            ctx,_canonical(data[3]['value']),expected_sha256=data[3]['sha256'])
        writer=storage.ArtifactWriter(self.path)
        try:
            original=writer._publish_head;writer._publish_head=lambda h:self._publish(writer,original,h)
            if existing:writer._resume(digest,binding,cp)
            else:self._reserve('initialize');writer._create(binding,cp)
            if writer._last is None or writer._last['status']=='yielded':
                self._guard();self._reserve('advance');chunk=continuation.advance_chunk(ctx,writer.checkpoint,budget);self._guard()
                writer.append(chunk,expected_chunk_sha256=clock.source_chunk_sha256(ctx,chunk))
            if writer._last['status'] in ('completed','hold'):
                self._guard();self._reserve('finalize');writer.finalize();self._guard()
        finally:writer.close()
        return self.progress()


class JointServerCustody:
    def __init__(self,binding,directory,*,input_resolver,integrity_key):
        try:
            _need(type(binding) is farms.JointFarmBinding and callable(input_resolver)
                and farms.permissions._name(input_resolver.version) and type(integrity_key) is bytes and 32<=len(integrity_key)<=4096)
            binding._binding();_pins();path=files.operator_config._path(directory)
            fd=files.job_store._open_directory_nofollow(path)
            try:info=files._secure(fd,directory=True);identity=(info.st_dev,info.st_ino)
            finally:os.close(fd)
            self.binding,self.directory,self.input_resolver,self.integrity_key=binding,path,input_resolver,integrity_key
            self._identity=identity;self._fixed=self._pointers()
        except Exception:raise JointCustodyHold('joint calculation authority unavailable') from None

    def _pointers(self):
        return (self.binding,self.directory,self.input_resolver,self.input_resolver.version,self.integrity_key,self._identity)

    def _binding(self):
        _pins();_need(self._pointers()==self._fixed);self.binding._binding()
        fd=files.job_store._open_directory_nofollow(self.directory)
        try:info=files._secure(fd,directory=True);_need((info.st_dev,info.st_ino)==self._identity)
        finally:os.close(fd)

    @contextmanager
    def _open(self,tenant,request_raw,write):
        opened=[]
        try:
            self._binding();self.binding._guard(tenant,write);request=self.binding._request(request_raw)
            def resolve():
                value=self.input_resolver(tenant,request['input']['source_sha256'],request['input']['evidence_sha256'])
                _need(type(value) is tuple and len(value)==2 and isinstance(value[0],(str,Path)) and type(value[1]) is bytes)
                return value
            root=files.job_store._open_directory_nofollow(self.directory);opened.append(root)
            opened.append(files._file(root,'.custody-lock',lock=True));files._usage(root,'root')
            identity=_intent_id(tenant,request)
            if not files._exists(root,identity):
                _need(write and sum(_digest(n) for n in os.listdir(root))<LIMITS['root_intents'])
            intent=files._directory(root,identity,create=write);opened.append(intent)
            opened.append(files._file(intent,'.intent-lock',lock=True))
            if files._exists(intent,'intent.json'):
                raw=files._read(intent,'intent.json',LIMITS['intent_bytes'])
                old=_checked(raw,self.integrity_key,INTENT_DOMAIN,LIMITS['intent_bytes'])
                if old.get('request_sha256')!=_hash(request_raw):raise JointCustodyConflict('joint calculation revision conflict')
                binding_raw=farms.documents._canonical(old['binding'])
            else:
                _need(write);directory,receipt=resolve();binding_raw=self.binding.prepare(tenant,request_raw,directory,receipt)
            payload={'version':INTENT_VERSION,'scope':SCOPE,'G0_G4':'not_assessed','tenant_id':tenant,'intent_id':identity,
                'request_sha256':_hash(request_raw),'binding':files.inputs._json(binding_raw),
                'resolver_version':self.input_resolver.version,'custody_code_sha256':CODE_SHA256,
                'dependency_sha256':DEPENDENCY_SHA256,'limits':LIMITS}
            intent_raw=_signed(payload,self.integrity_key,INTENT_DOMAIN)
            if files._exists(intent,'intent.json'):_need(raw==intent_raw)
            def current():
                self._binding();d,r=resolve()
                return self.binding.current(tenant,request_raw,d,r,binding_raw,write=write)
            _need(current()==binding_raw)
            if not files._exists(intent,'intent.json'):
                n,c=files._usage(root,'root')
                _need(n+2*LIMITS['intent_bytes']<=LIMITS['root_bytes'] and c+4<=LIMITS['root_files'])
            files._immutable(intent,'intent.json',intent_raw,LIMITS['intent_bytes'],'.intent-')
            proofs=files._directory(intent,'proofs',create=write);opened.append(proofs)
            artifact=files._directory(intent,'artifact',create=write);opened.append(artifact)
            session=_Session(self,root,intent,proofs,artifact,identity,intent_raw,binding_raw,current)
            def prepare():
                session._guard();d,r=resolve();source=request['input']
                verified=self.binding.input_authority.verify(d,source['source_sha256'],r,
                    expected_context_sha256=source['context_sha256'],expected_binding_sha256=source['time_binding_sha256'])
                raw,_=evidence._current(d,source['source_sha256']);v=evidence._source(raw['source.json'])
                profiles={k+'_profile':cls(raw[k+'.json']) for k,cls in zip(continuation.PROFILE_NAMES,evidence._CLASSES,strict=True)}
                ctx=continuation.prepare_context(**{k:v[k] for k in ('scenario','events','output_steps','step_seconds','step_count')},**profiles)
                binding=clock.prepare_binding(ctx,origin=v['time_origin'])
                _need(_canonical(evidence._record(binding))==_canonical(verified.record));session._guard();return binding
            yield session,prepare
        except (JointCustodyConflict,PermissionError):raise
        except files.CycleCustodyPending:raise JointCustodyPending('joint calculation custody busy') from None
        except Exception:raise JointCustodyHold('joint calculation custody unavailable') from None
        finally:
            for fd in reversed(opened):os.close(fd)

    def advance(self,tenant,request_raw,*,budget):
        _need(type(budget) is int and 1<=budget<=continuation.MAX_CHUNK_BOUNDARIES)
        with self._open(tenant,request_raw,True) as (session,prepare):return session.advance(budget,prepare)

    def inspect(self,tenant,request_raw):
        with self._open(tenant,request_raw,False) as (session,_):return session.progress()

    def page(self,tenant,request_raw,expected_progress_raw,kind,*,start=0,limit=None):
        with self._open(tenant,request_raw,False) as (session,_):
            _need(type(expected_progress_raw) is bytes and 0<len(expected_progress_raw)<=LIMITS['progress_bytes']
                and session.progress()==expected_progress_raw)
            head,_,_=session._load();_need(_digest(head['artifact_sha256']))
            with storage.open_artifact(session.path,head['artifact_sha256']) as reader:page=reader.page(kind,start=start,limit=limit)
            _need(session.progress()==expected_progress_raw);return page
