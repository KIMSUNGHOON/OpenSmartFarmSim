# Agent workflow

1. Read [README.md](README.md) for scope, then the relevant authoritative document below; do not copy its rules into code comments or new plans.
2. Product path and claim gates: [PROJECT_SPEC](docs/PROJECT_SPEC.md).
3. Process, object, API, and runtime worker contracts: [ARCHITECTURE](docs/ARCHITECTURE.md).
4. Software choices and lock policy: [TECH_STACK](docs/TECH_STACK.md).
5. Source quality and unresolved research: [RESEARCH_BASELINE](docs/RESEARCH_BASELINE.md).
6. Farm arithmetic: [ECONOMICS](docs/ECONOMICS.md); market timing and vintages: [MARKET_INTELLIGENCE](docs/MARKET_INTELLIGENCE.md).
7. First build boundary: [IMPLEMENTATION_SLICE](docs/IMPLEMENTATION_SLICE.md); observed blockers: [IMPLEMENTATION_READINESS](docs/IMPLEMENTATION_READINESS.md).
8. Use [tasks/todo.md](tasks/todo.md) for future code tasks and [tasks/plan.md](tasks/plan.md) for dependencies; update checkboxes only after their acceptance evidence exists.

## Judgment and evidence

9. Substantive source research, agricultural or economic domain choices, and architecture judgments require Codex CLI with the exact model `gpt-6-sol` and reasoning effort `xhigh`.
10. Product runtime research, collection review, and assessment also require that exact CLI model and effort; record actual invocation and output. An agent already running in that CLI session must not launch another CLI recursively.
11. Treat CLI proposals as reviewable evidence, not approved data or gate decisions. A deterministic server validates sources, rights, schemas, scope, and G0–G4 gates.
12. Record source URL/product ID, observation and publication times, `available_at`, retrieval time, vintage/revision, units, QC, raw hash, use/display/redistribution rights, and reviewer before adopting data.
13. Keep immutable inputs, model/parameter versions, decision IDs, run manifests, gate evidence, and explicit hold reasons. Later corrections create new versions.
14. Use deterministic versioned code for heat/vapor and money/quantity calculations; use `Decimal` for money. Never let generated prose supply coefficients, tariffs, crop outputs, or arithmetic results.
15. G0 permits only rights- and quality-checked inputs; G1 supports calculation/replay claims; G2 needs independent local measurements; G3a needs independent future crop/economic validation; G3b needs paired candidate comparison; G4 needs deployment proof.
16. A synthetic fixture tests software contracts only. Do not report crop growth, harvest, energy purchases, future margin, or ranking without the corresponding evidence and gates.

## Changes and verification

17. Keep each task small, preserve the modular self-hosted stack, and follow its stated dependencies and acceptance procedure.
18. Run focused checks, inspect changed files and links, and report what passed, what was not run, and any remaining hold.
19. Keep credentials, personal farm records, and raw restricted third-party data out of the repository, prompts, logs, and public manifests.
