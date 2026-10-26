from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from app import crop_funded_shoot_clock as clock
from app.crop_leaf_funded_birth_artifact_producer import produce_funded_leaf_artifact
from app.crop_leaf_funded_birth_artifact_reader import read_funded_leaf_frame, read_funded_leaf_manifest
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_leaf_funded_birth_artifact import calculated_inputs, profiles
from test_crop_leaf_carbon_stock_artifact import ACCESS, encoded

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def sources(tmp_path_factory, profiles):
    base = tmp_path_factory.mktemp('funded-shoot-clock'); leaf_cases = []
    stem_program = (ROOT/'web/public/morphology-rational-replay/input.json').read_bytes()
    stem_root = produce_rational_morphology_artifact(base/'stem', ACCESS, program_raw=stem_program)
    for case in range(6):
        inputs, _ = calculated_inputs(profiles, case, steps=(0,2), dt=1/3, count=4)
        directory = base/str(case)
        root = produce_funded_leaf_artifact(directory, ACCESS, inputs_raw=encoded(inputs), **profiles)
        leaf_cases.append((directory, root))
    return base/'stem', stem_root, leaf_cases


def derived(sources, case=0):
    stem, stem_root, leaves = sources; directory, root = leaves[case]
    return clock.derive_funded_shoot_clock(directory, stem, ACCESS, leaf_root_sha256=root, stem_root_sha256=stem_root)


def frac(q): return Fraction(int(q['numerator']), int(q['denominator']))


def snapshot(directory):
    return {p.name: (p.stat().st_mode,p.stat().st_mtime_ns,p.stat().st_ctime_ns,sha256(p.read_bytes()).hexdigest()) for p in directory.iterdir()}


@pytest.mark.parametrize('case', range(6))
def test_real_funded_samples_preserve_phases_and_use_original_dynamic_air_integral(sources, case):
    directory, root = sources[2][case]; before = snapshot(directory); result = derived(sources, case)
    assert result['G0_G4'] == 'not_assessed' and result['leaf_artifact_sha256'] == root
    assert result['stem_artifact_sha256'] == sources[1] and len(result['frames']) == 7
    for index, frame in enumerate(result['frames']):
        original = read_funded_leaf_frame(directory, ACCESS, root, index=index)
        assert {k: frame[k] for k in ('index','step_index','phase','event_sequence','checkpoint_sha256','at')} == {k: original[k] for k in ('index','step_index','phase','event_sequence','checkpoint_sha256','at')}
        integral = Fraction.from_float(original['integrated_transfers']['indoor_air_temperature_time']['value'])
        elapsed = frac(original['at']['elapsed_seconds_exact'])
        expected = (integral - Fraction(5)*elapsed)/86400
        assert frac(frame['shoot_age_exact']) == expected
        assert frame['air_temperature_integral'] == original['integrated_transfers']['indoor_air_temperature_time']
        assert len(frame['initial_internodes']) == 3
        assert all(frac(node['age_exact']) == expected for node in frame['initial_internodes'])
    assert result['frames'][0]['shoot_age_exact'] == result['frames'][1]['shoot_age_exact']
    assert result['frames'][3]['shoot_age_exact'] == result['frames'][4]['shoot_age_exact']
    assert snapshot(directory) == before


@pytest.mark.parametrize('kind', ['negative-age','different-origin','different-initial-at','false-rights','missing-transfer','wrong-unit','same-time-transfer','code'])
def test_mismatch_denied_without_claiming_the_original_fixed_air_pose_is_coupled(sources, monkeypatch, kind):
    read = clock.leaf.read_funded_leaf_frame; manifest = clock.stem.read_rational_morphology_manifest
    if kind in ('different-origin','different-initial-at'):
        original = clock.stem._parse
        def altered(raw, maximum):
            value = original(raw, maximum)
            if 'initial_state' in value:
                value = deepcopy(value); key = 'started_at' if kind == 'different-origin' else 'at'
                value['initial_state']['timeline_state'][key] = '2026-09-30T00:00:00Z'
            return value
        monkeypatch.setattr(clock.stem,'_parse',altered)
    elif kind == 'false-rights':
        def denied(*a,**k):
            value = manifest(*a,**k); value['program_rights']['display'] = False; return value
        monkeypatch.setattr(clock.stem,'read_rational_morphology_manifest',denied)
    elif kind == 'code': monkeypatch.setattr(clock,'CODE_SHA256','0'*64)
    else:
        def altered(*a,**k):
            value = read(*a,**k)
            if value['index'] in (1,6):
                row=value['integrated_transfers']['indoor_air_temperature_time']
                if kind == 'negative-age': row['value']=-100.
                elif kind == 'missing-transfer': del value['integrated_transfers']['indoor_air_temperature_time']
                elif kind == 'wrong-unit': row['unit']='degC'
                elif kind == 'same-time-transfer': row['value']=1.
            return value
        monkeypatch.setattr(clock.leaf,'read_funded_leaf_frame',altered)
    with pytest.raises(clock.FundedShootClockHold): derived(sources)


def test_no_growth_DB_CLI_network_or_writes_and_detached_results(sources, monkeypatch):
    import subprocess,socket,psycopg
    calls=[]
    def forbidden(*a,**k): calls.append(1); raise AssertionError('read-only clock derivation')
    monkeypatch.setattr(subprocess,'Popen',forbidden);monkeypatch.setattr(socket,'socket',forbidden);monkeypatch.setattr(psycopg,'connect',forbidden)
    monkeypatch.setattr(MorphologyBlobStore,'put',forbidden)
    original_open=os.open
    def readonly(path,flags,*a,**k):
        if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):return forbidden()
        return original_open(path,flags,*a,**k)
    monkeypatch.setattr(os,'open',readonly)
    result=derived(sources);result['frames'][0]['shoot_age_exact']['numerator']='99'
    assert derived(sources)['frames'][0]['shoot_age_exact']['numerator']=='0' and calls==[]


def test_dynamic_air_is_not_replaced_by_constant_22_degree_stem_forcing(sources):
    result=derived(sources);end=result['frames'][-1]
    assert frac(end['shoot_age_exact']) != Fraction(17)*frac(end['at']['elapsed_seconds_exact'])/86400
    assert result['stem_pose_after_initial']=='not_bound_to_this_clock' and result['new_internode_events']=='not_calculated'


@pytest.mark.parametrize('kind',['rights','code','program','capacity'])
def test_final_source_rights_code_and_bounded_result_fences(sources,monkeypatch,kind):
    if kind=='rights':
        read=clock.stem.read_rational_morphology_manifest;calls=[]
        def changed(*a,**k):
            value=read(*a,**k);calls.append(1)
            if len(calls)>1:value['program_rights']['display']=False
            return value
        monkeypatch.setattr(clock.stem,'read_rational_morphology_manifest',changed)
    elif kind=='code':
        pins=clock._pins;calls=[]
        def changed():
            value=pins();calls.append(1)
            if len(calls)>1:value[next(iter(value))]='0'*64
            return value
        monkeypatch.setattr(clock,'_pins',changed)
    elif kind=='program':
        read=MorphologyBlobStore.get;calls=[]
        target=clock.stem.read_rational_morphology_manifest(sources[0],ACCESS,sources[1])['program_sha256']
        def changed(self,digest,**kwargs):
            value=read(self,digest,**kwargs)
            if digest==target:
                calls.append(1)
                if len(calls)>2:return value+b' '
            return value
        monkeypatch.setattr(MorphologyBlobStore,'get',changed)
    else:monkeypatch.setattr(clock,'MAX_BYTES',1024)
    with pytest.raises(clock.FundedShootClockHold):derived(sources)
