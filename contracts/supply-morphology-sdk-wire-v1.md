# Supply morphology SDK: original receipt wire boundary v1

Wire child accepted 2026-10-30; [evidence](../research/crop-supply-morphology-sdk-wire-20261030.md).
Full strict SDK remains pending.

This boundary expands the accepted parent-referenced receipt encoding for the
subsequent strict browser SDK. `expandSupplyMorphologyReceipt(parentSeedRaw,
packedRaw, modelPinsRaw)` returns the original JSON string after checking its
receipt hash. It does not return an approved crop replay or evaluate crop equations.
Full source/Context/CP/state/clock/ledger semantics and HTTP/UI remain subsequent.

The parent is the genuine immediate predecessor's raw seed. Model pins are its
original 99-code dictionary. Root cardinality/identity binding is checked by the
subsequent graph validator; low-level encoding tests also use smaller dictionaries.
This codec bounds the dictionary to1–102 entries. Require the exact encoding version, four closed fields,
code-set hash and receipt hash. Preserve original scalar and reference subtree
tokens, including Python binary64 spelling; never reconstruct them with
`JSON.stringify(JSON.parse(...))`.

Tags are lexical integers: `[0, object]`, `[1, array]`, `[2, 0|1, path]`.
Source0 is the immediate parent, source1 the code dictionary. Traverse only actual
own object keys or nonnegative safe integer array indices. References may not
traverse primitives or inherited properties. Object output uses Python Unicode
codepoint key order. Reject malformed tags, duplicate keys, nonfinite numbers,
missing paths, invalid selectors/indices/depth and hash drift.

Keep the accepted 2MiB input and expanded byte caps and64-depth/path caps. Enforce
the expansion budget while constructing the result; do not allocate unbounded
referenced output before checking it. Parse containers locally within each call,
reusing at most4096 entries keyed by their immutable raw strings. There is no shared
or persistent cache and no network/CLI/DB write.

Acceptance uses all five original own-public receipts from the accepted six-Context
fixture against the existing Python decoder's independently recorded byte lengths,
receipt/calculation/candidate/state/program hashes, plus malformed and amplification
cases. Preserve the accepted export source/output closure, public bytes, old GUI and
WSL limits. This is one child of `supply-morphology-repeat-strict-sdk`; completing it
does not complete that parent, G0–G4, R2 or the full product goal.
