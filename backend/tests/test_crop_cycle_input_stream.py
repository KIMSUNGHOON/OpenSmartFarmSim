from copy import deepcopy
from datetime import timedelta
from fractions import Fraction
import json
from pathlib import Path

import pytest

from app import crop_cycle_input_stream as stream
from app import crop_plant_startup_integration as physical
from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters

ROOT=Path(__file__).resolve().parents[2]
CASES=json.loads((ROOT/'fixtures/crop-plant-startup-integration-reference-v1.json').read_bytes())['cases']
PROFILES={
    'growth_profile':ReferenceParameters((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()),
    'cohort_profile':ReferenceFruitCohortParameters((ROOT/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()),
    'transport_profile':ReferenceFruitTransportParameters((ROOT/'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes()),
}


def program():return deepcopy(CASES[1]['program'])


def write(directory,p=None,outputs=None):
    p=p or program()
    return stream.write_input_packet(directory,initial_state=p['initial_state'],segments=iter(p['segments']),
        events=iter(p['events']),anchors=iter(p['output_times']),
        outputs=iter(p['output_times'] if outputs is None else outputs),solver=p['solver'],
        program_id='own-synthetic-software-test-v1',**PROFILES)


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['case_id'])
def test_original_short_program_records_clocks_and_boundaries_preserved(tmp_path,case):
    p=deepcopy(case['program']);before=deepcopy(p);path=tmp_path/'packet';receipt=write(path,p)
    expected,boundaries,planned=physical.legacy._prepare(p['initial_state'],p['segments'],p['events'],p['output_times'],p['solver'])
    with stream.open_input_packet(path,receipt['root_sha256'],**PROFILES) as reader:
        for kind in ('segments','events'):
            assert [reader.record(kind,i) for i in range(len(expected[kind]))]==expected[kind]
        assert reader.plan['planned_steps']==planned
        assert reader.manifest['initial_state']==expected['initial_state']
        rows=[];cursor=None
        while True:
            page=reader.boundary_page(cursor,limit=2);rows.extend(page['boundaries'])
            cursor=reader.restore_cursor(reader.cursor_bytes(page['cursor']))
            if page['complete']:break
        assert [row['at'] for row in rows]==[physical._stamp(t) for t in boundaries]
        assert [row['at'] for row in rows if row['output']]==p['output_times']
        assert [row['event'] for row in rows if row['event'] is not None]==expected['events']
        total=Fraction.from_float(float(p['initial_state']['values']['temperature_sum']['value']))
        for i,segment in enumerate(expected['segments']):
            actual=reader.segment(i);clock=actual['clock']
            assert actual['segment']==segment
            prefix=Fraction(int(clock['prefix']['numerator']),int(clock['prefix']['denominator']))
            slope=Fraction(int(clock['slope']['numerator']),int(clock['slope']['denominator']))
            assert prefix==total
            assert slope==Fraction.from_float(segment['forcing']['values']['canopy_temperature']['value'])/86400
            total+=slope*int((physical._utc(segment['end'])-physical._utc(segment['start'])).total_seconds())
    assert p==before and reader.closed


def test_display_subset_preserves_calculation_identity_and_original_grid(tmp_path):
    p=deepcopy(CASES[4]['program']);receipts=[write(tmp_path/'all',p),write(tmp_path/'ends',p,[p['output_times'][0],p['output_times'][-1]])]
    with stream.open_input_packet(tmp_path/'all',receipts[0]['root_sha256'],**PROFILES) as a, \
         stream.open_input_packet(tmp_path/'ends',receipts[1]['root_sha256'],**PROFILES) as b:
        assert a.calculation_sha256==b.calculation_sha256
        assert receipts[0]['root_sha256']!=receipts[1]['root_sha256']
        x=a.boundary_page()['boundaries'];y=b.boundary_page()['boundaries']
        assert [r['at'] for r in x]==[r['at'] for r in y]
        assert sum(r['output'] for r in y)==2 and len(x)>2


def test_existing_directory_is_not_modified(tmp_path):
    directory=tmp_path/'owned-by-user';directory.mkdir();marker=directory/'marker';marker.write_text('keep')
    with pytest.raises(stream.CycleInputRejected):write(directory)
    assert marker.read_text()=='keep'
