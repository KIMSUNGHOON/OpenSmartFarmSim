# 과실 제거 원장과 건물·생과 환산 — v1 후보

2026-10-07 KST. **구현 전 계약 초안**이다. [환산 조사](../research/crop-harvest-conversion-baseline-20261006.md)의
출처·차원 검토와 현재 저장 형식을 다음 작은 작업으로 연결한다. 계수·자료·구현 수용 기록이 아니다.
개발/게시 조건은 [명세 5.3](../docs/PROJECT_SPEC.md#53-개발-착수와-결과-게시),
선행 순서는 [계획](../tasks/plan.md), 현장 자료는 [확보 상태](../research/crop-independent-data-status.json)를 따른다.
원 cycle3D/전체 작기 부하 수용 뒤 구현하며, 지금은 계약만 준비한다.

## 원량과 사건을 먼저 구분한다

첫 core는 예정된 `backend/app/crop_harvest.py`, `backend/tests/test_crop_harvest.py`와 이 계약이다.
기존 solver·저장 artifact·API/3D를 보존하고 검증된 원 결과를 읽는 순수 adapter부터 시작한다.
원 결과 ID/root·입력/모델/정책 판본·선택 UTC 구간과 원 sample/event 위치를 파생 행에 결속한다.
HTTP의 임의 수치를 검증된 결과로 간주하거나 새로운 server 계산 이력을 발행하지 않는다.

| 원 경로 | 사용할 양 | 원장 의미 |
| --- | --- | --- |
| `sample.cumulative.terminal_carbohydrate` / `terminal_number` | 확인된 경계 사이 누적 차이 | 해당 구간의 모델 마지막 구획 유출 C/N |
| `event.removed.fruit_carbohydrate` / `fruit_number` | 같은 사건의 원50개 C/N 벡터와 합계 | 명시 관리 사건의 과실 제거 C/N |
| `event.removed.leaf` / `stem_root` | 과실 합계에서 제외 | 잎·줄기/뿌리 제거 C |
| `sample.cumulative.event_carbohydrate` | 원 수지 대사에만 사용 | 모든 기관의 관리 제거 C |

현재 [적분 코드](../backend/app/crop_plant_startup_integration.py)와
[artifact 검사](../backend/app/crop_startup_artifact.py)는 `event_carbohydrate`에 잎·줄기/뿌리·과실을 합산한다.
이를 과실 수확량으로 환산하면 적엽·적심을 과실에 더하는 오류가 된다.
과실 제거 C는 사건 journal의 과실 벡터에서 얻고 전체 기관 제거와 별도로 대사한다.

C 단위는 `mg_CH2O/m2_floor`, N은 `fruits_equivalent/m2_floor`다.
이미 적분된 누적량/사건량에 시간을 다시 곱하지 않는다. 같은 경계/사건을 두 번 배정하지 않고
시작/끝·사건 전후·페이지 경계의 배정 규칙을 고정한다. 현재 sample은 사건 후 상태이므로
첫 시각 사건도 journal에서 한 번만 처리한다. 누락/혼합 결과·불완전 미래는 거부한다.
첫 원장의 종류는 `model_terminal_outflow`와 `explicit_fruit_removal`이며 수확/숙기/판매를 뜻하지 않는다.
N 상당수를 실제 과실 정수·개수 분포로 반올림하지 않는다.

## 명시 계수의 질량 환산

동일 제거 모집단에 적용하는 검토된 계수 판본 또는 명시 소유 합성 시험 입력으로
아래 항등식을 결정적 코드로 계산한다. 원량과 변환 결과는 각각 보존한다.

```text
DM_kg_per_m2_floor = C_removed_mg_CH2O_per_m2_floor * eta_mg_DM_per_mg_CH2O * 1e-6
FW_kg_per_m2_floor = DM_kg_per_m2_floor / d_kg_DM_per_kg_FW
```

`eta>0`, `0<d<=1`, 유한성·단위를 검사한다. 값·단위·계수 ID/판본·모집단/시각·근거가
없으면 환산하지 않는다. 서버의 기존 source/권리 검사를 prose나 클라이언트 승인 표시로 대체하지 않는다.
실제 품종 프로필에 기본 eta/DMC·평균 과중·Brix 대체값을 넣지 않는다.
합성 계수 산술 검사는 실제 계수 채택이나 작물 생산 결과 게시로 연결하지 않는다.

구간별 계수가 다르면 해당 구간의 원 제거를 변환해 합산한다. 전체 누적 C를 표본 DMC의
산술 평균으로 나누지 않는다. 기존300초 결과만으로 그 사이 시간별 계수/유량의 적분을
복원할 수 없으면 세분화된 근거나 명시된 구간 상수 정책이 필요하다.
없는 해상도의 수확 시각·계수 변화와 미래 정보의 당시 이용 가능성을 만들지 않는다.

첫 환산은 같은 바닥 면적당 값이다. 절대 kg·다른 면적·줄기당 값은 검토된 분모/면적·
해당 시각 밀도와 모집단 대응이 있을 때 별도 변환한다. 상당수당 과중은 같은 제거의 N>0일 때만
정의하며 실제 개별 과중으로 표시하지 않는다. 비유한·overflow·양수 underflow·수지 불일치를
0 또는 임의 비율로 보정하지 않는다. 물리량 float64와 기존 Decimal 금액 계산의 경계를 유지한다.

## 실제 수확 의미와 배치 연결

원 제거를 수확·적과·폐기·채취로 분류하려면 원 모집단/사건·시각·근거와 검토된 배정 정책이
필요하다. 같은 과실의 원 terminal과 후속 수확 관측을 두 번 더하지 않고 미배정량은 보존한다.
실측 수확과 모델 제거의 차이도 유지하며 실측을 모델 예측으로 재명명하지 않는다.
`H`·등급별 `P`·계약상 `S`는 [경제 계약](../docs/ECONOMICS.md#3-판매량가격비용-공식)의
별도 근거와 배치/달력을 따른다. 환산만으로 등급·판매 가능률·실제 판매·매출을 생성하지 않는다.
후속 저장/API/3D는 원 result ID/UTC와 파생 판본을 연결하는 별도 작은 작업에서 검증한다.

## 첫 구현 한 단계의 수용 기준

`crop-removal-ledger`는 원 C/N 분리만 구현한다. eta/DMC/FW·H/P/S는 다음 단계다.

1. 독립 소유 합성 예제에서 terminal 구간 차이와 사건50개 과실 C/N 합계를 각각 대사한다.
2. 잎/줄기만 제거하는 사건의 과실 원장은0이고, 혼합 사건에도 과실 외 C가 들어가지 않는다.
3. 초기/마지막·사건 전후·페이지 경계를 한 번 또는 나누어 읽어도 동일 원량/행 ID다.
4. 반복/혼합 result·root·역순/누락·잘못된 단위·음수/비유한·불완전 미래를 거부한다.
5. 기존 검증된 작은 저장 결과의 원 event/sample·UTC를 대사하고 조회 RHS0·현재 권리·FD 정리를 확인한다.
6. 원 artifact/수식/공개 응답을 보존하고 집중 시험·code/input/output hash를 기록한 뒤 자식만 체크한다.

둘째 단계는 독립 Decimal/Fraction 차원/역환산·구간 계수/분모·불능 나눗셈·numeric hold를 검증한다.
셋째 단계는 중복 배정 방지·미배정/폐기 보존·수확 관측 대응과 실제 적용 범위를 검증한다.
한 자식의 소프트웨어 시험으로 부모 생산량을 수용하지 않는다.
현재 실제 DMC/수확/등급·면적/밀도·당시 판본과 국내 독립 검증은 미확보다.
구현 완료일은 전체 작기 부하 수용과 이 근거 상태를 확인한 뒤 추정한다.
