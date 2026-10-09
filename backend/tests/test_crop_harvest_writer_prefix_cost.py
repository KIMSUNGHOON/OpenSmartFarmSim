from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path

import pytest

from test_crop_harvest_replay import owned_directory, replay, source_and_parameters

PATH = Path(__file__).resolve().parents[2]/'research/crop-harvest-writer-prefix-cost.py'
SPEC = importlib.util.spec_from_file_location('owned_writer_prefix_test',PATH)
prefix = importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(prefix)


def prepared():
    read, mass, allocation = source_and_parameters(True)
    return read, *prefix.revise_profiles(mass, allocation)


def stopped(directory, read, mass, allocation):
    original = replay._put
    with prefix.PrefixBoundary(directory) as boundary:
        with pytest.raises(prefix.PrefixStop):replay._write(directory, read, mass, allocation)
    assert replay._put is original and boundary.stopped
    return boundary.pages


def maps(read):
    return ({i:replay._canonical(row) for i,row in enumerate(read.samples)},
            {i:replay._canonical(row) for i,row in enumerate(read.events)})


def test_new_profile_only_changes_revision_and_its_mass_hash_reference():
    _,mass,allocation = source_and_parameters(True)
    new_mass,new_allocation = prefix.revise_profiles(mass,allocation)
    m=json.loads(mass);a=json.loads(allocation);m['revision']=prefix.PROFILE_REVISION
    a.update(revision=prefix.PROFILE_REVISION,mass_parameter_sha256=sha256(new_mass).hexdigest())
    assert new_mass==replay._canonical(m) and new_allocation==replay._canonical(a)
    assert new_mass != mass and new_allocation != allocation


@pytest.mark.parametrize('which', ['mass','allocation'])
def test_invalid_or_mixed_profile_is_rejected_before_revision(which):
    _,mass,allocation=source_and_parameters(True)
    if which=='mass':mass+=b'\n'
    else:
        a=json.loads(allocation);a['source']['payload_sha256']='9'*64;allocation=replay._canonical(a)
    with pytest.raises(replay.harvest.CropRemovalHold):prefix.revise_profiles(mass,allocation)


def test_normal_two_page_stop_unpublished_rows_match_independent_decimal_and_originals(tmp_path):
    directory=owned_directory(tmp_path);read,mass,allocation=prepared();before=len(os.listdir('/proc/self/fd'))
    pages=stopped(directory,read,mass,allocation)
    samples,events=maps(read);audit=prefix.audit_prefix(directory,pages,samples,events,mass,allocation)
    assert audit['rows']==128 and audit['terminal_rows']+audit['event_rows']==128
    assert audit['every_prefix_row_independently_checked'] and not audit['whole_crop_totals_and_observations_evaluated']
    rows=[row for p in pages for row in json.loads((directory/(p['sha256']+'.json')).read_bytes())]
    assert rows==list(replay.harvest._read_allocations(read,mass,allocation))[:128]
    assert set(os.listdir(directory))=={'.writer-lock',*(p['sha256']+'.json' for p in pages)}
    assert not (directory/'HEAD').exists() and len(os.listdir('/proc/self/fd'))==before


def test_existing_or_different_artifact_directory_is_not_written(tmp_path):
    directory=owned_directory(tmp_path);read,mass,allocation=prepared();other=tmp_path/'other';other.mkdir(mode=0o700)
    before=len(os.listdir('/proc/self/fd'))
    with prefix.PrefixBoundary(directory):
        with pytest.raises(ValueError):replay._write(other,read,mass,allocation)
    assert not list(other.glob('*.json'))
    (directory/'HEAD').write_bytes(b'owned-existing')
    with pytest.raises(ValueError),prefix.PrefixBoundary(directory):pass
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('change',['blob','mass','UTC','source-position','missing-sample'])
def test_prefix_audit_refuses_changed_stored_or_original_values(tmp_path,change):
    directory=owned_directory(tmp_path);read,mass,allocation=prepared();pages=stopped(directory,read,mass,allocation)
    samples,events=maps(read);before=len(os.listdir('/proc/self/fd'))
    if change=='blob':
        path=directory/(pages[0]['sha256']+'.json');path.chmod(0o600);path.write_bytes(b'[]');path.chmod(0o400)
    else:
        if change=='missing-sample':del samples[1]
        elif change=='UTC':
            row=json.loads(samples[1]);row['at']='2026-10-01T00:00:30Z';samples[1]=replay._canonical(row)
        elif change=='source-position':
            row=json.loads(samples[1]);samples[1]=samples[2];samples[2]=replay._canonical(row)
        else:
            path=directory/(pages[0]['sha256']+'.json');rows=json.loads(path.read_bytes())
            rows[0]['mass']['fresh_matter']['value']+=1;raw=replay._canonical(rows)
            digest=sha256(raw).hexdigest();new=directory/(digest+'.json');new.write_bytes(raw);new.chmod(0o400)
            pages=deepcopy(pages);pages[0]['sha256']=digest
    with pytest.raises(ValueError):prefix.audit_prefix(directory,pages,samples,events,mass,allocation)
    assert len(os.listdir('/proc/self/fd'))==before
