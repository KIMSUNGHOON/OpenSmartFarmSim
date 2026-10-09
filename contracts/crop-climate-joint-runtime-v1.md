# Joint crop/climate protected runtime v1

This extends [API assembly](api-runtime-assembly-v1.md) for the existing
[current HTTP reader](api-crop-climate-joint-route-v1.md). It assembles a reader;
it does not execute a model, register results, adopt inputs, or approve G0–G4.

## Explicit configuration

`app.crop_climate_joint_operator_config.load_joint_api_runtime(path)` accepts
only `operator-joint-crop-climate-api-config-v1`. Top-level fields and protected
file rules are those of [operator configuration](operator-config-v1.md).
`crop_climate_joint_result_storage` is a required exact boolean. Optional existing
crop flags retain their defaults; `crop_cycle_calculation_result_storage` may
also be supplied explicitly. Either new joint storage or calculation-cycle
storage requires `crop_cycle_result_storage=True`. Existing joint farm bindings
use that authority profile, so a joint-enabled runtime also requires the existing
legacy cycle store factory. No legacy calculation or result is created by this
prerequisite.

The legacy and calculation operator versions continue accepting joint flag
omission/exact False and rejecting True or this new version. No file is rewritten
to pass another loader. Duplicate JSON keys, unknown/missing fields, nonfinite
values, invalid booleans, paths, credentials and dependency references fail closed
before listening. Configuration, TLS, DSN and key bytes are read through existing
protected-file helpers and checked again after the trusted factory and after
assembly. Any changed bytes or newly invalid file metadata reject the invocation.
`OSSF_API_CONFIG` and this module's `api_service()` reuse the existing HTTPS
foreground entrypoint. Errors contain only `operator_config_rejected`.

## Typed assembly

Two optional `ApiRuntimeDependencies` factories default to None:

- `crop_climate_joint_result_store_factory(farm_authoring_service=...)`
- `crop_climate_joint_current_query_factory(result_store=...)`

The policy flag and both factories must agree before any database or source I/O.
Enabled assembly requires an exact `JointCropClimateResultStore` and exact
`JointCropClimateCurrentQuery`, the runtime's same jobs/farm objects and
`current_principal`, and the query's same store. Existing binding checks verify
the native input authority, model/code pins and custody configuration. Input,
server-custody and DB-result integrity keys must be distinct. No implicit key,
grant, input resolver, migration, provisioning or directory creation is supplied.
The authority connection audits the selected, already provisioned grant matrix.
The runtime exposes `joint_crop_results` and `joint_crop_query` and passes those
same instances to the existing HTTP installer. False leaves the authenticated
route unavailable with 503.

The trusted factory owns protected custody roots, keys, rights and input resolver
configuration. Native current reads recheck actual source rights, farm identity,
proofs and account authority. Startup alone is not proof of any particular
result's rights or correctness. Misassembly is `API runtime assembly rejected`.

## Acceptance

Focused pure checks cover closed flags/versions, missing or foreign dependencies,
protected-file changes, generic failures and old-loader compatibility. Real owned
SCRAM fixtures reconstruct the same registered completed/hold results through
this loader and verified TLS. Summary/sample/event bytes and microsecond UTC
must equal the original current-query responses; late rights/account denial must
remain effective. Numerical entrypoints and registration are forbidden after
seed preparation. DB counts, input/config bytes, descriptors, owned temporary
resources and the existing user preview must be preserved. Synthetic 32-second
fixtures prove software wiring only; same-UTC 3D, live checkpoints/U3, full-cycle
joint forcing, independent local evidence and production claims remain separate.
