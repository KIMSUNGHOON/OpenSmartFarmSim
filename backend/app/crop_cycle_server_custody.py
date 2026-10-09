"""Server-owned crop execution with durable signatures before HEAD selection."""
from contextlib import contextmanager
from copy import deepcopy
import fcntl
from hashlib import sha256
import hmac
import os
from pathlib import Path
import stat
from uuid import uuid4

from . import crop_cycle_artifact as artifact
from . import crop_cycle_farm_binding as farms
from . import crop_cycle_input_stream as inputs
from . import crop_cycle_stream_execution as engine
from . import job_store
from . import operator_config
from .crop_result_store import _name
from .job_store import _open_directory_nofollow
from .thermal_run_store import _canonical

VERSION='crop-cycle-server-custody-v1'
INTENT_VERSION='crop-cycle-server-intent-v1'
PROOF_VERSION='crop-cycle-server-head-v1'
SCOPE='synthetic_crop_math_only'
INTENT_DOMAIN=b'ossf-crop-cycle-server-intent-v1\0'
PROOF_DOMAIN=b'ossf-crop-cycle-server-head-v1\0'
IDENTITY_DOMAIN=b'ossf-crop-cycle-server-identity-v1\0'
LIMITS={'intent_bytes':192*1024,'proof_bytes':8192,'progress_bytes':128*1024,
    'proof_directory_bytes':128*1024*1024,'proof_files':32770,
    'intent_directory_bytes':640*1024*1024,'intent_files':98310,
    'root_bytes':1024*1024*1024,'root_files':131072,'root_intents':128}
_LIMITS_RAW=_canonical(LIMITS)
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES={'artifact':artifact,'farm_binding':farms,'input_stream':inputs,'execution':engine,
    'directory_helper':job_store,'file_helper':operator_config}
DEPENDENCY_SHA256={k:sha256(Path(m.__file__).read_bytes()).hexdigest() for k,m in _MODULES.items()}


class CycleCustodyHold(ValueError):
    pass


class CycleCustodyConflict(ValueError):
    pass


class CycleCustodyPending(ValueError):
    pass


def _need(condition):
    if not condition:raise CycleCustodyHold('cycle execution custody unavailable')


def _hash(raw):return sha256(raw).hexdigest()


def _pins():
    _need(_hash(Path(__file__).read_bytes())==CODE_SHA256 and _canonical(LIMITS)==_LIMITS_RAW
        and {k:_hash(Path(m.__file__).read_bytes()) for k,m in _MODULES.items()}==DEPENDENCY_SHA256)


def _intent_id(tenant,request):
    return _hash(IDENTITY_DOMAIN+_canonical({'tenant_id':tenant,'study_id':request['study_id'],'revision':request['revision']}))


def _secure(fd,*,directory=False,modes=(0o400,)):
    info=os.fstat(fd)
    _need(info.st_uid==os.geteuid() and stat.S_IMODE(info.st_mode) in ((0o700,) if directory else modes)
        and (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink==1))
    operator_config._no_acl(fd)
    return info


def _directory(parent,name,*,create=False):
    if create:
        try:os.mkdir(name,mode=0o700,dir_fd=parent);os.fsync(parent)
        except FileExistsError:pass
    fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
    try:_secure(fd,directory=True);return fd
    except BaseException:os.close(fd);raise


def _file(parent,name,*,lock=False,modes=(0o400,)):
    flags=(os.O_RDWR|os.O_CREAT) if lock else os.O_RDONLY
    fd=os.open(name,flags|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,0o600,dir_fd=parent)
    try:
        info=_secure(fd,modes=(0o600,) if lock else modes)
        if lock:
            _need(info.st_size==0)
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise CycleCustodyPending('cycle execution custody busy') from None
        return fd
    except BaseException:os.close(fd);raise


def _read(parent,name,maximum):
    fd=_file(parent,name)
    try:
        before=_secure(fd);_need(1<=before.st_size<=maximum)
        with os.fdopen(fd,'rb',closefd=False) as handle:raw=handle.read(maximum+1)
        after=_secure(fd)
        _need(len(raw)==before.st_size and operator_config._metadata(before)==operator_config._metadata(after))
        return raw
    finally:os.close(fd)


def _exists(parent,name):
    try:os.stat(name,dir_fd=parent,follow_symlinks=False);return True
    except FileNotFoundError:return False


def _immutable(parent,name,raw,maximum,prefix):
    _need(type(raw) is bytes and 1<=len(raw)<=maximum)
    if _exists(parent,name):
        _need(_read(parent,name,maximum)==raw);return _hash(raw)
    temporary=prefix+uuid4().hex+'.tmp';fd=None
    try:
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=parent)
        with os.fdopen(fd,'wb') as handle:
            fd=None;handle.write(raw);handle.flush();os.fchmod(handle.fileno(),0o400);os.fsync(handle.fileno())
        os.link(temporary,name,src_dir_fd=parent,dst_dir_fd=parent,follow_symlinks=False);os.fsync(parent)
    finally:
        if fd is not None:os.close(fd)
        try:os.unlink(temporary,dir_fd=parent);os.fsync(parent)
        except FileNotFoundError:pass
    return _hash(raw)


def _signed(payload,key,domain):
    raw=_canonical(payload)
    return _canonical({'payload':payload,'signature':hmac.new(key,domain+raw,'sha256').hexdigest()})


def _checked(raw,key,domain,maximum):
    _need(type(raw) is bytes and 1<=len(raw)<=maximum)
    envelope=inputs._json(raw)
    _need(type(envelope) is dict and set(envelope)=={'payload','signature'} and _canonical(envelope)==raw
        and type(envelope['payload']) is dict and inputs._digest(envelope['signature'])
        and hmac.compare_digest(envelope['signature'],hmac.new(key,domain+_canonical(envelope['payload']),'sha256').hexdigest()))
    return envelope['payload']


def _usage(fd,kind):
    _secure(fd,directory=True);names=os.listdir(fd);size=count=directories=0
    maximum={'root':LIMITS['root_files']+LIMITS['root_intents']+1,
        'intent':LIMITS['intent_files']+2,'proofs':LIMITS['proof_files'],'artifact':artifact.LIMITS['files']}[kind]
    _need(len(names)<=maximum)
    for name in names:
        child_kind=None
        if kind=='root' and inputs._digest(name):child_kind='intent';directories+=1
        if kind=='intent' and name in ('proofs','artifact'):child_kind=name
        if child_kind:
            child=_directory(fd,name)
            try:n,c=_usage(child,child_kind);size+=n;count+=c
            finally:os.close(child)
            continue
        immutable=(kind=='intent' and name=='intent.json') or (kind in ('proofs','artifact')
            and (name=='HEAD' and kind=='artifact' or name.endswith('.json') and inputs._digest(name[:-5])))
        lock=(kind=='root' and name=='.custody-lock') or (kind=='intent' and name=='.intent-lock') or (kind=='artifact' and name=='.writer-lock')
        prefixes={'root':(),'intent':('.intent-',),'proofs':('.proof-',),'artifact':('.blob-','.head-')}[kind]
        temporary=any(name.startswith(p) and name.endswith('.tmp')
            and len(name)==len(p)+36 and all(c in '0123456789abcdef' for c in name[len(p):-4]) for p in prefixes)
        _need(immutable or lock or temporary)
        child=_file(fd,name,modes=(0o600,) if lock else (0o400,0o600) if temporary else (0o400,))
        try:
            info=os.fstat(child);_need(not lock or info.st_size==0);size+=info.st_size;count+=1
        finally:os.close(child)
    caps={'root':('root_bytes','root_files'),'intent':('intent_directory_bytes','intent_files'),
        'proofs':('proof_directory_bytes','proof_files')}
    if kind=='artifact':_need(size<=artifact.LIMITS['directory_bytes'] and count<=artifact.LIMITS['files'])
    else:
        a,b=caps[kind];_need(size<=LIMITS[a] and count<=LIMITS[b])
    if kind=='root':_need(directories<=LIMITS['root_intents'])
    return size,count


def _head(value):
    _need(type(value) is dict and set(value)=={'version','header_sha256','latest_commit_sha256','commit_count','artifact_sha256'}
        and value['version']==artifact.VERSION and inputs._digest(value['header_sha256'])
        and type(value['commit_count']) is int and 0<=value['commit_count']<=artifact.LIMITS['commits']
        and (value['latest_commit_sha256'] is None if value['commit_count']==0 else inputs._digest(value['latest_commit_sha256']))
        and (value['artifact_sha256'] is None or inputs._digest(value['artifact_sha256'])))
    return _hash(artifact._canonical(value))


def _secure_input(reader):
    _need(type(reader) is inputs.InputPacket and not reader.closed);_secure(reader._fd,directory=True)
    expected={'root.json'}|{b['sha256']+'.json' for stream in reader.manifest['streams'].values() for b in stream['blocks']}
    _need(set(os.listdir(reader._fd))==expected)
    for name in expected:
        fd=_file(reader._fd,name,modes=(0o400,0o600,0o644));os.close(fd)


def _same_directory(parent,name,fd):
    _secure(fd,directory=True);actual=os.stat(name,dir_fd=parent,follow_symlinks=False);expected=os.fstat(fd)
    _need((actual.st_dev,actual.st_ino)==(expected.st_dev,expected.st_ino))


class _Journal:
    def __init__(self,root_fd,intent_fd,context,binding_raw,tenant,request_raw,resolver_version,key,current,*,notice_raw,create):
        self.writer=None;self.proof_fd=None;self.artifact_fd=None
        try:
            self.root_fd,self.intent_fd,self.context=root_fd,intent_fd,context
            self.binding_raw,self.key,self.current,self.notice=binding_raw,key,current,notice_raw
            _need(type(key) is bytes and 32<=len(key)<=4096 and type(binding_raw) is bytes
                and len(binding_raw)<=farms.MAX_BINDING_BYTES and type(create) is bool)
            request=inputs._json(request_raw);self._identity=_intent_id(tenant,request)
            self.header=artifact._header(context,notice_raw);self.header_sha256=_hash(artifact._canonical(self.header))
            payload={'version':INTENT_VERSION,'scope':SCOPE,'tenant_id':tenant,'intent_id':self._identity,
                'request_sha256':_hash(request_raw),'binding':inputs._json(binding_raw),'context_sha256':context.root_sha256,
                'header_sha256':self.header_sha256,'notice_sha256':_hash(notice_raw),'resolver_version':resolver_version,
                'custody_code_sha256':CODE_SHA256,'dependency_sha256':DEPENDENCY_SHA256,'limits':LIMITS}
            self.genesis_raw=_signed(payload,key,INTENT_DOMAIN)
            self.intent_sha256=_hash(self.genesis_raw);self.binding_sha256=_hash(binding_raw)
            _pins();_secure_input(context.reader);_need(self.current()==binding_raw)
            _secure_input(context.reader);_same_directory(root_fd,self._identity,intent_fd);_usage(root_fd,'root')
            if _exists(intent_fd,'intent.json'):
                old_raw=_read(intent_fd,'intent.json',LIMITS['intent_bytes'])
                old=_checked(old_raw,key,INTENT_DOMAIN,LIMITS['intent_bytes'])
                if old.get('request_sha256')!=payload['request_sha256']:
                    raise CycleCustodyConflict('cycle execution revision conflict')
                _need(old_raw==self.genesis_raw)
            else:
                _need(create and not _exists(intent_fd,'artifact') and not _exists(intent_fd,'proofs'))
                n,c=_usage(root_fd,'root')
                _need(n+2*LIMITS['intent_bytes']+2*artifact.LIMITS['metadata_bytes']+32768<=LIMITS['root_bytes']
                    and c+12<=LIMITS['root_files'])
                _immutable(intent_fd,'intent.json',self.genesis_raw,LIMITS['intent_bytes'],'.intent-')
            self.proof_fd=_directory(intent_fd,'proofs',create=create)
            self.artifact_fd=_directory(intent_fd,'artifact',create=create)
            path='/proc/self/fd/'+str(intent_fd)+'/artifact'
            if _exists(self.artifact_fd,'HEAD'):
                head=inputs._json(_read(self.artifact_fd,'HEAD',8192));head_sha=_head(head)
                self._selected(head)
                self.writer=artifact.open_writer(path,head_sha,context,notice_raw=notice_raw)
            else:
                _need(create);self._initial_files()
                self.writer=artifact.ArtifactWriter(path);self.writer._acquire()
                self.writer.context=context;self.writer.notice=notice_raw
                self.writer._hashes=[];self.writer._checkpoint=deepcopy(self.header['initial_checkpoint']);self.writer._summary=None
                _need(self.writer._put(artifact._canonical(self.header),artifact.LIMITS['metadata_bytes'])==self.header_sha256)
            _need((os.fstat(self.writer._fd).st_dev,os.fstat(self.writer._fd).st_ino)==
                (os.fstat(self.artifact_fd).st_dev,os.fstat(self.artifact_fd).st_ino))
            original=self.writer._publish_head
            self.writer._publish_head=lambda head:self._publish(head,original)
            if not _exists(self.artifact_fd,'HEAD'):
                self.writer._publish_head({'version':artifact.VERSION,'header_sha256':self.header_sha256,
                    'latest_commit_sha256':None,'commit_count':0,'artifact_sha256':None})
            _usage(root_fd,'root')
        except (CycleCustodyConflict,CycleCustodyPending,PermissionError):self.close();raise
        except Exception:self.close();raise CycleCustodyHold('cycle execution custody unavailable') from None

    def close(self):
        if self.writer is not None:self.writer.close();self.writer=None
        for key in ('proof_fd','artifact_fd'):
            fd=getattr(self,key,None)
            if fd is not None:os.close(fd);setattr(self,key,None)

    def _guard(self):
        _pins();_secure_input(self.context.reader);_need(self.current()==self.binding_raw)
        _secure_input(self.context.reader)
        _secure(self.root_fd,directory=True);_secure(self.intent_fd,directory=True)
        _same_directory(self.root_fd,self._identity,self.intent_fd)
        _same_directory(self.intent_fd,'proofs',self.proof_fd)
        _same_directory(self.intent_fd,'artifact',self.artifact_fd)
        _need(_read(self.intent_fd,'intent.json',LIMITS['intent_bytes'])==self.genesis_raw)
        artifact._pins(self.context,self.notice)

    def _initial_files(self):
        initial={'version':artifact.VERSION,'header_sha256':self.header_sha256,
            'latest_commit_sha256':None,'commit_count':0,'artifact_sha256':None}
        digest=_head(initial)
        for name in os.listdir(self.proof_fd):
            _need(name==digest+'.json')
            self._proof(initial)
        for name in os.listdir(self.artifact_fd):
            if name=='.writer-lock':continue
            if name==self.header_sha256+'.json':
                _need(_read(self.artifact_fd,name,artifact.LIMITS['metadata_bytes'])==artifact._canonical(self.header));continue
            _need(name.startswith(('.head-','.blob-')) and name.endswith('.tmp'))
            fd=_file(self.artifact_fd,name,modes=(0o400,0o600))
            try:
                _need(os.fstat(fd).st_size<=artifact.LIMITS['metadata_bytes'])
                with os.fdopen(fd,'rb',closefd=False) as handle:raw=handle.read(artifact.LIMITS['metadata_bytes']+1)
                _need(raw in (artifact._canonical(initial),artifact._canonical(self.header)))
            finally:os.close(fd)

    def _proof(self,head):
        digest=_head(head);raw=_read(self.proof_fd,digest+'.json',LIMITS['proof_bytes'])
        payload=_checked(raw,self.key,PROOF_DOMAIN,LIMITS['proof_bytes'])
        _need(set(payload)=={'version','intent_sha256','binding_sha256','head','parent','sequence','action'}
            and payload['version']==PROOF_VERSION and payload['intent_sha256']==self.intent_sha256
            and payload['binding_sha256']==self.binding_sha256 and _head(payload['head'])==digest
            and type(payload['sequence']) is int and 0<=payload['sequence']<=artifact.LIMITS['commits']+1
            and payload['action'] in ('initialize','advance','finalize'))
        parent=payload['parent']
        if payload['sequence']==0:
            _need(parent is None and payload['action']=='initialize' and head['commit_count']==0
                and head['artifact_sha256'] is None and head['header_sha256']==self.header_sha256)
        else:
            _need(type(parent) is dict and set(parent)=={'head_sha256','proof_sha256'}
                and all(inputs._digest(v) for v in parent.values()) and payload['action']!='initialize')
        return payload,_hash(raw)

    def _selected(self,head):
        _need(head['header_sha256']==self.header_sha256)
        current,signature_sha=self._proof(head);selected=(current,signature_sha)
        for _ in range(artifact.LIMITS['commits']+2):
            if current['sequence']==0:return selected
            parent=current['parent'];raw=_read(self.proof_fd,parent['head_sha256']+'.json',LIMITS['proof_bytes'])
            _need(_hash(raw)==parent['proof_sha256'])
            previous=_checked(raw,self.key,PROOF_DOMAIN,LIMITS['proof_bytes'])
            _need(_head(previous['head'])==parent['head_sha256'])
            previous,_=self._proof(previous['head'])
            _need(previous['sequence']==current['sequence']-1 and previous['head']['header_sha256']==head['header_sha256']
                and previous['head']['artifact_sha256'] is None)
            if current['action']=='advance':
                _need(current['head']['commit_count']==previous['head']['commit_count']+1 and current['head']['artifact_sha256'] is None)
            else:
                _need(current['action']=='finalize' and current['head']['commit_count']==previous['head']['commit_count']
                    and current['head']['latest_commit_sha256']==previous['head']['latest_commit_sha256']
                    and inputs._digest(current['head']['artifact_sha256']))
            current=previous
        raise CycleCustodyHold('cycle execution custody unavailable')

    def _reserve(self,operation):
        sizes={kind:_usage(fd,kind) for kind,fd in (('root',self.root_fd),('intent',self.intent_fd),
            ('artifact',self.artifact_fd),('proofs',self.proof_fd))}
        if operation=='advance':
            extra=2*artifact.LIMITS['delta_bytes']+4*artifact.LIMITS['metadata_bytes']+2*LIMITS['proof_bytes']+16384;files=40
        elif operation=='finalize':extra=2*artifact.LIMITS['root_bytes']+2*LIMITS['proof_bytes']+16384;files=8
        else:extra=2*LIMITS['proof_bytes']+16384;files=4
        for kind,a,b in (('root','root_bytes','root_files'),('intent','intent_directory_bytes','intent_files')):
            n,c=sizes[kind];_need(n+extra<=LIMITS[a] and c+files<=LIMITS[b])
        n,c=sizes['proofs'];_need(n+2*LIMITS['proof_bytes']<=LIMITS['proof_directory_bytes'] and c+2<=LIMITS['proof_files'])
        n,c=sizes['artifact'];_need(n+extra<=artifact.LIMITS['directory_bytes'] and c+files<=artifact.LIMITS['files'])

    def _publish(self,head,original):
        self._guard();self._reserve('publish');new_sha=_head(head)
        old=None
        if _exists(self.artifact_fd,'HEAD'):
            old=inputs._json(_read(self.artifact_fd,'HEAD',8192))
            previous,proof_sha=self._selected(old)
            _need(_head(old)==self.writer.head_sha256)
            parent={'head_sha256':self.writer.head_sha256,'proof_sha256':proof_sha}
            sequence=previous['sequence']+1
            action='finalize' if head['artifact_sha256'] is not None else 'advance'
            _need(old['artifact_sha256'] is None and head['header_sha256']==old['header_sha256'])
            if action=='advance':_need(head['commit_count']==old['commit_count']+1)
            else:_need(head['commit_count']==old['commit_count'] and head['latest_commit_sha256']==old['latest_commit_sha256'])
        else:
            parent=None;sequence=0;action='initialize'
            _need(head['header_sha256']==self.header_sha256 and head['commit_count']==0 and head['artifact_sha256'] is None)
        body={'version':PROOF_VERSION,'intent_sha256':self.intent_sha256,'binding_sha256':self.binding_sha256,
            'head':head,'parent':parent,'sequence':sequence,'action':action}
        raw=_signed(body,self.key,PROOF_DOMAIN)
        _immutable(self.proof_fd,new_sha+'.json',raw,LIMITS['proof_bytes'],'.proof-')
        original(head)

    def _progress(self):
        _need(self.writer is not None and not self.writer.closed)
        head,actual=self.writer._head();_need(actual==self.writer.head_sha256)
        _,proof_sha=self._selected(head)
        _,_,summary,_,counts=artifact._wrap_validation(self.writer._load_prefix,self.context,self.notice,head)
        size,count=_usage(self.artifact_fd,'artifact')
        value={'version':VERSION,'scope':SCOPE,'intent_sha256':self.intent_sha256,'binding_sha256':self.binding_sha256,
            'input_root_sha256':self.context.reader.root_sha256,'context_sha256':self.context.root_sha256,
            'custody_code_sha256':CODE_SHA256,'head_sha256':actual,'proof_sha256':proof_sha,
            'header_sha256':head['header_sha256'],'artifact_sha256':head['artifact_sha256'],
            'status':'yielded' if summary is None else summary['status'],'commit_count':head['commit_count'],
            'steps':0 if summary is None else summary['steps'],'planned_steps':self.context.planned_steps,
            'counts':counts,'storage_bytes':size,'file_count':count}
        raw=_canonical(value);_need(len(raw)<=LIMITS['progress_bytes']);return raw

    def inspect(self):
        try:
            self._guard();_usage(self.root_fd,'root');raw=self._progress();self._guard();return raw
        except PermissionError:raise
        except Exception:raise CycleCustodyHold('cycle execution custody unavailable') from None

    def advance(self,budget):
        try:
            artifact._budget(budget);self._guard()
            _need(self.writer is not None and not self.writer.closed)
            if self.writer._summary is None or self.writer._summary['status']=='yielded':
                self._reserve('advance');self.writer.advance(budget)
            if self.writer._summary is not None and self.writer._summary['status'] in ('completed','hold'):
                head,_=self.writer._head()
                if head['artifact_sha256'] is None:self._reserve('finalize');self.writer.finalize()
            self._guard();_usage(self.root_fd,'root');return self._progress()
        except PermissionError:raise
        except Exception:raise CycleCustodyHold('cycle execution custody unavailable') from None

    def page(self,expected_progress_raw,kind,start=0,limit=None):
        try:
            _need(type(expected_progress_raw) is bytes and 1<=len(expected_progress_raw)<=LIMITS['progress_bytes'])
            self._guard();_usage(self.root_fd,'root');current=self._progress();_need(current==expected_progress_raw)
            head,_=self.writer._head();_need(inputs._digest(head['artifact_sha256']))
            path='/proc/self/fd/'+str(self.intent_fd)+'/artifact'
            with artifact.open_artifact(path,head['artifact_sha256'],self.context,notice_raw=self.notice) as reader:
                page=reader.page(kind,start,limit)
            self._guard();_usage(self.root_fd,'root');_need(self._progress()==current);return page
        except PermissionError:raise
        except Exception:raise CycleCustodyHold('cycle execution custody unavailable') from None


class CycleServerCustody:
    def __init__(self,binding,directory,*,input_resolver,integrity_key):
        try:
            _need(type(binding) is farms.CycleFarmBinding and callable(input_resolver) and _name(input_resolver.version)
                and type(integrity_key) is bytes and 32<=len(integrity_key)<=4096)
            binding._binding();_pins();path=operator_config._path(directory)
            fd=_open_directory_nofollow(path)
            try:info=_secure(fd,directory=True);identity=(info.st_dev,info.st_ino)
            finally:os.close(fd)
            self.binding,self.directory,self.input_resolver,self.integrity_key=binding,path,input_resolver,integrity_key
            self._identity=identity;self._fixed=self._pointers()
        except Exception:raise CycleCustodyHold('cycle execution authority unavailable') from None

    def _pointers(self):
        return (self.binding,self.directory,self.input_resolver,self.input_resolver.version,self.integrity_key,self._identity)

    def _binding(self):
        _pins();_need(self._pointers()==self._fixed);self.binding._binding()
        fd=_open_directory_nofollow(self.directory)
        try:info=_secure(fd,directory=True);_need((info.st_dev,info.st_ino)==self._identity)
        finally:os.close(fd)

    @contextmanager
    def _open(self,tenant,request_raw,write):
        root=intent=root_lock=intent_lock=None;journal=None
        try:
            self._binding();self.binding._guard(tenant,write);request=self.binding._request(request_raw)
            root=_open_directory_nofollow(self.directory);root_lock=_file(root,'.custody-lock',lock=True)
            _usage(root,'root');name=_intent_id(tenant,request)
            if not write:_need(_exists(root,name))
            intent=_directory(root,name,create=write);intent_lock=_file(intent,'.intent-lock',lock=True)
            reader=self.input_resolver(request['input']['root_sha256'],**self.binding._profiles())
            if isinstance(reader,inputs.InputPacket) and type(reader) is not inputs.InputPacket:
                inputs.InputPacket.close(reader)
                raise CycleCustodyHold('cycle execution custody unavailable')
            _need(type(reader) is inputs.InputPacket and not reader.closed)
            with reader:
                _secure_input(reader)
                context=engine.prepare_context(reader,**self.binding._profiles())
                if _exists(intent,'intent.json'):
                    old=_checked(_read(intent,'intent.json',LIMITS['intent_bytes']),self.integrity_key,INTENT_DOMAIN,LIMITS['intent_bytes'])
                    if old.get('request_sha256')!=_hash(request_raw):raise CycleCustodyConflict('cycle execution revision conflict')
                    _need('binding' in old);binding_raw=_canonical(old['binding'])
                else:_need(write);binding_raw=self.binding.prepare(tenant,request_raw,reader)
                def current():
                    self._binding();_secure(reader._fd,directory=True)
                    return self.binding.current(tenant,request_raw,reader,binding_raw,write=write)
                journal=_Journal(root,intent,context,binding_raw,tenant,request_raw,self.input_resolver.version,
                    self.integrity_key,current,notice_raw=self.binding.notice_raw,create=write)
                yield journal
        except (CycleCustodyConflict,CycleCustodyPending,PermissionError):raise
        except Exception:raise CycleCustodyHold('cycle execution custody unavailable') from None
        finally:
            if journal is not None:journal.close()
            for fd in (intent_lock,intent,root_lock,root):
                if fd is not None:os.close(fd)

    def advance(self,tenant,request_raw,*,budget):
        try:artifact._budget(budget)
        except Exception:raise CycleCustodyHold('cycle execution custody unavailable') from None
        with self._open(tenant,request_raw,True) as journal:return journal.advance(budget)

    def inspect(self,tenant,request_raw):
        with self._open(tenant,request_raw,False) as journal:return journal.inspect()

    def page(self,tenant,request_raw,expected_progress_raw,kind,start=0,limit=None):
        with self._open(tenant,request_raw,False) as journal:return journal.page(expected_progress_raw,kind,start,limit)
