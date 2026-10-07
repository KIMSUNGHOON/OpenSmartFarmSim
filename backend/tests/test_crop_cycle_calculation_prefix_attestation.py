"""Actual signed continuation: fresh delta QC and current historical bytes."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import importlib.util
import json
import os
from pathlib import Path

import pytest

from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_prefix as prefix
from test_crop_cycle_calculation_server_custody import (
    journal_setup, open_journal, close_journal, engine, custody, KEY, BUDGET)

SMALL = {'max_steps':17, 'max_transitions':31}


def write_private(path, raw):
    path.chmod(0o600); path.write_bytes(raw); path.chmod(0o400)


def selected_proof(setup, progress):
    return setup[1]/'proofs'/(progress['head_sha256']+'.json')


def test_reopening_three_advances_validates_only_each_actual_new_delta(journal_setup, monkeypatch):
    validations = []; loads = []; counts = []
    validate = artifact._validate_delta
    load = artifact._Files._load_prefix
    def measured(*args, **kwargs):
        validations.append(args[2]['steps'])
        return validate(*args, **kwargs)
    def loaded(*args, **kwargs):
        loads.append(True)
        return load(*args, **kwargs)
    monkeypatch.setattr(artifact, '_validate_delta', measured)
    monkeypatch.setattr(artifact._Files, '_load_prefix', loaded)
    budget = SMALL
    for _ in range(3):
        start = len(validations)
        journal = open_journal(journal_setup)
        try:
            progress = json.loads(journal.advance(budget))
            checkpoint = deepcopy(journal.writer._checkpoint)
        finally:
            close_journal(journal)
        counts.append(len(validations)-start)
    expected = engine._start(journal_setup[2])
    for _ in range(3):
        expected = engine.advance_chunk(journal_setup[2], expected, budget)['checkpoint']
    assert checkpoint == expected and progress['steps'] == expected['steps']
    assert counts == [2, 2, 2], {'delta_validations':counts, 'historical_prefix_loads':len(loads)}
    assert not loads


@pytest.mark.parametrize('kind', ['version', 'code', 'checkpoint', 'confirmed', 'summary',
                                'counts', 'bool-count', 'extra', 'missing', 'old-domain'])
def test_resealed_invalid_validation_claim_cannot_restore(journal_setup, monkeypatch, kind):
    journal = open_journal(journal_setup)
    try:
        progress = json.loads(journal.advance(SMALL))
    finally:
        close_journal(journal)
    path = selected_proof(journal_setup, progress)
    body = json.loads(path.read_bytes())['payload']; value = body['validation']
    if kind == 'version': value['version'] = 'crop-cycle-verified-prefix-validation-v0'
    if kind == 'code': value['validation_code_sha256'] = '0'*64
    if kind == 'checkpoint': value.update(checkpoint_sha256='0'*64, confirmed_checkpoint_sha256='0'*64)
    if kind == 'confirmed': value['confirmed_checkpoint_sha256'] = '0'*64
    if kind == 'summary': value['summary_sha256'] = '0'*64
    if kind == 'counts': value['counts']['samples'] += 1
    if kind == 'bool-count': value['counts']['samples'] = True
    if kind == 'extra': value['approved'] = True
    if kind == 'missing': del value['counts']
    domain = b'ossf-crop-cycle-verified-server-head-v1\0' if kind == 'old-domain' else custody.PROOF_DOMAIN
    write_private(path, custody._signed(body, KEY, domain))
    monkeypatch.setattr(engine, 'advance_chunk', lambda *a: pytest.fail('bad claim reached equations'))
    with pytest.raises(custody.CalculationCustodyHold): open_journal(journal_setup, create=False)


def test_fresh_resume_and_repeated_inspect_hash_current_pages_without_historical_qc(journal_setup, monkeypatch):
    journal = open_journal(journal_setup)
    try:
        progress = journal.advance(SMALL)
    finally:
        close_journal(journal)
    calls = []; original = prefix._current_blob
    def measured(*args, **kwargs):
        calls.append(args[1]); return original(*args, **kwargs)
    def forbidden(*args, **kwargs): pytest.fail('history read evaluated equations or physical delta QC')
    monkeypatch.setattr(prefix, '_current_blob', measured)
    monkeypatch.setattr(artifact, '_validate_delta', forbidden)
    monkeypatch.setattr(artifact._Files, '_load_prefix', forbidden)
    monkeypatch.setattr(engine.short._Evaluator, 'rhs', forbidden)
    fresh = open_journal(journal_setup, create=False)
    try:
        head, _ = fresh.writer._head()
        chunk = json.loads((journal_setup[1]/'artifact'/(head['latest_commit_sha256']+'.json')).read_bytes())
        page = chunk['pages']['samples'][0]['sha256']; before = calls.count(page)
        assert before > 0
        assert fresh.inspect() == progress and calls.count(page) > before
        before = calls.count(page)
        assert fresh.inspect() == progress and calls.count(page) > before
    finally:
        close_journal(fresh)


@pytest.mark.parametrize('operation', ['inspect', 'advance', 'reopen'])
def test_same_size_mtime_historical_page_tamper_never_returns_success(journal_setup, monkeypatch, operation):
    journal = open_journal(journal_setup)
    try:
        journal.advance(SMALL); head, _ = journal.writer._head()
        chunk = json.loads((journal_setup[1]/'artifact'/(head['latest_commit_sha256']+'.json')).read_bytes())
        path = journal_setup[1]/'artifact'/(chunk['pages']['samples'][0]['sha256']+'.json')
        raw = path.read_bytes(); before = path.stat()
        write_private(path, raw[:-1]+b'}'); os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        assert path.stat().st_size == before.st_size and path.stat().st_mtime_ns == before.st_mtime_ns
        monkeypatch.setattr(engine, 'advance_chunk', lambda *a: pytest.fail('changed history reached equations'))
        if operation == 'reopen':
            close_journal(journal); journal = None
            with pytest.raises(custody.CalculationCustodyHold): open_journal(journal_setup, create=False)
        else:
            with pytest.raises(custody.CalculationCustodyHold):
                journal.inspect() if operation == 'inspect' else journal.advance(SMALL)
    finally:
        if journal is not None: close_journal(journal)


def test_snapshot_is_frozen_detached_and_caller_dict_is_rejected(journal_setup):
    journal = open_journal(journal_setup)
    try:
        journal.advance(SMALL); head, _ = journal.writer._head(); snapshot, _ = journal._prefix(head)
        with pytest.raises(FrozenInstanceError): snapshot.hashes = ()
        hashes, cp, summary, claim = prefix.unpack(snapshot, journal.context, head)
        cp['y'][0] = 999; summary['steps'] = 999; claim['counts']['samples'] = 999; hashes.clear()
        restored = prefix.unpack(snapshot, journal.context, head)
        assert restored[0] and restored[1] == journal.writer._checkpoint and restored[2] == journal.writer._summary
        assert restored[3]['counts']['samples'] != 999
        with pytest.raises(artifact.CalculationArtifactHold): prefix.unpack({'hashes':hashes}, journal.context, head)
    finally:
        close_journal(journal)


@pytest.mark.parametrize('field', ['checkpoint', 'summary', 'hashes'])
def test_mutable_writer_state_cannot_authorize_another_delta(journal_setup, monkeypatch, field):
    journal = open_journal(journal_setup)
    try:
        journal.advance(SMALL); before = (journal_setup[1]/'artifact/HEAD').read_bytes()
        if field == 'checkpoint': journal.writer._checkpoint['y'][0] += 1
        if field == 'summary': journal.writer._summary['status'] = 'completed'
        if field == 'hashes': journal.writer._hashes.append('0'*64)
        monkeypatch.setattr(engine, 'advance_chunk', lambda *a: pytest.fail('mutable state reached equations'))
        with pytest.raises(custody.CalculationCustodyHold): journal.advance(SMALL)
        assert (journal_setup[1]/'artifact/HEAD').read_bytes() == before
    finally:
        close_journal(journal)


def test_publisher_independently_rejects_new_delta_when_writer_validation_is_bypassed(journal_setup, monkeypatch):
    journal = open_journal(journal_setup)
    before = (journal_setup[1]/'artifact/HEAD').read_bytes(); calls = []
    calculate = engine.advance_chunk; validate = artifact._validate_delta
    def invalid(*args, **kwargs):
        result = calculate(*args, **kwargs); result['steps'] = True; return result
    def bypass_first(*args, **kwargs):
        calls.append(True)
        return args[2]['checkpoint'] if len(calls) == 1 else validate(*args, **kwargs)
    monkeypatch.setattr(engine, 'advance_chunk', invalid)
    monkeypatch.setattr(artifact, '_validate_delta', bypass_first)
    try:
        with pytest.raises(custody.CalculationCustodyHold): journal.advance(SMALL)
        assert len(calls) == 2 and (journal_setup[1]/'artifact/HEAD').read_bytes() == before
        assert len(list((journal_setup[1]/'proofs').glob('*.json'))) == 1
    finally:
        close_journal(journal)


def test_page_changed_after_proof_fsync_cannot_select_new_head(journal_setup, monkeypatch):
    journal = open_journal(journal_setup); before = (journal_setup[1]/'artifact/HEAD').read_bytes()
    original = custody._immutable
    def changed(parent, name, raw, maximum, temporary):
        value = original(parent, name, raw, maximum, temporary)
        if temporary == '.proof-' and json.loads(raw)['payload']['action'] == 'advance':
            head = json.loads(raw)['payload']['head']; directory = journal_setup[1]/'artifact'
            chunk = json.loads((directory/(head['latest_commit_sha256']+'.json')).read_bytes())
            path = directory/(chunk['pages']['samples'][0]['sha256']+'.json')
            write_private(path, path.read_bytes()[:-1]+b'}')
        return value
    monkeypatch.setattr(custody, '_immutable', changed)
    try:
        with pytest.raises(custody.CalculationCustodyHold): journal.advance(SMALL)
        assert (journal_setup[1]/'artifact/HEAD').read_bytes() == before
    finally:
        close_journal(journal)


def test_observer_counts_whole_current_bytes_and_restores_wrappers_after_exception(journal_setup):
    path = Path(__file__).resolve().parents[2]/'research/crop-cycle-calculation-prefix-cost.py'
    spec = importlib.util.spec_from_file_location('prefix_attestation_costs', path)
    observer = importlib.util.module_from_spec(spec); spec.loader.exec_module(observer)
    originals = (prefix.read_authenticated, prefix._current_blob, prefix.validate_advance,
        artifact._validate_delta, artifact._Files._load_prefix, engine.advance_chunk, engine.short._Evaluator.rhs)
    journal = open_journal(journal_setup)
    try:
        journal.advance(SMALL)
        with pytest.raises(RuntimeError, match='own observation interruption'):
            with observer.observation() as costs:
                journal.inspect()
                assert costs.values['prefix.authenticated_read']['calls'] > 0
                assert costs.values['prefix.current_blob']['successful_bytes'] > 0
                assert costs.values.get('artifact.delta_qc', {}).get('calls', 0) == 0
                assert costs.values.get('artifact.prefix_verify', {}).get('calls', 0) == 0
                raise RuntimeError('own observation interruption')
        assert originals == (prefix.read_authenticated, prefix._current_blob, prefix.validate_advance,
            artifact._validate_delta, artifact._Files._load_prefix, engine.advance_chunk, engine.short._Evaluator.rhs)
        assert not costs.stack
    finally:
        close_journal(journal)


def test_resume_checks_current_input_after_authenticated_prefix_read(journal_setup, monkeypatch):
    from test_crop_cycle_calculation_recheck_cost import change_input
    journal = open_journal(journal_setup)
    try:
        journal.advance(SMALL)
    finally:
        close_journal(journal)
    original = prefix.read_authenticated
    def changed(*args, **kwargs):
        value = original(*args, **kwargs)
        change_input(journal_setup[2], 'block')
        return value
    monkeypatch.setattr(prefix, 'read_authenticated', changed)
    reopened = None
    try:
        with pytest.raises(custody.CalculationCustodyHold):
            reopened = open_journal(journal_setup, create=False)
        assert journal_setup[2].reader.closed and not journal_setup[2]._cache
    finally:
        if reopened is not None: close_journal(reopened)
