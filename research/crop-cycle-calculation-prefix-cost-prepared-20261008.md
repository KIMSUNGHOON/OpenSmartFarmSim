# 등록 계산의 누적 비용 측정 — 코드 준비와 경량 검사

2026-10-08 KST. [측정 계약](../contracts/crop-cycle-calculation-prefix-cost-v1.md)에 따라
[측정 코드](crop-cycle-calculation-prefix-cost.py)와
[수동 시험](../backend/tests/crop_cycle_calculation_prefix_cost_smoke.py)을 준비했다.
**경량17개 통과·전체20개 수집이며 실제 등록 계산 시험3개는 아직 실행하지 않았다.**
[고정 영수증](artifacts/crop-cycle-calculation-prefix-cost-prepared-reference-20261008.json)에
실제 코드/로그 SHA·종료·검증 범위와 같은 native 실행의 부분 관측을 보존한다.
판단은 native Codex CLI `gpt-6.1-sol / xhigh`에서 했으며 재귀 CLI0회다.

## 구현한 측정 경계

기존 `crop-cycle-burden-profile.py`의 `Costs`를 재사용한다. context factory·입력 증명 검증·
실제 RHS·누적 prefix/delta 검사·journal·농장 등록/현재 권리·DB put/lookup을 관측한다.
중첩 inclusive/exclusive 시간과 호출 수를 분리한다. wrapper 오버헤드가 포함된 실측이며
관측 항목의 inclusive 합을 전체 실행 시간으로 사용하거나 오버헤드를 분리 추정하지 않는다.
계산 함수나 계수·저장/권리 정책·CI 설정은 수정하지 않았다.

실행 예산은 기존 artifact의128 transition 한도를 사용한다. 관측은 최대32회·20분이며,
이미 사용한 실행 의도를 거부한다. 매 호출의 실제 steps/counts/bytes/files와 비용을 기록하고
같은 checkpoint를 새 서비스에서 다시 연다. 호출 한도로 멈춘 `yielded`를 완료로 바꾸지 않는다.
표본 RSS는 현재 Python 프로세스의 생애 high-water이며 WSL 전체 메모리 사용량이 아니다.

## 확인한 범위

- 미구현 driver의 `FileNotFoundError`를 먼저 확인했다.
- 최종 경량 검사는 **17통과·3미선택 / 0.81초**다. 잘못된 예산/관측 한도의 선행 거부,
  실제 함수의 wrapper 복원과 예외 전파·중첩 시간 구분을 확인했다. 작물 RHS/PG는 실행하지 않았다.
- Python 구문 검사와 **20개 수집 / 0.82초**를 통과했다. 수집을 실제 DB 시험 통과로 표시하지 않는다.
- 원118 source SHA는 같다. 새 제품 API/모델/설정/웹 코드 변경은0이다.

## 다음 실제 시험과 남은 의존성

1. 실제 SCRAM 등록 농장의 정상/수치 hold를 한 호출과 bounded 호출로 계산한다.
   같은 불변 input proof를 재사용해 원 sample/event·121상태/seed/clock/누적을 비교한다.
   DB put/retry/read의 RHS0·현재 계정/권리 거부·원 행/파일·FD/DB/비밀/PG 정리를 확인한다.
2. 고정25시간 입력에서 실제32회 비용 곡선과 확정 과거의 원값을 확인한다.
   미완료 prefix의 게시를 거부하고 같은 checkpoint 재열기·현재 권리·불변을 확인한다.
3. 원166일 입력/격자/사건을 보존하는 실제 등록 농장·경제 기간을 검증하고,
   누적 비용 관측과 필요한 개선을 별도로 수행한다. 이3번 전에는 prefix-cost 부모를 체크하지 않는다.

[수정한 실제 native](web-crop-cycle-calculation-native-tls-hold-20261008.md)가 실행 중이라
새 PG/계산을 시작하지 않았다. 사설 실행기는 이전 native의 실제 종료·프로세스/PG/비밀 정리를
확인해야 시작하며 첫 관측 wall 예산은20분이다. 위 작은 실제 시험/곡선과 전체 입력 등록은
아직 통과하지 않았다. 전체166일 저장/복원·API/3D → 생과/자원 → Decimal 경제 순서를 유지한다.

작은 측정2.5–5집중시간의 기존 잠정 범위에는 전체166일 등록·개선/실행·CI·자료 확보가
포함되지 않는다. 실제 품종 입력·국내 독립 검증 자료·측정 작물 Run은0건이고,
G0–G4 `not_assessed`·예측/추천 보류를 유지한다. 전체 제품 완료 날짜는 확정하지 않는다.
