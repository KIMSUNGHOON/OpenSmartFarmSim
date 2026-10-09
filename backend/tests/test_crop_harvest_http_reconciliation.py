"""Current owned writer values through protected ASGI; no live DB, TLS, or full-load proof."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from urllib.parse import parse_qs

import pytest

from app import api_crop_harvest_replay as public, crop_harvest_current_query as current
from test_api_crop_harvest_route import assembly, get
from test_crop_harvest_current_query import forbid_all_reads_math
from test_crop_harvest_replay import replay, owned_directory
from test_crop_harvest import OwnedPages, mass_profile, allocation_profile

PATH = Path(__file__).resolve().parents[2] / 'research/crop-harvest-http-reconciliation.py'
SPEC = importlib.util.spec_from_file_location('owned_harvest_http_reconciliation', PATH)
check = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(check)


@pytest.fixture
def source(tmp_path):
    read = OwnedPages(); read.original['record']['result_id'] = current.current.storage.VERSION + ':' + '1' * 64
    mass = check.canonical(mass_profile(replay.harvest._source(read())))
    allocation = check.canonical(allocation_profile(replay.harvest._mass_parameters(mass)))
    directory = owned_directory(tmp_path); result = replay._write(directory, read, mass, allocation)
    parent_source = replay.harvest._source(read()); farm = {'scenario_id': 'owned-farm', 'scenario_revision': '1',
        'registration_sha256': '2' * 64, 'crop_id': 'owned-crop'}
    registry = current.registry
    packet = registry._packet(registry._base('tenant-1', parent_source['result_id'], farm, parent_source,
        {'mass_sha256': sha256(mass).hexdigest(), 'allocation_sha256': sha256(allocation).hexdigest()}), result)
    record = {'result_id': json.loads(packet)['result_id'], 'payload_raw': packet,
        'payload_sha256': sha256(packet).hexdigest(), 'recorded_at': datetime(2026, 10, 9, tzinfo=timezone.utc)}
    with replay._Reader(directory, result['artifact_sha256'], read) as stored:
        summary = stored.summary(); page = stored.page()
    return {'record': record, 'summary': summary, 'page': page, 'identity': {
        'version': current.VERSION, 'code_sha256': current.CODE_SHA256, 'dependency_sha256': current.DEPENDENCY_SHA256,
        'result_id': record['result_id'], 'payload_sha256': record['payload_sha256'],
        'artifact_sha256': result['artifact_sha256'], 'parent_source': parent_source, 'rights_or_gate_approval': False}}


@pytest.fixture
def observed(source, monkeypatch):
    farm = json.loads(source['record']['payload_raw'])['farm']; rows = source['page']['records']
    manifest = {'original_record': {k: v for k, v in source['record'].items() if k not in ('payload_raw', 'recorded_at')},
        'source': source['identity']['parent_source'], 'summary_sha256': sha256(check.canonical(source['summary'])).hexdigest(), 'pages': {}}
    manifest['original_record'].update(payload_raw_utf8=source['record']['payload_raw'].decode(),
                                       recorded_at=source['record']['recorded_at'].isoformat())
    for name, start, count in (('first', 0, 6), ('last', 5, 1)):
        manifest['pages'][name] = {'start': start, 'next': start + count, 'total': 6, 'count': count,
            'rows_sha256': sha256(b''.join(check.canonical(r) + b'\n' for r in rows[start:start + count])).hexdigest()}
    codes = {'query_version': current.VERSION, 'query_code_sha256': current.CODE_SHA256,
             'query_dependency_sha256': current.DEPENDENCY_SHA256, 'projection_code_sha256': public.CODE_SHA256}
    case = assembly(source, monkeypatch); app = case.app; sent = []
    async def capture(scope, receive, send):
        async def forward(message):
            sent.append(deepcopy(message)); await send(message)
        await app(scope, receive, forward)
    case.app = capture; forbid_all_reads_math(monkeypatch)
    def read(label):
        sent.clear(); target = check.target(manifest, farm, label)
        start = perf_counter(); status, _, headers = get(case, farm={}, query=target.partition('?')[2]); seconds = perf_counter() - start
        raw = b''.join(v.get('body', b'') for v in sent if v['type'] == 'http.response.body')
        return {'raw': raw, 'status': status, 'headers': {k.decode(): v.decode() for k, v in headers.items()},
            'seconds': seconds, 'emission': {'status': status, 'bytes': len(raw), 'sha256': sha256(raw).hexdigest(),
                'complete': any(v['type'] == 'http.response.body' and not v.get('more_body', False) for v in sent)}}
    return manifest, farm, codes, read


@pytest.mark.parametrize('label', ['summary', 'first', 'last'])
def test_original_summary_first_and_last_are_checked_without_regeneration(observed, label):
    manifest, farm, codes, read = observed; before = deepcopy(manifest); fd = len(os.listdir('/proc/self/fd'))
    found = check.reconcile(manifest, farm, codes, label, **read(label))
    assert found['stored_values_equal'] and found['G0_G4'] == 'not_assessed'
    assert manifest == before and fd == len(os.listdir('/proc/self/fd'))


@pytest.mark.parametrize('fault', ['quantity', 'unit', 'UTC', 'row-order', 'offset', 'recorded-at', 'source',
    'private-field', 'gate', 'bool-gate', 'wrong-result', 'summary', 'duplicate-key', 'over-time', 'nan-time',
    'bool-time', 'oversize', 'wire-sha', 'wire-bytes', 'incomplete', 'status', 'no-store', 'code-header'])
def test_changed_stored_values_wire_or_bounds_cannot_pass(observed, fault):
    manifest, farm, codes, read = observed; label = 'summary' if fault == 'summary' else 'first'
    response = read(label); value = json.loads(response['raw']); row = value['page']['records'][0] if label != 'summary' else None
    if fault == 'quantity': row['mass']['fresh_matter']['value'] += 1
    elif fault == 'unit': row['mass']['fresh_matter']['unit'] = 'kg_FW/m2_crop'
    elif fault == 'UTC': row['mass']['removal']['end_at'] = '2026-10-01T00:01:00Z'
    elif fault == 'row-order': value['page']['records'].reverse()
    elif fault == 'offset': value['page']['offset'] = False
    elif fault == 'recorded-at': value['recorded_at'] = '2026-10-01T00:00:00Z'
    elif fault == 'source': value['reference']['source']['artifact_sha256'] = '0' * 64
    elif fault == 'private-field': value['reference']['private_path'] = '/owned/private'
    elif fault in ('gate', 'bool-gate'): value['reference']['rights_or_gate_approval'] = True if fault == 'gate' else 0
    elif fault == 'wrong-result': value['result_id'] = 'crop-harvest-registered-result-v1:' + '0' * 64
    elif fault == 'summary': value['summary']['row_count'] += 1
    response['raw'] = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
    if fault == 'duplicate-key': response['raw'] = b'{"page":null,' + response['raw'][1:]
    if fault == 'oversize': response['raw'] += b' ' * (check.MAX_BYTES + 1)
    response['emission'].update(sha256=sha256(response['raw']).hexdigest(), bytes=len(response['raw']))
    if fault == 'over-time': response['seconds'] = 30.001
    elif fault == 'nan-time': response['seconds'] = float('nan')
    elif fault == 'bool-time': response['seconds'] = False
    elif fault == 'wire-sha': response['emission']['sha256'] = '0' * 64
    elif fault == 'wire-bytes': response['emission']['bytes'] -= 1
    elif fault == 'incomplete': response['emission']['complete'] = False
    elif fault == 'status': response['status'] = response['emission']['status'] = 503
    elif fault == 'no-store': response['headers']['cache-control'] = 'public'
    elif fault == 'code-header': response['headers']['x-ossf-harvest-query-code-sha256'] = '0' * 64
    with pytest.raises(ValueError, match='^harvest_http_reconciliation_failed$'):
        check.reconcile(manifest, farm, codes, label, **response)


def test_full_count_targets_keep_first_64_last_1_without_loading_all_rows(observed):
    manifest, farm, _, _ = observed; manifest = deepcopy(manifest)
    manifest['pages']['first'].update(start=0, next=64, total=47813, count=64)
    manifest['pages']['last'].update(start=47812, next=47813, total=47813, count=1)
    for name, offset, limit in (('first', '0', '64'), ('last', '47812', '1')):
        target = check.target(manifest, farm, name)
        assert target.partition('?')[0].endswith(manifest['original_record']['result_id'])
        assert parse_qs(target.partition('?')[2]) == {**{k: [v] for k, v in farm.items()},
            'view': ['records'], 'offset': [offset], 'limit': [limit]}


def test_exact_existing_response_bounds_remain_inclusive(observed):
    manifest, farm, codes, read = observed; response = read('summary')
    response['raw'] += b' ' * (2 * 1024**2 - len(response['raw']))
    response['seconds'] = 30
    response['emission'].update(bytes=len(response['raw']), sha256=sha256(response['raw']).hexdigest())
    response['headers']['content-length'] = str(len(response['raw']))
    assert check.reconcile(manifest, farm, codes, 'summary', **response)['bytes'] == 2 * 1024**2


def test_fresh_import_loads_no_app_or_network_and_leaks_no_descriptor():
    script = '''import importlib.util,os,socket,sys
def denied(*a,**k):raise AssertionError('network during import')
socket.create_connection=denied
before=len(os.listdir('/proc/self/fd'))
spec=importlib.util.spec_from_file_location('owned_http_check',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert before==len(os.listdir('/proc/self/fd'))
assert not any(n=='app' or n.startswith('app.') for n in sys.modules)
'''
    child = subprocess.run([sys.executable, '-c', script, str(PATH)], capture_output=True, timeout=10)
    assert child.returncode == 0, child.stderr
