"""The research adapter must return the original complete stored load."""
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys

from app import crop_greenhouse_solar_storage as storage
import test_crop_greenhouse_solar_storage as reference

profiles = reference.profiles
ROOT = Path(__file__).resolve().parents[2]


def candidate():
    name = 'app._research_solar_json_load_adapter'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT/'research/solar-json-load-adapter.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            del sys.modules[name]
            raise
    return sys.modules[name]


def test_native_load_preserves_complete_original_bytes_and_references(profiles, tmp_path):
    adapter = candidate()
    binding, initial, chunks = reference.prepared(profiles, budget=3)
    reference.write(tmp_path, binding, initial, chunks)
    with storage._Files(tmp_path) as original:
        head, _ = original._head()
        expected = storage._canonical(original._load(head))
        expected_seen = set(original._seen)
        expected_bytes = original._referenced_bytes
    audit = {}
    with storage._Files(tmp_path) as reader:
        actual = storage._canonical(adapter.load(reader, head, audit=audit))
        assert actual == expected
        assert reader._seen == expected_seen
        assert reader._referenced_bytes == expected_bytes
    assert audit['cache_hits'] == head['commit_count'], audit
    assert audit['disposed'] and audit['raw_bytes_after_close'] == 0
    assert audit['peak_raw_bytes'] <= 1024**2


from contextlib import contextmanager
from copy import deepcopy
import json
import shutil
import types
import pytest


@pytest.fixture(scope='module')
def saved_archive(tmp_path_factory):
    directory = tmp_path_factory.mktemp('native-json-load-source')
    binding, initial, chunks = reference.prepared(reference.profiles.__wrapped__(), budget=3)
    reference.write(directory, binding, initial, chunks)
    return directory


@pytest.fixture
def archive(saved_archive, tmp_path):
    return Path(shutil.copytree(saved_archive, tmp_path/'artifact'))


def original_result(directory):
    with storage._Files(directory) as reader:
        head, _ = reader._head()
        return head, storage._canonical(reader._load(head)), set(reader._seen), reader._referenced_bytes


@contextmanager
def at_chain_root(action):
    monitoring = sys.monitoring
    slot = next(i for i in range(5, -1, -1) if monitoring.get_tool(i) is None)
    code = storage._need.__code__
    fired = []
    def enter(called, offset):
        frame = sys._getframe(1)
        if frame.f_locals['reason'] == 'COMMIT_HOLD: chain root':
            assert not fired
            fired.append(True)
            action()
    monitoring.use_tool_id(slot, 'solar-load-root-boundary')
    monitoring.register_callback(slot, monitoring.events.PY_START, enter)
    monitoring.set_local_events(slot, code, monitoring.events.PY_START)
    try:
        yield fired
    finally:
        monitoring.set_local_events(slot, code, 0)
        monitoring.register_callback(slot, monitoring.events.PY_START, None)
        monitoring.free_tool_id(slot)


def outcome(call):
    try:
        return ('value', storage._canonical(call()))
    except (storage.JointStorageHold, storage.files.CycleArtifactRejected, RuntimeError, TypeError, KeyError) as exc:
        return ('error', type(exc).__module__, type(exc).__qualname__, str(exc))


def test_installed_reader_method_preserves_native_dispatch(archive, monkeypatch):
    adapter = candidate()
    head, expected, seen, size = original_result(archive)
    audit = {}
    with monkeypatch.context() as changed:
        changed.setattr(storage._Files, '_load', adapter.load)
        with storage._Files(archive) as reader:
            assert storage._canonical(reader._load(head, audit=audit)) == expected
            assert reader._seen == seen and reader._referenced_bytes == size
    assert audit['cache_hits'] == head['commit_count']
    assert audit['disposed'] and audit['raw_bytes_after_close'] == 0


@pytest.mark.parametrize('field,value', [
    ('version', 'wrong'), ('header_sha256', '0'*64), ('sequence', True),
    ('sequence', -1), ('parent_commit_sha256', None),
    ('parent_commit_sha256', 1), ('unknown', 0), ('source_meta', None),
])
def test_real_commit_chain_errors_match_original(archive, field, value):
    adapter = candidate()
    with storage._Files(archive) as reader:
        head, _ = reader._head()
    path = archive/(head['latest_commit_sha256']+'.json')
    commit = json.loads(path.read_bytes())
    commit[field] = value
    raw = storage._canonical(commit)
    digest = sha256(raw).hexdigest()
    (archive/(digest+'.json')).write_bytes(raw)
    head['latest_commit_sha256'] = digest
    with storage._Files(archive) as reader:
        original = outcome(lambda: reader._load(head))
    audit = {}
    with storage._Files(archive) as reader:
        actual = outcome(lambda: adapter.load(reader, head, audit=audit))
    assert actual == original and actual[0] == 'error'
    assert audit['disposed'] and audit['raw_bytes_after_close'] == 0


@pytest.mark.parametrize('slot', ['_load', '_load_header', '_records', '_need', 'records_body', 'pristine_wrong_slot'])
def test_initial_foreign_method_uses_actual_original_path(archive, monkeypatch, slot):
    adapter = candidate()
    with storage._Files(archive) as reader:
        head, _ = reader._head()
    def rejected(*args, **kwargs):
        raise RuntimeError('actual changed method')
    with monkeypatch.context() as changed:
        if slot == 'records_body':
            changed.setattr(storage._Files._records, '__code__', rejected.__code__)
        elif slot == 'pristine_wrong_slot':
            changed.setattr(storage._Files, '_records', storage._Files._load_header)
        else:
            owner = storage if slot == '_need' else storage._Files
            changed.setattr(owner, slot, rejected)
        with storage._Files(archive) as reader:
            original = outcome(lambda: reader._load(head))
        audit = {}
        with storage._Files(archive) as reader:
            actual = outcome(lambda: adapter.load(reader, head, audit=audit))
    assert actual == original and actual[0] == 'error'
    assert audit['whole_load_fallback'] and audit['cache_hits'] == 0


@pytest.mark.parametrize('change', ['file_bytes', 'decoder', 'decoder_body', 'blob_method', 'records_method', 'hash_binding', 'canonical_binding', 'load_body'])
def test_late_changes_after_chain_validation_preserve_original(archive, monkeypatch, change):
    adapter = candidate()
    head, _, _, _ = original_result(archive)
    with storage._Files(archive) as reader:
        first_digest = reader._load(head)[2][0]
    target = archive/(first_digest+'.json')
    original_raw = target.read_bytes()
    results = []
    audits = []
    for selected in ('original', 'candidate'):
        audit = {}
        with monkeypatch.context() as changed:
            def rejected(*args, **kwargs):
                raise RuntimeError('late changed helper')
            def inject():
                if change == 'file_bytes':
                    target.chmod(0o600)
                    target.write_bytes(original_raw+b' ')
                elif change == 'decoder':
                    changed.setattr(storage.files, '_json', rejected)
                elif change == 'decoder_body':
                    changed.setattr(storage.files._json, '__code__', rejected.__code__)
                elif change == 'blob_method':
                    changed.setattr(storage.files._Files, '_blob', rejected)
                elif change == 'records_method':
                    changed.setattr(storage._Files, '_records', rejected)
                elif change == 'hash_binding':
                    changed.setattr(storage, '_hash', rejected)
                elif change == 'canonical_binding':
                    changed.setattr(storage, '_canonical', rejected)
                else:
                    changed.setattr(storage._Files._load, '__code__', rejected.__code__)
            try:
                with storage._Files(archive) as reader, at_chain_root(inject) as fired:
                    call = (lambda: reader._load(head)) if selected == 'original' else (lambda: adapter.load(reader, head, audit=audit))
                    results.append(outcome(call))
                    assert fired == [True]
            finally:
                if change == 'file_bytes':
                    target.write_bytes(original_raw)
        audits.append(audit)
    assert results[0] == results[1]
    assert results[0][0] == ('value' if change == 'load_body' else 'error')
    assert audits[1]['disposed'] and audits[1]['raw_bytes_after_close'] == 0


def test_unsupported_initial_hash_keeps_original_error_and_does_not_reuse(archive, monkeypatch):
    adapter = candidate()
    with storage._Files(archive) as reader:
        head, _ = reader._head()
    def rejected(*args):
        raise RuntimeError('initial custom hash')
    with monkeypatch.context() as changed:
        changed.setattr(storage, '_hash', rejected)
        with storage._Files(archive) as reader:
            expected = outcome(lambda: reader._load(head))
        audit = {}
        with storage._Files(archive) as reader:
            actual = outcome(lambda: adapter.load(reader, head, audit=audit))
    assert actual == expected and actual[0] == 'error'
    assert audit['cache_hits'] == 0 and audit['disposed']


@pytest.mark.parametrize('failure', ['first-event', 'last-event', 'interval'])
def test_original_physical_hold_preserves_all_confirmed_rows_and_failed_utc(profiles, tmp_path, monkeypatch, failure):
    adapter = candidate()
    case = deepcopy(reference.reference.reference.CASES[0 if failure == 'interval' else 6])
    if failure == 'interval':
        case['scenario']['forcing']['canopy_non_solar_heat']['value'] = 1e7
    else:
        case['events'][0 if failure == 'first-event' else -1]['event']['values']['leaf']['value'] = 50000
    binding, initial, chunks = reference.prepared(profiles, case)
    reference.write(tmp_path, binding, initial, chunks)
    reference.reference.forbid_numerics(monkeypatch)
    head, expected, seen, size = original_result(tmp_path)
    audit = {}
    with storage._Files(tmp_path) as reader:
        value = adapter.load(reader, head, audit=audit)
        assert storage._canonical(value) == expected
        assert value[4]['status'] == 'hold' and value[3] is None
        assert reader._seen == seen and reader._referenced_bytes == size
    assert audit['cache_hits'] == head['commit_count']
    assert audit['disposed'] and audit['raw_bytes_after_close'] == 0
