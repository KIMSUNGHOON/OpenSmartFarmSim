"""Compare bounded HTTP observations with an already checked private harvest manifest."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite
from urllib.parse import urlencode

VERSION = 'owned-harvest-http-reconciliation-v1'
MAX_BYTES = 2 * 1024**2
MAX_SECONDS = 30


def need(value):
    if not value:
        raise ValueError('harvest_http_reconciliation_failed')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def pairs(items):
    value = {}
    for key, item in items:
        need(key not in value)
        value[key] = item
    return value


def document(raw):
    def invalid(_):
        raise ValueError('harvest_http_reconciliation_failed')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid)


def target(manifest, farm, label):
    need(label in ('summary', 'first', 'last'))
    query = dict(farm)
    if label != 'summary':
        page = manifest['pages'][label]
        query.update(view='records', offset=page['start'], limit=page['count'])
    return '/v1/crop-harvest-research-results/' + manifest['original_record']['result_id'] + '?' + urlencode(query)


def reconcile(manifest, farm, codes, label, raw, *, status, headers, seconds, emission):
    """No signature approval: callers must supply checked custody and actual wire observations."""
    try:
        need(label in ('summary', 'first', 'last') and type(raw) is bytes and 0 < len(raw) <= MAX_BYTES)
        need(type(seconds) in (int, float) and isfinite(seconds) and 0 <= seconds <= MAX_SECONDS)
        digest = sha256(raw).hexdigest()
        need(type(status) is int and status == 200 and emission['status'] == status
             and emission['complete'] is True and type(emission['bytes']) is int
             and emission['bytes'] == len(raw) and emission['sha256'] == digest)
        need(headers['cache-control'] == 'no-store' and headers['x-content-type-options'] == 'nosniff')
        for header, key in (('x-ossf-harvest-query-version', 'query_version'),
                            ('x-ossf-harvest-query-code-sha256', 'query_code_sha256'),
                            ('x-ossf-harvest-projection-code-sha256', 'projection_code_sha256')):
            need(headers[header] == codes[key])
        value = document(raw)
        need(set(value) == {'schema_version', 'result_id', 'recorded_at', 'farm', 'reference', 'summary', 'page'})
        saved = manifest['original_record']; packet_raw = saved['payload_raw_utf8'].encode()
        need(sha256(packet_raw).hexdigest() == saved['payload_sha256'])
        packet = document(packet_raw)
        stamp = datetime.fromisoformat(saved['recorded_at']); need(stamp.utcoffset() is not None)
        need(value['schema_version'] == 'crop-harvest-replay-v1' and value['result_id'] == saved['result_id'] == packet['result_id']
             and value['recorded_at'] == stamp.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
             and value['farm'] == farm == packet['farm'] and manifest['source'] == packet['source'])
        expected = {'storage_status': packet['status'], 'claim_scope': packet['claim_scope'],
            'scope': 'software_research_only', 'gates': 'not_assessed',
            'temporal_provenance': 'synthetic_research_program', 'rights_or_gate_approval': False,
            'parent_result_id': packet['parent_result_id'], 'source': packet['source'],
            'payload_sha256': saved['payload_sha256'], 'artifact_sha256': packet['artifact']['sha256'],
            'row_count': packet['artifact']['row_count'], 'row_chain_sha256': packet['artifact']['row_chain_sha256'],
            'mass_parameter_sha256': packet['parameters']['mass_sha256'],
            'allocation_parameter_sha256': packet['parameters']['allocation_sha256'], **packet['code'], **codes}
        need(canonical(value['reference']) == canonical(expected))
        if label == 'summary':
            need(value['page'] is None and sha256(canonical(value['summary'])).hexdigest() == manifest['summary_sha256'])
        else:
            page = value['page']; saved_page = manifest['pages'][label]; total = packet['artifact']['row_count']
            need(value['summary'] is None and set(page) == {'offset', 'limit', 'total', 'next_offset', 'records'})
            need(canonical({k: page[k] for k in ('offset', 'limit', 'total', 'next_offset')}) == canonical({
                'offset': saved_page['start'], 'limit': saved_page['count'], 'total': saved_page['total'],
                'next_offset': saved_page['next'] if saved_page['next'] < total else None}))
            need(type(page['records']) is list and len(page['records']) == saved_page['count']
                 and sha256(b''.join(canonical(row) + b'\n' for row in page['records'])).hexdigest() == saved_page['rows_sha256'])
        return {'version': VERSION, 'label': label, 'status': status, 'bytes': len(raw), 'sha256': digest,
                'seconds': seconds, 'stored_values_equal': True, 'scope': 'synthetic_research_only', 'G0_G4': 'not_assessed'}
    except Exception:
        raise ValueError('harvest_http_reconciliation_failed') from None
