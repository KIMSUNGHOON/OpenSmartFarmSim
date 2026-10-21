"""Calculate original v2 morphology, then sign its current registered-farm lineage."""
from hashlib import sha256

from . import crop_morphology_signed_artifact as signed
from . import crop_rational_morphology_artifact_producer as numerical


@signed._checked
def produce_registered_morphology(authority, tenant, request_raw, *, program_raw, source_raw, evidence_raw):
    signed._need(type(authority) is signed.MorphologyArtifactAuthority)
    authority._binding()
    packet = dict(program_raw=program_raw, source_raw=source_raw, evidence_raw=evidence_raw)
    binding_raw = authority.farm_binding.prepare(tenant, request_raw, **packet)
    binding = signed.reader._parse(binding_raw, signed.farms.MAX_BINDING_BYTES)
    signed._need(signed.reader._canonical(binding['request']) == request_raw and binding['tenant_id'] == tenant
        and all(sha256(packet[name]).hexdigest() == binding['input'][key] for name, key in (
            ('program_raw', 'program_sha256'), ('source_raw', 'source_sha256'), ('evidence_raw', 'evidence_sha256'))))
    root = numerical.produce_rational_morphology_artifact(authority.directory, authority.access, program_raw=program_raw)
    manifest = signed.reader.read_rational_morphology_manifest(authority.directory, authority.access, root)
    signed._linked(manifest, binding, program_raw)
    for index in range(len(manifest['samples'])):
        signed.reader.read_rational_morphology_frame(authority.directory, authority.access, root, index=index)
    signed._need(authority.farm_binding.current(tenant, request_raw, binding_raw, **packet, write=True) == binding_raw)
    authority._binding()
    with signed.MorphologyBlobStore(authority.directory, authority.access, write=True) as store:
        refs = {field: store.put(packet[name], maximum=maximum) for name, field, maximum in (
            ('program_raw', 'program_sha256', signed.reader.PROGRAM_MAX),
            ('source_raw', 'source_sha256', signed.farms.evidence.SOURCE_MAX),
            ('evidence_raw', 'input_evidence_sha256', signed.farms.evidence.EVIDENCE_MAX))}
        binding_sha256 = store.put(binding_raw, maximum=signed.farms.MAX_BINDING_BYTES)
        payload = {'schema_version': signed.VERSION, **signed.reader.FLAGS, 'tenant_id': tenant,
            'issuer_id': authority.issuer_id, 'key_id': authority.key_id,
            'study_id': binding['request']['study_id'], 'revision': binding['request']['revision'],
            **refs, 'binding_sha256': binding_sha256, 'numerical_root_sha256': root,
            'calculated_at': signed._stamp(signed._now()), 'code_sha256': dict(signed._CODE_PINS)}
        raw = authority._signed(payload)
        result_sha256 = store.put(raw, maximum=signed.PROOF_MAX)
    signed._need(authority.farm_binding.current(tenant, request_raw, binding_raw, **packet, write=True) == binding_raw)
    authority._binding()
    with signed.MorphologyBlobStore(authority.directory, authority.access) as store:
        signed._need(store.get(result_sha256, maximum=signed.PROOF_MAX) == raw)
    return result_sha256
