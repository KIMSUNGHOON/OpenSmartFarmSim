from copy import deepcopy
from datetime import timedelta
from fractions import Fraction
from hashlib import sha256
import json
import os
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


def long_program(count=257):
    p=program();base=p['segments'][0];begin=physical._utc(base['start']);segments=[]
    for i in range(count):
        segment=deepcopy(base);segment['start']=physical._stamp(begin+timedelta(seconds=i*300))
        segment['end']=physical._stamp(begin+timedelta(seconds=(i+1)*300))
        segment['forcing']['values']['canopy_temperature']['value']=(.1,.3,20.1)[i%3]
        segments.append(segment)
    p['segments']=segments;p['events']=[];p['solver']['max_steps']=40000000
    p['output_times']=[segments[0]['start'],segments[-1]['end']]
    return p


def test_cross_block_clock_prefix_and_random_records_preserve_original_fraction(tmp_path):
    p=long_program();path=tmp_path/'packet';receipt=write(path,p)
    with stream.open_input_packet(path,receipt['root_sha256'],**PROFILES) as reader:
        root=reader.manifest;assert [b['count'] for b in root['streams']['segments']['blocks']]==[128,128,1]
        total=Fraction.from_float(float(p['initial_state']['values']['temperature_sum']['value']))
        for i,s in enumerate(p['segments']):
            if i in (0,127,128,255,256):
                actual=reader.segment(i);prefix=actual['clock']['prefix']
                assert Fraction(int(prefix['numerator']),int(prefix['denominator']))==total
                assert float(total).hex()==float(Fraction(int(prefix['numerator']),int(prefix['denominator']))).hex()
                assert actual['segment']==s
            total+=Fraction.from_float(s['forcing']['values']['canopy_temperature']['value'])*Fraction(300,86400)
        changed=reader.record('segments',128);changed['forcing']['values']['canopy_temperature']['value']=999
        assert reader.record('segments',128)==p['segments'][128]
        changed=reader.manifest;changed['scope']='changed'
        assert reader.manifest['scope']=='software_research_only'
        assert reader.plan['planned_steps']==257*300


@pytest.mark.parametrize('kind',['gap','overlap','duplicate-anchor','unordered-output','not-anchor','outside-event','wrong-unit',
    'bool','array','reference-origin','step-budget','long-period'])
def test_invalid_input_is_rejected_and_owned_partial_directory_removed(tmp_path,kind):
    p=long_program(129);path=tmp_path/'packet';outputs=None
    if kind=='gap':p['segments'][128]['start']=physical._stamp(physical._utc(p['segments'][128]['start'])+timedelta(seconds=1))
    if kind=='overlap':p['segments'][128]['start']=p['segments'][127]['start']
    if kind=='duplicate-anchor':p['output_times'].insert(1,p['output_times'][0])
    if kind=='unordered-output':outputs=list(reversed(p['output_times']))
    if kind=='not-anchor':outputs=[p['output_times'][0],p['segments'][0]['end'],p['output_times'][-1]]
    if kind=='outside-event':
        event=deepcopy(CASES[3]['program']['events'][0]);event['at']='2025-12-31T23:59:59Z';p['events']=[event]
    if kind=='wrong-unit':p['segments'][0]['forcing']['values']['canopy_temperature']['unit']='K'
    if kind=='bool':p['segments'][0]['forcing']['values']['canopy_temperature']['value']=True
    if kind=='array':p['segments'][0]['relative_growth_rate']['values']['fruit_relative_growth_rate'].pop()
    if kind=='reference-origin':p['segments'][0]['forcing']['origin']='reference_observation'
    if kind=='step-budget':p['solver']['max_steps']=1
    if kind=='long-period':p['segments'][-1]['end']='2027-01-03T00:00:00Z';p['output_times'][-1]=p['segments'][-1]['end']
    with pytest.raises(stream.CycleInputRejected):write(path,p,outputs)
    assert not path.exists()


def edit_root(path,edit):
    root=json.loads((path/'root.json').read_bytes());edit(root)
    raw=json.dumps(root,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    (path/'root.json').write_bytes(raw)
    return sha256(raw).hexdigest()


@pytest.mark.parametrize('kind',['scope','code','profile','clock','count','index','time-index','chain','extra'])
def test_rehashed_bad_root_descriptor_is_rejected_without_fd_leak(tmp_path,kind):
    path=tmp_path/'packet';write(path,long_program(129));before=len(os.listdir('/proc/self/fd'))
    def edit(root):
        if kind=='scope':root['scope']='approved_crop_run'
        if kind=='code':root['normalization_sha256']['input_stream']='0'*64
        if kind=='profile':root['profile_sha256']['growth_profile']='0'*64
        if kind=='clock':root['streams']['segments']['blocks'][1]['clock_prefix']['numerator']='9'*1000
        if kind=='count':root['streams']['segments']['count']=True
        if kind=='index':root['streams']['segments']['blocks'][1]['start_index']=1
        if kind=='time-index':root['streams']['segments']['blocks'][1]['first_at']='2026-01-01T00:00:01Z'
        if kind=='chain':root['streams']['segments']['record_chain_sha256']='0'*64
        if kind=='extra':root['rights_approved']=True
    expected=edit_root(path,edit)
    with pytest.raises(stream.CycleInputRejected):stream.open_input_packet(path,expected,**PROFILES)
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('kind',['symlink-root','symlink-block','fifo-block','large-block','missing-block','bad-bytes'])
def test_unsafe_or_changed_files_fail_without_fd_leak(tmp_path,kind):
    path=tmp_path/'packet';receipt=write(path)
    root=json.loads((path/'root.json').read_bytes());block=path/(root['streams']['segments']['blocks'][0]['sha256']+'.json')
    if kind=='symlink-root':
        raw=(path/'root.json').read_bytes();target=tmp_path/'root-copy';target.write_bytes(raw);(path/'root.json').unlink();(path/'root.json').symlink_to(target)
    if kind=='symlink-block':
        target=tmp_path/'block-copy';target.write_bytes(block.read_bytes());block.unlink();block.symlink_to(target)
    if kind=='fifo-block':block.unlink();os.mkfifo(block)
    if kind=='large-block':block.write_bytes(b' '*(stream.MAX_BLOCK_BYTES+1))
    if kind=='missing-block':block.unlink()
    if kind=='bad-bytes':block.write_bytes(b'[]')
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(stream.CycleInputRejected):stream.open_input_packet(path,receipt['root_sha256'],**PROFILES)
    assert len(os.listdir('/proc/self/fd'))==before


def test_unavailable_directory_is_typed_rejection(tmp_path):
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(stream.CycleInputRejected):stream.open_input_packet(tmp_path/'missing','0'*64,**PROFILES)
    assert len(os.listdir('/proc/self/fd'))==before


def reseal(cursor):
    cursor['cursor_sha256']=physical._hash({k:v for k,v in cursor.items() if k!='cursor_sha256'})
    return cursor


@pytest.mark.parametrize('kind',['root','version','bool','future','counter','extra','non-boundary','initial','unsealed'])
def test_rehashed_bad_cursor_cannot_skip_or_repeat_original_prefix(tmp_path,kind):
    path=tmp_path/'packet';receipt=write(path,long_program(129))
    with stream.open_input_packet(path,receipt['root_sha256'],**PROFILES) as reader:
        cursor=reader.boundary_page(limit=128)['cursor']
        if kind=='root':cursor['root_sha256']='0'*64
        if kind=='version':cursor['version']='other'
        if kind=='bool':cursor['positions']['segments']=True
        if kind=='future':cursor['positions']['segments']=130
        if kind=='counter':cursor['positions']['segments']-=1
        if kind=='extra':cursor['positions']['other']=0
        if kind=='non-boundary':cursor['last_at']=physical._stamp(physical._utc(cursor['last_at'])+timedelta(seconds=1))
        if kind=='initial':cursor['last_at']=None
        if kind=='unsealed':cursor['positions']['segments']-=1
        if kind!='unsealed':reseal(cursor)
        with pytest.raises(stream.CycleInputRejected):reader.cursor_bytes(cursor)


@pytest.mark.parametrize('raw',[b'null',b'{',b'{"x":0,"x":1}',b'{"x":NaN}',b'\xff',b' '*65537,b'['*2000+b']'*2000])
def test_invalid_cursor_bytes_rejected(tmp_path,raw):
    path=tmp_path/'packet';receipt=write(path)
    with stream.open_input_packet(path,receipt['root_sha256'],**PROFILES) as reader:
        with pytest.raises(stream.CycleInputRejected):reader.restore_cursor(raw)


@pytest.mark.parametrize('limit',[False,0,-1,129,1.,None])
def test_bad_boundary_page_budget_rejected(tmp_path,limit):
    path=tmp_path/'packet';receipt=write(path)
    with stream.open_input_packet(path,receipt['root_sha256'],**PROFILES) as reader:
        with pytest.raises(stream.CycleInputRejected):reader.boundary_page(limit=limit)


def test_closed_reader_and_terminal_cursor_do_not_duplicate_records(tmp_path):
    path=tmp_path/'packet';receipt=write(path)
    with stream.open_input_packet(path,receipt['root_sha256'],**PROFILES) as reader:
        page=reader.boundary_page();assert page['complete']
        assert reader.boundary_page(page['cursor'])['boundaries']==[]
        with pytest.raises(stream.CycleInputRejected):reader.restore_cursor(json.dumps(page['cursor']).encode('utf-16'))
    with pytest.raises(stream.CycleInputRejected):reader.boundary_page()
    with pytest.raises(stream.CycleInputRejected):reader.record('segments',0)


@pytest.mark.parametrize('kind',['segments','anchors','events','outputs'])
def test_noniterable_stream_is_typed_rejection_and_owned_directory_removed(tmp_path,kind):
    p=program();values={'initial_state':p['initial_state'],'segments':p['segments'],'events':p['events'],
        'anchors':p['output_times'],'outputs':p['output_times'],'solver':p['solver'],'program_id':'own-test',**PROFILES}
    values[kind]=None;path=tmp_path/'packet'
    with pytest.raises(stream.CycleInputRejected):stream.write_input_packet(path,**values)
    assert not path.exists()
