# Authored thermal Run in the standard HTTPS runtime v1

Status: optional internal read assembly candidate. This extends
[runtime assembly](api-runtime-assembly-v1.md) and consumes the existing
[authored Run read](api-authored-thermal-run-v1.md). No source or release is
approved by construction.

An operator may configure `ApiRuntimeConfig.authored_run_gate_key` and
`ApiRuntimeDependencies.authored_run_store_factory` together. The key is a
separate 32–4096 byte server secret, omitted from repr. The factory receives
only keyword `job_store`, `farm_scenario_service`, and `gate_key`; it must
return an exact `AuthoredRunStore`. The runtime requires the v8
`authored_run_storage` login profile and the owned research, stored thermal
scenario and user source services needed for a real `FarmReplayScenarioService`.
It rejects a one-sided configuration, a wrong profile, a changed job store,
farm replay service, or gate key before listening. No factory is called when
the authored option is absent. With the option absent, authored routes keep
their existing fail-closed unavailable result.

The trusted operator factory constructs the real authoring/review/completion/
release/preparation chain with its protected reviewer keys, evidence resolver,
execution verifier and code root. Runtime assembly supplies its exact job and
farm services; it neither invents independent review nor accepts those
dependencies from HTTP or a CLI proposal. The resulting Run store revalidates
current rights, release, code, bytes and the atomic job publication on each
read under the same request principal used by the HTTPS app. Authored Run IDs
remain separate from fixed synthetic Run IDs.

Focused software verification must cover pair/profile/binding failures, the
default unavailable route, authenticated HTTPS reads of an actually stored
synthetic Run, denied and foreign reads, and stale evidence returning a hold.
Synthetic test authorities do not prove product CLI execution, independent
release, G1 or G4. The operator's real factory and browser-to-HTTPS flow need
their own integration evidence before an operator-facing authored demo claim.
