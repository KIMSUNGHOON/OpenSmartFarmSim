# Solar result database schema acceptance — 2026-10-16

Accepted [contract](../contracts/crop-greenhouse-solar-result-schema-v1.md),
[implementation](../backend/app/crop_greenhouse_solar_result_schema.py),
[tests](../backend/tests/test_crop_greenhouse_solar_result_schema.py) and
[machine evidence](artifacts/crop-greenhouse-solar-result-schema-implementation-20261016.json).
Goal stays **active**. Previous turn made progress:1f5c11d/signed custody11tests.

Native parent CLI **gpt-6.1-sol/xhigh**, context2026-10-16T14:01:53.949Z,
made the design/acceptance judgment. Actual context/design/output hashes are
recorded. No recursive CLI, external data adoption, coefficient or equation
change occurred.

## Accepted boundary

Separate immutable `crop_greenhouse_solar_research_results` retains metadata
and original custody progress as two independent bytea/hash documents, each
at most128KiB. Metadata binds the progress hash. Closed metadata/current26key
progress tie source/context/UTC/provenance/custody code/farm/intent/HEAD/proof/
artifact identity and counters to columns. Result/storage/custody versions
identify the model family; detailed model/profile identity stays in binding.
Both documents require synthetic scope, unassessed gates and false rights
approval. Existing schema/models/profiles/keys/results/grants are preserved.

This is a schema contract. Nested states/units/checkpoints/UTC arrays, canonical
metadata, result-ID content identity, HMAC, actual farm registration/current
rights and original artifact must be verified by the subsequent store. Hash
agreement alone does not authenticate data or approve G0–G4.

## Verification

Original20452:0: **7new tests**,5.83s pytest/6.977s guard.
Original66467:0: **35regression tests** (5old ventilation schema+30fixture-policy),
3.89s pytest/4.764s guard. Total **42distinct passed,0skipped**, two separate
successful batches with active Python assertions and `--assert=plain`.

- Actual SCRAM provisioner round-trips all41supplied columns plus DB recorded_at;
  metadata/progress each exactly131,072bytes and both hashes/UTC remain equal.
  Existing4runtime roles reject all20SELECT/INSERT/UPDATE/DELETE/TRUNCATE attempts.
  Full existing grant audit passes with no new grants.
-114invalid column/bound/time cases,95rehashed metadata cases and74rehashed
  progress cases reject, including34metadata and19progress column pins,
  hash/size/type/decimal/exponent/bool/closed-shape/duplicate Unicode-key faults.
  Exact scalar upper bounds pass;600seconds+1microsecond rejects.
- Same-tenant FK, unique study/result/intent, held zero-step record, immutable
  UPDATE/DELETE, duplicate install and partial-install rollback pass. Three
  existing cycle/verified-cycle/ventilation tables and their original rows remain
  identical in all6database cases. Scratch schemas/roles end0.
- The [portable captured progress](../fixtures/synthetic-solar-custody-progress-v1.json)
  is the canonical36,617-byte32second synthetic output from accepted custody
  original32642:0. An independent explicit mapping stores/reads every original
  byte/hash and microsecond UTC without calculation. Its SHA is
  `cd32057672e845030eee485359d7d4c7a6d39f16460ce8c4de598bbeebdf53a4`.
  It contains computed fixture state/hashes, not acquired farm measurements or
  credentials; it is not a new registered input or signed farm authorization.

Original97000:1 exposed an invalid SQL bool→jsonb literal cast; corrected JSON
quoting retains exact-false checks. Original29597:1 rejected a fixture artifact
prefix missing `ventilation` from the actual solar storage version. The fixture
now uses the registered version; schema checks were not weakened. Corrected
smoke42480:0 and final7pass. Original failures/hashes/cleanup remain recorded.

Successful focused/regression guards preserve5roots/dynamic descendants,
2,148original entries,frozen sources/assets,HTTP5173,FD4→4 and owned process/
PG/temp PG/passfiles0. Peak137,015,296bytes/PID and977,747,968combined, nominal
0.25s sampling, within512MiB/PID/combined1GiB. User services/auth/routes/keys
were not changed or restarted; source/config edits did not overlap pending guards.
No physics/context/restore/CLI execution or actual farm Runs occurred. Full CI,
current DOM/WebGL and entire crop/custody suites were not rerun.

## Visible result and next acceptance

Both localhost development feeds report the schema acceptance after publication;
original80480:0 confirms both200/`no-store`/byte-identical at2026-10-16
23:22:49KST, SHA `3bf150b64cd14bb472662d1f9e628adbc2f934c3d2c9031dc258fd38872b7997`.
Both frozen HTML entries and2,173ventilation files remain equal. Current browser
DOM/WebGL was not rerun. Existing
ventilation remains available; **new solar results are not deployed to API/3D**.

Next slice: **explicit result authority**. Introduce a default-false model choice
and complete grant audit through the existing version/namespace approach.
Actual SCRAM must prove only the intended authority can SELECT/INSERT the new
table, all unintended role/column/inherited/PUBLIC/grant-option privileges reject,
old settings remain compatible, and old models/tables/rows/grants/keys and5roots/
resource caps remain preserved. Installation failure/rollback and owned cleanup
must pass before enabling signed registration/current query.

Then source/farm/rights/HMAC-checked atomic registration/fresh current query,
late revocation rollback/read computation0, API/automatic worker, same UTC3D
and user normal/hold/cancel/reconnect/restart acceptance remain separate stages.
Actual source rights and independent local/future farm/cultivar/optics/market
evidence remain external holds. G0–G4 are unassessed, actual farm Runs0; real
production/purchased energy/future margins/ranking/final UI/full completion date
remain unaccepted/unknown.
