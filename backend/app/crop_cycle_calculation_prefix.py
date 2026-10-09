"""Authenticated current artifact bytes and independently validated new deltas."""
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path

from . import crop_cycle_calculation_artifact as artifact

engine, inputs = artifact.engine, artifact.inputs
VERSION = 'crop-cycle-verified-prefix-validation-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_DECLARATIONS = (VERSION, CODE_SHA256)
_TOKEN = object()
_canonical = artifact._canonical


def _need(condition):
    artifact._need(condition, 'PREFIX_HOLD: authenticated calculation prefix required')


def _pins():
    _need((VERSION, CODE_SHA256) == _DECLARATIONS
          and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256)


def check_claim(value):
    _need(type(value) is dict and set(value) == {'version', 'validation_code_sha256',
        'checkpoint_sha256', 'confirmed_checkpoint_sha256', 'counts', 'summary_sha256'}
        and value['version'] == VERSION and value['validation_code_sha256'] == CODE_SHA256)
    _need(type(value['counts']) is dict and set(value['counts']) == {'samples', 'events'}
        and all(type(n) is int and 0 <= n for n in value['counts'].values())
        and all(value[k] is None or inputs._digest(value[k]) for k in
            ('checkpoint_sha256', 'confirmed_checkpoint_sha256', 'summary_sha256')))
    if value['checkpoint_sha256'] is not None:
        _need(value['checkpoint_sha256'] == value['confirmed_checkpoint_sha256'])


def _claim(checkpoint, confirmed, counts, summary):
    value = {'version':VERSION, 'validation_code_sha256':CODE_SHA256,
        'checkpoint_sha256':None if checkpoint is None else checkpoint['checkpoint_sha256'],
        'confirmed_checkpoint_sha256':None if confirmed is None else confirmed['checkpoint_sha256'],
        'counts':dict(counts), 'summary_sha256':None if summary is None else artifact._hash(summary)}
    check_claim(value)
    return value


def _current_blob(fd, digest, limit, read):
    _need(inputs._digest(digest))
    raw = read(fd, digest+'.json', limit)
    _need(sha256(raw).hexdigest() == digest)
    return raw


class _CurrentFiles:
    _records = artifact._Files._records

    def __init__(self, fd, read):
        self.fd, self.read = fd, read
        self.seen = set(); self.size = 8192

    def _blob(self, digest, limit, *, decode=True):
        raw = _current_blob(self.fd, digest, limit, self.read)
        if digest not in self.seen:
            self.seen.add(digest); self.size += len(raw)
            _need(self.size <= artifact.LIMITS['directory_bytes']
                and len(self.seen) <= artifact.LIMITS['files'])
        if not decode:
            return None, len(raw)
        value = artifact._json(raw)
        _need(_canonical(value) == raw)
        return value, len(raw)


@dataclass(frozen=True, slots=True)
class _Prefix:
    context_sha256: str
    head_raw: bytes
    hashes: tuple
    checkpoint_raw: bytes
    summary_raw: bytes
    claim_raw: bytes
    _token: object = field(repr=False, compare=False)


def unpack(value, context, head):
    _need(type(value) is _Prefix and value._token is _TOKEN
        and value.context_sha256 == context.root_sha256 and value.head_raw == _canonical(head))
    return (list(value.hashes), inputs._json(value.checkpoint_raw),
        inputs._json(value.summary_raw), inputs._json(value.claim_raw))


def _header(files, context, notice, head):
    _pins(); artifact._pins(context, notice)
    value, _ = files._blob(head['header_sha256'], artifact.LIMITS['metadata_bytes'])
    _need(_canonical(value) == _canonical(artifact._header(context, notice)))
    return value


def initial_claim(fd, context, notice, head, *, read):
    header = _header(_CurrentFiles(fd, read), context, notice, head)
    _need(head['commit_count'] == 0 and head['latest_commit_sha256'] is None
        and head['artifact_sha256'] is None)
    cp = header['initial_checkpoint']; engine._checkpoint_bytes(context, cp)
    return _claim(cp, cp, {'samples':0, 'events':0}, None)


def _chunk(files, digest, header_sha, sequence):
    chunk, _ = files._blob(digest, artifact.LIMITS['metadata_bytes'])
    _need(type(chunk) is dict and set(chunk) == {'version', 'header_sha256', 'sequence',
        'parent_commit_sha256', 'input_checkpoint_sha256', 'budget', 'result', 'pages'}
        and chunk['version'] == artifact.VERSION and chunk['header_sha256'] == header_sha
        and type(chunk['sequence']) is int and chunk['sequence'] == sequence
        and type(chunk['pages']) is dict and set(chunk['pages']) == {'samples', 'events'})
    artifact._budget(chunk['budget'])
    return chunk


def _page_counts(files, pages):
    counts = {}; total = number = 0
    for kind in ('samples', 'events'):
        descriptors = pages[kind]
        _need(type(descriptors) is list and len(descriptors) <= artifact.LIMITS['pages_per_commit'])
        counts[kind] = 0
        for descriptor in descriptors:
            _need(type(descriptor) is dict and set(descriptor) == {'sha256', 'count', 'first_at', 'last_at'}
                and type(descriptor['count']) is int and 1 <= descriptor['count'] <= artifact.LIMITS['page_records'])
            _, size = files._blob(descriptor['sha256'], artifact.LIMITS['page_bytes'], decode=False)
            total += size; number += 1; counts[kind] += descriptor['count']
        _need(counts[kind] <= 128)
    _need(total <= artifact.LIMITS['delta_bytes'] and number <= artifact.LIMITS['pages_per_commit'])
    return counts


def _root(files, head, hashes, summary):
    if head['artifact_sha256'] is not None:
        value, _ = files._blob(head['artifact_sha256'], artifact.LIMITS['root_bytes'])
        _need(summary is not None and summary['status'] in ('completed', 'hold')
            and _canonical(value) == _canonical({'version':artifact.VERSION,
                'header_sha256':head['header_sha256'], 'commits':hashes, 'status':summary['status']}))


def read_authenticated(fd, context, notice, head, *, proof, read):
    """The caller authenticates the entire selected proof chain before this read."""
    files = _CurrentFiles(fd, read); header = _header(files, context, notice, head)
    current = {**head, 'latest_commit_sha256':None, 'commit_count':0, 'artifact_sha256':None}
    previous, previous_sha = proof(current)
    cp = header['initial_checkpoint']; counts = {'samples':0, 'events':0}; summary = None
    _need(previous['validation'] == _claim(cp, cp, counts, None))
    hashes = []; digest = head['latest_commit_sha256']
    for sequence in range(head['commit_count'], 0, -1):
        chunk = _chunk(files, digest, head['header_sha256'], sequence)
        hashes.append(digest); digest = chunk['parent_commit_sha256']
    _need(digest is None); hashes.reverse()
    for sequence, digest in enumerate(hashes, 1):
        chunk = _chunk(files, digest, head['header_sha256'], sequence)
        _need(cp is not None and (summary is None or summary['status'] == 'yielded')
            and chunk['input_checkpoint_sha256'] == cp['checkpoint_sha256']
            and chunk['parent_commit_sha256'] == current['latest_commit_sha256'])
        next_head = {**current, 'latest_commit_sha256':digest, 'commit_count':sequence}
        signed, signature_sha = proof(next_head); claim = signed['validation']; check_claim(claim)
        _need(signed['action'] == 'advance' and signed['parent'] == {
            'head_sha256':artifact._hash(current), 'proof_sha256':previous_sha})
        delta = _page_counts(files, chunk['pages']); meta = chunk['result']
        _need(type(meta) is dict and claim['summary_sha256'] == artifact._hash(meta))
        held = meta.get('status') == 'hold'
        keys = {'status', 'scope', 'steps', 'planned_steps', 'output_start', 'event_start', 'checkpoint'}
        _need(set(meta) == keys | ({'hold', 'last_confirmed'} if held else set())
            and meta['status'] in ('yielded', 'completed', 'hold') and meta['scope'] == 'software_research_only'
            and all(type(meta[k]) is int for k in ('steps', 'planned_steps', 'output_start', 'event_start'))
            and meta['output_start'] == counts['samples'] and meta['event_start'] == counts['events']
            and cp['steps'] <= meta['steps'] <= cp['steps']+chunk['budget']['max_steps']
            and meta['planned_steps'] == context.planned_steps)
        counts = {kind:counts[kind]+delta[kind] for kind in counts}; cp = meta['checkpoint']
        _need(claim['counts'] == counts and (cp is None if held else type(cp) is dict)
            and claim['checkpoint_sha256'] == (None if cp is None else cp['checkpoint_sha256']))
        if cp is not None:
            _need(cp['parent_sha256'] == chunk['input_checkpoint_sha256'] and cp['steps'] == meta['steps']
                and cp['output_cursor'] == counts['samples'] and cp['event_cursor'] == counts['events'])
        summary, previous, previous_sha, current = meta, signed, signature_sha, next_head
    if head['artifact_sha256'] is not None:
        signed, _ = proof(head)
        _need(signed['action'] == 'finalize' and signed['validation'] == previous['validation']
            and signed['parent'] == {'head_sha256':artifact._hash(current), 'proof_sha256':previous_sha})
    else:
        _need(current == head)
    if cp is not None:
        engine._checkpoint_bytes(context, cp)
    _root(files, head, hashes, summary)
    return _Prefix(context.root_sha256, _canonical(head), tuple(hashes), _canonical(cp),
        _canonical(summary), _canonical(previous['validation']), _TOKEN)


def validate_advance(fd, context, notice, old, head, previous, *, read):
    hashes, cp, summary, claim = unpack(previous, context, old)
    _need(old['artifact_sha256'] is None and head['artifact_sha256'] is None and cp is not None
        and (summary is None or summary['status'] == 'yielded')
        and head['header_sha256'] == old['header_sha256'] and head['commit_count'] == len(hashes)+1)
    files = _CurrentFiles(fd, read); _header(files, context, notice, head)
    chunk = _chunk(files, head['latest_commit_sha256'], head['header_sha256'], head['commit_count'])
    _need(chunk['parent_commit_sha256'] == old['latest_commit_sha256']
        and chunk['input_checkpoint_sha256'] == cp['checkpoint_sha256'])
    records = {}; size = pages = 0
    for kind in ('samples', 'events'):
        records[kind], n = files._records(chunk['pages'][kind]); size += n; pages += len(chunk['pages'][kind])
    _need(size <= artifact.LIMITS['delta_bytes'] and pages <= artifact.LIMITS['pages_per_commit'])
    confirmed = artifact._wrap_validation(artifact._validate_delta, context, cp,
        chunk['result'], records, chunk['budget'])
    counts = {kind:claim['counts'][kind]+len(records[kind]) for kind in records}
    return _claim(chunk['result']['checkpoint'], confirmed, counts, chunk['result'])


def validate_finalize(fd, context, notice, old, head, previous, *, read):
    hashes, cp, summary, claim = unpack(previous, context, old)
    _need(old['artifact_sha256'] is None and inputs._digest(head['artifact_sha256'])
        and {**old, 'artifact_sha256':head['artifact_sha256']} == head)
    files = _CurrentFiles(fd, read); _header(files, context, notice, head)
    _root(files, head, hashes, summary)
    return claim
