"""Offline quantity/byte audit of an already accepted immutable synthetic cycle."""
from contextlib import ExitStack
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from math import ulp
import os
from pathlib import Path
import stat
from time import perf_counter
from unittest.mock import patch

from app import crop_cycle_calculation_artifact as original
from app import crop_harvest as harvest
from app import crop_harvest_replay as replay
from test_crop_harvest import mass_profile, allocation_profile

VERSION = 'crop-harvest-full-capacity-v1'
RECEIPT = 'research/artifacts/crop-cycle-calculation-full166-same-db-completed-reference-20261008.json'
RECEIPT_SHA256 = '1ace1677e1f13c5183a3f6f90d4652183eb3cd92eb2982de9365b5b836995033'
ARTIFACT_SHA256 = 'f1bf669180fa3b07f39c4b582fedc5c7edcf28b5e35497cde9947dcdd5eb6a8c'
KEYS = ('carbohydrate', 'number', 'dry_matter', 'fresh_matter')
UNITS = (harvest.MASS_UNIT, harvest.NUMBER_UNIT, 'kg_DM/m2_floor', 'kg_FW/m2_floor')
KINDS = ('model_terminal_outflow', 'explicit_fruit_removal')
PURPOSES = ('harvest', 'thinning', 'disposal', 'sampling', 'unassigned')


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def fd_inventory():
    result = {}
    for name in os.listdir('/proc/self/fd'):
        try:
            info = os.fstat(int(name))
            result[name] = (info.st_dev, info.st_ino, info.st_mode, os.readlink('/proc/self/fd/' + name))
        except FileNotFoundError:
            pass
        except OSError as exc:
            if exc.errno != 9:
                raise
    return result


def inventory(directory):
    """Bounded content and identity inventory, including HEAD and the empty lock."""
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        rows = []
        names = sorted(os.listdir(fd))
        need(len(names) <= original.LIMITS['files'], 'archive file count exceeded')
        need(sum(os.stat(n, dir_fd=fd, follow_symlinks=False).st_size for n in names) <= original.LIMITS['directory_bytes'],
             'archive directory bytes exceeded')
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mode, s.st_mtime_ns, s.st_ctime_ns)
        for name in names:
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            need(stat.S_ISREG(info.st_mode) and info.st_size <= original.LIMITS['directory_bytes'], 'archive regular bounded file required')
            handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
            try:
                need(identity(os.fstat(handle)) == identity(info), 'archive file replaced')
                digest = sha256()
                with os.fdopen(handle, 'rb', closefd=False) as stream:
                    while block := stream.read(1024 * 1024):
                        digest.update(block)
                need(identity(os.fstat(handle)) == identity(info), 'archive file changed')
            finally:
                os.close(handle)
            rows.append([name, info.st_size, info.st_mode, info.st_dev, info.st_ino, digest.hexdigest()])
        return {'files': len(rows), 'bytes': sum(r[1] for r in rows),
                'content_mode_inode_sha256': sha256(harvest._canonical(rows)).hexdigest()}
    finally:
        os.close(fd)


class Archive:
    """Structural reader of the pinned accepted root; no current DB authority."""
    def __init__(self, files, receipt):
        self.files = files
        self.head, self.head_sha = files._head()
        observation = receipt['observation']
        self.expected = observation['comparison_counts_hashes']
        root, _ = files._blob(self.head['artifact_sha256'], original.LIMITS['root_bytes'])
        need(root['status'] == 'completed' and root['version'] == original.VERSION
             and root['header_sha256'] == self.head['header_sha256']
             and len(root['commits']) == self.head['commit_count']
             and root['commits'][-1] == self.head['latest_commit_sha256'], 'archive root mismatch')
        self.header, _ = files._blob(root['header_sha256'], original.LIMITS['metadata_bytes'])
        manifest = self.header['manifest']
        self.source = {'result_id': observation['replay']['published_result_id'],
                       'payload_sha256': observation['replay']['payload_sha256'],
                       'input_root_sha256': manifest['input_root_sha256'],
                       'artifact_sha256': self.head['artifact_sha256'],
                       'math_manifest_sha256': sha256(harvest._canonical(manifest)).hexdigest(),
                       'source_status': 'completed'}
        need(self.head['artifact_sha256'] == ARTIFACT_SHA256, 'accepted artifact root mismatch')
        self.index = {kind: [] for kind in ('samples', 'events')}
        counts = dict.fromkeys(self.index, 0)
        parent = None
        checkpoint = self.header['initial_checkpoint']
        for sequence, digest in enumerate(root['commits'], 1):
            commit, _ = files._blob(digest, original.LIMITS['metadata_bytes'])
            need(commit['version'] == original.VERSION and commit['sequence'] == sequence
                 and commit['parent_commit_sha256'] == parent
                 and commit['header_sha256'] == root['header_sha256']
                 and commit['input_checkpoint_sha256'] == checkpoint['checkpoint_sha256'], 'commit lineage mismatch')
            result = commit['result']
            need(result['output_start'] == counts['samples'] and result['event_start'] == counts['events']
                 and result['status'] == ('completed' if sequence == len(root['commits']) else 'yielded'),
                 'commit cursor/status mismatch')
            for kind in self.index:
                descriptors = commit['pages'][kind]
                need(len(descriptors) <= original.LIMITS['pages_per_commit'], 'archive page count exceeded')
                for d in descriptors:
                    need(set(d) == {'sha256', 'count', 'first_at', 'last_at'}
                         and type(d['count']) is int and 1 <= d['count'] <= original.LIMITS['page_records'],
                         'archive page descriptor mismatch')
                    self.index[kind].append({'start': counts[kind], **d})
                    counts[kind] += d['count']
            checkpoint = result['checkpoint']; parent = digest
            need(checkpoint['output_cursor'] == counts['samples'] and checkpoint['event_cursor'] == counts['events'],
                 'checkpoint cursor mismatch')
        need(counts == self.expected['counts'] and result['steps'] == manifest['planned_steps'],
             'accepted complete counts/steps mismatch')
        self.counts = counts
        self.hashes = {}

    def rows(self, kind):
        chain = sha256(); previous = None; count = 0
        for d in self.index[kind]:
            rows, _ = self.files._blob(d['sha256'], original.LIMITS['page_bytes'])
            need(type(rows) is list and len(rows) == d['count'] and rows[0]['at'] == d['first_at']
                 and rows[-1]['at'] == d['last_at'], 'archive page range mismatch')
            for row in rows:
                harvest._at(row['at'])
                need(previous is None or previous < row['at'], 'archive UTC order mismatch')
                previous = row['at']; chain.update(harvest._canonical(row) + b'\n')
                yield count, row
                count += 1
        self.hashes[kind] = chain.hexdigest()
        need(count == self.counts[kind] and self.hashes[kind] == self.expected['candidate_row_sha256'][kind],
             'accepted original row hash/count mismatch')


def removals(samples, events, source):
    """Merge original intervals/events using the existing pure removal functions."""
    samples, events = iter(samples), iter(events)
    previous = next(samples); event = next(events, None)
    need(previous[0] == 0, 'initial sample required')
    need(all(previous[1]['cumulative'][k]['value'] == 0 for k in ('terminal_carbohydrate', 'terminal_number')),
         'initial terminal cumulative must be zero')
    if event is not None:
        need(event[1]['at'] >= previous[1]['at'], 'event before original cycle')
        if event[1]['at'] == previous[1]['at']:
            yield harvest._event_row(source, event), ('event', event)
            event = next(events, None)
    for selected in samples:
        while event is not None and event[1]['at'] < selected[1]['at']:
            yield harvest._event_row(source, event), ('event', event)
            event = next(events, None)
        yield harvest._terminal_row(source, previous, selected), ('terminal', previous, selected)
        if event is not None and event[1]['at'] == selected[1]['at']:
            yield harvest._event_row(source, event), ('event', event)
            event = next(events, None)
        previous = selected
    need(event is None, 'event outside complete original cycle')


class Packing:
    def __init__(self, limits):
        self.limits = deepcopy(limits); self.page = []; self.size = 2
        self.pages = []; self.count = self.bytes = self.peak_reserved = self.maximum_row = 0

    def flush(self):
        if not self.page:
            return
        raw = b'[' + b','.join(self.page) + b']'
        need(len(raw) == self.size, 'page byte accounting mismatch')
        self.peak_reserved = max(self.peak_reserved, self.bytes + 2 * len(raw))
        self.pages.append({'sha256': sha256(raw).hexdigest(), 'start': self.count,
                           'count': len(self.page), 'bytes': len(raw)})
        self.count += len(self.page); self.bytes += len(raw)
        self.page = []; self.size = 2

    def add(self, raw):
        need(type(raw) is bytes and len(raw) + 2 <= self.limits['page_bytes'], 'single derived row exceeds page')
        if self.page and (len(self.page) == self.limits['page_records'] or self.size + len(raw) + 1 > self.limits['page_bytes']):
            self.flush()
        self.size += len(raw) + bool(self.page); self.page.append(raw)
        self.maximum_row = max(self.maximum_row, len(raw))

    def finish(self, *, root_known_bytes=0):
        self.flush()
        # A real writer will supply its original query identity and actual root.
        # This bound reserves the maximum root twice plus a complete HEAD window.
        peak = max(self.peak_reserved, self.bytes + 2 * self.limits['root_bytes']) + 8192
        comparisons = {'root_known_bytes': [root_known_bytes, self.limits['root_bytes']],
                       'pages': [len(self.pages), self.limits['pages']],
                       'directory_bytes_with_reserve': [peak, self.limits['directory_bytes']],
                       'files_with_reserve': [len(self.pages) + 5, self.limits['files']]}
        holds = [key for key, (used, limit) in comparisons.items() if used > limit]
        return {'scope': 'exact_derived_page_bytes_conditional_root_maximum_not_actual_writer',
                'row_count': self.count, 'maximum_row_bytes': self.maximum_row,
                'page_count': len(self.pages), 'packed_page_bytes': self.bytes,
                'maximum_page_bytes': max((p['bytes'] for p in self.pages), default=0),
                'page_inventory_sha256': sha256(harvest._canonical(self.pages)).hexdigest(),
                'root_known_bytes_with_empty_identity': root_known_bytes,
                'remaining_root_bytes_for_original_identity': self.limits['root_bytes'] - root_known_bytes,
                'root_maximum_reserved_bytes': self.limits['root_bytes'],
                'comparisons_used_limit': comparisons, 'hold_reasons': holds, 'limits': self.limits}


def decimal_number(value):
    need(type(value) in (float, int), 'numeric quantity required')
    result = Decimal.from_float(value) if type(value) is float else Decimal(value)
    need(result.is_finite() and result >= 0, 'finite nonnegative quantity required')
    return result


def exact_quantity(quantity, expected, unit):
    need(set(quantity) == {'value', 'unit', 'exact'} and type(quantity['value']) in (int, float)
         and quantity['unit'] == unit and quantity['value'] == float(expected), 'quantity value/unit mismatch')
    need(set(quantity['exact']) == {'numerator', 'denominator'}
         and all(type(v) is str for v in quantity['exact'].values()), 'exact quantity schema mismatch')
    numerator = Decimal(quantity['exact']['numerator']); denominator = Decimal(quantity['exact']['denominator'])
    need(numerator.is_finite() and denominator.is_finite() and denominator > 0
         and numerator == expected * denominator, 'exact allocation conservation mismatch')


class QuantityAudit:
    """Decimal reference independent of the product's Fraction calculations."""
    def __init__(self, mass, allocation):
        self.mass = mass; self.allocation = allocation
        self.groups = {kind: {purpose: {'rows': 0, 'sums': dict.fromkeys(KEYS, Decimal(0))}
                              for purpose in PURPOSES} for kind in KINDS}
        self.balance = {kind: {key: {'original': Decimal(0), 'rounded': Decimal(0), 'budget': Decimal(0)}
                               for key in KEYS[:2]} for kind in KINDS}
        self.leaf_stem = dict.fromkeys(('leaf', 'stem_root'), Decimal(0))
        self.assignments = dict.fromkeys((r['assignment_id'] for r in allocation['rules']), Decimal(0))
        self.rows = 0; self.last_order = None; self.terminal_count = self.event_count = 0; self.chain = sha256()

    def add(self, row, reference):
        mass = row['mass']; removal = mass['removal']; kind = removal['kind']
        need(removal['source'] == self.mass['source'] == self.allocation['source'], 'source mixed')
        need(all(x['rights_or_gate_approval'] is False for x in (row, mass, removal))
             and row['claim_scope'] == 'synthetic_harvest_allocation_math_only'
             and mass['claim_scope'] == 'synthetic_removal_mass_math_only', 'synthetic scope changed')
        if reference[0] == 'terminal':
            (_, left), (_, right) = reference[1:]
            need(kind == KINDS[0] and removal['position']['samples'] == [self.terminal_count, self.terminal_count + 1]
                 and removal['start_at'] == left['at'] and removal['end_at'] == right['at'], 'terminal position mismatch')
            need(removal['position']['sample_sha256'] == [sha256(harvest._canonical(v)).hexdigest() for v in (left, right)],
                 'terminal sample hash mismatch')
            amounts = []
            for key, unit in zip(('terminal_carbohydrate', 'terminal_number'), UNITS):
                need(left['cumulative'][key]['unit'] == right['cumulative'][key]['unit'] == unit, 'cumulative unit changed')
                amounts.append(decimal_number(right['cumulative'][key]['value']) - decimal_number(left['cumulative'][key]['value']))
            self.terminal_count += 1
        else:
            index, event = reference[1]
            need(kind == KINDS[1] and index == self.event_count == removal['position']['event']
                 and removal['start_at'] == removal['end_at'] == event['at']
                 and removal['position']['event_sha256'] == sha256(harvest._canonical(event)).hexdigest(), 'event position mismatch')
            amounts = []
            for key, unit in zip(('fruit_carbohydrate', 'fruit_number'), UNITS):
                vector = event['removed'][key]
                need(len(vector) == 50 and all(v['unit'] == unit for v in vector), 'fruit vector/unit mismatch')
                amounts.append(sum((decimal_number(v['value']) for v in vector), Decimal(0)))
            for key in self.leaf_stem:
                need(event['removed'][key]['unit'] == UNITS[0], 'leaf/stem unit mismatch')
                self.leaf_stem[key] += decimal_number(event['removed'][key]['value'])
            self.event_count += 1
        order = (removal['end_at'], 0 if kind == KINDS[0] else 1)
        need(self.last_order is None or self.last_order < order, 'removal merge order mismatch')
        self.last_order = order
        for key, unit, exact in zip(KEYS, UNITS, amounts):
            q = removal[key]; value = decimal_number(q['value'])
            need(exact >= 0 and q['unit'] == unit and q['value'] == float(exact), 'original removal quantity mismatch')
            b = self.balance[kind][key]; b['original'] += exact; b['rounded'] += value
            b['budget'] += Decimal.from_float(ulp(q['value'])) / 2
        segments = [s for i, s in enumerate(self.mass['segments'])
                    if (s['start_at'] <= removal['start_at'] < removal['end_at'] <= s['end_at'] if kind == KINDS[0]
                        else s['start_at'] <= removal['start_at'] < s['end_at']
                        or i == len(self.mass['segments']) - 1 and removal['start_at'] == s['end_at'])]
        need(len(segments) == 1 and mass['parameters']['segment'] == segments[0], 'mass segment mismatch')
        segment = segments[0]
        carbon = decimal_number(removal['carbohydrate']['value']); count = decimal_number(removal['number']['value'])
        dry = carbon * decimal_number(segment['eta']['value']) / Decimal(1000000)
        fresh = dry / decimal_number(segment['dmc']['value'])
        need(mass['dry_matter'] == {'value': float(dry), 'unit': UNITS[2]}
             and mass['fresh_matter'] == {'value': float(fresh), 'unit': UNITS[3]}
             and mass['fresh_mass_per_equivalent'] == {'value': float(fresh / count) if count else None,
                                                       'unit': 'kg_FW/fruit_equivalent'}, 'independent mass conversion mismatch')
        expected = {**removal, 'dry_matter': mass['dry_matter'], 'fresh_matter': mass['fresh_matter']}
        rules = []
        for rule in self.allocation['rules']:
            s = rule['selector']
            if s['kind'] == kind and (s['first_sample'] <= removal['position']['samples'][0] < s['last_sample']
                                      if kind == KINDS[0] else s['event'] == removal['position']['event']):
                rules.append(rule)
        need(len(row['allocations']) == len(rules), 'allocation coverage mismatch')
        weights = []
        for part, rule in zip(row['allocations'], rules, strict=True):
            need(part['assignment_id'] == rule['assignment_id'] and part['purpose'] == rule['purpose']
                 and part['fraction'] == rule['fraction'], 'allocation selector/purpose/fraction mismatch')
            weights.append(Decimal(rule['fraction']['value']))
        unassigned = Decimal(1) - sum(weights, Decimal(0))
        need(unassigned >= 0, 'allocation exceeds one')
        exact_quantity(row['unassigned']['fraction'], unassigned, '1')
        parts = row['allocations'] + [{'purpose': 'unassigned', **row['unassigned']}]
        for part, weight in zip(parts, weights + [unassigned], strict=True):
            group = self.groups[kind][part['purpose']]; group['rows'] += 1
            for key, unit in zip(KEYS, UNITS, strict=True):
                value = decimal_number(expected[key]['value']) * weight
                exact_quantity(part['quantities'][key], value, unit)
                group['sums'][key] += value
            if part['purpose'] != 'unassigned':
                self.assignments[part['assignment_id']] += decimal_number(expected['fresh_matter']['value']) * weight
        self.rows += 1; self.chain.update(harvest._canonical(row) + b'\n')

    def finish(self, summary):
        need(summary['row_count'] == self.rows and summary['row_chain_sha256'] == self.chain.hexdigest(), 'summary chain/count mismatch')
        balances = {}
        for kind in KINDS:
            balances[kind] = {}
            for key, b in self.balance[kind].items():
                residual = abs(b['rounded'] - b['original'])
                need(residual <= b['budget'], 'independent cumulative rounding budget exceeded')
                balances[kind][key] = {'original_exact_decimal': str(b['original']),
                    'rounded_row_sum_exact_decimal': str(b['rounded']), 'absolute_residual_decimal': str(residual),
                    'half_ULP_sum_budget_decimal': str(b['budget']), 'within_budget': True}
            for purpose, group in self.groups[kind].items():
                actual = summary['totals_by_kind_and_purpose'][kind][purpose]
                need(actual['rows'] == group['rows'], 'summary purpose count mismatch')
                for key, unit in zip(KEYS, UNITS, strict=True):
                    exact_quantity(actual['quantities'][key], group['sums'][key], unit)
        for comparison in summary['observation_comparisons']:
            observation = comparison['observation']
            value = sum((self.assignments[k] for k in observation['assignment_ids']), Decimal(0))
            need(comparison['status'] == 'compared_synthetic_fixture', 'incomplete whole-fixture observation')
            exact_quantity(comparison['modeled_fresh_matter'], value, UNITS[3])
            exact_quantity(comparison['observed_minus_modeled'], decimal_number(observation['fresh_matter']['value']) - value, UNITS[3])
        return {'rows': self.rows, 'terminal_rows': self.terminal_count, 'event_rows': self.event_count,
                'row_chain_sha256': self.chain.hexdigest(), 'all_rows_independently_checked': True,
                'decimal_precision': 2200, 'balances': balances,
                'excluded_leaf_stem_exact_decimal_mg_CH2O_per_m2_floor': {k: str(v) for k, v in self.leaf_stem.items()}}


def profiles(archive):
    first = archive.index['samples'][0]['first_at']; last = archive.index['samples'][-1]['last_at']
    mass = mass_profile(archive.source)
    mass['revision'] = 'full166-synthetic-v1'
    mass['segments'][0].update(start_at=first, end_at=last)
    mass_raw = harvest._canonical(mass); parameters = harvest._mass_parameters(mass_raw)
    allocation = allocation_profile(parameters, last_sample=archive.counts['samples'] - 1,
                                    last_event=archive.counts['events'] - 1)
    allocation['revision'] = 'full166-synthetic-v1'
    allocation_raw = harvest._canonical(allocation)
    return mass_raw, allocation_raw


def audit(directory):
    started = perf_counter(); descriptors = fd_inventory()
    raw = (Path(__file__).resolve().parents[1] / RECEIPT).read_bytes()
    need(sha256(raw).hexdigest() == RECEIPT_SHA256, 'accepted receipt SHA mismatch')
    receipt = json.loads(raw); before = inventory(directory)
    need(all(before[k] == receipt['artifact_inventory'][k] for k in ('files', 'bytes')), 'accepted archive inventory mismatch')
    with original._Files(directory) as files, localcontext() as context:
        context.prec = 2200
        archive = Archive(files, receipt)
        mass_raw, allocation_raw = profiles(archive)
        parameters = harvest._mass_parameters(mass_raw)
        allocation = harvest._allocation_parameters(allocation_raw, parameters)
        checker = QuantityAudit(parameters[0], allocation[0]); packing = Packing(replay.LIMITS)
        def stream():
            for removal, reference in removals(archive.rows('samples'), archive.rows('events'), archive.source):
                row = harvest._allocation_row(harvest._mass_row(removal, parameters), allocation)
                checker.add(row, reference); packing.add(harvest._canonical(row))
                yield row
        summary = harvest._allocation_totals(stream(), allocation)
        quantities = checker.finish(summary); packing.flush()
        known = {'version': replay.VERSION, 'code_sha256': replay.CODE_SHA256, 'dependency_sha256': replay.DEPENDENCY_SHA256,
                 'limits': replay.LIMITS, 'source': archive.source, 'parameter_raw_utf8': mass_raw.decode(),
                 'allocation_raw_utf8': allocation_raw.decode(), 'pages': [
                     {k: p[k] for k in ('sha256', 'start', 'count')} for p in packing.pages],
                 'row_count': packing.count, 'row_chain_sha256': summary['row_chain_sha256'], 'summary': summary}
        # Byte accounting only; no fabricated query object is supplied to a writer.
        known_bytes = len(harvest._canonical(known)) + len(b',"query_identity":{}')
        capacity = packing.finish(root_known_bytes=known_bytes)
        need(checker.terminal_count == archive.counts['samples'] - 1 and checker.event_count == archive.counts['events'],
             'whole interval/event coverage mismatch')
        need(archive.hashes == archive.expected['candidate_row_sha256'], 'complete archive rows not checked')
        need(files._head() == (archive.head, archive.head_sha), 'archive HEAD changed')
        result = {'version': VERSION, 'scope': 'owned_synthetic_offline_quantity_capacity_only',
            'accepted_source_receipt_sha256': RECEIPT_SHA256, 'source': archive.source,
            'counts': archive.counts, 'original_row_sha256': archive.hashes, 'archive_HEAD_sha256': archive.head_sha,
            'parameter_raw_utf8': mass_raw.decode(), 'parameter_sha256': parameters[1],
            'allocation_raw_utf8': allocation_raw.decode(), 'allocation_sha256': allocation[1],
            'quantities': quantities, 'capacity': capacity, 'summary': summary}
    need(files.closed and inventory(directory) == before, 'original archive content/identity changed')
    need(fd_inventory() == descriptors, 'audit descriptor identity changed')
    result.update(archive_inventory=before, archive_preserved=True, FD_inventory_preserved=True,
                  wall_seconds=perf_counter() - started, RHS_calls=0, new_proof_or_publication_calls=0,
                  DB_or_HTTP_calls=0, actual_full_writer_accepted=False, current_rights_revalidated=False,
                  gate_state={g: 'not_assessed' for g in ('G0', 'G1', 'G2', 'G3a', 'G3b', 'G4')},
                  production_forecast_margin_ranking='hold')
    return result


def main():
    import argparse
    import socket
    import subprocess
    import psycopg
    from app import crop_cycle_calculation_result_evidence as evidence
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args()
    def forbidden(*a, **k):
        raise AssertionError('capacity audit attempted RHS, proof, publication, DB, HTTP or subprocess')
    with ExitStack() as stack:
        for module, name in ((original.engine.short._Evaluator, 'rhs'), (original.engine, 'advance_chunk'),
                             (original.ArtifactWriter, 'advance'), (replay, '_write'),
                             (evidence.CalculationResultEvidenceAuthority, 'issue'),
                             (harvest.current_query.CalculationCurrentCycleQuery, 'read'),
                             (psycopg, 'connect'), (socket, 'create_connection'), (subprocess, 'Popen')):
            stack.enter_context(patch.object(module, name, forbidden))
        result = audit(args.archive)
    raw = harvest._canonical(result)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fchmod(stream.fileno(), 0o400); os.fsync(stream.fileno())
    print(json.dumps({'version': VERSION, 'rows': result['quantities']['rows'],
                      'page_bytes': result['capacity']['packed_page_bytes'], 'holds': result['capacity']['hold_reasons'],
                      'result_sha256': sha256(raw).hexdigest(), 'wall_seconds': result['wall_seconds']}, sort_keys=True))
    return 2 if result['capacity']['hold_reasons'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
