# Authored Run financial web workflow v1

Status: focused software checks passed; not accepted G1 or deployment proof.
Evidence: [implementation and verification](../research/web-authored-economic-assessment-implementation.md).

An authenticated owner selects a stored authored Run from the existing catalog.
The exact current [financial selection](authored-financial-selection-v1.md)
must match that catalog Run/job before any input or result is displayed. The
client uses the server-derived closed economic input V3. It never searches for
a replacement candidate or fills in coefficients, tariffs or missing amounts.
The existing economic POST performs current admission checks again.

The page shows the selected farm revision and synthetic replay scope, new
economic admission, current status/result and existing monthly cash pages,
then the existing three-field assessment POST and persisted hold report.
Only a currently verified succeeded economic parent enables assessment. The
exact selected thermal job and economic job are pinned in the assessment intent.
The same saved thermal job opens the existing authored 3D replay.

History pages contain recovery links, not approved results. Selecting an
economic link requires a fresh status and completed result read; selecting an
assessment link requires its actual linked economic parent and current status/
hold reads. Refresh clears old money, cash and hold content before fetching.
Each new selection/history/cash response is bounded and checked for closed
shape, identity and cursor consistency. Account reconnect invalidates prior
async work and clears the selected Run, links and results.

An unresolved POST retains its immutable body and caller key, locks parent
switching and connection changes, and retries only the identical request.
Once acknowledged, the owner can recover records through the server history
after reconnect/reload, without manually entering job IDs. A bounded refusal
allows a new intent; an invalid positive response remains unresolved. Unknown
intents across a hard reload are not silently resubmitted: the server history
shows persisted jobs, and the user chooses a record before any new calculation.

Money/null strings and monthly cash are rendered without client arithmetic.
Amounts are conditional user assumptions; market/crop recommendation remains
hold. Assessment cannot render proceed, a selected crop or a ranking. Current
rights/refusal clears content. The desktop shell and narrow stacked panels
reuse the existing design system with keyboard controls, readable labels and
HTML tables, while keeping synthetic/conditional/hold text visible.

Acceptance requires meaningful response-boundary tests and actual browser tests
for selection, V3 admission, exact values/nulls, cash pagination, held assessment,
history recovery, same-request retries, stale/denied/account changes, keyboard/
narrow/enlarged-text layout and the same 3D parent. The actual HTTPS/SCRAM
browser path uses real stores/workers with explicit synthetic CLI/signatures;
it does not prove actual product model execution, independent release or G1–G4.
