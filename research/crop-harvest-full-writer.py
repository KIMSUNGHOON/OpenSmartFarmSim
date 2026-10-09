"""Normal whole synthetic harvest publication, independent audit and authenticated retention."""
from dataclasses import asdict
from decimal import localcontext
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('whole_harvest_prefix',ROOT/'research/crop-harvest-writer-prefix-cost.py')
prefix = importlib.util.module_from_spec(spec);spec.loader.exec_module(prefix)
storage, capacity = prefix.storage, prefix.capacity
backup, registry, harvest, replay = prefix.backup, prefix.registry, prefix.harvest, prefix.replay
need, canonical = prefix.need, prefix.canonical
REFERENCE = 'research/artifacts/crop-harvest-full-parent-restored-reference-20261009.json'
REFERENCE_SHA256 = '6c57a23352bc2ad19d8146c52977da3149a8f98546d3c7190d03c9443eec6185'


def audit_rows(reader, references, mass_raw, allocation_raw):
    mass = harvest._mass_parameters(mass_raw)
    allocation = harvest._allocation_parameters(allocation_raw,mass)
    def audit():
        with localcontext() as context:
            context.prec = 2200;checker = capacity.QuantityAudit(mass[0],allocation[0])
            def rows():
                for descriptor in reader._root['pages']:
                    values = replay._blob(reader._fd,descriptor['sha256'],replay.LIMITS['page_bytes'])
                    need(type(values) is list and len(values) == descriptor['count'])
                    yield from values
            for row, (_,reference) in zip(rows(),references,strict=True):checker.add(row,reference)
            return checker.finish(reader._root['summary'])
    return reader._operation(audit)


def source_receipt(source):
    raw = (ROOT/REFERENCE).read_bytes();need(sha256(raw).hexdigest() == REFERENCE_SHA256)
    accepted = json.loads(raw);comparison = accepted['comparison']
    need(accepted['whole_parent_restoration_accepted'] and comparison['all_original_rows_compared'])
    return {'observation': {'comparison_counts_hashes': {
        'counts':comparison['counts'],'candidate_row_sha256':comparison['candidate_row_sha256']},
        'replay':{'published_result_id':source['result_id'],'payload_sha256':source['payload_sha256']}}}


def audit_registered(publisher, result, source, farm, artifact_directory, mass_raw, allocation_raw):
    receipt = source_receipt(source)
    row = publisher._find('tenant-1',result['result_id']);packet = publisher._row(row,'tenant-1',farm)
    need(publisher._record(row) == result and packet['source'] == source)
    artifact = packet['artifact']
    with capacity.original._Files(artifact_directory) as files:
        archive = capacity.Archive(files,receipt);need(archive.source == source)
        references = capacity.removals(archive.rows('samples'),archive.rows('events'),source)
        try:
            with replay.open_harvest_artifact(publisher.directory/artifact['key'],artifact['sha256'],
                    publisher.query,'tenant-1',source['result_id'],farm) as reader:
                need(reader._root['parameter_raw_utf8'].encode() == mass_raw
                     and reader._root['allocation_raw_utf8'].encode() == allocation_raw)
                observed = audit_rows(reader,references,mass_raw,allocation_raw)
        finally:references.close()
        need(archive.hashes == receipt['observation']['comparison_counts_hashes']['candidate_row_sha256']
             and observed['rows'] == 47813)
        row = publisher._find('tenant-1',result['result_id'])
        need(publisher._row(row,'tenant-1',farm) == packet and publisher._record(row) == result)
        return observed


def register(parent_path, parent_sha, directory):
    parent_path = Path(parent_path);parent = backup.checked(parent_path,parent_sha)
    directory = Path(directory);directory.mkdir(mode=0o700);before_fd = capacity.fd_inventory();timing = {}
    with backup.readonly_guard():
        with backup.restored(parent_path,parent_sha,directory/'source-parent') as context:
            current = backup.current_query(parent_path,parent_sha,context)
            started = perf_counter()
            source,old_mass,old_allocation = storage.profiles(current,parent['original_record']['result_id'],parent['farm'])
            mass,allocation = prefix.revise_profiles(old_mass,old_allocation)
            original = current.read('tenant-1',source['result_id'],parent['farm'])
            packet = json.loads(original['record']['payload_raw'])
            need(packet['artifact']['sample_count'] == 47809 and packet['artifact']['event_count'] == 5
                 and source['source_status'] == 'completed')
            artifact_directory = current.store.server.directory/replay.current.server._intent_id(
                'tenant-1',packet['binding']['request'])/'artifact'
            with capacity.original._Files(artifact_directory) as files:
                archive = capacity.Archive(files,source_receipt(source))
                need(archive.source == source and archive.counts == {'samples':47809,'events':5})
            backup.write(directory/'preparation-verified.private.json',canonical({'source':source,
                'source_counts':archive.counts,'artifact_sha256':source['artifact_sha256'],
                'mass_sha256':sha256(mass).hexdigest(),'allocation_sha256':sha256(allocation).hexdigest(),
                'profile_revision':prefix.PROFILE_REVISION,'whole_writer_completed':False}))
            timing['prepare_seconds'] = perf_counter()-started
            policy,dsns = storage.install(context,directory);key = os.urandom(32)
            for name,raw in (('harvest-key.private',key),('mass.private.json',mass),('allocation.private.json',allocation)):
                backup.write(directory/name,raw)
            root = directory/'registry';root.mkdir(mode=0o700)
            publisher = registry.HarvestRegistry(current,policy,root,dsn=dsns['publisher'],integrity_key=key)
            started = perf_counter();result = publisher.put('tenant-1',source['result_id'],parent['farm'],mass,allocation)
            timing['normal_put_seconds'] = perf_counter()-started
            backup.write(directory/'registered.private.json',canonical(storage.record(result)))
            started = perf_counter()
            merged,merged_sha = backup.backup(directory/'merged-parent',admin_dsn=context['admin'],
                owned_data=context['directory']/'data',binary=Path(parent['binary']),
                config=context['config'],config_sha256=context['config_sha256'],
                db_key=storage.runtime.private_bytes(parent_path.parent/'DB-key.private'),
                result_key=storage.runtime.private_bytes(parent_path.parent/'result-key.private'),
                result_proof=storage.runtime.private_bytes(parent_path.parent/'result-proof.private'),
                record=original['record'],farm=parent['farm'])
            timing['early_authenticated_backup_seconds'] = perf_counter()-started
            backup.write(directory/'unaccepted-backup.private.json',canonical({'backup':str(merged),
                'backup_sha256':merged_sha,'scope':'normal_registered_research_before_independent_audit'}))
            started = perf_counter()
            with storage.read_guard():audit = audit_registered(publisher,result,source,parent['farm'],artifact_directory,mass,allocation)
            timing['independent_all_rows_seconds'] = perf_counter()-started
            backup.write(directory/'all-rows-audit.private.json',canonical(audit))
            reader = storage.query.HarvestCurrentQuery(registry.HarvestRegistry(current,policy,root,
                dsn=dsns['reader'],integrity_key=key))
            started = perf_counter()
            with storage.read_guard():observed = storage.selected(reader,result['result_id'],parent['farm'])
            need(observed['source'] == source and current.read('tenant-1',source['result_id'],parent['farm']) == original)
            timing['current_selected_seconds'] = perf_counter()-started
    for name in ('publisher.pgpass','reader.pgpass'):(directory/name).chmod(0o400)
    value = {'version':storage.VERSION,'scope':'owned_synthetic_only','code_sha256':storage.CODE_SHA256,
        'dependencies':storage.DEPENDENCIES,'parent_backup':str(merged),'parent_backup_sha256':merged_sha,
        'policy':asdict(policy),'registry_directory':str(root),'files_sha256':{name:sha256(
            backup.private_read(directory/name,65536)).hexdigest() for name in storage.FILES},**observed}
    path = directory/'storage.private.json';raw = canonical(value);backup.write(path,raw)
    storage.checked(path,sha256(raw).hexdigest())
    need(capacity.fd_inventory() == before_fd and not (directory/'source-parent/data/postmaster.pid').exists())
    backup.write(directory/'producer-verified.private.json',canonical({'storage_manifest':str(path),
        'storage_manifest_sha256':sha256(raw).hexdigest(),'timing':timing,'audit':audit,
        'FD_before_after':[len(before_fd),len(capacity.fd_inventory())],
        'source_postmaster_absent':True,'RHS_and_new_crop_publication_proof_calls':0,
        'scope':'owned_whole_synthetic_harvest_only','actual_crop_Runs':0,'G0_G4':'not_assessed'}))
    return path,sha256(raw).hexdigest()


def fresh(path, digest, directory, output):
    value = storage.checked(path,digest);parent = backup.checked(value['parent_backup'],value['parent_backup_sha256'])
    before_fd = capacity.fd_inventory()
    with backup.readonly_guard(),storage.read_guard():
        with storage.restored_storage(value,directory) as context:
            service = storage.reader(path,digest,context)
            observed = storage.selected(service,value['original_record']['result_id'],parent['farm'])
            need(all(observed[k] == value[k] for k in observed))
            args = ('tenant-1',value['original_record']['result_id'],parent['farm'])
            try:service.read('foreign',args[1],args[2])
            except PermissionError:pass
            else:raise AssertionError('foreign tenant read whole harvest')
            rights = service.store.query.store.server.binding.input_rights;original_call = type(rights).__call__
            def denied(instance,*args):
                return False if instance is rights else original_call(instance,*args)
            with patch.object(type(rights),'__call__',denied):
                try:service.read(*args)
                except (PermissionError,storage.query.HarvestCurrentQueryHold):pass
                else:raise AssertionError('display denial read whole harvest')
            need(service.read(*args)['record']['payload_sha256'] == value['original_record']['payload_sha256'])
    need(capacity.fd_inventory() == before_fd and not (Path(directory)/'data/postmaster.pid').exists())
    backup.write(output,canonical({**observed,'foreign_tenant_and_scoped_display_denied_restored':True,
        'shared_control_files_changed':False,'FD_before_after':[len(before_fd),len(capacity.fd_inventory())],
        'fresh_postmaster_absent':True,'RHS_harvest_generation_registration_proof_calls':0}))


def main():
    import argparse
    parser = argparse.ArgumentParser();sub = parser.add_subparsers(dest='mode',required=True)
    producer = sub.add_parser('produce');producer.add_argument('--backup',required=True,type=Path)
    producer.add_argument('--sha256',required=True);producer.add_argument('--directory',required=True,type=Path)
    reader = sub.add_parser('fresh');reader.add_argument('--manifest',required=True,type=Path)
    reader.add_argument('--sha256',required=True);reader.add_argument('--directory',required=True,type=Path)
    reader.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    if args.mode == 'produce':register(args.backup,args.sha256,args.directory)
    else:fresh(args.manifest,args.sha256,args.directory,args.output)


if __name__ == '__main__':main()
