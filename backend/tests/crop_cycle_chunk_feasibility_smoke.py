"""Manual pure calculation probe; does not enlarge artifact or server budgets."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

import pytest

from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_context as engine
from crop_cycle_full_prefix_cost_smoke import packet, original_rows, same_checkpoint_values
from crop_cycle_calculation_prefix_cost_smoke import driver, tree
from crop_cycle_full_calendar_registration_smoke import save
from test_crop_cycle_input_evidence import authority


def test_actual_full_input_4096_transitions_match_32_committed_chunks(driver, monkeypatch):
    paths, receipt, proof = packet()
    before = {key: tree(paths[key]) for key in ('derived', 'original', 'artifact')}
    assert len(before['derived']) == len(before['original']) == 750
    assert len(before['artifact']) == 29141
    baseline_raw = Path(os.environ['OSSF_CHUNK_FEASIBILITY_BASELINE']).read_bytes()
    assert sha256(baseline_raw).hexdigest() == os.environ['OSSF_CHUNK_FEASIBILITY_BASELINE_SHA256']
    baseline = json.loads(baseline_raw)
    assert len(baseline['growth_curve']) == 32
    assert baseline['last_progress']['status'] == 'yielded'
    assert baseline['checkpoint']['sequence'] == 4096
    budget = {'max_steps': 10000, 'max_transitions': 4096}
    with pytest.raises(artifact.CalculationArtifactHold, match='bounded artifact chunk budget'):
        artifact._budget(budget)
    descriptors = len(os.listdir('/proc/self/fd'))
    started = perf_counter()
    with driver.observation() as costs:
        with engine.open_calculation_context(paths['derived'], receipt['target_root_sha256'],
                proof, authority=authority()) as context:
            initial = engine.start(context)
            result = engine.advance_chunk(context, initial, budget)
    elapsed = perf_counter()-started
    assert context.reader.closed and not context.reader._cache and not context._cache
    assert result['status'] == 'yielded' and result['planned_steps'] == 1816704
    checkpoint = result['checkpoint']
    assert checkpoint['sequence'] == 4096 and result['steps'] == baseline['last_progress']['steps']
    lineage = {'parent_sha256', 'checkpoint_sha256'}
    assert {k:v for k,v in checkpoint.items() if k not in lineage} == {
        k:v for k,v in baseline['checkpoint'].items() if k not in lineage}
    counts = {kind:len(result[kind]) for kind in ('samples', 'events')}
    assert counts == baseline['last_progress']['counts']
    assert costs.values['rhs']['calls'] > 0
    with monkeypatch.context() as no_math:
        no_math.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('reference read ran RHS'))
        expected, reference = original_rows(paths, counts, advance_count=32)
    assert expected == {kind:result[kind] for kind in ('samples', 'events')}
    assert same_checkpoint_values(checkpoint, reference['shifted_source_checkpoint'])
    # Reuse the real page packer in memory; no artifact, proof, or HEAD is issued.
    blobs = {}
    def put(raw, limit):
        assert len(raw) <= limit
        digest = sha256(raw).hexdigest()
        blobs[digest] = raw
        return digest
    packer = SimpleNamespace(_put=put)
    pages = {kind:artifact.ArtifactWriter._pages(packer, result[kind]) for kind in counts}
    meta = {k:v for k,v in result.items() if k not in ('manifest', 'samples', 'events')}
    chunk = {'version':artifact.VERSION, 'header_sha256':'0'*64, 'sequence':1,
        'parent_commit_sha256':None, 'input_checkpoint_sha256':initial['checkpoint_sha256'],
        'budget':budget, 'result':meta, 'pages':pages}
    metadata_bytes = len(engine._canonical(chunk))
    delta_bytes = sum(len(engine._canonical(result[kind])) for kind in counts)
    assert delta_bytes <= artifact.LIMITS['delta_bytes']
    assert sum(map(len, pages.values())) <= artifact.LIMITS['pages_per_commit']
    assert metadata_bytes <= artifact.LIMITS['metadata_bytes']
    assert all(len(raw) <= artifact.LIMITS['page_bytes'] for raw in blobs.values())
    assert all(d['count'] <= artifact.LIMITS['page_records'] for rows in pages.values() for d in rows)
    assert all(before[key] == tree(paths[key]) for key in before)
    assert Path(os.environ['OSSF_CHUNK_FEASIBILITY_BASELINE']).read_bytes() == baseline_raw
    assert len(os.listdir('/proc/self/fd')) == descriptors
    report = {'version':'crop-cycle-calculation-chunk-feasibility-v1',
        'scope':'owned_synthetic_pure_prefix_probe_only', 'budget':budget,
        'existing_artifact_rejected_candidate_budget':True, 'product_limits_changed':False,
        'registered_farm_execution':False, 'artifact_or_proof_issued':False,
        'whole166day_accepted':False, 'baseline_sha256':sha256(baseline_raw).hexdigest(),
        'input_root_sha256':receipt['target_root_sha256'],
        'checkpoint':checkpoint, 'all_non_lineage_checkpoint_fields_equal':True,
        'original_rows_exact_after_explicit_shift':True, 'counts':counts,
        'row_sha256':{kind:sha256(b''.join(engine._canonical(row)+b'\n' for row in result[kind])).hexdigest()
            for kind in counts},
        'steps':result['steps'], 'planned_steps':result['planned_steps'],
        'source_checkpoint_sequence':reference['shifted_source_checkpoint']['sequence'],
        'original_and_derived_input_files_each':len(before['derived']),
        'original_artifact_files':len(before['artifact']),
        'all_original_and_derived_files_preserved':True,
        'packing_projection':{'metadata_bytes':metadata_bytes, 'delta_bytes':delta_bytes,
            'page_count':sum(map(len, pages.values())), 'maximum_page_bytes':max(map(len, blobs.values())),
            'limits':deepcopy(artifact.LIMITS)},
        'calculation_context_factory_and_start_advance_wall_seconds':elapsed,
        'costs':costs.values, 'read_rhs_calls':0, 'FD_before_after':[descriptors,descriptors],
        'contexts_closed_caches_empty':True,
        'gates':'not_assessed', 'forecast_and_ranking':'hold'}
    save('chunk-feasibility-observed.json', report)
