"""Operator-installed owned inputs; the original author declaration is not G0."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from .thermal import MANIFEST_SHA256, _read_inputs


def collection_record_bytes(value):
    """Serialize the bounded owned record; job inputs still forbid raw content."""
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode('utf-8')
    if type(value) is not dict or not 1 <= len(encoded) <= 131072:
        raise ValueError('owned collection record rejected')
    return encoded


class OwnedFixtureRegistry:
    provider_id = 'project-fixture:manifest-v2'

    def __init__(self, root):
        self._root = Path(root).resolve()
        self._read()

    def _read(self):
        with (self._root/'fixtures/manifest-v2.json').open('rb') as stream:
            manifest_raw = stream.read(65537)
        if sha256(manifest_raw).hexdigest() != MANIFEST_SHA256:
            raise ValueError('owned fixture registry rejected')
        manifest = json.loads(manifest_raw)
        if len(manifest['files']) != 3:
            raise ValueError('owned fixture registry rejected')
        sources = []
        for row in manifest['files']:
            path = 'fixtures/'+row['fixture_id']+'.json'
            if (row['path'] != path or row['source_locator'] != path or row['synthetic'] is not True or
                    row['rights']['license'] != 'Apache-2.0' or
                    row['rights']['holder'] != manifest['author'] or
                    any(row['rights'].get(key) != 'allowed' for key in
                        ('access', 'store', 'transform', 'display', 'redistribute'))):
                raise ValueError('owned fixture source rejected')
            with (self._root/path).open('rb') as stream:
                raw = stream.read(row['byte_length']+1)
            digest = sha256(raw).hexdigest()
            if (digest != row['sha256'] or len(raw) != row['byte_length'] or
                    row['content_id'] != 'sha256:'+digest):
                raise ValueError('owned fixture source rejected')
            sources.append({'metadata': row, 'raw_utf8': raw.decode('utf-8')})
        return manifest_raw, sources

    def read_bundle(self, decision_at_utc, claim_mode):
        try:
            manifest, sources = self._read()
            by_id = {row['metadata']['fixture_id']: row['raw_utf8'].encode() for row in sources}
            _, weather, _, _ = _read_inputs(manifest, by_id['synthetic-weather-v1'],
                by_id['synthetic-thermal-parameters-v1'], datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                decision_at_utc=decision_at_utc, claim_mode=claim_mode)
            bundle = {'registry_version': 'owned-fixture-registry-v1', 'registry_sha256': MANIFEST_SHA256,
                'provider_id': self.provider_id, 'start_utc': weather['start_utc'],
                'end_utc': weather['end_utc'], 'sources': sources,
                'qc': {'version': 'owned-fixture-contract-qc-v1', 'status': 'software_checks_only',
                    'checks': ['original_manifest_and_bytes', 'declared_owned_rights',
                               'existing_units_clock_and_thermal_input_checks']}}
            collection_record_bytes(bundle)
            return bundle
        except Exception:
            raise ValueError('owned fixture bundle unavailable') from None
