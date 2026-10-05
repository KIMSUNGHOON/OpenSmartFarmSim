# 빈 과실 요청 유보의 짧은 기관 적분 — v1

상태: **다음 작은 구현의 계약; 시간 전진/저장/3D 미수용**.
선행: [새 기관 순간 결합의 로컬 수용](../research/crop-plant-startup-rates-implementation.md).
파일: `backend/app/crop_plant_startup_integration.py`,
`backend/tests/test_crop_plant_startup_integration.py`.
독립 참조 생성기/fixture와 실제 출력·검증 기록을 함께 보존한다.
기존 모델/프로그램/manifest/불변 결과 bytes는 수정하지 않는다.

## 프로그램과 계산 범위

새 `crop-plant-startup-program-v1`과 `crop-plant-startup-rk4-research-v1`을 사용한다.
입력 block·단위/UTC·구간/사건 순서·닫힌 solver·자원 한도는
[기존 짧은 적분 계약](crop-plant-cohort-integration-v1.md)의 구조를 재사용한다.
코드 공유는 변경 없는 순수 helper만 허용하며 전역 RHS/모델을 바꿔 실행하지 않는다.
새 RHS는 `calculate_plant_startup_rates`다. S/W1/RGR는 매 구간의 명시 입력이다.
초기 N/C는 0을 허용하지만 자동 착과·seed·pre-onset/실제 품종 적용은 허용하지 않는다.
전체 작기·생과 kg·구매 자원이나 경제를 이 단계에 추가하지 않는다.

입력 준비는 최대 24시간·128구간/128사건·512출력·10,000 step의 한도를 유지한다.
RK4의 모든 trial/후보·사건 후 상태를 원식/유한/비음수/C>0⇒N>0 조건과 검사한다.
음수/양의 underflow·초과 제거/수지 실패를 epsilon·clip·임의 과실로 채우지 않는다.
실패는 phase/UTC/reason과 확인된 과거 samples·last_confirmed만 남긴다.
Tsum의 Fraction 적분·T24 필터·동일 N/C 비율 관리 제거는 기존 규칙을 유지한다.

## 누적 진단과 보존

기존 외부 탄소·개수 수지에 새 내부 유보량을 외부 유입/유출로 더하지 않는다.
동일 RK4 가중으로 요청 과실 구조 탄소·실현·유보·실현 과실 생장 호흡을
별도로 누적한다. 출력 단위는 유량이 아닌 `mg_CH2O/m2_floor`다.

    cumulative_requested_fruit_C
      -cumulative_realized_fruit_C-cumulative_deferred_fruit_C = 0
    cumulative_fruit_growth_respiration
      -cG*cumulative_realized_fruit_C = 0

각 step/경계/사건/출력에서 기존 두 보존과 이 두 진단을 유한한 반올림 예산으로
확인한다. buffer 미분에는 `(1+cG)×R`, 전체 호흡에는 `cG×Fa`만 반영한다.
과실 이동·구획 유지 호흡과 사건 제거를 두 번 차감하지 않는다.
새 누적 필드의 음수/곱 underflow와 진단을 숨기는 과도한 절대 tolerance도 거부한다.

## 재현과 수치 해석의 한계

새 manifest는 프로그램/적분/RHS 판본과 코드·고정 profile·기존 배분/새 시작 정책 hash,
정규화 입력 ID/origin·solver/UTC/온도 합 규칙·연구 가정·Python 판본을 묶는다.
새 모델의 결과를 기존 v1/v2 저장 decoder에 넣거나 예전 결과 판본을 덮어쓰지 않는다.
같은 환경/입력에서는 실제 samples/사건/hold·manifest와 결과 hash를 재현한다.

이 시작 정책은 tail 수요가 0이면 진입만, 양수이면 요청 전체를 실현한다.
따라서 tail 출현/전량 제거의 전환에서 RHS가 불연속일 수 있다.
이는 실험으로 검증된 총 sink 용량이나 연속 자동 착과식이 아니다.
그 전환까지 RK4의 4차 정확도를 가정하지 않는다. 각 참조 프로그램의
간격 반감 오차와 hold를 실제 기록하고, 미검증 프로그램의 수렴은 미평가로 표시한다.

## 수용 기준과 사용자 산출물

1. 제품을 import하지 않는 고정 70자리 Decimal RHS/짧은 적분과 독립 선형 N 이동
   해석해로 빈 초기/첫 명시적 진입/무진입·양의 tail의 기관/50 N/C·누적량을 대사한다.
2. 원 v1과 겹치는 양의 tail 프로그램의 상태/기존 누적량 동등성,
   새 요청=실현+유보·호흡=cG×실현과 기존 탄소/개수 수지를 확인한다.
3. 8/4/2/1초 등 명시 반감 프로그램에서 실제 coarse/fine/reference 오차를 기록한다.
   0↔양의 tail 전환은 일반 smooth 구간과 구분해 관측 오차로 수용/hold를 결정한다.
4. 초기/끝·구간/출력 경계와 부분/전량 사건 제거, S/W1/RGR 변화·단위·영역·수치/
   자원/예산 오류, hold의 확인된 과거 상태와 재현/불변/hash를 검증한다.
5. 새 집중 시험과 기존 작물 회귀·판본/파일/링크를 통과한 뒤 수용한다.
   사용자는 UTC별 기관·50구획/LAI와 누적 요청/실현/유보·호흡·보존 표를 확인한다.

후속은 별도 artifact/불변 저장 판본과 API/동일 UTC 3D 계약이다.
국내 독립 농장 자료 확보는 병행한다. 실제 forcing/품종/초기/관리·수확 변환의 근거와
예측/추천 게시의 G0–G4는 기존대로 남으며 합성 참조는 그 관문을 통과시키지 않는다.
