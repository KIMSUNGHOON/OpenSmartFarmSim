"""Manual RHS0 integer/byte capacity audit; no new crop result or farm Run."""
from bisect import bisect_right
from copy import deepcopy
from datetime import datetime, timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter

import pytest

from app import crop_cycle_artifact as original
from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_context as engine
from app import crop_cycle_calculation_server_custody as custody
from crop_cycle_full_prefix_cost_smoke import packet
from crop_cycle_full_calendar_registration_smoke import save, tree
from test_crop_cycle_input_evidence import authority


def plan_chunks(rows, *, transitions=4096, boundaries=128):
    if not rows or not 1 <= transitions <= 4096 or not 1 <= boundaries <= 128:
        raise ValueError('bounded nonempty capacity grid required')
    previous = (0, 0, 0)
    for row in rows:
        if (len(row) != 3 or any(type(v) is not int or v < 0 for v in row)
                or row[0] < previous[0] or any(row[i]-previous[i] not in (0, 1) for i in (1, 2))):
            raise ValueError('monotone steps and single output/event per boundary required')
        previous = row
    post = [r[0]+i+1 for i, r in enumerate(rows)]
    cuts = []; sequence = cursor = 0
    while sequence < post[-1]:
        end = min(sequence+transitions, post[min(cursor+boundaries, len(rows))-1])
        cursor = bisect_right(post, end)
        steps, samples, events = rows[cursor-1] if cursor else (0, 0, 0)
        cuts.append({'sequence':end, 'steps':end-cursor, 'boundary_cursor':cursor,
                     'samples':samples, 'events':events})
        sequence = end
    return cuts


class Packing:
    def __init__(self, cuts, kind):
        self.cuts, self.kind = cuts, kind
        self.offset = self.cursor = self.records = self.bytes = self.maximum_record = 0
        self.pages = []
        self.current = {'count':0, 'bytes':2}

    def flush(self):
        if self.current['count']:
            self.pages.append({'chunk':self.cursor+1, **self.current})
        self.current = {'count':0, 'bytes':2}

    def add(self, raw):
        self.offset += 1
        while self.offset > self.cuts[self.cursor][self.kind]:
            self.flush(); self.cursor += 1
        length = len(raw)
        assert length+2 <= artifact.LIMITS['page_bytes']-4096
        extra = length+int(self.current['count'] > 0)
        if (self.current['count'] == artifact.LIMITS['page_records']
                or self.current['bytes']+extra > artifact.LIMITS['page_bytes']):
            self.flush(); extra = length
        self.current['count'] += 1; self.current['bytes'] += extra
        self.maximum_record = max(self.maximum_record, length)

    def finish(self):
        self.flush()
        assert self.offset == self.cuts[-1][self.kind]
        return {'records':self.offset, 'maximum_record_bytes':self.maximum_record,
                'pages':self.pages, 'page_bytes':sum(p['bytes'] for p in self.pages)}


def capacity(cuts, packed):
    limits, server = artifact.LIMITS, custody.LIMITS
    commits = len(cuts)
    all_pages = [p for kind in packed.values() for p in kind['pages']]
    per_chunk = [{'pages':0, 'bytes':0} for _ in cuts]
    for page in all_pages:
        assert page['count'] <= limits['page_records'] and page['bytes'] <= limits['page_bytes']
        bucket = per_chunk[page['chunk']-1]; bucket['pages'] += 1; bucket['bytes'] += page['bytes']
    assert all(p['pages'] <= limits['pages_per_commit'] and p['bytes'] <= limits['delta_bytes'] for p in per_chunk)
    # Reference row packing plus format maxima; never a new actual result size.
    artifact_bytes = sum(p['bytes'] for p in all_pages)+(commits+1)*limits['metadata_bytes']+limits['root_bytes']+8192
    artifact_files = len(all_pages)+commits+4
    proof_files = commits+2
    proof_bytes = proof_files*server['proof_bytes']
    intent_bytes = artifact_bytes+proof_bytes+server['intent_bytes']+16384
    intent_files = artifact_files+proof_files+5
    reservations = {
        'advance':{'bytes':2*limits['delta_bytes']+4*limits['metadata_bytes']+2*server['proof_bytes']+16384, 'files':40},
        'finalize':{'bytes':2*limits['root_bytes']+2*server['proof_bytes']+16384, 'files':8},
        'publish':{'bytes':2*server['proof_bytes']+16384, 'files':4}}
    reserve_bytes = max(v['bytes'] for v in reservations.values())
    reserve_files = max(v['files'] for v in reservations.values())
    comparisons = {
        'commits':[commits, limits['commits']],
        'artifact_bytes_with_reserve':[artifact_bytes+reserve_bytes, limits['directory_bytes']],
        'artifact_files_with_reserve':[artifact_files+reserve_files, limits['files']],
        'proof_bytes_with_reserve':[proof_bytes+2*server['proof_bytes'], server['proof_directory_bytes']],
        'proof_files_with_reserve':[proof_files+2, server['proof_files']],
        'intent_bytes_with_reserve':[intent_bytes+reserve_bytes, server['intent_directory_bytes']],
        'intent_files_with_reserve':[intent_files+reserve_files, server['intent_files']],
        'root_bytes_with_reserve':[intent_bytes+reserve_bytes+16384, server['root_bytes']],
        'root_files_with_reserve':[intent_files+reserve_files+4, server['root_files']],
        'root_intents':[1, server['root_intents']]}
    assert all(used <= limit for used, limit in comparisons.values())
    return {'scope':'conditional_same_reference_rows_clean_single_intent_not_actual_new_result',
        'reference_packed_pages':len(all_pages), 'reference_packed_bytes':sum(p['bytes'] for p in all_pages),
        'maximum_delta_page_bytes':max(p['bytes'] for p in per_chunk),
        'maximum_pages_per_delta':max(p['pages'] for p in per_chunk),
        'artifact_upper_bytes_before_reserve':artifact_bytes, 'artifact_upper_files_before_reserve':artifact_files,
        'proof_upper_bytes':proof_bytes, 'proof_upper_files':proof_files,
        'reservations':reservations, 'comparisons_used_limit':comparisons,
        'artifact_limits':deepcopy(limits), 'server_limits':deepcopy(server)}


def test_actual_full_grid_reference_capacity_without_rhs(monkeypatch):
    paths, receipt, proof = packet()
    preserved = {k:tree(paths[k]) for k in ('derived', 'original', 'artifact')}
    descriptors = len(os.listdir('/proc/self/fd')); started = perf_counter()
    def forbidden(*args, **kwargs): pytest.fail('RHS/advance forbidden in capacity audit')
    monkeypatch.setattr(engine.short._Evaluator, 'rhs', forbidden)
    monkeypatch.setattr(engine, 'advance_chunk', forbidden)
    monkeypatch.setattr(artifact.ArtifactWriter, 'advance', forbidden)
    with engine.open_calculation_context(paths['derived'], receipt['target_root_sha256'], proof,
            authority=authority()) as context:
        rows = []
        for i in range(context.boundary_count):
            row = engine._boundary(context, i)
            rows.append((row['steps'], row['positions']['outputs'], row['positions']['events']))
        assert rows[-1] == (context.planned_steps, 47809, 5)
        cuts = plan_chunks(rows)
        accepted = json.loads((Path(__file__).resolve().parents[2]/
            'research/artifacts/crop-cycle-calculation-registered-chunk-cost-reference-20261008.json').read_bytes())
        for cut, name in zip(cuts[:2], ('first', 'second'), strict=True):
            cp = accepted['observation'][name]['checkpoint']
            assert all(cut[k] == cp[k] for k in ('sequence','steps','boundary_cursor'))
            assert (cut['samples'],cut['events']) == (cp['output_cursor'],cp['event_cursor'])
        context.recheck()
    assert context.reader.closed and not context._cache and not context.reader._cache
    grid_wall = perf_counter()-started
    packing = {kind:Packing(cuts, kind) for kind in ('samples', 'events')}
    hashes = {kind:sha256() for kind in packing}; shifted_hashes = {kind:sha256() for kind in packing}
    previous_at = {kind:None for kind in packing}; old_commits = metadata_bytes = old_page_bytes = 0
    with original._Files(paths['artifact']) as files:
        head, head_sha = files._head()
        root, _ = files._blob('15b609576243c73b67a4947b5affc2db14047787e4851064b3aabeafd3d0286d', original.LIMITS['root_bytes'])
        assert head['artifact_sha256'] == sha256(original._canonical(root)).hexdigest()
        assert root['commits'][-1] == head['latest_commit_sha256'] and root['status'] == 'completed'
        header, _ = files._blob(root['header_sha256'], original.LIMITS['metadata_bytes'])
        previous = None
        for number, digest in enumerate(root['commits'], 1):
            commit, length = files._blob(digest, original.LIMITS['metadata_bytes'])
            assert commit['sequence'] == number and commit['parent_commit_sha256'] == previous
            assert commit['header_sha256'] == root['header_sha256']
            old_commits += 1; metadata_bytes += length; previous = digest
            for kind in packing:
                for descriptor in commit['pages'][kind]:
                    page, length = files._blob(descriptor['sha256'], original.LIMITS['page_bytes'])
                    assert len(page) == descriptor['count'] and page[0]['at'] == descriptor['first_at'] and page[-1]['at'] == descriptor['last_at']
                    old_page_bytes += length
                    for row in page:
                        assert previous_at[kind] is None or previous_at[kind] < row['at']
                        previous_at[kind] = row['at']
                        raw = original._canonical(row); hashes[kind].update(raw+b'\n')
                        shifted = {**row, 'at':(datetime.fromisoformat(row['at'].replace('Z','+00:00'))+timedelta(days=273)).isoformat().replace('+00:00','Z')}
                        shifted_raw = original._canonical(shifted)
                        assert len(raw) == len(shifted_raw)
                        shifted_hashes[kind].update(shifted_raw+b'\n'); packing[kind].add(shifted_raw)
        assert old_commits == head['commit_count'] == 14567
        assert commit['result']['status'] == 'completed' and commit['result']['steps'] == 1816704
    assert files.closed
    expected = {'samples':'b00e63d96debcbfc2c80eb5c17b71a9a9bd7bd0634acdb1d6ffe47655ae53dbd',
                'events':'0900f8ff0753d3d7746a2ea32b75ed579ba0c07a7789d99e4b4cee01850e1eb8'}
    assert {k:h.hexdigest() for k,h in hashes.items()} == expected
    packed = {k:p.finish() for k,p in packing.items()}
    limits = capacity(cuts, packed)
    assert all(preserved[k] == tree(paths[k]) for k in preserved)
    assert len(os.listdir('/proc/self/fd')) == descriptors
    save('full-capacity-cursors.json', {'scope':'integer_capacity_positions_not_crop_checkpoints', 'cuts':cuts,
        'reference_packing':packed})
    save('full-capacity-observed.json', {'version':'crop-cycle-calculation-full-capacity-v1',
        'scope':'owned_synthetic_RHS0_reference_capacity_only', 'root_sha256':receipt['target_root_sha256'],
        'full_boundary_count':len(rows), 'planned_chunks':len(cuts), 'final_capacity_cursor':cuts[-1],
        'first_two_actual_checkpoint_cursors_match':True, 'grid_wall_seconds':grid_wall,
        'capacity':limits, 'original_commits':old_commits, 'original_metadata_bytes':metadata_bytes,
        'original_page_bytes':old_page_bytes, 'original_row_sha256':expected,
        'translated_row_sha256':{k:h.hexdigest() for k,h in shifted_hashes.items()},
        'original_HEAD_sha256':head_sha, 'RHS_calls':0, 'advance_calls':0, 'new_crop_results':0,
        'FD_before_after':[descriptors,descriptors], 'contexts_closed_caches_empty':True,
        'original_and_derived_inputs_and_artifact_preserved':True, 'wall_seconds':perf_counter()-started,
        'full_registered_execution_budget_fixed':False, 'whole166_registered_accepted':False,
        'gates':'not_assessed', 'forecast_and_ranking':'hold'})
