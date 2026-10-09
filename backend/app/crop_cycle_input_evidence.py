"""Authenticated original input checks; current rights remain a separate check."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import platform
import re

from . import crop_cycle_input_stream as inputs
from . import crop_cycle_stream_execution as engine
from . import crop_cycle_server_custody as files

VERSION = 'crop-cycle-input-evidence-v1'
SCOPE = 'synthetic_input_math_validation_only'
DOMAIN = b'ossf-crop-cycle-input-evidence-v1\0'
MAX_EVIDENCE_BYTES = 1024*1024
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_TOKEN = object()
_PHYSICAL = engine.physical
_MODULES = {
    'input_stream': inputs, 'stream_execution': engine, 'continuation': engine.short,
    'file_custody': files, 'directory_helper': files.job_store, 'file_metadata': files.operator_config,
    'integrator': _PHYSICAL, 'coupled': _PHYSICAL.coupled, 'startup': _PHYSICAL.startup,
    'plant': _PHYSICAL.plant, 'cohorts': _PHYSICAL.fruit, 'allocation': _PHYSICAL.allocation,
    'transport': _PHYSICAL.transport, 'legacy_helpers': _PHYSICAL.legacy,
    'original_rates': _PHYSICAL.legacy.coupled,
}
DEPENDENCY_SHA256 = {name:sha256(Path(module.__file__).read_bytes()).hexdigest()
                     for name,module in _MODULES.items()}
_CONTEXT_KEYS = {'manifest','initial','initial_clock','seed','start_at','planned_steps',
                 'boundary_count','segment_count','context_sha256','plan','index'}


class InputEvidenceHold(ValueError):
    """No usable original input-check evidence for the requested identity."""


def _need(condition):
    if not condition:
        raise InputEvidenceHold('crop input validation evidence unavailable')


def _identifier(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', value) is not None


def _pins():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
          and {name:sha256(Path(module.__file__).read_bytes()).hexdigest()
               for name,module in _MODULES.items()} == DEPENDENCY_SHA256)


def _context_record(context):
    engine._require_context(context)
    index = [{'cursor':None if page.cursor is None else json.loads(page.cursor),
              'previous':page.previous,'steps':page.steps} for page in context.index]
    _need(inputs._hash(index) == context.manifest['grid_index_sha256'])
    return {'manifest':context.manifest,'initial':json.loads(context._initial),
            'initial_clock':json.loads(context._initial_clock),'seed':list(context.seed),
            'start_at':context.start_at,'planned_steps':context.planned_steps,
            'boundary_count':context.boundary_count,'segment_count':context.segment_count,
            'context_sha256':context.root_sha256,'plan':context.reader.plan,'index':index}


def _current_bytes(directory, expected_root):
    _need(inputs._digest(expected_root))
    fd = files.job_store._open_directory_nofollow(Path(directory))
    try:
        before = files._secure(fd, directory=True)
        raw = files._read(fd, 'root.json', inputs.MAX_ROOT_BYTES)
        _need(sha256(raw).hexdigest() == expected_root)
        root = inputs._json(raw)
        _need(inputs._canonical(root) == raw)
        names = {block['sha256'] for stream in root['streams'].values() for block in stream['blocks']}
        _need(all(inputs._digest(name) for name in names)
              and set(os.listdir(fd)) == {'root.json',*(name+'.json' for name in names)})
        total = len(raw)
        for name in sorted(names):
            current = files._read(fd, name+'.json', inputs.MAX_BLOCK_BYTES)
            _need(sha256(current).hexdigest() == name)
            total += len(current)
            _need(total <= inputs.MAX_PACKET_BYTES)
        after = files._secure(fd, directory=True)
        _need(files.operator_config._metadata(before) == files.operator_config._metadata(after))
        return root, total, len(names)
    finally:
        os.close(fd)


@dataclass(frozen=True)
class VerifiedInputEvidence:
    _context_raw: bytes = field(repr=False)
    evidence_sha256: str
    referenced_bytes: int
    unique_blob_count: int
    _token: object = field(repr=False)

    @property
    def context(self):
        _need(self._token is _TOKEN)
        return inputs._json(self._context_raw)

    @property
    def rights_or_gate_approval(self):
        return False


class InputEvidenceAuthority:
    def __init__(self, profiles, notice_raw, *, integrity_key, issuer_id, key_id):
        try:
            _need(type(profiles) is dict and set(profiles) == {
                'growth_profile','cohort_profile','transport_profile'})
            _need(type(integrity_key) is bytes and 32 <= len(integrity_key) <= 4096
                  and _identifier(issuer_id) and _identifier(key_id))
            _need(type(notice_raw) is bytes and sha256(notice_raw).hexdigest() == files.artifact.samples.NOTICE_SHA256)
            self.profiles = dict(profiles)
            self.notice_raw, self.integrity_key = notice_raw, integrity_key
            self.issuer_id, self.key_id = issuer_id, key_id
            self._fixed = self._pointers()
            self._binding()
        except Exception:
            raise InputEvidenceHold('crop input validation evidence unavailable') from None

    def _pointers(self):
        return (self.integrity_key,self.issuer_id,self.key_id,self.notice_raw,
                tuple(self.profiles[name] for name in sorted(self.profiles)),
                inputs._canonical(inputs._profiles(**self.profiles)))

    def _binding(self):
        _pins()
        _need(self._pointers() == self._fixed)

    def _signature(self, payload):
        return hmac.new(self.integrity_key, DOMAIN+inputs._canonical(payload), 'sha256').hexdigest()

    def issue(self, directory, root_sha256):
        try:
            self._binding()
            owned_root, owned_bytes, owned_count = _current_bytes(directory, root_sha256)
            with inputs.open_input_packet(directory, root_sha256, **self.profiles) as reader:
                context = _context_record(engine.prepare_context(reader, **self.profiles))
            root, total, count = _current_bytes(directory, root_sha256)
            _need(root == owned_root and total == owned_bytes == context['plan']['packet_referenced_bytes']
                  and count == owned_count)
            payload = {'version':VERSION,'scope':SCOPE,'issuer_id':self.issuer_id,'key_id':self.key_id,
                       'validated_at':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                       'evidence_code_sha256':CODE_SHA256,'dependency_sha256':DEPENDENCY_SHA256,
                       'python_version':platform.python_version(),'notice_sha256':sha256(self.notice_raw).hexdigest(),
                       'profile_sha256':inputs._profiles(**self.profiles),'input_root_sha256':root_sha256,
                       'unique_blob_count':count,'context':context}
            self._context(context, root)
            self._binding()
            raw = inputs._canonical({'payload':payload,'hmac_sha256':self._signature(payload)})
            _need(len(raw) <= MAX_EVIDENCE_BYTES)
            return raw
        except Exception:
            raise InputEvidenceHold('crop input validation evidence unavailable') from None

    def _context(self, context, root):
        _need(type(context) is dict and set(context) == _CONTEXT_KEYS)
        manifest, plan = context['manifest'], context['plan']
        initial = root['initial_state']['values']
        seed = ([initial[name]['value'] for name in _PHYSICAL.PLANT]
                + [quantity['value'] for name in _PHYSICAL.ARRAY_UNITS for quantity in initial[name]]
                + [0.0]*len(_PHYSICAL.FLUX))
        clock = context['initial_clock']
        _need(type(plan) is dict and set(plan) == {'planned_steps','boundaries','counts','packet_referenced_bytes'}
              and inputs._canonical(context['seed']) == inputs._canonical(seed)
              and type(context['index']) is list and 1 <= len(context['index']) <= engine.MAX_INDEX_PAGES
              and all(type(page) is dict and set(page) == {'cursor','previous','steps'} for page in context['index'])
              and type(clock) is dict and set(clock) == {'segment_start','prefix','slope'}
              and clock['segment_start'] == root['period']['start']
              and clock['prefix'] == inputs._fraction(Fraction.from_float(initial['temperature_sum']['value'])))
        _need(inputs._hash(manifest) == context['context_sha256']
              and inputs._hash(context['index']) == manifest['grid_index_sha256']
              and manifest['input_root_sha256'] == inputs._hash(root)
              and manifest['profile_sha256'] == inputs._profiles(**self.profiles)
              and manifest['engine_version'] == engine.VERSION and manifest['scope'] == 'software_research_only'
              and manifest['physical_program_version'] == _PHYSICAL.PROGRAM_VERSION
              and manifest['rate_model_version'] == _PHYSICAL.coupled.MODEL_VERSION
              and manifest['grid_page_records'] == inputs.BLOCK_RECORDS
              and manifest['time_rule'] == 'UTC_POSIX_whole_seconds_v1'
              and manifest['temperature_sum_method'] == 'analytic_piecewise_constant_fraction_v1'
              and manifest['code_sha256'] == {'input_stream':inputs.CODE_SHA256,
                  'stream_execution':engine.CODE_SHA256,'continuation':engine.short.CODE_SHA256}
              and manifest['physical_code_sha256'] == _PHYSICAL.CODE_HASHES
              and manifest['policy_sha256'] == _PHYSICAL.startup.POLICY_SHA256
              and manifest['allocation_policy_sha256'] == _PHYSICAL.allocation.POLICY_SHA256
              and manifest['python_version'] == platform.python_version()
              and manifest['solver'] == root['solver']
              and context['initial'] == root['initial_state']
              and context['start_at'] == root['period']['start']
              and context['segment_count'] == root['streams']['segments']['count']
              and context['planned_steps'] == manifest['planned_steps'] == plan['planned_steps']
              and context['boundary_count'] == manifest['boundary_count'] == plan['boundaries']
              and plan['counts'] == {name:stream['count'] for name,stream in root['streams'].items()})

    def verify(self, directory, root_sha256, evidence_raw):
        try:
            self._binding()
            _need(type(evidence_raw) is bytes and 0 < len(evidence_raw) <= MAX_EVIDENCE_BYTES)
            envelope = inputs._json(evidence_raw)
            _need(type(envelope) is dict and set(envelope) == {'payload','hmac_sha256'}
                  and inputs._canonical(envelope) == evidence_raw and inputs._digest(envelope['hmac_sha256']))
            payload = envelope['payload']
            _need(type(payload) is dict and set(payload) == {'version','scope','issuer_id','key_id','validated_at',
                'evidence_code_sha256','dependency_sha256','python_version','notice_sha256','profile_sha256',
                'input_root_sha256','unique_blob_count','context'})
            _need(hmac.compare_digest(envelope['hmac_sha256'], self._signature(payload)))
            _PHYSICAL._utc(payload['validated_at'])
            _need(payload['version'] == VERSION and payload['scope'] == SCOPE
                  and payload['issuer_id'] == self.issuer_id and payload['key_id'] == self.key_id
                  and payload['evidence_code_sha256'] == CODE_SHA256
                  and payload['dependency_sha256'] == DEPENDENCY_SHA256
                  and payload['python_version'] == platform.python_version()
                  and payload['notice_sha256'] == sha256(self.notice_raw).hexdigest()
                  and payload['profile_sha256'] == inputs._profiles(**self.profiles)
                  and payload['input_root_sha256'] == root_sha256)
            root, total, count = _current_bytes(directory, root_sha256)
            context = payload['context']
            self._context(context, root)
            _need(type(payload['unique_blob_count']) is int and payload['unique_blob_count'] == count
                  and total == context['plan']['packet_referenced_bytes'])
            self._binding()
            return VerifiedInputEvidence(inputs._canonical(context), sha256(evidence_raw).hexdigest(),
                                         total, count, _TOKEN)
        except Exception:
            raise InputEvidenceHold('crop input validation evidence unavailable') from None
