# 개선 판본 전체 입력 비용과 실행 예산

2026-10-08 KST. 작업 `crop-cycle-calculation-full-budget`의 관측 전 계약이다.
선행은 [입력 재검사 개선 수용](../research/crop-cycle-calculation-recheck-cost-implementation-20261008.md)이다.
판단은 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 하며 재귀 CLI를 실행하지 않는다.

## 첫 관측

기존 `research/crop-cycle-calculation-prefix-cost.py`와
`backend/tests/crop_cycle_full_prefix_cost_smoke.py`의 실제 등록 시험을 재사용한다.
`OSSF_FULL_PREFIX_MAX_ADVANCES=32`로 개선 판본의 같은 전체 입력/증명·solver·예산을 관측한다.
사용하는 별도 달력 root는 `05a58cc9092682f663bb3e2f827003f51ec8a778f746bb429126a663e841fc04`다.
원 입력·원 전체 순수 결과·새 입력과 기존 등록 이력은 보존한다.

한 소유 PG/계산만 nice19로 실행하며 원 명령 종료·PID 시작 identity·source pin·정리를 지속 기록한다.
관측기는900초가 지난 다음 호출을 시작하지 않고 감독자는1200초에 소유 pytest 중단을 요청한다.
이 상한은 실험의 자원 경계다. 관측 만료만으로 프로세스 종료를 추정하거나 재시작하지 않는다.
실제 결과·명령 종료와 소유 자원을 대사한 뒤 source freeze를 해제한다.

## 수용과 후속 판단

1. 실제32회 관측의 걸음·시점/사건·bytes/files·각 비용 곡선을 보존한다.
   32회에 못 미치면 부분 관측으로 기록하고 이 자식의 최종 수용을 보류한다.
2. 원32번째 checkpoint의121상태/seed/clock/cursor와 원 확정 행을 기존 명시 달력 변환으로 대사한다.
   fresh 서비스 복원·조회 RHS0·현재 권리/계정·미완료 게시 거부와 원 입력/이력·FD/PG/비밀 정리가 필요하다.
3. 기존 같은32회 관측과 초기/중간/끝의 입력/권리·prefix 검증·저장/RHS 호출과 비용을 구분한다.
   중첩 비용을 합산하지 않으며 초기 비용의 선형 외삽으로 전체 작기 완료 시간을 확정하지 않는다.
4. 현재 코드의 reopen/progress/prefix 검증 범위와 기존 전체 순수 결과 비용을 대조해
   전체 등록 실행에 필요한 예산·마감/중단·선택 checkpoint 재개·terminal/게시 수용 절차를 고정한다.
   이 근거로 장시간 실행이 아직 적절하지 않으면 관측한 원인과 필요한 작은 수정/검증을 먼저 기록한다.
5. 실제 명령/고정 영수증·검토와 위 예산 판단이 있어야 이 자식을 체크한다.
   전체 등록 terminal/DB/API/같은 UTC3D와 누적 비용 부모의 수용은 해당 실제 증거를 요구한다.

산출물은 개선 판본의32회 관측 보고서·불변 영수증과 전체 등록 실행의 실행/보류 판단이다.
생산량·자원·경제 연결과 실제 자료/예측·추천 관문은 [명세](../docs/PROJECT_SPEC.md)의 기존 조건을 따른다.
