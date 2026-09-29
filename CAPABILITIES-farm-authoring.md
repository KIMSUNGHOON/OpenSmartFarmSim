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
The storage module currently has an internal immutable registration candidate;
its [unpublished numerical trajectory candidate](contracts/farm-thermal-candidate-v1.md)
is reproducible from that registration. Authored snapshot review/release and
worker binding are its next dependency. The viewer still reads only accepted
Run records.
An [owned authored review admission candidate](contracts/farm-authored-review-v1.md)
now pins that full trajectory to an immutable `collection_review` intent and
server CLI proposal contract. Runtime CLI routing, independent release and Run
publication remain open.
