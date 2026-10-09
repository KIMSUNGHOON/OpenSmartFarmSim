from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path

import pytest

from test_crop_harvest_replay import replay,source_and_parameters,owned_directory

PATH=Path(__file__).resolve().parents[2]/'research/crop-harvest-full-writer.py'
SPEC=importlib.util.spec_from_file_location('owned_full_harvest_writer',PATH)
whole=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(whole)


def references(read,source):
    return whole.capacity.removals(enumerate(read.samples),enumerate(read.events),source)


def test_all_stored_rows_independently_match_source_and_summary_without_rederiving(tmp_path,monkeypatch):
    directory=owned_directory(tmp_path);read,mass,allocation=source_and_parameters(True)
    mass,allocation=whole.prefix.revise_profiles(mass,allocation)
    result=replay._write(directory,read,mass,allocation);source=replay.harvest._source(read())
    before=len(os.listdir('/proc/self/fd'))
    with replay._Reader(directory,result['artifact_sha256'],read) as reader,whole.storage.read_guard():
        observed=whole.audit_rows(reader,references(read,source),mass,allocation)
    assert observed['rows']==132 and observed['all_rows_independently_checked']
    assert observed['row_chain_sha256']==result['row_chain_sha256'] and len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('change',['missing-reference','extra-reference','mass','last-blob','source-UTC'])
def test_independent_full_audit_refuses_corruption_and_missing_or_extra_source(tmp_path,change):
    directory=owned_directory(tmp_path);read,mass,allocation=source_and_parameters(True)
    result=replay._write(directory,read,mass,allocation);source=replay.harvest._source(read())
    with replay._Reader(directory,result['artifact_sha256'],read) as reader:
        refs=list(references(read,source))
        if change=='missing-reference':refs.pop()
        elif change=='extra-reference':refs.append(refs[-1])
        elif change=='source-UTC':refs[1][1][2][1]['at']='2026-10-01T00:00:30Z'
        elif change=='last-blob':
            path=directory/(reader._root['pages'][-1]['sha256']+'.json')
            path.chmod(0o600);path.write_bytes(b'[]');path.chmod(0o400)
        else:
            path=directory/(reader._root['pages'][0]['sha256']+'.json');rows=json.loads(path.read_bytes())
            rows[0]['mass']['fresh_matter']['value']+=1;raw=replay._canonical(rows);digest=sha256(raw).hexdigest()
            p=directory/(digest+'.json');p.write_bytes(raw);p.chmod(0o400)
            reader._root['pages'][0]['sha256']=digest
        with pytest.raises(ValueError):whole.audit_rows(reader,iter(refs),mass,allocation)
        assert reader._fd is None


def test_final_authority_guard_refuses_a_completed_numeric_audit(tmp_path,monkeypatch):
    directory=owned_directory(tmp_path);read,mass,allocation=source_and_parameters(True)
    result=replay._write(directory,read,mass,allocation);source=replay.harvest._source(read())
    with replay._Reader(directory,result['artifact_sha256'],read) as reader:
        original=replay._blob;last=reader._root['pages'][-1]['sha256']
        def revoke(fd,digest,maximum):
            value=original(fd,digest,maximum)
            if digest==last:read.original['identity']['artifact_sha256']='9'*64
            return value
        monkeypatch.setattr(replay,'_blob',revoke)
        with pytest.raises(replay.HarvestArtifactHold):whole.audit_rows(reader,references(read,source),mass,allocation)
        assert reader._fd is None
