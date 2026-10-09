"""Focused counterexamples for the offline audit; no farm validation claims."""
from copy import deepcopy
from decimal import localcontext
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path

import pytest

from app import crop_harvest as harvest
from app import crop_harvest_replay as replay
from app import crop_cycle_calculation_artifact as original
from test_crop_harvest import OwnedPages, mass_profile, allocation_profile

PATH = Path(__file__).resolve().parents[2] / 'research/crop-harvest-full-capacity.py'
SPEC = importlib.util.spec_from_file_location('harvest_capacity_audit', PATH)
capacity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capacity)


def fixture_rows(*, leaf_only=False, mid_event=False):
    pages = OwnedPages()
    if leaf_only:
        for event in pages.events:
            for key in ('fruit_carbohydrate', 'fruit_number'):
                for q in event['removed'][key]:q['value'] = 0
    if mid_event:
        middle = deepcopy(pages.events[1]); middle.update(at='2026-10-01T00:06:25Z', input_id='owned-between-samples')
        pages.events.insert(2, middle)
        packet = json.loads(pages.original['record']['payload_raw']);packet['artifact']['event_count'] += 1
        pages.original['record']['payload_raw'] = harvest._canonical(packet)
    source = harvest._source(pages())
    mass = harvest._mass_parameters(harvest._canonical(mass_profile(source)))
    profile = allocation_profile(mass, last_sample=len(pages.samples)-1, last_event=len(pages.events)-1)
    allocation = harvest._allocation_parameters(harvest._canonical(profile), mass)
    pairs = list(capacity.removals(enumerate(pages.samples), enumerate(pages.events), source))
    rows = [harvest._allocation_row(harvest._mass_row(removal, mass), allocation) for removal, _ in pairs]
    return pages, mass, allocation, pairs, rows


@pytest.mark.parametrize('mid_event', [False, True])
def test_offline_merge_matches_product_including_initial_end_and_unsampled_event(mid_event):
    pages, mass, allocation, pairs, rows = fixture_rows(mid_event=mid_event)
    assert [p[0] for p in pairs] == list(harvest._read_ledger(pages, sample_page_size=1, event_page_size=1))
    assert rows == list(harvest._read_allocations(pages, harvest._canonical(mass[0]), harvest._canonical(allocation[0])) )


@pytest.mark.parametrize('leaf_only', [False, True])
def test_independent_decimal_all_rows_and_summary_exclude_leaf_stem(leaf_only):
    _, mass, allocation, pairs, rows = fixture_rows(leaf_only=leaf_only, mid_event=True)
    with localcontext() as context:
        context.prec = 2200
        checker = capacity.QuantityAudit(mass[0], allocation[0])
        for row, (_, reference) in zip(rows, pairs, strict=True):checker.add(row, reference)
        result = checker.finish(harvest._allocation_totals(iter(rows), allocation))
    assert result['rows'] == 7 and result['terminal_rows'] == 3 and result['event_rows'] == 4
    assert result['excluded_leaf_stem_exact_decimal_mg_CH2O_per_m2_floor'] == {'leaf': '4000000', 'stem_root': '8000000'}
    assert all(b['within_budget'] for group in result['balances'].values() for b in group.values())
    if leaf_only:
        assert all(row['mass']['fresh_matter']['value'] == 0 for row in rows if row['mass']['removal']['kind'] == 'explicit_fruit_removal')


@pytest.mark.parametrize('change', ['numerator', 'mass', 'original-amount', 'purpose', 'source', 'unit', 'position', 'scope'])
def test_independent_checker_rejects_corrupted_row(change):
    _, mass, allocation, pairs, rows = fixture_rows()
    row = rows[0]
    if change == 'numerator':row['allocations'][0]['quantities']['fresh_matter']['exact']['numerator'] = '123'
    elif change == 'mass':row['mass']['fresh_matter']['value'] += 1
    elif change == 'original-amount':row['mass']['removal']['carbohydrate']['value'] += 1
    elif change == 'purpose':row['allocations'][0]['purpose'] = 'sales'
    elif change == 'source':row['mass']['removal']['source']['artifact_sha256'] = '9'*64
    elif change == 'unit':row['allocations'][0]['quantities']['number']['unit'] = 'fruits'
    elif change == 'position':row['mass']['removal']['position']['event'] = 1
    else:row['rights_or_gate_approval'] = True
    with localcontext() as context:
        context.prec = 2200
        with pytest.raises(ValueError):capacity.QuantityAudit(mass[0], allocation[0]).add(row, pairs[0][1])


@pytest.mark.parametrize('change', ['count', 'chain', 'purpose-total', 'observation'])
def test_independent_checker_rejects_corrupted_summary(change):
    _, mass, allocation, pairs, rows = fixture_rows()
    with localcontext() as context:
        context.prec = 2200; checker = capacity.QuantityAudit(mass[0], allocation[0])
        for row, (_, reference) in zip(rows, pairs, strict=True):checker.add(row, reference)
        summary = harvest._allocation_totals(iter(rows), allocation)
        if change == 'count':summary['row_count'] += 1
        elif change == 'chain':summary['row_chain_sha256'] = '9'*64
        elif change == 'purpose-total':summary['totals_by_kind_and_purpose']['model_terminal_outflow']['harvest']['quantities']['fresh_matter']['exact']['numerator'] = '123'
        else:summary['observation_comparisons'][0]['modeled_fresh_matter']['value'] += 1
        with pytest.raises(ValueError):checker.finish(summary)


@pytest.mark.parametrize('change', ['duplicate-event', 'event-before', 'event-after', 'missing-sample', 'initial-cumulative'])
def test_merge_refuses_incomplete_or_reordered_originals(change):
    pages, mass, allocation, _, _ = fixture_rows()
    samples = list(enumerate(pages.samples))
    if change == 'duplicate-event':pages.events.insert(1, deepcopy(pages.events[0]))
    elif change == 'event-before':pages.events[0]['at'] = '2026-09-30T23:59:59Z'
    elif change == 'event-after':pages.events[-1]['at'] = '2026-10-01T00:15:01Z'
    elif change == 'missing-sample':samples.pop(1)
    else:pages.samples[0]['cumulative']['terminal_carbohydrate']['value'] = 1
    with localcontext() as context:
        context.prec = 2200; checker = capacity.QuantityAudit(mass[0], allocation[0])
        with pytest.raises((ValueError, harvest.CropRemovalHold)):
            for removal, reference in capacity.removals(samples, enumerate(pages.events), mass[0]['source']):
                checker.add(harvest._allocation_row(harvest._mass_row(removal, mass), allocation), reference)


def test_packing_matches_actual_small_writer_page_bytes(tmp_path):
    pages, mass, allocation, _, rows = fixture_rows()
    packing = capacity.Packing(replay.LIMITS)
    for row in rows:packing.add(harvest._canonical(row))
    result = packing.finish();tmp_path.chmod(0o700)
    written = replay._write(tmp_path, pages, harvest._canonical(mass[0]), harvest._canonical(allocation[0]))
    root = json.loads((tmp_path/(written['artifact_sha256']+'.json')).read_bytes())
    assert [{k:p[k] for k in ('sha256','start','count')} for p in packing.pages] == root['pages']
    assert result['packed_page_bytes'] == sum((tmp_path/(p['sha256']+'.json')).stat().st_size for p in root['pages'])
    assert result['hold_reasons'] == [] and result['row_count'] == written['row_count']


def test_packing_exact_record_and_byte_boundaries_with_original_limits():
    packing = capacity.Packing(replay.LIMITS)
    for _ in range(65):packing.add(b'{}')
    packing.finish();assert [p['count'] for p in packing.pages] == [64, 1]
    packing = capacity.Packing(replay.LIMITS)
    packing.add(b'0' * (replay.LIMITS['page_bytes']-2));packing.add(b'{}')
    packing.finish();assert packing.pages[0]['bytes'] == replay.LIMITS['page_bytes']
    with pytest.raises(ValueError):packing.add(b'0' * (replay.LIMITS['page_bytes']-1))


@pytest.mark.parametrize('limit', ['directory_bytes', 'files', 'pages'])
def test_packing_reports_explicit_hold_instead_of_reducing_rows_or_raising_limits(limit):
    limits = {**replay.LIMITS, limit: 1};packing = capacity.Packing(limits);packing.add(b'{}');packing.add(b'{}')
    result = packing.finish()
    if limit == 'pages':
        packing = capacity.Packing({**limits,'page_records':1});packing.add(b'{}');packing.add(b'{}');result = packing.finish()
    assert result['hold_reasons'] and result['row_count'] == 2 and result['limits'][limit] == 1


def test_root_metadata_excess_is_a_hold_even_when_pages_fit():
    packing = capacity.Packing(replay.LIMITS);packing.add(b'{}')
    result = packing.finish(root_known_bytes=replay.LIMITS['root_bytes'] + 1)
    assert result['hold_reasons'] == ['root_known_bytes'] and result['row_count'] == 1


def test_fd_identity_detects_replacement_without_a_count_change(tmp_path):
    first = tmp_path/'first';second = tmp_path/'second';first.write_bytes(b'first');second.write_bytes(b'second')
    a = os.open(first, os.O_RDONLY);b = os.open(second, os.O_RDONLY)
    try:
        before = capacity.fd_inventory();os.dup2(b, a);after = capacity.fd_inventory()
        assert set(before) == set(after) and before != after and before[str(a)] != after[str(a)]
    finally:
        os.close(a);os.close(b)


def test_inventory_preserves_fd_and_detects_content_mode_inode_and_symlink(tmp_path):
    file = tmp_path/'owned';file.write_bytes(b'owned');before_fd = len(os.listdir('/proc/self/fd'))
    first = capacity.inventory(tmp_path);assert first == capacity.inventory(tmp_path)
    file.write_bytes(b'other');second = capacity.inventory(tmp_path);assert second != first
    file.chmod(0o400);assert capacity.inventory(tmp_path) != second
    file.unlink();file.symlink_to(PATH)
    with pytest.raises(ValueError):capacity.inventory(tmp_path)
    assert len(os.listdir('/proc/self/fd')) == before_fd


def fixture_archive(tmp_path, monkeypatch, change=None):
    pages = OwnedPages()
    if change == 'duplicate-UTC':pages.samples[1]['at'] = pages.samples[0]['at']
    def blob(value):
        raw = harvest._canonical(value);digest = sha256(raw).hexdigest()
        (tmp_path/(digest+'.json')).write_bytes(raw)
        return digest
    descriptors = {}
    for kind in ('samples', 'events'):
        rows = getattr(pages, kind)
        descriptors[kind] = [{'sha256': blob(rows), 'count': len(rows), 'first_at': rows[0]['at'], 'last_at': rows[-1]['at']}]
    if change == 'oversize-count':descriptors['samples'][0]['count'] = 129
    header = {'initial_checkpoint': {'checkpoint_sha256': '1'*64},
              'manifest': {'input_root_sha256': '2'*64, 'planned_steps': 3}}
    header_sha = blob(header)
    commit = {'version': original.VERSION, 'sequence': 1, 'parent_commit_sha256': None,
              'header_sha256': header_sha, 'input_checkpoint_sha256': '1'*64, 'pages': descriptors,
              'result': {'status': 'completed', 'steps': 3, 'output_start': 0, 'event_start': 0,
                         'checkpoint': {'output_cursor': 4, 'event_cursor': 3}}}
    if change == 'lineage':commit['parent_commit_sha256'] = '3'*64
    if change == 'cursor':commit['result']['output_start'] = 1
    commit_sha = blob(commit)
    root_sha = blob({'version': original.VERSION, 'header_sha256': header_sha, 'commits': [commit_sha], 'status': 'completed'})
    head = {'version': original.VERSION, 'artifact_sha256': root_sha, 'header_sha256': header_sha,
            'latest_commit_sha256': commit_sha, 'commit_count': 1}
    (tmp_path/'HEAD').write_bytes(harvest._canonical(head))
    monkeypatch.setattr(capacity, 'ARTIFACT_SHA256', root_sha if change != 'root' else '9'*64)
    receipt = {'observation': {'replay': {'published_result_id': 'owned-result', 'payload_sha256': '4'*64},
        'comparison_counts_hashes': {'counts': {'samples': 4, 'events': 3},
            'candidate_row_sha256': {kind: sha256(b''.join(harvest._canonical(row)+b'\n' for row in getattr(pages,kind))).hexdigest()
                                     for kind in ('samples','events')}}}}
    if change == 'count':receipt['observation']['comparison_counts_hashes']['counts']['samples'] += 1
    if change == 'row-hash':receipt['observation']['comparison_counts_hashes']['candidate_row_sha256']['samples'] = '9'*64
    if change == 'blob-hash':
        (tmp_path/(descriptors['samples'][0]['sha256']+'.json')).write_bytes(b'[]')
    return pages, receipt


def test_archive_bounded_hash_reader_and_complete_original_rows(tmp_path, monkeypatch):
    pages, receipt = fixture_archive(tmp_path, monkeypatch)
    fd_count = len(os.listdir('/proc/self/fd'))
    with original._Files(tmp_path) as files:
        archive = capacity.Archive(files, receipt)
        for kind in ('samples','events'):
            assert list(archive.rows(kind)) == list(enumerate(getattr(pages,kind)))
        assert archive.hashes == receipt['observation']['comparison_counts_hashes']['candidate_row_sha256']
    assert files.closed and len(os.listdir('/proc/self/fd')) == fd_count


@pytest.mark.parametrize('change', ['lineage','cursor','count','root','oversize-count','duplicate-UTC','row-hash','blob-hash'])
def test_archive_rejects_changed_lineage_counts_UTC_and_hashes_without_fd_leak(tmp_path, monkeypatch, change):
    _, receipt = fixture_archive(tmp_path, monkeypatch, change)
    fd_count = len(os.listdir('/proc/self/fd'))
    with pytest.raises((ValueError, original.CalculationArtifactHold)):
        with original._Files(tmp_path) as files:
            archive = capacity.Archive(files, receipt)
            list(archive.rows('samples'));list(archive.rows('events'))
    assert files.closed and len(os.listdir('/proc/self/fd')) == fd_count
