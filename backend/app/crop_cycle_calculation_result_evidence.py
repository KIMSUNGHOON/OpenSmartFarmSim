"""Authenticated terminal result checks, separate from current farm authority."""
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import os
from pathlib import Path
import platform

from . import crop_cycle_input_evidence as input_evidence
from . import crop_cycle_calculation_artifact as artifact
from . import crop_cycle_calculation_context as calculation

inputs, engine, files = input_evidence.inputs, calculation, input_evidence.files
VERSION = 'crop-cycle-verified-result-evidence-v1'
SCOPE = 'synthetic_result_math_validation_only'
DOMAIN = b'ossf-crop-cycle-verified-result-evidence-v1\0'
MAX_EVIDENCE_BYTES = 8*1024*1024
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_TOKEN = object()
_MODULES = {'input_evidence':input_evidence, 'calculation_context':calculation, 'artifact':artifact,
    'startup_artifact':artifact.samples, 'legacy_artifact':artifact.samples.legacy_artifact,
    'canonical_json':artifact.json_store}
DEPENDENCY_SHA256 = {name:sha256(Path(module.__file__).read_bytes()).hexdigest()
                     for name,module in _MODULES.items()}
_PAYLOAD_KEYS = {'version','scope','issuer_id','key_id','validated_at','evidence_code_sha256',
    'dependency_sha256','python_version','input_root_sha256','input_evidence_sha256',
    'context_sha256','input_inode','artifact_sha256','snapshot','summary','index'}
_DECLARATIONS = (VERSION, SCOPE, DOMAIN, MAX_EVIDENCE_BYTES, CODE_SHA256,
                 tuple(sorted(DEPENDENCY_SHA256.items())), frozenset(_PAYLOAD_KEYS))


class CalculationResultEvidenceHold(ValueError):
    """No terminal-result check evidence for the requested current identities."""


def _need(condition):
    if not condition:
        raise CalculationResultEvidenceHold('crop result validation evidence unavailable')


def _pins():
    _need((VERSION, SCOPE, DOMAIN, MAX_EVIDENCE_BYTES, CODE_SHA256,
           tuple(sorted(DEPENDENCY_SHA256.items())), frozenset(_PAYLOAD_KEYS)) == _DECLARATIONS
          and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
          and {name:sha256(Path(module.__file__).read_bytes()).hexdigest()
               for name,module in _MODULES.items()} == DEPENDENCY_SHA256)
    calculation._pins()


def _calculation_record(record, input_raw):
    value = deepcopy(record)
    value['manifest'] = calculation._manifest(record, input_raw)
    value['context_sha256'] = inputs._hash(value['manifest'])
    return value


def _inode(directory):
    fd = files.job_store._open_directory_nofollow(Path(directory))
    try:
        info = files._secure(fd, directory=True)
        return [info.st_dev, info.st_ino]
    finally:
        os.close(fd)


def _stored_record_hash(fd, head, root):
    def blob(digest):
        _need(inputs._digest(digest))
        raw = files._read(fd, digest+'.json', artifact.LIMITS['metadata_bytes'])
        value = inputs._json(raw)
        _need(sha256(raw).hexdigest() == digest and inputs._canonical(value) == raw)
        return value
    header = blob(head['header_sha256'])
    _need(type(header) is dict and set(header) == {'schema_version','scope','manifest',
        'initial_checkpoint','notice_raw_utf8','artifact_code_sha256','dependency_sha256','limits'}
        and header['schema_version'] == artifact.VERSION and header['scope'] == 'software_research_only'
        and header['artifact_code_sha256'] == artifact.CODE_SHA256
        and header['dependency_sha256'] == artifact.DEPENDENCY_SHA256 and header['limits'] == artifact.LIMITS)
    index, counts, parent, terminal = {'samples':[], 'events':[]}, {'samples':0, 'events':0}, None, None
    for sequence, digest in enumerate(root['commits'], 1):
        chunk = blob(digest)
        _need(type(chunk) is dict and set(chunk) == {'version','header_sha256','sequence',
            'parent_commit_sha256','input_checkpoint_sha256','budget','result','pages'}
            and chunk['version'] == artifact.VERSION and chunk['header_sha256'] == head['header_sha256']
            and type(chunk['sequence']) is int and chunk['sequence'] == sequence
            and chunk['parent_commit_sha256'] == parent
            and type(chunk['pages']) is dict and set(chunk['pages']) == set(index))
        for kind in index:
            pages = chunk['pages'][kind]
            _need(type(pages) is list and len(pages) <= artifact.LIMITS['pages_per_commit'])
            for page in pages:
                _need(type(page) is dict and set(page) == {'sha256','count','first_at','last_at'}
                      and type(page['count']) is int and 1 <= page['count'] <= artifact.LIMITS['page_records'])
                index[kind].append({'start':counts[kind], **page}); counts[kind] += page['count']
        parent, terminal = digest, chunk['result']
    _need(type(terminal) is dict and terminal['status'] == root['status'])
    summary = {'artifact_id':artifact.VERSION+':'+head['artifact_sha256'],
        'artifact_sha256':head['artifact_sha256'], 'scope':'software_research_only',
        'manifest':header['manifest'], 'notice_raw_utf8':header['notice_raw_utf8'],
        'commit_count':len(root['commits']), 'counts':counts, **terminal}
    return inputs._hash({'summary':summary, 'index':index})


def _snapshot(directory, artifact_sha256):
    _need(inputs._digest(artifact_sha256))
    fd = files.job_store._open_directory_nofollow(Path(directory))
    try:
        before = files._secure(fd, directory=True)
        names = set(os.listdir(fd))
        _need('HEAD' in names and len(names) <= artifact.LIMITS['files'])
        controls = {'HEAD'}
        if '.writer-lock' in names:
            lock = files._file(fd, '.writer-lock', modes=(0o600,))
            try:
                _need(files._secure(lock, modes=(0o600,)).st_size == 0)
            finally:
                os.close(lock)
            controls.add('.writer-lock')
        blobs = sorted(names-controls)
        _need(blobs and all(name.endswith('.json') and inputs._digest(name[:-5]) for name in blobs))
        raw = files._read(fd, 'HEAD', 8192)
        head = inputs._json(raw)
        _need(type(head) is dict and set(head) == {'version','header_sha256','latest_commit_sha256',
            'commit_count','artifact_sha256'} and inputs._canonical(head) == raw
            and head['version'] == artifact.VERSION and head['artifact_sha256'] == artifact_sha256
            and inputs._digest(head['header_sha256']) and inputs._digest(head['latest_commit_sha256'])
            and type(head['commit_count']) is int and 1 <= head['commit_count'] <= artifact.LIMITS['commits'])
        head_sha = sha256(raw).hexdigest()
        total, inventory, root = len(raw), [], None
        for name in blobs:
            current = files._read(fd, name, artifact.LIMITS['root_bytes'])
            digest = name[:-5]
            _need(sha256(current).hexdigest() == digest)
            total += len(current)
            _need(total <= artifact.LIMITS['directory_bytes'])
            inventory.append({'sha256':digest, 'bytes':len(current)})
            if digest == artifact_sha256:
                root = inputs._json(current)
                _need(inputs._canonical(root) == current)
        _need(type(root) is dict and set(root) == {'version','header_sha256','commits','status'}
              and root['version'] == artifact.VERSION and root['header_sha256'] == head['header_sha256']
              and type(root['commits']) is list and len(root['commits']) == head['commit_count']
              and all(inputs._digest(value) for value in root['commits'])
              and root['commits'][-1] == head['latest_commit_sha256']
              and root['status'] in ('completed','hold'))
        record_sha = _stored_record_hash(fd, head, root)
        _need(sha256(files._read(fd, 'HEAD', 8192)).hexdigest() == head_sha)
        after = files._secure(fd, directory=True)
        _need(files.operator_config._metadata(before) == files.operator_config._metadata(after))
        return {'inode':[before.st_dev,before.st_ino], 'head':head, 'head_sha256':head_sha,
                'root':root, 'inventory':inventory, 'storage_bytes':total, 'file_count':len(names),
                'record_sha256':record_sha}
    finally:
        os.close(fd)


@dataclass(frozen=True)
class VerifiedCalculationResultEvidence:
    _payload_raw: bytes = field(repr=False)
    _context_raw: bytes = field(repr=False)
    evidence_sha256: str
    _token: object = field(repr=False)

    def _payload(self):
        _need(self._token is _TOKEN)
        return inputs._json(self._payload_raw)

    @property
    def summary(self):
        return self._payload()['summary']

    @property
    def index(self):
        return self._payload()['index']

    @property
    def context(self):
        _need(self._token is _TOKEN)
        return inputs._json(self._context_raw)

    @property
    def identity(self):
        payload = self._payload()
        return {'evidence_version':VERSION, 'evidence_code_sha256':CODE_SHA256,
            'evidence_sha256':self.evidence_sha256, 'artifact_sha256':payload['artifact_sha256'],
            'input_root_sha256':payload['input_root_sha256'], 'math_context_sha256':payload['context_sha256'],
            'scope':SCOPE}

    @property
    def rights_or_gate_approval(self):
        return False


class CalculationResultEvidenceAuthority:
    def __init__(self, input_authority, *, integrity_key, issuer_id, key_id):
        try:
            _need(type(input_authority) is input_evidence.InputEvidenceAuthority
                  and type(integrity_key) is bytes and 32 <= len(integrity_key) <= 4096
                  and integrity_key != input_authority.integrity_key
                  and input_evidence._identifier(issuer_id) and input_evidence._identifier(key_id))
            self.input_authority, self.integrity_key = input_authority, integrity_key
            self.issuer_id, self.key_id = issuer_id, key_id
            self._fixed = self._pointers()
            self._binding()
        except Exception:
            raise CalculationResultEvidenceHold('crop result validation evidence unavailable') from None

    def _pointers(self):
        return (self.input_authority, self.integrity_key, self.issuer_id, self.key_id)

    def _binding(self):
        _pins(); _need(self._pointers() == self._fixed)
        self.input_authority._binding()

    def _signature(self, payload):
        return hmac.new(self.integrity_key, DOMAIN+inputs._canonical(payload), 'sha256').hexdigest()

    def _metadata(self, payload):
        _need(type(payload) is dict and set(payload) == _PAYLOAD_KEYS
              and payload['version'] == VERSION and payload['scope'] == SCOPE
              and payload['issuer_id'] == self.issuer_id and payload['key_id'] == self.key_id
              and payload['evidence_code_sha256'] == CODE_SHA256
              and payload['dependency_sha256'] == DEPENDENCY_SHA256
              and payload['python_version'] == platform.python_version())
        _need(engine.physical._stamp(engine.physical._utc(payload['validated_at'])) == payload['validated_at'])

    def _record(self, payload, context, snapshot):
        self._metadata(payload)
        _need(payload['context_sha256'] == context['context_sha256'] and payload['snapshot'] == snapshot
              and inputs._hash({'summary':payload['summary'], 'index':payload['index']}) == snapshot['record_sha256'])
        summary, index = payload['summary'], payload['index']
        held = snapshot['root']['status'] == 'hold'
        keys = {'artifact_id','artifact_sha256','scope','manifest','notice_raw_utf8','commit_count','counts',
                'status','steps','planned_steps','output_start','event_start','checkpoint'}
        _need(type(summary) is dict and set(summary) == keys|({'hold','last_confirmed'} if held else set())
              and summary['artifact_sha256'] == payload['artifact_sha256']
              and summary['artifact_id'] == artifact.VERSION+':'+payload['artifact_sha256']
              and summary['scope'] == 'software_research_only' and summary['manifest'] == context['manifest']
              and summary['notice_raw_utf8'] == self.input_authority.notice_raw.decode()
              and summary['commit_count'] == snapshot['head']['commit_count']
              and summary['status'] == snapshot['root']['status']
              and summary['planned_steps'] == context['planned_steps']
              and type(summary['steps']) is int and 0 <= summary['steps'] <= context['planned_steps']
              and type(summary['counts']) is dict and set(summary['counts']) == {'samples','events'}
              and type(index) is dict and set(index) == {'samples','events'})
        inventory = {item['sha256'] for item in snapshot['inventory']}
        for kind, source in (('samples','outputs'),('events','events')):
            count = summary['counts'][kind]
            _need(type(count) is int and 0 <= count <= context['plan']['counts'][source]
                  and type(index[kind]) is list and len(index[kind]) <= artifact.LIMITS['files'])
            cursor, previous = 0, None
            for page in index[kind]:
                _need(type(page) is dict and set(page) == {'start','sha256','count','first_at','last_at'}
                      and type(page['start']) is int and page['start'] == cursor
                      and type(page['count']) is int and 1 <= page['count'] <= artifact.LIMITS['page_records']
                      and page['sha256'] in inventory)
                first, last = (engine.physical._utc(page[key]) for key in ('first_at','last_at'))
                _need(first <= last and (previous is None or previous <= first))
                cursor += page['count']; previous = last
            _need(cursor == count)
        if not held:
            cp = summary['checkpoint']
            _need(summary['steps'] == context['planned_steps']
                  and summary['counts'] == {'samples':context['plan']['counts']['outputs'],
                                            'events':context['plan']['counts']['events']}
                  and type(cp) is dict and cp['version'] == calculation.CHECKPOINT_VERSION
                  and cp['root_sha256'] == context['context_sha256']
                  and cp['seed'] == context['seed'] and cp['steps'] == summary['steps']
                  and cp['output_cursor'] == summary['counts']['samples']
                  and cp['event_cursor'] == summary['counts']['events']
                  and cp['checkpoint_sha256'] == inputs._hash({k:v for k,v in cp.items() if k != 'checkpoint_sha256'}))
        else:
            _need(summary['checkpoint'] is None and type(summary['hold']) is dict)

    def issue(self, result_directory, artifact_sha256, input_directory, input_root_sha256, input_evidence_raw):
        try:
            self._binding()
            input_inode = _inode(input_directory)
            verified = self.input_authority.verify(input_directory, input_root_sha256, input_evidence_raw)
            before = _snapshot(result_directory, artifact_sha256)
            record = _calculation_record(verified.context, input_evidence_raw)
            with calculation.open_calculation_context(input_directory, input_root_sha256,
                    input_evidence_raw, authority=self.input_authority) as context:
                _need(context.manifest == record['manifest'] and context.root_sha256 == record['context_sha256']
                      and inputs._canonical(verified.context) == context._record_raw)
                with artifact.open_artifact(result_directory, artifact_sha256, context,
                        notice_raw=self.input_authority.notice_raw) as result:
                    summary, index = result.summary, deepcopy(result._index)
                    _need(result._seen == {item['sha256'] for item in before['inventory']})
            after = _snapshot(result_directory, artifact_sha256)
            current = self.input_authority.verify(input_directory, input_root_sha256, input_evidence_raw)
            _need(before == after and _inode(input_directory) == input_inode and current.context == verified.context
                  and after['inode'] == _inode(result_directory))
            payload = {'version':VERSION,'scope':SCOPE,'issuer_id':self.issuer_id,'key_id':self.key_id,
                'validated_at':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'evidence_code_sha256':CODE_SHA256,'dependency_sha256':DEPENDENCY_SHA256,
                'python_version':platform.python_version(),'input_root_sha256':input_root_sha256,
                'input_evidence_sha256':sha256(input_evidence_raw).hexdigest(),
                'context_sha256':record['context_sha256'],'input_inode':input_inode,
                'artifact_sha256':artifact_sha256,'snapshot':after,'summary':summary,'index':index}
            self._record(payload, record, after); self._binding()
            raw = inputs._canonical({'payload':payload,'hmac_sha256':self._signature(payload)})
            _need(len(raw) <= MAX_EVIDENCE_BYTES)
            return raw
        except Exception:
            raise CalculationResultEvidenceHold('crop result validation evidence unavailable') from None

    def verify(self, result_directory, artifact_sha256, input_directory, input_root_sha256, input_evidence_raw, evidence_raw):
        try:
            self._binding()
            _need(type(evidence_raw) is bytes and 0 < len(evidence_raw) <= MAX_EVIDENCE_BYTES)
            value = inputs._json(evidence_raw)
            _need(type(value) is dict and set(value) == {'payload','hmac_sha256'}
                  and inputs._canonical(value) == evidence_raw and inputs._digest(value['hmac_sha256'])
                  and type(value['payload']) is dict)
            payload = value['payload']
            _need(hmac.compare_digest(value['hmac_sha256'], self._signature(payload))
                  and set(payload) == _PAYLOAD_KEYS
                  and payload['input_root_sha256'] == input_root_sha256
                  and payload['artifact_sha256'] == artifact_sha256
                  and payload['input_evidence_sha256'] == sha256(input_evidence_raw).hexdigest()
                  and payload['issuer_id'] == self.issuer_id and payload['key_id'] == self.key_id)
            self._metadata(payload)
            verified = self.input_authority.verify(input_directory, input_root_sha256, input_evidence_raw)
            _need(payload['input_inode'] == _inode(input_directory))
            snapshot = _snapshot(result_directory, artifact_sha256)
            current = self.input_authority.verify(input_directory, input_root_sha256, input_evidence_raw)
            _need(current.context == verified.context and payload['input_inode'] == _inode(input_directory)
                  and snapshot['inode'] == _inode(result_directory))
            record = _calculation_record(current.context, input_evidence_raw)
            self._record(payload, record, snapshot); self._binding()
            return VerifiedCalculationResultEvidence(inputs._canonical(payload), inputs._canonical(record),
                                          sha256(evidence_raw).hexdigest(), _TOKEN)
        except Exception:
            raise CalculationResultEvidenceHold('crop result validation evidence unavailable') from None
