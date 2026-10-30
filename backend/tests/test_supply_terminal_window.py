"""Original stored cohorts/terminal transfers, not a new crop run."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore
from app import crop_supply_terminal_window as terminal

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / 'web/public/supply-morphology-replay/own-public-v1'
ARTIFACT = '84daf00c44a964f904aa0b78e2c64f44c2753ec97641f23566fdfcc349bf4476'
MASS, NUMBER = 'mg_CH2O/m2_floor', 'fruits_equivalent/m2_floor'


@pytest.fixture(scope='module')
def original(tmp_path_factory):
    index = json.loads((PUBLIC/'index.json').read_bytes())
    assert index['artifact_sha256'] == ARTIFACT
    access = ContentAccess(os.getuid(), os.getgid())
    directory = tmp_path_factory.mktemp('supply-terminal')/'cas'
    with MorphologyBlobStore(directory, access, write=True) as store:
        for item in [index['root'], *index['blobs']]:
            raw = (PUBLIC/item['path']).read_bytes()
            assert len(raw) == item['bytes'] and sha256(raw).hexdigest() == item['sha256']
            assert store.put(raw, maximum=16*1024**2) == item['sha256']
    frames = [json.loads((PUBLIC/f'frame-{i}.json').read_bytes())['frame'] for i in range(38)]
    root = json.loads((PUBLIC/'root.json').read_bytes())
    contexts = [json.loads((directory/s['context']['sha256']).read_bytes()) for s in root['segments']]
    return directory, access, frames, contexts


def read(original, **window):
    directory, access, *_ = original
    return terminal.read_supply_terminal_window(directory, access, ARTIFACT, **window)


def decimal_exact(q):
    return Decimal(q['numerator'])/Decimal(q['denominator'])


def expected_lifetime(original, frame):
    directory, _, _, contexts = original
    if frame['checkpoint_sha256'] is not None:
        return json.loads((directory/frame['checkpoint_sha256']).read_bytes())['lifetime_transfers_exact']
    # A material point preserves these two physical counters. Read the separately
    # stored successor seed at the same point; do not call the new projection.
    matches = [c['descriptor']['seed']['lifetime_transfers_exact'] for c in contexts
               if c['descriptor']['seed']['initial_sample']['at'] == frame['at']
               and c['descriptor']['seed']['event_sequence'] == frame['event_sequence']+1]
    assert len(matches) == 1
    return matches[0]


def test_authentic_all38_cohorts_exact_counters_and_telescope(original):
    result = read(original)
    assert result['schema_version'] == 'supply-terminal-window-v1'
    assert result['scope'] == 'software_research_only'
    assert result['claim_scope'] == 'synthetic_terminal_quantities_only'
    assert result['G0_G4'] == 'not_assessed' and result['R2'] == 'not_approved'
    assert result['source']['artifact_sha256'] == ARTIFACT
    assert result['source']['terminal'] == {'hold': None, 'status': 'completed'}
    assert len(result['frames']) == 38 and len(result['intervals']) == 37
    assert len(json.dumps(result).encode()) <= 2*1024**2
    with localcontext() as ctx:
        ctx.prec = 2200
        for actual, source in zip(result['frames'], original[2], strict=True):
            assert actual['at'] == source['at'] and actual['phase'] == source['phase']
            for key in ['index','context_sha256','checkpoint_sha256','receipt_sha256',
                        'event_sequence','output_cursor','output_prefix_sha256']:
                assert actual['reference'][key] == source[key]
            state = source['snapshot']['state']
            assert actual['fruit_carbohydrate'] == {'unit': MASS, 'values': state[3:53]}
            assert actual['fruit_number'] == {'unit': NUMBER, 'values': state[53:103]}
            assert decimal_exact(actual['carbohydrate_stock_exact']) == sum(map(Decimal.from_float,state[3:53]))
            assert decimal_exact(actual['number_stock_exact']) == sum(map(Decimal.from_float,state[53:103]))
            lifetime = expected_lifetime(original, source)
            assert actual['terminal_carbohydrate_exact'] == lifetime['terminal_carbon']
            assert actual['terminal_number_exact'] == lifetime['terminal_number']
        zero = 0
        for row, left, right in zip(result['intervals'], result['frames'][:-1], result['frames'][1:], strict=True):
            assert row['from_frame'] == left['reference'] and row['to_frame'] == right['reference']
            assert row['start_at'] == left['at'] and row['end_at'] == right['at']
            for target, key in [('carbohydrate_exact','terminal_carbohydrate_exact'),('number_exact','terminal_number_exact')]:
                assert decimal_exact(row[target]) == decimal_exact(right[key])-decimal_exact(left[key])
            if row['start_at'] == row['end_at']:
                zero += 1
                assert row['kind'] == 'zero_duration_material_boundary'
                assert decimal_exact(row['carbohydrate_exact']) == decimal_exact(row['number_exact']) == 0
            else:
                assert row['kind'] == 'model_terminal_outflow'
        assert zero == 5
        before, after = result['frames'][0], result['frames'][-1]
        for key in ['terminal_carbohydrate_exact','terminal_number_exact']:
            field = 'carbohydrate_exact' if key == 'terminal_carbohydrate_exact' else 'number_exact'
            expected = decimal_exact(after[key])-decimal_exact(before[key])
            assert decimal_exact(result['totals'][key]) == expected
            assert sum(decimal_exact(row[field]) for row in result['intervals']) == expected


@pytest.mark.parametrize('first,last',[(0,0),(37,37),(3,9),(10,25)])
def test_original_inclusive_window_and_nonzero_baseline(original, first, last):
    result = read(original, first_frame=first, last_frame=last)
    assert [f['reference']['index'] for f in result['frames']] == list(range(first,last+1))
    assert result['window'] == {'first_frame':first,'last_frame':last,
                                'start_at':original[2][first]['at'],'end_at':original[2][last]['at']}
    assert len(result['intervals']) == last-first
    if first == last:
        assert result['totals']['terminal_carbohydrate_exact']['numerator'] == '0'
        assert result['totals']['terminal_number_exact']['numerator'] == '0'


@pytest.mark.parametrize('window',[
    {'first_frame':True},{'first_frame':-1},{'first_frame':38},{'first_frame':None},
    {'first_frame':'0'},{'last_frame':False},{'last_frame':38},{'last_frame':1.0},
    {'first_frame':8,'last_frame':7},
])
def test_invalid_window_never_returns_a_projection(original,window):
    with pytest.raises(terminal.SupplyTerminalHold):
        read(original,**window)


def test_returned_copies_cannot_change_the_next_read(original):
    first = read(original,first_frame=2,last_frame=3)
    expected = deepcopy(first)
    first['frames'][0]['fruit_carbohydrate']['values'][0] = 987654321.
    first['source']['source_rights'].clear()
    first['intervals'][0]['carbohydrate_exact']['numerator'] = '999'
    assert read(original,first_frame=2,last_frame=3) == expected


def test_terminal_differences_reject_reverse_or_invalid_boundaries(original):
    frames = read(original)['frames']
    left, right = next((a,b) for a,b in zip(frames,frames[1:]) if a['at'] == b['at'])
    changes = [
        ('at', {**right['at'],'time_origin_utc':'2020-01-02T00:00:00Z'}),
        ('at', {**right['at'],'elapsed_seconds_exact':{'numerator':'-1','denominator':'1','unit':'s'}}),
        ('terminal_carbohydrate_exact', {'numerator':'-1','denominator':'1','unit':MASS}),
        ('terminal_number_exact', {'numerator':'-1','denominator':'1','unit':NUMBER}),
        ('terminal_carbohydrate_exact', {'numerator':'999999999','denominator':'1','unit':MASS}),
        ('terminal_number_exact', {'numerator':'1','denominator':'1','unit':'kg'}),
        ('phase', left['phase']),
    ]
    for field, value in changes:
        changed = {**right,field:value}
        with pytest.raises(ValueError):
            terminal._interval(left,changed)


def test_current_file_policy_change_is_rejected(original):
    path = original[0]/ARTIFACT
    path.chmod(0o600)
    try:
        with pytest.raises(terminal.SupplyTerminalHold):
            read(original)
    finally:
        path.chmod(0o640)


def test_late_source_change_after_parent_validation_clears_everything(original,monkeypatch):
    path = original[0]/ARTIFACT
    raw = path.read_bytes()
    project = terminal._stock_frame
    changed = False
    def mutate(*args,**kwargs):
        nonlocal changed
        result = project(*args,**kwargs)
        if not changed:
            changed = True
            path.write_bytes(raw+b' ')
        return result
    monkeypatch.setattr(terminal,'_stock_frame',mutate)
    try:
        with pytest.raises(terminal.SupplyTerminalHold):
            read(original)
        assert changed
    finally:
        path.write_bytes(raw)


def test_own_code_identity_is_current(original,monkeypatch):
    monkeypatch.setattr(terminal,'CODE_SHA256','0'*64)
    with pytest.raises(terminal.SupplyTerminalHold):
        read(original)
