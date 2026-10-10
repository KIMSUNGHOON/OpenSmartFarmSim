# Joint crop/climate protected runtime v1

This extends [API assembly](api-runtime-assembly-v1.md) for the existing
[current HTTP reader](api-crop-climate-joint-route-v1.md). The base version assembles
a reader; the explicit execution version is specified below. Assembly does not
execute a model, register results, adopt inputs, or approve G0–G4.

## Explicit configuration

The reader configuration of
`app.crop_climate_joint_operator_config.load_joint_api_runtime(path)` uses
`operator-joint-crop-climate-api-config-v1`. Top-level fields and protected
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

## Explicit execution API assembly

The same loader additionally accepts
`operator-joint-crop-climate-execution-api-config-v1`. Its closed top-level fields
are the reader version's fields plus required exact boolean
`crop_climate_joint_execution`. True requires joint result storage and its existing
cycle authority prerequisite. False disables execution. The reader version still
rejects that extra field, and the legacy/calculation loaders reject the execution
version. `ApiRuntimeConfig.crop_climate_joint_execution` defaults to False; no new
SQL table, grant, migration or package is introduced.

Enabled assembly derives `JointCropClimateExecutionService`,
`JointExecutionCheckpointStore` and `JointExecutionQuery` from the exact selected
joint result store's server, binding and input resolver. It exposes
`joint_execution_admission`, `joint_execution_checkpoints`, `joint_execution_query`
and supplies the same admission/query instances to the protected execution HTTP
installer. There is no second resolver, farm selection, custody root or key default.
Disabled assembly exposes three None values and execution routes remain 503 for
otherwise authorized requests. The current-result routes keep their existing policy.

HTTP stores retain request-scoped `current_principal`. Assembly neither starts a
background task nor lends a request identity to a worker after its request ends.
An operator's separate trusted factory constructs the existing
`JointExecutionWorker`/`DeterministicWorkerLoop` with its explicitly authorized
tenant principal, the same provisioned authority policy/schema and immutable input,
custody and result configurations. Across processes these are equivalent protected
configurations, not Python object identity. Within each process checkpoint/server/
result/jobs bindings must be identical as enforced by their constructors. Existing
E5b discovery consumes admitted jobs without receiving a target UUID. The selected
inputs and all current rights are rechecked at admission, execution and reading.

Execution acceptance requires real owned SCRAM and verified TLS admission, queued
and running reads, independent automatic consumption, normal and numerical-hold
result selection with original stored response bytes, and running cancellation
acknowledged by that actual consumer. Startup must perform no numerical or job
mutation calls. Configuration/protected-file rejection, old default behavior,
existing user preview, original files and scoped process cleanup remain required.
This acceptance activates no user preview or UI polling by itself; E7–E9 remain
necessary for the user's execution screen. A live confirmed-prefix 3D reader remains
separate from completed-result replay.

## Explicit confirmed prefix assembly

`operator-joint-crop-climate-prefix-api-config-v1` uses the execution version's
closed fields plus required exact boolean `crop_climate_joint_prefix`.
True requires `crop_climate_joint_execution=True`. `ApiRuntimeConfig` defaults
the prefix flag to False. Existing joint versions keep prefix disabled and reject
the extra field; generic/calculation loaders reject the prefix version.

Enabled assembly creates `JointExecutionPrefixQuery` from its same execution
query and exposes `joint_prefix_query`. The API conditionally installs the three
[prefix GET routes](crop-climate-joint-prefix-view-v1.md) with the same jobs,
server, farm, result store and principal. Disabled assembly passes None and does
not call the installer or add prefix paths to the default OpenAPI contract.

Reader v2 reads signed immutable snapshots without acquiring calculation custody
locks. Actual unpaused worker/TLS acceptance must cover running accepted prefixes
or transient snapshot retries, original normal/hold results and worker cancellation.
No runtime acceptance activates the SDK, calculation-time 3D or user deployment.
