"""Bounded original-result comparison and one deadline from preparation."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys

import pytest

SCRIPT=Path(__file__).resolve().parents[2]/'research/crop-cycle-registered-full-path.py'


@pytest.fixture
def path_module():
    spec=importlib.util.spec_from_file_location('owned_full_path',SCRIPT)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


class Reader:
    def __init__(self,rows,change=None):self.rows=rows;self.change=change;self.calls=[];self.checked=0
    def page(self,kind,start,limit):
        self.calls.append((kind,start,limit))
        selected=deepcopy(self.rows[kind][start:start+limit])
        page={'kind':kind,'start':start,'next':start+len(selected),'total':len(self.rows[kind]),'records':selected}
        if self.change:self.change(page)
        return page
    def recheck(self):self.checked+=1


def rows(n=129):
    return {'samples':[{'at':'2026-01-01T00:00:00Z','value':i} for i in range(n)],
            'events':[{'at':'2026-01-01T00:00:00Z','before':{},'after':{},'removed':{}}]}


def test_comparison_streams_all_rows_but_keeps_only_browser_preview(path_module):
    original=rows();shifted=deepcopy(original)
    for values in shifted.values():
        for row in values:row['at']='2026-10-01T00:00:00Z'
    left,right=Reader(original),Reader(shifted)
    observed=path_module.compare_rows(left,right,counts={'samples':129,'events':1},offset_days=273,check=lambda:None)
    assert len(observed['preview']['samples'])==64 and len(observed['preview']['events'])==1
    assert observed['preview']['samples']==shifted['samples'][:64]
    assert observed['counts']=={'samples':129,'events':1} and observed['pages']=={'samples':3,'events':1}
    assert observed['original_row_sha256']['samples']==sha256(b''.join(path_module.canonical(r)+b'\n' for r in original['samples'])).hexdigest()
    assert max(limit for kind,_,limit in left.calls if kind=='samples')<=64
    assert max(limit for kind,_,limit in left.calls if kind=='events')<=8
    assert left.checked==right.checked==1


@pytest.mark.parametrize('fault',['late_value','next','start','total','missing','duplicate'])
def test_malformed_or_changed_later_page_is_held(path_module,fault):
    data=rows()
    def change(page):
        if page['kind']!='samples' or page['start']<64:return
        if fault=='late_value':page['records'][-1]['value']=-1
        elif fault in ('next','start','total'):page[fault]+=1
        elif fault=='missing':page['records'].pop()
        elif fault=='duplicate':page['records'][0]=deepcopy(page['records'][1])
    with pytest.raises(ValueError):
        path_module.compare_rows(Reader(data),Reader(data,change),counts={'samples':129,'events':1},offset_days=0,check=lambda:None)


def test_checkpoint_compares_all_semantics_and_only_explicit_clock_shift(path_module):
    original={'version':'old','root_sha256':'old','at':'2026-01-01T00:00:00Z',
        'clock':{'segment_start':'2026-01-01T00:00:00Z','counter':7},'state':list(range(121)),'flows':{'carbon':2}}
    candidate=deepcopy(original);candidate.update(version='new',root_sha256='new',at='2026-10-01T00:00:00Z')
    candidate['clock']['segment_start']=candidate['at']
    path_module.compare_checkpoint(original,candidate,offset_days=273)
    for mutate in (lambda x:x['state'].__setitem__(120,-1),lambda x:x['clock'].__setitem__('counter',8),
                   lambda x:x['flows'].__setitem__('carbon',3),lambda x:x.__setitem__('at','2026-10-02T00:00:00Z')):
        bad=deepcopy(candidate);mutate(bad)
        with pytest.raises(ValueError):path_module.compare_checkpoint(original,bad,offset_days=273)
    assert original['at']=='2026-01-01T00:00:00Z'


def test_deadline_exists_before_setup_and_cannot_be_recreated_or_extended(path_module,tmp_path,monkeypatch):
    source=tmp_path/'source';source.write_bytes(b'fixed')
    monkeypatch.setattr(path_module,'sources',lambda:{str(source):sha256(source.read_bytes()).hexdigest()})
    path,digest=path_module.begin(tmp_path/'preparation',wall_seconds=30,scope='owned_small')
    value=path_module.checked(path,digest)
    assert value['deadline_ns']-value['started_ns']==30*10**9
    assert 0<path_module.remaining(value)<=30 and path.stat().st_mode&0o777==0o400
    with pytest.raises(FileExistsError):path_module.begin(tmp_path/'preparation',wall_seconds=30,scope='owned_small')
    monkeypatch.setattr(path_module.time,'time_ns',lambda:value['deadline_ns']+1)
    with pytest.raises(ValueError):path_module.checked(path,digest)


def test_current_source_change_is_held(path_module,tmp_path,monkeypatch):
    source=tmp_path/'source';source.write_bytes(b'fixed')
    monkeypatch.setattr(path_module,'sources',lambda:{str(source):sha256(source.read_bytes()).hexdigest()})
    path,digest=path_module.begin(tmp_path/'preparation',wall_seconds=30,scope='owned_small')
    source.write_bytes(b'changed')
    with pytest.raises(ValueError):path_module.checked(path,digest)


def test_original_nonzero_child_exit_is_preserved_and_rejected(path_module,tmp_path,monkeypatch):
    source=tmp_path/'source';source.write_bytes(b'fixed')
    monkeypatch.setattr(path_module,'sources',lambda:{str(source):sha256(source.read_bytes()).hexdigest()})
    prepared=path_module.begin(tmp_path/'preparation',wall_seconds=30,scope='owned_small')
    with pytest.raises(ValueError):
        path_module.child([sys.executable,'-c','raise SystemExit(7)'],name='failed',prepared=prepared,evidence=tmp_path)
    _,receipt=path_module.supervisor.read_json(tmp_path/'failed.command.json')
    assert receipt['actual_exit_code']==7 and receipt['reason'] is None
    assert receipt['log_sha256']==sha256((tmp_path/'failed.log').read_bytes()).hexdigest()
    assert not Path('/proc',str(receipt['worker']['pid'])).exists()
