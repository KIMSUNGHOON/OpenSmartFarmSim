# Fresh input JSON duplicate-key candidate — 2026-10-20

**Decision: reject before timing; no production change.**
[Machine evidence](artifacts/solar-fresh-input-json-pairs-evaluation-20261020.json) ·
[candidate](solar-fresh-input-json-pairs.py) ·
[28 checks](../backend/tests/test_solar_fresh_input_json_pairs.py).

## Observed behavior

The proposed replacement constructs a fresh `dict(items)` and checks its length
against the pairs collection. It retains the original `_json` body, decoder and
constant hooks, globals and outer exception handling. No decoded value is cached.
On 24 standard-input cases, baseline and candidate produce the same canonical
value or original error type/message/cause chain. Cases include nested and escaped
duplicate keys, Unicode/UTF-8, nonfinite constants, float overflow, malformed input,
large integers and recursion. A separate case confirms every call invokes the
decoder and returns independent mutable results with the original key order.

Three controlled opaque decoder cases disqualify the candidate:

| Hook input | Original loop | Bulk dictionary candidate |
| --- | --- | --- |
| List subclass exposing mapping methods | Iterates `a=1,b=2` | Calls mapping methods and returns `a=999,b=999` |
| Iterator of pairs | Returns `a=1` | Raises `TypeError` on `len(items)` |
| String subclass raising on its second hash | Propagates `RuntimeError` | Hashes once and returns `a=1` |

These are explicit counterexamples to the required opaque decoder behavior,
not failures observed with the standard JSON decoder. The tests assert both
outcomes; their green result proves rejection evidence, not candidate equivalence.
No extra dispatch/ownership tables or retired JSON cache are introduced to rescue
this candidate. No primitive benchmark or whole worker quantum timing was run.
There is no speedup claim and no unchanged-source normal64 retry.

## Verification and preserved state

The same final **28 distinct checks** passed on CPython3.12.3 and locked3.12.13;
these are two executions of28 checks, not56 distinct cases. Final owned guards
took0.874450/0.892413seconds. Peak observed aggregate RSS was496,668,672bytes,
maximum PID96,878,592bytes, below the original1GiB/512MiB caps. Each kept FD4→4,
five live protected roots,2,148 original entries and both frozen UI sources/assets;
owned processes/PostgreSQL/temp/passfile remainders were0. This small-test resource
observation does not accept combined production/browser capacity.

The initial same candidate run also passed28; a subsequent removal of an unused
import and redundant assertion produced the final test source above. Only the
final two executions count here. Backend app261 files remain591eff7d….
No whole backend/browser CI, new DOM/WebGL, real farm data or G0–G4 acceptance ran.
Native Codex CLI gpt-6.1-sol/xhigh performed the review in the existing session;
the private preflight pins the existing context/output and candidate/test sources.
Recursive CLI/subagents0. No new agricultural or economic coefficients/data.

## Next user-facing path and dependencies

The existing U1 result catalogue is independent of new Solar execution: its
prerequisites are current farm registration/display rights and stored growth/
harvest queries. Its API, SDKs and selection components already exist. Source
inspection of `App.tsx` confirms the list-to-`SelectedCropReplay` branch; the
preserved SCRAM/HTTPS acceptance harness already clones saved results. Current
source pins for10 relevant files are in the machine evidence. This inspection
does not accept the current rendered path or extend historical tests to new code.

Proceed with the existing `product-ui-result-catalog-native` acceptance work:

1. Pin the current build/API and immutable clone inputs/manifests; preserve both
   running previews and all protected roots. Reuse saved results without producing
   or signing replacements.
2. In one owned fixture, select farm→crop→stored growth/harvest through the real
   catalogue API and verify original IDs, UTC, C/N and harvest quantities in the
   existing replay. Record current rights and zero calculation/publication.
3. Complete the existing design/render review, reload/backend restart, account/
   rights denial, late-response and WSL cleanup/resource conditions before checking
   the corresponding U1 children or deploying a replacement preview.

WSL fixture execution stays sequential. Independent U1 work does not open the
new Solar normal64→hold→HTTP cancel→live WebGL→WSL activation chain. The last
uninstrumented normal still ended with stopped metadata46/64; diagnostic
confirm50/64 is separate. New Solar deployment, whole UI/U3/end-to-end G1 and
independent agricultural/economic/market gates remain incomplete; goal active.

The old U1–U5 estimate54–96focused hours was the initial UI scope estimate, not a
fresh estimate of remaining work. Its conditional October18–25 calendar is no
longer a current schedule. Re-estimate remaining UI work from the current
acceptance gaps and measured fixture preparation; whole product date stays unset.

## User progress publication

[Publication receipt](artifacts/solar-fresh-json-catalog-status-publication-20261020.json)
confirms HTTP200/no-store and identical current JSON at5173/5174, unchanged
HTML/2,173 frozen ventilation files and protected/original/owned cleanup. The
existing ventilation deployment flag is retained; new Solar/U1 are not deployed.
No browser DOM/WebGL rerun was performed.
