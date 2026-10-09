"""Manual owned SCRAM restore: current metadata without reading or generating crop rows."""
from contextlib import ExitStack
from datetime import datetime
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import psycopg
from psycopg import sql
import pytest

from app import crop_result_catalog as catalog


def inventory(roots):
    found={}
    for root in roots:
        for p in (root,*sorted(root.rglob('*'))):
            info=p.lstat();assert not p.is_symlink()
            found[str(p)]=(info.st_dev,info.st_ino,info.st_mode,info.st_size,info.st_mtime_ns,info.st_ctime_ns,
                           sha256(p.read_bytes()).hexdigest() if p.is_file() else None)
    return found


def replace_control(path, raw):
    path.chmod(0o600)
    with path.open('wb') as stream:
        stream.write(raw);stream.flush();os.fchmod(stream.fileno(),0o400);os.fsync(stream.fileno())


def test_preserved_growth_and_harvest_catalog_current_rights_and_no_result_reads():
    root=Path(__file__).resolve().parents[2]
    spec=importlib.util.spec_from_file_location('catalog_preserved_storage',root/'research/crop-harvest-storage-preservation.py')
    storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    path=Path(os.environ['OSSF_CROP_CATALOG_STORAGE']);digest=os.environ['OSSF_CROP_CATALOG_STORAGE_SHA256']
    stage=Path(os.environ['OSSF_CROP_CATALOG_STAGE']);stage.mkdir(mode=0o700,exist_ok=True)
    value=storage.checked(path,digest);parent=storage.backup.checked(value['parent_backup'],value['parent_backup_sha256'])
    original_config=json.loads(storage.runtime.private_bytes(Path(value['parent_backup']).parent/'original-runtime.private'))
    roots=[path.parent,Path(value['parent_backup']).parent,Path(original_config['input']['directory']),
           Path(original_config['server_directory']),Path(value['registry_directory'])]
    original=inventory(roots);fd_before=len(os.listdir('/proc/self/fd'));observed=[]
    with storage.restored_storage(value,stage/'restore') as context:
        config=json.loads(storage.runtime.private_bytes(context['config']))
        # Only this clone's controls may change during denials; the open preview uses the originals.
        for field in ('principal','rights'):
            target=stage/(field+'.private');storage.backup.write(target,storage.runtime.private_bytes(config[field+'_file']))
            config[field+'_file']=str(target)
        artifacts=stage/'job-artifacts';artifacts.mkdir(mode=0o700)
        config['artifact_root']=str(artifacts)
        config_path=stage/'catalog-runtime.private.json';raw=storage.canonical(config);storage.backup.write(config_path,raw)
        context={**context,'config':config_path,'config_sha256':sha256(raw).hexdigest()}
        reader=storage.reader(path,digest,context);service=catalog.CropResultCatalog(reader.store.query,reader)
        farm=parent['farm']
        growth_row=service.calculation.store._find('tenant-1',result_id=parent['original_record']['result_id'])
        assert growth_row['payload_sha256']==parent['original_record']['payload_sha256']
        growth_expected={**parent['original_record'],'recorded_at':growth_row['recorded_at'].isoformat()}
        def forbidden(*args,**kwargs):raise AssertionError('metadata list read/generated/published crop values')
        with ExitStack() as stack:
            stack.enter_context(storage.backup.readonly_guard());stack.enter_context(storage.read_guard())
            for target,name in ((catalog.calculation.CalculationCurrentCycleQuery,'open'),
                    (catalog.harvest.HarvestCurrentQuery,'open'),
                    (catalog.calculation.results,'open_calculation_result_read_context')):
                stack.enter_context(patch.object(target,name,forbidden))
            for kind,expected in zip(catalog.KINDS,(growth_expected,value['original_record'])):
                started=perf_counter();page=service.read('tenant-1',kind,farm,limit=1);elapsed=perf_counter()-started
                assert len(page['items'])==1 and page['next_cursor'] is None
                item=page['items'][0]
                assert item['result_id']==expected['result_id']
                assert item['recorded_at']==catalog._time(datetime.fromisoformat(expected['recorded_at']))
                assert item['calculation_status']=='completed' and page['rights_or_gate_approval'] is False
                assert page['selection_validation_required'] is True
                if kind==catalog.KINDS[0]:
                    assert item['sample_count']==3 and item['event_count']==3
                else:
                    assert item['parent_result_id']==parent['original_record']['result_id'] and item['row_count']==5
                before={'recorded_at':datetime.fromisoformat(item['recorded_at']),'result_id':item['result_id']}
                assert service.read('tenant-1',kind,farm,limit=1,before=before)['items']==[]
                for changes in ({'crop_id':'missing-crop'},{'registration_sha256':'0'*64}):
                    with pytest.raises(catalog.CropResultCatalogHold):service.read('tenant-1',kind,{**farm,**changes})
                with pytest.raises(PermissionError):service.read('foreign',kind,farm)
                for field in ('principal','rights'):
                    control=Path(config[field+'_file']);saved=storage.runtime.private_bytes(control);document=json.loads(saved)
                    if field=='principal':document['scopes'].remove('crop_result_read')
                    else:document['allowed']=False
                    try:
                        with pytest.raises((PermissionError,catalog.CropResultCatalogHold)):
                            with service.open('tenant-1',kind,farm,limit=1):replace_control(control,storage.canonical(document))
                        with pytest.raises((PermissionError,catalog.CropResultCatalogHold)):service.read('tenant-1',kind,farm)
                    finally:replace_control(control,saved)
                assert service.read('tenant-1',kind,farm,limit=1)==page
                store=service.calculation.store if kind==catalog.KINDS[0] else service.harvest.store
                original_row=store._find('tenant-1',result_id=item['result_id']) if kind==catalog.KINDS[0] else store._find('tenant-1',item['result_id'])
                table=sql.Identifier(store.jobs.schema,catalog.calculation.storage.schema.TABLE) if kind==catalog.KINDS[0] else sql.Identifier(store.policy.schema,catalog.harvest.registry.schema.TABLE)
                def signature(value):
                    with psycopg.connect(context['admin']) as conn:
                        conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(table))
                        conn.execute(sql.SQL('UPDATE {} SET integrity_signature=%s WHERE tenant_id=%s AND result_id=%s').format(table),
                                     (value,'tenant-1',item['result_id']))
                        conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER USER').format(table))
                try:
                    signature('0'*64)
                    with pytest.raises(catalog.CropResultCatalogHold):service.read('tenant-1',kind,farm,limit=1)
                finally:signature(original_row['integrity_signature'])
                assert service.read('tenant-1',kind,farm,limit=1)==page
                encoded=storage.canonical(page)
                assert not any(key.encode() in encoded for key in ('payload_raw','integrity_signature','password','passfile'))
                observed.append({'kind':kind,'items':len(page['items']),'response_bytes':len(encoded),'read_seconds':elapsed,
                    'original_result_and_recorded_at_preserved':True,'equal_cursor_empty':True,
                    'foreign_scope_registration_crop_rights_tamper_and_post_projection_denied':True})
    assert not (stage/'restore/data/postmaster.pid').exists()
    assert inventory(roots)==original and len(os.listdir('/proc/self/fd'))==fd_before
    storage.backup.write(stage/'accepted.private.json',storage.canonical({'status':'metadata_catalog_local_only',
        'observations':observed,'guarded_crop_read_RHS_publication_proof_calls':0,
        'source_entries_unchanged':len(original),'FD_before_after':[fd_before,len(os.listdir('/proc/self/fd'))],
        'restored_postmaster_absent':True,'G0_G4':'not_assessed','actual_crop_Runs':0}))
