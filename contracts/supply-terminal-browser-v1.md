# Supply terminal browser replay v1

Reuse the accepted101-file immutable public source graph. Its strict quantity
reader already returns original Contexts, CPs, validated material receipts and
frames. Another raw export or fabricated crop result is unnecessary. This
implements the source-bound transfer/parser task using that existing transfer.
Accepted backend/model/SDK modules and the deployed preview stay unchanged.

`readSupplyTerminalReplay(readFile, anchor, signal)` validates the whole current
source graph with `readSupplyMorphologyStoredQuantities` once per invocation.
It returns defensive `summary()`, `frame(index)` and `window(first=0,last=end)`
methods. A frame binds its original morphology DTO and C/N quantities at the same
index/at/phase; a window uses inclusive original indices and never renumbers.
Malformed indices fail before a partial window is exposed. No validation cache
survives a new load. Browser transport uses the existing bounded no-store,
redirect-error, credentials-omit read helper. Latest-request/cancel handling
rejects delayed superseded results, including a transport that ignores abort.

Quantity frames, intervals and totals follow the recorded backend terminal
contract: original50C/N coordinates, exact binary64 stock sums, exact terminal
lifetime from the actual CP or material-before pending receipt, original frame
and state SHA/Context/CP/receipt/prefix identity, same floor basis, exact time,
37nonnegative differences/5zero-duration boundaries and endpoint telescoping.
BigInt rational arithmetic only sums/subtracts recorded quantities. It performs
no crop equation, fresh mass conversion, money calculation or animation.

The browser projection has its own version `supply-terminal-browser-window-v1`;
it must not claim that Python executed in the browser. A separately identified
backend reference version/code SHA and actual recorded reference output SHA
support cross-language verification. Reference fixtures are own synthetic
software data and must retain origin/provenance/rights and explicit claim scope.
The original terminal status, source/model/profile/rights and G0–G4/R2 propagate.
N means fractional model fruit-number equivalents, not nitrogen or individual
fruit IDs, positions, shape, maturity, real harvest or sales. Response2MiB,
512frame/32768scalar and existing per-file/store/HTTP bounds remain in force.

Acceptance: all38source frames/3800cohort coordinates, exact stock/lifetime and
37intervals/5ties match the accepted Python output independently audited with
Decimal2200precision. Check first/last/single/partial windows, zero nonzero-start
baseline, bad selections, source changes after a previous success, rights/hash/
unit/quantity failure, cancellation/latest requests, defensive copies, bounded
output and unchanged original101files/model/GUI/finite preview under WSL limits.
Run focused unit/type checks and a separate actual HTTP read of the immutable
bundle; no new model/CLI/DB/worker or source writes. Display/WebGL integration,
external farm current rights/custody, full season, economics and G0–G4/R2
acceptance remain separate. Scope is `synthetic_terminal_quantities_only`.
