# 현재 개별 기관 CP의 다음 한 걸음과 첫 threshold — research v1

`probe_next_shoot_threshold(context,raw_checkpoint,expected_sha256,time_tolerance_seconds_exact)`는 [가변 기관 재개](crop-organ-funded-continuation-v1.md)의 실제 현재 CP와 [현재 줄기 시계](crop-organ-current-shoot-clock-v1.md)의 원 shoot 이력을 사용한다. 실제 source의 미소비 `next_threshold_exact`/`next_sequence`/phyllochron을 사용하며 호출자가 기준을 바꾸거나 이미 지난 기준을 건너뛰지 않는다. 왼쪽 나이가 기준 이상이면 `SCHEDULE_HOLD`이며 후속의 명시 사건/일정 채택이 필요하다.

원 CP 검증의 RHS1회를 첫 stage로 사용하고 같은 원 dt/global index의 k2/k3/k4/endpoint RHS4회를 계산한다. 현재106+3n+m state·모든21+3n+3m 유량·원 anchors/D0를 사용한다. segment 적분과 원 lifetime·point/개별/전체 장부 및 output prefix를 원 재개와 같은 함수/순서로 계산한다. prospective endpoint의 원512KiB cap도 검사하지만 새 integrator checkpoint는 발급하지 않는다. 원 프로그램/CP를 다시 초기화하거나 과거 구간을 재계산하지 않는다.

네 실제 stage의 air temperature는 새 벡터의104번이다. [기존 근 계산](crop-funded-event-time-v1.md)의 명시 RK4 3차 연속식/정확 도함수 최소/최대128이분법을 그대로 사용한다. 방법 출처는 [Izgin-Melnikov, 식(28)](https://link.springer.com/article/10.1007/s42967-025-00480-8), CC BY4.0이며 원 적분에 적용한 자체 연구 변경이다. MPRK/양수 보장은 채택하지 않는다. 기온이나 나이 변화를 clip하지 않는다.

정확 다항식은 현재 저장 shoot 나이에서 시작한다. 최소 도함수가 양수여야 하며 그렇지 않으면 `MONOTONICITY_HOLD`다. 첫 기준에 대해 다항식 우단과 저장 endpoint 나이의 통과 여부가 같아야 하며 반올림으로 달라지면 `ROUNDING_HOLD`다. 둘 다 미통과이면 `no_crossing`/root=None이다. 통과하면 `threshold_bracket`과 원 interval 안의 lower/upper exact seconds·signed residual·폭·이분 횟수를 반환한다. 우단의 정확한 근은 허용하며 좌단의 미처리 기준은 건너뛰지 않는다. 여러 기준을 지날 수 있어도 첫 미소비 기준만 계산하고 일정 상태를 변경하지 않는다.

허용 오차는 원 step 이하의 명시 양의 기약 유리수 초이며 분자/분모는 원1024자리 제한을 유지한다. 폭은 이 다항식의 근 고립 오차만 제한하며 ODE/누적/계수/실제 출현 오차가 아니다. 이상적인 다항식과 저장 endpoint 나이의 차이를 기록하고 보정하지 않는다. 네 stage의 state/rates/flux·hash와 prospective endpoint sample/장부는 독립 검증에 사용할 수 있으나 채택된 사건/새 상태로 게시하지 않는다.

원 source/선택/rights/code/profile/환경·Context/CP bytes·기관 IDs/anchors/C/A와 장부·원점/step/prefix를 보존하고 최종 source fence를 통과한다. source/rights/단계/domain/수지/정밀도/한도/늦은 변경 실패는 결과와 새 CP를 발급하지 않는다. RuntimeError는 정상 hold로 숨기지 않는다. 응답2MiB·원 모든 부모/입력 cap과 WSL 예산을 유지한다.

수용은 실제6조건/양쪽 point·복수점·초기/중간/끝전/완료 hold, 수용된 advance_chunk 한 걸음과 전체 endpoint/장부 byte 일치, 실제 저장07시 초기 이력의 crossing·독립 고정밀 근/산술·경계/반올림/비단조/정밀도·fresh/no replay·권리/late 변경·기존 자료/GUI/WSL 보존이다. 합성 연구/G0–G4 미평가를 유지한다. 후속은 같은 분수 시각의 전체 상태/누적량·수지/오차→material point/일정 채택/원 격자 잔여 재개→실제 기관 시각/ID→공급 제한 형상/불변 저장3D다.
