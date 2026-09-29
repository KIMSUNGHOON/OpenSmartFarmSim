# Farm authoring capability map

Status: implementation sequence, 2026-09-30. Scope follows
[Scenario](docs/ARCHITECTURE.md#도메인-데이터-계약) and the
[first build](docs/IMPLEMENTATION_SLICE.md).

| Module id | Responsibility | Depends on |
| --- | --- | --- |
| farm-inputs | Validate explicit facility, initial state, control/forcing, cultivation calendar, objective, constraints and economic pins; compile immutable numerical inputs | Existing owned fixture and economic contracts |
| farm-authoring-storage | Register new versions with current ownership, rights, source/context checks and immutable custody; prepare authored snapshots | farm-inputs; existing source, job and snapshot stores |
| farm-authoring-execution | Bind actual thermal/economic workers and held Assessment to the authored version; verify replay and release | farm-authoring-storage; existing execution services |
| farm-authoring-web | Author facility/calendar and the complete dated economic ledger; submit and recover the same intent; replay the completed calculation | farm-authoring-execution; existing source intake and web SDK |

Build order: farm-inputs → farm-authoring-storage → farm-authoring-execution →
farm-authoring-web. Provider contract: [farm-inputs](contracts/farm-inputs-v1.md).
The larger existing G1 tasks remain open until the whole path is accepted.
