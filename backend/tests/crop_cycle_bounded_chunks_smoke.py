"""Manual stored 4096-transition prefix; not a registered or terminal crop Run."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import pytest

from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_context as engine
from crop_cycle_full_prefix_cost_smoke import packet, original_rows, same_checkpoint_values
from crop_cycle_calculation_prefix_cost_smoke import driver, tree
from crop_cycle_full_calendar_registration_smoke import save
from test_crop_cycle_artifact import NOTICE
from test_crop_cycle_input_evidence import authority

CHILD = r'''
import json, os, sys
from pathlib import Path
from hashlib import sha256
from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_context as engine
from test_crop_cycle_artifact import NOTICE
from test_crop_cycle_input_evidence import authority
before = len(os.listdir('/proc/self/fd'))
proof = Path(os.environ['OSSF_FULL_CALENDAR_PROOF']).read_bytes()
root = json.loads(Path(os.environ['OSSF_FULL_CALENDAR_RECEIPT']).read_bytes())['target_root_sha256']
rhs = engine.short._Evaluator.rhs
def forbidden(*a, **k): raise AssertionError('read-only recovery ran RHS')
engine.short._Evaluator.rhs = forbidden
with engine.open_calculation_context(os.environ['OSSF_FULL_CALENDAR_INPUTS'], root, proof,
        authority=authority()) as context:
    with artifact.open_writer(sys.argv[1], sys.argv[2], context, notice_raw=NOTICE) as writer:
        recovered = writer._checkpoint
        assert recovered['sequence'] == 4096
        recovered_sha = sha256(engine._canonical(recovered)).hexdigest()
        calls = []
        def measured(*a, **k):
            calls.append(True); return rhs(*a, **k)
        engine.short._Evaluator.rhs = measured
        progress = writer.advance({'max_steps': 1, 'max_transitions': 1})
        resumed = writer._checkpoint
    assert context.reader.closed is False
assert context.reader.closed and not context.reader._cache and not context._cache
assert len(os.listdir('/proc/self/fd')) == before
print(json.dumps({'pid': os.getpid(), 'recovered_checkpoint_sha256': recovered_sha,
    'read_RHS_calls': 0, 'resume_RHS_calls': len(calls), 'checkpoint': resumed,
    'progress': progress, 'FD_before_after': [before, before], 'contexts_closed_caches_empty': True}))
'''


def test_actual_4096_stored_prefix_matches_32_chunks_and_fresh_python_resume(tmp_path, driver, monkeypatch):
    paths, receipt, proof = packet()
    before = {key: tree(paths[key]) for key in ('derived', 'original', 'artifact')}
    baseline_raw = Path(os.environ['OSSF_CHUNK_FEASIBILITY_BASELINE']).read_bytes()
    assert sha256(baseline_raw).hexdigest() == os.environ['OSSF_CHUNK_FEASIBILITY_BASELINE_SHA256']
    baseline = json.loads(baseline_raw)
    assert len(baseline['growth_curve']) == 32 and baseline['checkpoint']['sequence'] == 4096
    descriptors = len(os.listdir('/proc/self/fd'))
    started = perf_counter()
    directory = tmp_path/'stored-prefix'
    with engine.open_calculation_context(paths['derived'], receipt['target_root_sha256'], proof,
            authority=authority()) as context:
        with driver.observation() as costs:
            with artifact.create_writer(directory, context, notice_raw=NOTICE) as writer:
                progress = writer.advance({'max_steps': 10000, 'max_transitions': 4096})
                checkpoint = deepcopy(writer._checkpoint)
                head, _ = writer._head()
                commit, metadata_bytes = writer._blob(head['latest_commit_sha256'], artifact.LIMITS['metadata_bytes'])
                records = {kind: writer._records(commit['pages'][kind])[0] for kind in ('samples', 'events')}
        calculation_wall = perf_counter()-started
        assert progress['status'] == 'yielded' and progress['commit_count'] == 1
        assert progress['steps'] == checkpoint['steps'] == 3990 and checkpoint['sequence'] == 4096
        assert commit['budget'] == {'max_steps': 10000, 'max_transitions': 4096}
        assert head['artifact_sha256'] is None
        assert costs.values['rhs']['calls'] > 0
        lineage = {'parent_sha256', 'checkpoint_sha256'}
        assert {k:v for k,v in checkpoint.items() if k not in lineage} == {
            k:v for k,v in baseline['checkpoint'].items() if k not in lineage}
        counts = {kind:len(values) for kind,values in records.items()}
        assert counts == {'samples': 105, 'events': 2}
        with monkeypatch.context() as no_math:
            no_math.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('reference read RHS'))
            expected, reference = original_rows(paths, counts, advance_count=32)
        assert records == expected and same_checkpoint_values(checkpoint, reference['shifted_source_checkpoint'])
        child_started = perf_counter()
        child = subprocess.run([sys.executable, '-c', CHILD, str(directory), progress['head_sha256']],
            capture_output=True, text=True, timeout=90)
        assert child.returncode == 0, child.stderr
        resumed = json.loads(child.stdout)
        assert resumed['pid'] != os.getpid() and resumed['read_RHS_calls'] == 0 and resumed['resume_RHS_calls'] > 0
        assert resumed['recovered_checkpoint_sha256'] == sha256(engine._canonical(checkpoint)).hexdigest()
        expected_next = engine.advance_chunk(context, checkpoint, {'max_steps': 1, 'max_transitions': 1})
        assert resumed['checkpoint'] == expected_next['checkpoint']
        assert resumed['checkpoint']['sequence'] == 4097
        child_wall = perf_counter()-child_started
    assert context.reader.closed and not context._cache and not context.reader._cache
    assert all(before[key] == tree(paths[key]) for key in before)
    assert Path(os.environ['OSSF_CHUNK_FEASIBILITY_BASELINE']).read_bytes() == baseline_raw
    assert len(os.listdir('/proc/self/fd')) == descriptors
    pages = [page for values in commit['pages'].values() for page in values]
    assert len(pages) == 2 and all(p['count'] <= 128 for p in pages)
    assert metadata_bytes <= artifact.LIMITS['metadata_bytes']
    save('bounded-chunks-observed.json', {'version':'crop-cycle-calculation-bounded-chunks-observed-v1',
        'scope':'owned_synthetic_stored_prefix_and_fresh_python_only', 'progress':progress,
        'checkpoint':checkpoint, 'all_non_lineage_checkpoint_fields_equal':True,
        'original_rows_exact_after_explicit_shift':True, 'counts':counts, 'page_count':len(pages),
        'maximum_page_bytes':max((directory/(p['sha256']+'.json')).stat().st_size for p in pages),
        'metadata_bytes':metadata_bytes, 'effective_budget':commit['budget'],
        'row_sha256':{kind:sha256(b''.join(engine._canonical(row)+b'\n' for row in records[kind])).hexdigest() for kind in counts},
        'baseline_sha256':sha256(baseline_raw).hexdigest(), 'artifact_code_sha256':artifact.CODE_SHA256,
        'context_create_and_stored_advance_wall_seconds':calculation_wall, 'costs':costs.values,
        'fresh_python':resumed, 'fresh_python_and_expected_resume_wall_seconds':child_wall,
        'original_and_derived_files_preserved':True, 'original_and_derived_input_files_each':750,
        'original_artifact_files':29141, 'FD_before_after':[descriptors,descriptors],
        'contexts_closed_caches_empty':True, 'registered_farm_execution':False,
        'terminal_artifact_issued':False, 'whole166day_accepted':False,
        'gates':'not_assessed', 'forecast_and_ranking':'hold'})
