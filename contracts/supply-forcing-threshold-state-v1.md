# 같은 문턱 시각의 전체 상태·누적량 후보 v1

상태: **합성 수치 후보 수용 — 2026-10-31 KST.** [119검사/실제 두 source·보존](../research/supply-forcing-threshold-state-20261031.md)을 근거로 한다.
[근 정밀화](supply-forcing-threshold-v1.md)의 genuine forcing handle/pending을 그대로 사용한다.
`crop_supply_forcing_threshold_state.calculate_threshold_state(handle, pending_page_sha256,
time_tolerance_seconds_exact, *, cancelled=None, wall_seconds=60)`는 미게시 수치 후보를 반환한다.
권한 없는 DTO를 이전 Context/CP/handle로 바꾸지 않으며 기존 owner/kernel/locator는 변경하지 않는다.

## 원 입력과 시각

처음 접수한 허용 폭을 정확 Fraction으로 분리하고 변경하지 않은 locator를 호출한다.
실제 owner session/restore를 다시 열어 current/basis/cursor bytes와 원 pending page·span/input hash를 대사한다.
같은 held source의 같은 pending 첫 단계를 검증한 뒤에만 그 rates/flux를 재사용한다.
locator의5RHS와 과거 확정 구간 재적분0을 별도로 계측한다.

선택 시각은 인증된 증가 다항식 근 범위의 **정확 upper bound**다. 정확한 수학적 근이나 실제 출현 시각이 아니다.
현재 활성 입력 구간에 남아 있어야 하며 입력 경계와 순서가 미해결이면 후보를 만들지 않는다.
기관/실내 기온 시계를 문턱에 맞추거나 기존 나이/geometry를 다시 초기화하지 않는다.
원점·ID/layout·point·transfer origin·source sequence와 권리 AND를 그대로 유지한다.

## 모든 성분과 정확 합

원 네 RK4 단계의 기존 3차 continuous-extension weights와 one-round binary64 combine을
모든176상태와185부분 적분량에 적용한다. 고정 개수는 이번 실제 source의 관측이며 일반 품종 한도가 아니다.
비유한 값/비제로 underflow·반올림으로 사라진 비제로 변화를 거부한다. 후보 전체의 실제 RHS 도메인을 검사한다.

순수 helper `crop_supply_threshold_state_books.packet`은 기존 physical/geometry row builder를
실제 program/organs/costs/layout의 일반 수치 view에만 사용한다. 이전 authority 객체를 만들지 않는다.
부분 구간의124수지를 원 `64*(steps+1)*ULP(scale)`로 검사한다. source의 branch/global 잔차에
부분 잔차를 **정확히 더하고**, 예산도 기존 예산과 원 부분 예산의 합만 허용한다.
이는 원 source의 검증된 수지에 대한 telescoping 합성이며 새 point/CP나 독립 root 재검증 승인이 아니다.

원 branch binary64 누산기와 부분 binary64 누산기, 원 lifetime과 부분 누산기의 합은 Fraction으로 유지한다.
먼저 반올림한 합으로 원 누산기를 갈아 끼우지 않는다. partial·pending branch/lifetime을 별도 이름으로 내보낸다.
shoot age도 원 누적 시계에 부분 air-temperature integral/정확 기간을 더해 계산한다.
dense 상태의 표현된 나이가 문턱을 넘지 않으면 ROUNDING_HOLD다. 잔차를 지우거나 시계를 맞추지 않는다.

## 동일 시각의 간격 축소

같은 원 왼쪽 상태에서 동일한 선택 시각까지1·2·4개의 동일 RK4 substep을 별도로 계산한다.
검증한 원 k1과 각 이전 endpoint의 rates/flux를 재사용한다. 모든 실제 중간/끝 RHS는 원 도메인을 통과해야 한다.
각 부분 끝은 같은124수지를 검사한다. 간격 축소 결과는 선택 시각에 문턱을 넘지 않을 수도 있으며
그 여부/잔차를 그대로 보고한다. 이는 새 근/ODE·농업 오차 보증이 아닌 국소 진단이다.

원 locator5 + dense1 + refinement4*(1+2+4)=34RHS를 계측한다. 과거 확정 구간은 다시 전진하지 않는다.
176상태/185적분량 각각에 dense→1,1→2,2→4의 정확 차이를 단위/좌표와 함께 기록한다.
모든 성분의 차이가 감소한다고 주장하지 않는다. 원 상태와 과거 point는 변경하지 않는다.

## 결과·실패·다음 단계

`candidate_ready`는 source/root certificate·모델/코드/권리·선택 시각·dense/refinement·차이/계측과
계산 hash를 가진다. 각 packet은 원7point/transfer origins와 sequence를 보존한다.
`checkpoint_issued=False`, `history_committed=False`, `material_consumed=False`다.
이 결과를 kernel 상태/기존 checkpoint schema로 표시하지 않는다. 현재 owner의 미소비 pending는 그대로다.

전체 wall1–60초에서 locator에 남은 시간만 전달하고, 새 RHS29회/결과2MiB·기존 source/CAS 상한을 유지한다.
코드/profile·source/current/pending·수치 입력의 fence를 시작/구간/반환에 검사한다.
취소/수지/도메인·권리/늦은 변경/크기 실패 시 후보와 부분 refinement를 모두 제거한다.
계산기는 CAS/DB/API/CLI/network에 쓰지 않는다. private 관찰 파일은 제품 게시가 아니다.

수용은 모든 성분/누적의 독립 고정밀 반올림,124잔차/원 예산과185합성, RK4 비선형 수렴,
같은 시각 trace/차이·full/split/fresh-process 일치, 취소/변조/수지 오류·원 자료/기존 화면/WSL 보존이다.
다음은 이 후보에 결속한 명시 물질 조달·신규 기관/수지 point 산술이다. 원자 저장/일정 소비·새 layout/격자 재개는
point 검증 뒤 별도 수용이며, 긴 작기/같은 상태3D·생산/자원/경제·실제 품종/관문은 미완료다.
