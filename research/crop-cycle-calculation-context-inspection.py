"""Inspect current calculation boundaries without executing crop equations."""
import argparse
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path


def function(tree, name, owner=None):
    body = tree.body
    if owner:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == owner).body
    return next(n for n in body if isinstance(n, ast.FunctionDef) and n.name == name)


def calls(node):
    return [ast.unparse(n.func) for n in ast.walk(node) if isinstance(n, ast.Call)]


def inspect(workspace, supervision, native_cli):
    native = json.loads(native_cli.read_text())
    assert native['model'] == 'gpt-6.1-sol' and native['effort'] == 'xhigh'
    paths = {name: workspace / ('backend/app/crop_cycle_' + name + '.py') for name in (
        'stream_execution', 'input_stream', 'input_evidence', 'input_read_context',
        'artifact', 'farm_binding', 'server_custody')}
    trees = {name: ast.parse(path.read_text()) for name, path in paths.items()}
    stream = trees['stream_execution']
    prepare = function(stream, 'prepare_context')
    require = function(stream, '_require_context')
    assert 'type(reader) is inputs.InputPacket' in ast.unparse(prepare)
    assert 'type(context) is StreamContext' in ast.unparse(require)
    assert 'context._token is _TOKEN' in ast.unparse(require)
    manifest = next(n.value for n in prepare.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'manifest' for t in n.targets))
    keys = [key.value for key in manifest.keys]
    assert len(keys) == len(set(keys)) == 19
    assert '_require_context' in calls(function(stream, 'start'))
    assert '_require_context' in calls(function(stream, '_validate_checkpoint'))
    for name in ('checkpoint_bytes', 'restore_checkpoint', 'advance_chunk'):
        assert '_validate_checkpoint' in calls(function(stream, name))
    helpers = ['_boundary', '_evaluator', '_clock_record', '_seal', '_confirmed']
    helper_lines = {name: function(stream, name).lineno for name in helpers}
    packet = trees['input_stream']
    assert 'self._preflight' in calls(function(packet, '__init__', 'InputPacket'))
    assert 'normalization_sha256' in ast.unparse(function(packet, '_validate_root', 'InputPacket'))
    evidence = trees['input_evidence']
    issue = calls(function(evidence, 'issue', 'InputEvidenceAuthority'))
    verify = calls(function(evidence, 'verify', 'InputEvidenceAuthority'))
    assert issue.count('_current_bytes') == 2
    assert 'inputs.open_input_packet' in issue and 'engine.prepare_context' in issue
    assert verify.count('_current_bytes') == 1
    assert 'inputs.open_input_packet' not in verify and 'engine.prepare_context' not in verify
    read_class = next(n for n in trees['input_read_context'].body
                      if isinstance(n, ast.ClassDef) and n.name == 'InputReadContext')
    read_public = [n.name for n in read_class.body if isinstance(n, ast.FunctionDef)
                   and not n.name.startswith('_')]
    assert not {'start', 'advance_chunk', 'restore_checkpoint'} & set(read_public)
    assert 'engine._require_context' in calls(function(trees['artifact'], '_pins'))
    bind = function(trees['farm_binding'], '_input', 'CycleFarmBinding')
    assert 'type(reader) is inputs.InputPacket' in ast.unparse(bind)
    assert 'reader._preflight' in calls(bind)
    assert calls(function(trees['farm_binding'], '_bind', 'CycleFarmBinding')).count('self._input') == 2
    custody = function(trees['server_custody'], '_open', 'CycleServerCustody')
    assert 'type(reader) is inputs.InputPacket' in ast.unparse(custody)
    assert 'engine.prepare_context' in calls(custody)
    pins = json.loads(supervision.read_text())['source_sha256']
    assert len(pins) == 55
    for name, digest in pins.items():
        assert sha256((workspace / name).read_bytes()).hexdigest() == digest, name
    return {
        'reference_version': 'crop-cycle-calculation-context-inspection-v1',
        'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'static current-source dependency inspection; no new calculation acceptance',
        'inspector_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'native_cli': native, 'recursive_cli_invocations': 0,
        'source_sha256': {str(p.relative_to(workspace)): sha256(p.read_bytes()).hexdigest()
                          for p in paths.values()},
        'original_manifest_keys': keys, 'proposed_added_manifest_key': 'input_validation',
        'fixed_original_helpers': helper_lines, 'guarded_public_context_operations': 4,
        'issue_full_QC_and_context': True, 'verify_current_bytes_without_full_reprepare': True,
        'read_type_has_no_calculation_API': True, 'artifact_requires_original_context': True,
        'farm_binding_full_preflight_calls': 2, 'custody_requires_original_reader_and_context': True,
        'live_source_pins_preserved': 55, 'new_runtime_tests_run': 0,
        'actual_crop_runs': 0, 'adopted_inputs': 0, 'independent_domestic_datasets': 0,
        'gate_status': 'not_assessed',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--supervision', type=Path, required=True)
    parser.add_argument('--native-cli', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.workspace.resolve(), args.supervision, args.native_cli)
    with args.output.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
    args.output.chmod(0o400)
    print(json.dumps({'source_files': len(result['source_sha256']), 'pins': 55,
                      'original_manifest_keys': len(result['original_manifest_keys']),
                      'artifact_dependency': 'explicit new writer/reader required',
                      'output_sha256': sha256(args.output.read_bytes()).hexdigest()}))
