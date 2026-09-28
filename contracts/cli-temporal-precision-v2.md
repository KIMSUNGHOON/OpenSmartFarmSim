# CLI temporal precision v2

The generic decision validator now records `decision-server-v2`; the thermal
review validator records `thermal-review-server-v2`. The `decision-v1` proposal
envelope and existing stage input versions are unchanged.

UTC input, authority and evidence timestamps accept whole seconds or one to six
fractional digits followed by `Z`. Calendar-invalid dates, offsets, missing
fractions and precision above six digits hold. The parser uses an aware Python
datetime for comparisons and preserves the original input text/hash. It never
rounds a signed planning D to seconds or silently truncates higher precision.
The exact input/authority context quartet still has to match.

This connects the real microsecond clock from
[planning-event-v1](planning-event-v1.md) to generic research/collection/assessment
and custom thermal review. An ex-ante evidence availability one microsecond
after D remains `late_evidence`. Initial preparation may still use the existing
all-null context quartet; that supplies no actual/hypothetical decision-time
knowledge or later publication authority.

The [checks](../backend/tests/test_cli_temporal_precision.py) include real
authenticated planning writer/reader, generated test signatures, all three
generic stages, exact supported timestamp text, invalid time/precision and the
one-microsecond ex-ante cutoff. Tests use synthetic authority facts and do not
approve agricultural/economic data or actual model invocation. Existing records
and releases remain immutable; changed code requires new independent release
evidence before G1 adoption.
