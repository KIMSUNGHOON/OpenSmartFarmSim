"""Read preserved synthetic results with an explicitly selected source closure."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import ssl
import sys
from urllib.parse import urlencode
import urllib.request


SELECTED = {
    'backend/app/operator_config.py':
        'd38a57ee2b3d1902682065d2c6b87184fc6793759301a1117ce55a796def5dac',
    'backend/app/runtime_roles.py':
        'a58200a3fb2b4084813e305b9ed6748cc4ac4e89bfd681563aa65bc1c27ad5c3',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-manifest', required=True, type=Path)
    parser.add_argument('--original-directory', required=True, type=Path)
    parser.add_argument('--active-run', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    manifest_raw = args.source_manifest.read_bytes()
    manifest = json.loads(manifest_raw)
    root = Path(manifest['source_root'])
    assert root.is_absolute() and root.is_dir()
    assert manifest['schema_version'] == 'owned-source-dependency-selection-v2'
    assert manifest['new_model_activation'] is False
    assert manifest['all_other_tracked_files_from_base'] is True
    assert {v['path']: v['sha256'] for v in manifest['selected_dependencies']} == SELECTED
    assert all(v['git_commit'] == 'f6be606' for v in manifest['selected_dependencies'])

    def snapshot_ok():
        for name, digest in manifest['files'].items():
            rel = Path(name)
            assert not rel.is_absolute() and '..' not in rel.parts
            path = root/rel
            assert not path.is_symlink() and sha256(path.read_bytes()).hexdigest() == digest
        assert args.source_manifest.read_bytes() == manifest_raw

    snapshot_ok()
    original = args.original_directory
    main_root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root/'backend'), str(main_root/'backend/tests'), str(original)]
    import joint_prefix_live_operator_v1 as operator
    from app import operator_config, runtime_roles
    from app.crop_climate_joint_execution_query import JointExecutionQuery
    from app.crop_climate_joint_current_query import JointCropClimateCurrentQuery
    from app import crop_climate_joint_input_evidence as evidence
    from psycopg import sql
    from pytest import MonkeyPatch
    import test_crop_climate_joint_execution_query as tests

    for name, module in [('backend/app/operator_config.py', operator_config),
                         ('backend/app/runtime_roles.py', runtime_roles)]:
        assert Path(module.__file__) == root/name
        assert sha256(Path(module.__file__).read_bytes()).hexdigest() == SELECTED[name]
    assert evidence.DEPENDENCY_SHA256['file_metadata'] == SELECTED['backend/app/operator_config.py']
    worker = operator.worker().worker
    with worker.jobs.connect() as conn:
        assert conn.pgconn.used_password
        assert conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
        rows = conn.execute(sql.SQL('SELECT job_id,input_bytes FROM {} WHERE state=%s '
            'ORDER BY created_at DESC').format(worker.jobs._table('jobs')), ('succeeded',)).fetchall()
    selected = next(row for row in rows if json.loads(row['input_bytes']).get('input_version')
                    == 'joint-crop-climate-execution-input-v1')
    job_id = str(selected['job_id'])
    body = json.loads(selected['input_bytes'])['request']
    access = json.loads((original/args.active_run/'access.private.json').read_bytes())
    ready = json.loads((original/args.active_run/'ready.private.json').read_bytes())
    trust = ssl.create_default_context(cafile=str(original/args.active_run/'cert.pem'))

    def get(path):
        request = urllib.request.Request(ready['backend']+path,
            headers={'Authorization': 'Bearer '+access['token']})
        with urllib.request.urlopen(request, context=trust, timeout=30) as response:
            assert response.status == 200 and response.headers['Cache-Control'] == 'no-store'
            return json.loads(response.read())

    checked_inputs = 0
    with MonkeyPatch.context() as patch:
        calls = tests.forbid(patch)
        for source, item in operator.load()['inputs'].items():
            proof = Path(item['proof']).read_bytes()
            record = json.loads(proof)['payload']['record']
            checked = worker.server.binding.input_authority.verify(Path(item['directory']), source, proof,
                expected_context_sha256=record['context_sha256'],
                expected_binding_sha256=record['binding_sha256'])
            assert not checked.rights_or_gate_approval
            checked_inputs += 1
        expected = json.loads(JointExecutionQuery(worker.checkpoints, worker.results).read('tenant-1', job_id))
        current = get('/v1/jobs/'+job_id+'/crop-climate-joint-execution')
        assert expected['job']['state'] == 'succeeded'
        assert expected['result']['status'] == 'completed'
        for value in (expected, current):
            stamp = datetime.fromisoformat(value.pop('observed_at').replace('Z', '+00:00'))
            assert stamp.tzinfo == timezone.utc
        assert current == expected
        result_id = expected['result']['result_id']
        samples = json.loads(JointCropClimateCurrentQuery(worker.results).read('tenant-1', result_id,
            body['farm'], view='samples', offset=0, limit=64))
        assert get('/v1/crop-climate-joint-research-results/'+result_id+'?'+urlencode({
            **body['farm'], 'view': 'samples', 'offset': 0, 'limit': 64})) == samples
        assert not any(calls.values())
    snapshot_ok()
    record = {'version': 'joint-input-source-closure-probe-v1', 'actual_HTTPS_SCRAM': True,
        'source_selection_manifest_sha256': sha256(manifest_raw).hexdigest(),
        'base_commit': manifest['base_commit'], 'selected_dependencies': SELECTED,
        'actual_selected_module_paths_verified': True, 'all_snapshot_files_preserved': True,
        'original_inputs_verified': checked_inputs, 'original_samples': len(samples['page']['records']),
        'old_joint_summary_and_original_samples_equal_current_storage': True,
        'only_observation_timestamp_differs': True, 'read_calculation_and_write_calls': calls,
        'same_bearer_preserved': True, 'new_model_user_deployed': False,
        'real_farm_runs': 0, 'G0_G4': 'not_assessed'}
    with args.output.open('x') as stream:
        os.fchmod(stream.fileno(), 0o400)
        json.dump(record, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(record, sort_keys=True))


if __name__ == '__main__':
    main()
