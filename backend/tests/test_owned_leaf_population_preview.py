"""Opt-in owned-preview boundaries; these controls do not prove native runtime."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

from fastapi import FastAPI
import pytest

from test_api_crop_leaf_population_execution import BODY


path = Path(__file__).resolve().parents[2]/'research/owned_leaf_population_preview.py'
spec = importlib.util.spec_from_file_location('owned_leaf_preview', path)
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


def configuration():
    return {'schema_version': preview.VERSION, 'request': deepcopy(BODY), 'label': 'Owned synthetic leaf study',
        'input_key_file': '/owned/key', 'review_file': '/owned/review', 'rights_file': '/owned/rights',
        'issuer_id': 'owned-software', 'key_id': 'owned-leaf-key-v1',
        'packet_files': {name: '/owned/'+name for name in preview.PACKET_NAMES},
        'signed': {'directory': '/owned/signed', 'key_file': '/owned/signed-key',
            'issuer_id': 'owned-software', 'key_id': 'owned-leaf-result-key-v1'}}


def test_missing_opt_in_preserves_old_app_and_reads_no_private_file():
    app = FastAPI(); before = tuple(app.routes)
    def forbidden(*_): pytest.fail('disabled configuration accessed private data')
    assert preview.attach_leaf_population(app, config=None, parent_query=None, tenant_id='tenant-1',
        read_private=forbidden, authorized=forbidden, access=forbidden, error=forbidden) is None
    assert tuple(app.routes) == before


@pytest.mark.parametrize('fault', ['partial', 'unknown', 'version', 'packet', 'signed', 'path', 'relative', 'label', 'request'])
def test_invalid_opt_in_is_rejected_before_private_reads(fault):
    value = configuration()
    if fault == 'partial': value.pop('input_key_file')
    elif fault == 'unknown': value['arbitrary_callback'] = 'not-accepted'
    elif fault == 'version': value['schema_version'] = 'future'
    elif fault == 'packet': value['packet_files']['unexpected'] = '/owned/extra'
    elif fault == 'signed': value['signed'].pop('key_file')
    elif fault == 'path': value['packet_files']['program_raw'] = '/owned/../escape'
    elif fault == 'relative': value['signed']['directory'] = 'relative'
    elif fault == 'label': value['label'] = 'x'*161
    else: value['request']['parent'] = {}
    reads = []
    with pytest.raises(ValueError, match='owned leaf preview configuration rejected'):
        preview.attach_leaf_population(FastAPI(), config=value, parent_query=None, tenant_id='tenant-1',
            read_private=lambda *a: reads.append(a), authorized=None, access=None, error=None)
    assert reads == []


def test_file_resolver_is_tenant_and_exact_reference_bound_and_rereads_bytes():
    value = configuration(); calls = []; generation = [b'first']
    def read(path, maximum): calls.append((path, maximum)); return generation[0]
    resolver = preview.OwnedLeafResolver(value, tenant_id='tenant-1', read_private=read)
    assert resolver('tenant-1', value['request']['input']) == {k:b'first' for k in preview.PACKET_NAMES}
    generation[0] = b'changed'
    assert resolver('tenant-1', value['request']['input']) == {k:b'changed' for k in preview.PACKET_NAMES}
    assert len(calls) == 6
    with pytest.raises(PermissionError): resolver('other', value['request']['input'])
    changed = deepcopy(value['request']['input']); changed['program_sha256'] = '0'*64
    with pytest.raises(PermissionError): resolver('tenant-1', changed)
    assert len(calls) == 6


def test_file_rights_require_exact_current_owned_declaration_and_allowed_use():
    value = configuration(); declaration = value['request']['rights']; source = value['request']['input']['source_sha256']
    state = {'schema_version': preview.RIGHTS_VERSION, 'status': 'allowed_for_software_validation',
        'tenant_id': 'tenant-1', 'declaration': declaration, 'source_sha256': source}
    rights = preview.OwnedLeafRights(value, tenant_id='tenant-1', read_private=lambda *_:json.dumps(state).encode())
    assert rights('tenant-1', declaration, source, 'research_calculation') is True
    assert rights('tenant-1', declaration, source, 'research_display') is True
    assert rights('tenant-1', declaration, source, 'redistribute') is False
    assert rights('other', declaration, source, 'research_display') is False
    assert rights('tenant-1', declaration, '0'*64, 'research_display') is False
    state['status'] = 'revoked'
    assert rights('tenant-1', declaration, source, 'research_display') is False
