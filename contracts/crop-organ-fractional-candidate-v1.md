# 새 개별 기관 벡터의 분수 시각 상태/장부 — research v1

`calculate_fractional_shoot_candidate(context,raw_checkpoint,expected_sha256,time_tolerance_seconds_exact)`는 [현재 한 구간/첫 기준](crop-organ-next-threshold-v1.md)을 실제로 계산하고 `threshold_bracket`의 upper exact 시각을 선택한다. 미통과 구간은 `THRESHOLD_HOLD`다. 시각/나이/면적을 문턱에 맞춰 보정하지 않는다. 원 source/선택·current CP/시계·권리·profile/code·네 stage/hash/배치/유량 순서와 결속한다.

[기존 후보](crop-funded-event-state-v1.md)의 dimension-independent `_weights`/`_combine`만 재사용한다. 모든106+3n+m 상태와21+3n+3m partial 유량을 exact Fraction 시간/계수로 결합하고 각 조합을 한 번 binary64로 반올림한다. 비유한/비영 underflow/소실 increment는 hold다. 기존107-vector의 ledger/refine/CP를 새 벡터로 가장하지 않는다. 후보에서 실제 새 RHS를 평가해 domain/derived/원 curve residual·D0를 확인한다.

현재 CP에서 후보까지의 local C/과실수/수관·공기 현열/수증기/열용량/reduced energy·leaf별 나이/C·stem/root별 C 및 합계를 정확한 표현 입력의 유리수 합으로 검사한다. local 예산은 기존 `64*(steps+1)*ULP(scale)`이며 dense 구간은1step이다. 새 품종 계수·mass↔area 변환·절대 epsilon을 추가하지 않는다.

원 현재 lifetime/segment prefix와 pending partial은 정확히 더하되 새 CP로 채택하지 않는다. 원 root 초기 재고와 실제 birth bases/point totals에서 global 장부를 계산한다. 원 현재 global residual을 정확 산술로 재검사하고 원 예산 안이어야 한다. 각 candidate global residual은 `exact_source_global_residual + exact_local_residual`과 같아야 하며 예산은 `원 current global 예산 + local 예산`만 사용한다. 기존 prefix/point bytes는 수정하지 않는다. 새 leaf/stem 목록과 root 하나·명시 조달 비용을 보존한다.

같은 exact 시각까지1/2/4개의 같은 길이 classical RK4 부분 step을 독립 계산한다. 상태/유량 조합은 같은 exact-time/한 번 반올림 방식이다. 모든 RHS stage의 domain과 각 substep endpoint의 누적 local/global 장부를 확인한다. refined 경로의 문턱 통과는 별도 정보이며 새 근이 아니다. 차이는 국소 수치 진단이고 ODE/물리 오차의 인증 상한이 아니다.

full-step dense와 원 accepted endpoint의 각 상태/유량 차이를 원 단위로 기록하며 θ=1도 bit 일치를 강제하지 않는다. dense 후보의 pending 기온 적분으로 계산한 shoot 나이가 문턱 미만이면 `ROUNDING_HOLD`다. refinements는 다른 경로의 같은 시각 진단이므로 미통과도 표시한다. 원 fixed RK4와 새 exact-time 조합의 수치 방법을 분리 기록한다.

일반 실행 RHS는 probe5 + dense1 + refinements(5+9+17) =37회다. 과거 전진·기존/새 기관 초기화·point/일정 채택·새 integrator CP·DB/CLI/network/쓰기0이다. 원 CP512KiB·모든 부모 cap과 응답2MiB를 유지하고 source/rights/code/profile/late 변경·수지/domain/정밀도/한도 실패에 부분 후보를 발급하지 않는다. RuntimeError를 정상 hold로 숨기지 않는다.

수용은 실제 single/mixed 목록의 원 첫 후보 시각·전 상태/partial 유량·독립 고정밀 산술·local/global 정확 합성·부분 step1/2/4 및 비선형 해석해 수렴·원 prefix/점/IDs/D0·실패/상한/권리/late/fresh/no effects·원 자료/GUI/WSL 보존이다. 합성 연구/G0–G4 미평가이며 후속은 실제 material point/일정 채택·새 분수 CP/원 격자 잔여/분할 재개→기관 시각/ID→공급 제한 형상/같은 저장3D다.
