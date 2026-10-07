"""Current farm authority and original server trace for stored crop queries."""
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path

from . import crop_cycle_result_store as storage
from . import crop_cycle_result_read_context as results
from .thermal_run_store import _canonical

VERSION='crop-cycle-current-query-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
server, inputs, evidence = storage.server, storage.inputs, results.evidence
_MODULES={'original_store':storage,'result_read_context':results}
DEPENDENCY_SHA256={name:sha256(Path(module.__file__).read_bytes()).hexdigest()
    for name,module in _MODULES.items()}
_DEPENDENCY_RAW=_canonical(DEPENDENCY_SHA256)


class CurrentCycleQueryHold(ValueError):
    """No currently authorized original stored crop result."""


def _need(condition):
    if not condition:raise CurrentCycleQueryHold('current crop research query unavailable')


def _pins():
    _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256
        and _canonical(DEPENDENCY_SHA256)==_DEPENDENCY_RAW
        and {name:sha256(Path(module.__file__).read_bytes()).hexdigest()
            for name,module in _MODULES.items()}==DEPENDENCY_SHA256)


class _ReadTrace:
    """Read-only use of pinned signature decoding; no legacy journal or writer."""
    _proof=server._Journal._proof
    _selected=server._Journal._selected

    def __init__(self, custody, tenant, packet, snapshot):
        self._fds=[]
        try:
            self.custody,self.packet,self.snapshot=custody,packet,snapshot
            self.request=packet['binding']['request'];self.name=server._intent_id(tenant,self.request)
            self.key=custody.integrity_key
            progress=packet['policies']['server_progress']
            self.intent_sha256=progress['intent_sha256'];self.binding_sha256=progress['binding_sha256']
            self.header_sha256=progress['header_sha256']
            self.expected_intent={'version':server.INTENT_VERSION,'scope':server.SCOPE,
                'tenant_id':tenant,'intent_id':self.name,'request_sha256':sha256(_canonical(self.request)).hexdigest(),
                'binding':packet['binding'],'context_sha256':progress['context_sha256'],
                'header_sha256':self.header_sha256,'notice_sha256':packet['policies']['notice_sha256'],
                'resolver_version':packet['policies']['resolver_version'],'custody_code_sha256':server.CODE_SHA256,
                'dependency_sha256':server.DEPENDENCY_SHA256,'limits':server.LIMITS}
            self.root_fd=server._open_directory_nofollow(custody.directory);self._fds.append(self.root_fd)
            self.intent_fd=server._directory(self.root_fd,self.name);self._fds.append(self.intent_fd)
            self.proof_fd=server._directory(self.intent_fd,'proofs');self._fds.append(self.proof_fd)
            self.artifact_fd=server._directory(self.intent_fd,'artifact');self._fds.append(self.artifact_fd)
            self.check()
        except Exception:self.close();raise

    def close(self):
        while self._fds:os.close(self._fds.pop())

    def check(self):
        self.custody._binding()
        info=server._secure(self.root_fd,directory=True)
        _need((info.st_dev,info.st_ino)==self.custody._identity)
        server._same_directory(self.root_fd,self.name,self.intent_fd)
        server._same_directory(self.intent_fd,'proofs',self.proof_fd)
        server._same_directory(self.intent_fd,'artifact',self.artifact_fd)
        info=server._secure(self.artifact_fd,directory=True)
        _need([info.st_dev,info.st_ino]==self.snapshot['inode'])
        raw=server._read(self.intent_fd,'intent.json',server.LIMITS['intent_bytes'])
        intent=server._checked(raw,self.key,server.INTENT_DOMAIN,server.LIMITS['intent_bytes'])
        _need(sha256(raw).hexdigest()==self.intent_sha256 and _canonical(intent)==_canonical(self.expected_intent))
        raw=server._read(self.artifact_fd,'HEAD',8192);head=inputs._json(raw)
        head_sha=server._head(head);_,proof_sha=self._selected(head)
        progress=self.packet['policies']['server_progress']
        _need(head==self.snapshot['head'] and head_sha==self.snapshot['head_sha256']==progress['head_sha256']
            and proof_sha==progress['proof_sha256'] and head['header_sha256']==progress['header_sha256']
            and head['artifact_sha256']==progress['artifact_sha256'] and head['commit_count']==progress['commit_count'])
        size,count=server._usage(self.artifact_fd,'artifact')
        _need(size==self.snapshot['storage_bytes']==progress['storage_bytes']
            and count==self.snapshot['file_count']==progress['file_count'])
        server._usage(self.root_fd,'root')


class CurrentCycleQuery:
    def __init__(self, store, authority, *, evidence_resolver):
        try:
            _need(type(store) is storage.CycleCropResultStore
                and type(authority) is evidence.ResultEvidenceAuthority
                and callable(evidence_resolver) and storage._name(evidence_resolver.version))
            self.store,self.authority,self.evidence_resolver=store,authority,evidence_resolver
            self._fixed=self._pointers();self._binding()
        except Exception:raise CurrentCycleQueryHold('current crop query authority unavailable') from None

    def _pointers(self):
        return (self.store,self.store._pointers(),self.authority,self.evidence_resolver,self.evidence_resolver.version)

    def _binding(self):
        _pins();_need(self._pointers()==self._fixed)
        self.store._binding();self.authority._binding();self.authority.input_authority._binding()
        farm=self.store.server.binding;issuer=self.authority.input_authority
        _need(issuer.profiles==farm._profiles() and issuer.notice_raw==farm.notice_raw
            and len({self.store.integrity_key,self.store.server.integrity_key,
                issuer.integrity_key,self.authority.integrity_key})==4)

    def _current(self, tenant, record, packet, farm_ref, reader, trace, source):
        self._binding();self.store._guard(tenant)
        row=self.store._find(tenant,result_id=record['result_id'])
        current=self.store._row(row,tenant,farm_ref)
        _need(self.store._record(row)==record and _canonical(current)==_canonical(packet))
        binding=self.store.server.binding;request=packet['binding']['request']
        registration=binding._registration(tenant,request,source)
        _need(_canonical(registration)==_canonical(packet['binding']['registration'])
            and packet['policies']['input_rights_version']==binding.input_rights.policy_version
            and packet['policies']['resolver_version']==self.store.server.input_resolver.version
            and packet['policies']['notice_sha256']==sha256(binding.notice_raw).hexdigest())
        declaration=deepcopy(request['rights'])
        _need(binding.input_rights(tenant,declaration,source['root_sha256'],'research_display') is True
            and _canonical(declaration)==_canonical(request['rights']))
        reader.recheck();trace.check()
        _need(_canonical(binding._registration(tenant,request,source))==_canonical(registration))
        row=self.store._find(tenant,result_id=record['result_id'])
        current=self.store._row(row,tenant,farm_ref)
        _need(self.store._record(row)==record and _canonical(current)==_canonical(packet))
        self._binding();self.store._guard(tenant)

    def read(self, tenant, result_id, farm_ref, *, kind=None, start=0, limit=None):
        with self.open(tenant,result_id,farm_ref,kind=kind,start=start,limit=limit) as value:
            return value

    @contextmanager
    def open(self, tenant, result_id, farm_ref, *, kind=None, start=0, limit=None):
        trace=None
        try:
            self._binding();self.store._guard(tenant)
            _need(type(result_id) is str and result_id.startswith(storage.VERSION+':')
                and inputs._digest(result_id[len(storage.VERSION)+1:]))
            _need(kind in (None,'samples','events') and (kind is not None
                or type(start) is int and start==0 and limit is None))
            row=self.store._find(tenant,result_id=result_id)
            if row is None:
                self._binding();self.store._guard(tenant);yield None
                self._binding();self.store._guard(tenant);return
            packet=self.store._row(row,tenant,farm_ref);record=self.store._record(row)
            owned_packet=deepcopy(packet)
            resolved=self.evidence_resolver(tenant,owned_packet)
            _need(_canonical(owned_packet)==_canonical(packet) and type(resolved) is dict
                and set(resolved)=={'input_directory','input_evidence_raw','result_evidence_raw'})
            root=packet['input_root_sha256'];progress=packet['policies']['server_progress']
            result_directory=self.store.server.directory/server._intent_id(tenant,packet['binding']['request'])/'artifact'
            with results.open_result_read_context(result_directory,packet['artifact']['sha256'],
                    resolved['input_directory'],root,resolved['input_evidence_raw'],resolved['result_evidence_raw'],
                    authority=self.authority) as reader:
                context=reader.context_record;summary=reader.summary
                snapshot=inputs._json(resolved['result_evidence_raw'])['payload']['snapshot']
                fd=server._open_directory_nofollow(Path(resolved['input_directory']))
                try:raw=server._read(fd,'root.json',inputs.MAX_ROOT_BYTES)
                finally:os.close(fd)
                _need(sha256(raw).hexdigest()==root);original=inputs._json(raw)
                source={k:original[k] for k in ('program_id','period','profile_sha256','normalization_sha256','python_version')}
                source.update(root_sha256=root,calculation_sha256=context['manifest']['calculation_sha256'],plan=context['plan'])
                _need(_canonical(source)==_canonical(packet['binding']['input'])
                    and context['context_sha256']==progress['context_sha256']
                    and summary['status']==progress['status'] and summary['steps']==progress['steps']
                    and summary['planned_steps']==progress['planned_steps'] and summary['counts']==progress['counts'])
                trace=_ReadTrace(self.store.server,tenant,packet,snapshot)
                self._current(tenant,record,packet,farm_ref,reader,trace,source)
                page=None if kind is None else reader.page(kind,start,limit)
                keys={'status','scope','steps','planned_steps','output_start','event_start','checkpoint','manifest'}
                if summary['status']=='hold':keys.update(('hold','last_confirmed'))
                terminal={key:summary[key] for key in keys}
                identity={**reader.identity,'query_version':VERSION,'query_code_sha256':CODE_SHA256,
                    'query_dependency_sha256':dict(DEPENDENCY_SHA256),'evidence_resolver_version':self.evidence_resolver.version,
                    'input_evidence_sha256':sha256(resolved['input_evidence_raw']).hexdigest(),
                    'original_payload_sha256':record['payload_sha256'],'original_binding_sha256':progress['binding_sha256'],
                    'original_intent_sha256':progress['intent_sha256'],'original_head_sha256':progress['head_sha256'],
                    'original_proof_sha256':progress['proof_sha256'],'rights_or_gate_approval':False}
                yield {'record':deepcopy(record),'terminal':deepcopy(terminal),'page':page,'identity':identity}
                self._current(tenant,record,packet,farm_ref,reader,trace,source)
        except PermissionError:raise
        except Exception:raise CurrentCycleQueryHold('current crop research query unavailable') from None
        finally:
            if trace is not None:trace.close()
