"""Calculate the original leaf population once and sign its current parent/farm lineage."""
from hashlib import sha256

from . import crop_leaf_population_signed_artifact as signed
from . import crop_leaf_population_artifact_producer as numerical


@signed._checked
def produce_registered_leaf_population(authority,tenant,request_raw,*,program_raw,source_raw,evidence_raw):
    signed._need(type(authority) is signed.LeafPopulationArtifactAuthority);authority._binding()
    packet=dict(program_raw=program_raw,source_raw=source_raw,evidence_raw=evidence_raw)
    binding_raw=authority.farm_binding.prepare(tenant,request_raw,**packet)
    binding=signed.reader._parse(binding_raw,signed.farms.MAX_BINDING_BYTES)
    signed._need(signed.reader._canonical(binding['request'])==request_raw and binding['tenant_id']==tenant
        and all(sha256(packet[name]).hexdigest()==binding['input'][field] for name,field in (
            ('program_raw','program_sha256'),('source_raw','source_sha256'),('evidence_raw','evidence_sha256'))))
    root=numerical.produce_leaf_population_artifact(authority.directory,authority.access,
        stem_directory=authority.farm_binding.parent_authority.directory,program_raw=program_raw)
    manifest=signed.reader.read_leaf_population_manifest(authority.directory,authority.access,root)
    signed._linked(manifest,binding,program_raw)
    for index in range(len(manifest['samples'])):
        signed.reader.read_leaf_population_frame(authority.directory,authority.access,root,index=index)
    signed._need(authority.farm_binding.current(tenant,request_raw,binding_raw,**packet,write=True)==binding_raw)
    authority._binding();parent=binding['parent']
    with signed.MorphologyBlobStore(authority.directory,authority.access,write=True) as store:
        refs={field:store.put(packet[name],maximum=maximum) for name,field,maximum in (
            ('program_raw','program_sha256',signed.reader.MAX),('source_raw','source_sha256',signed.farms.evidence.SOURCE_MAX),
            ('evidence_raw','input_evidence_sha256',signed.farms.evidence.EVIDENCE_MAX))}
        payload={'schema_version':signed.VERSION,**signed.FLAGS,'tenant_id':tenant,
            'issuer_id':authority.issuer_id,'key_id':authority.key_id,'study_id':binding['request']['study_id'],
            'revision':binding['request']['revision'],**refs,'binding_sha256':store.put(binding_raw,maximum=signed.farms.MAX_BINDING_BYTES),
            'numerical_root_sha256':root,'parent_job_id':parent['job_id'],'parent_result_sha256':parent['result_sha256'],
            'parent_numerical_root_sha256':parent['numerical_root_sha256'],'parent_calculated_at':parent['calculated_at'],
            'calculated_at':signed.parent_signed._stamp(signed.parent_signed._now()),'code_sha256':dict(signed._CODE_PINS)}
        raw=authority._signed(payload);result_sha256=store.put(raw,maximum=signed.PROOF_MAX)
    signed._need(authority.farm_binding.current(tenant,request_raw,binding_raw,**packet,write=True)==binding_raw)
    authority._binding()
    with signed.MorphologyBlobStore(authority.directory,authority.access) as store:
        signed._need(store.get(result_sha256,maximum=signed.PROOF_MAX)==raw)
    return result_sha256
