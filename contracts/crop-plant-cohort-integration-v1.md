# 기관·명시적 과실 구획의 짧은 연구 적분 — v1

상태: **다음 구현의 입력/수용 계약; 적분 코드·실행 미수용**.
[순간 기관 결합](crop-plant-cohort-rates-v1.md)을 시간 전진하는 다음 작은 단계다.
전체 작기 개발은 [작기 처리 작업](../tasks/todo.md)의 별도 의존성으로 유지한다.

## 계산 범위와 입력

고정 기존 growth/cohort/transport profile과 명시적 착과 연구 정책을 사용한다.
기관 유입·잎/줄기 fixed-RGR와 supplied cohort RGR의 연구 가정은 순간 계약 그대로다.
별도 연구 integrator 판본 `crop-plant-cohort-rk4-research-v1`과 모든 원 코드 hash를 기록한다.
동일 입력의 현재 startup/원식 domain hold를 임의 기본값으로 해소하지 않는다.

`integrate_plant_cohorts(*, initial_state, segments, events, output_times,
growth_profile, cohort_profile, transport_profile, solver)`를 구현할 예정이다.

- `initial_state`: 닫힌 input_id/origin/values. buffer/leaf/stem_root·두 온도 상태와
  정확한 50개 fruit_number/fruit_carbohydrate. 단위는 순간 계약과 같다.
  독립 total fruit·초기 RGR은 넣지 않는다. 총 fruit는 매번 C 합계에서 파생한다.
- `segments`: 닫힌 start/end/forcing/removals/fruit_entry/relative_growth_rate.
  forcing/removals/S/W1은 순간 계약의 명시 block이며 RGR block의 values는
  정확한 50개 `fruit_relative_growth_rate`(1/s)다. 한 구간에서 값은 일정하다.
  구간은 연속이고 겹치지 않는다. 빈 초기 sink/entry 예산 실패는 hold다.
- `events`: 닫힌 at/removals. removals values는 leaf/stem_root 제거 CH2O와
  50개 `fruit_fraction`(unit 1, 0–1)이다. 이는 명시적 연구 관리 입력이며
  품종별 적심/수확 정책이나 실제 기록을 자동 생성하지 않는다.
  각 구획의 같은 비율로 N/C를 함께 제거하고 실제 제거 개수/CH2O를 누적 기록한다.
  초기/마지막 시각을 포함한 정렬된 한 시각당 한 사건만 허용한다.
- `output_times`: 전체 시작/끝을 포함한 엄격히 증가하는 whole-second UTC 배열.
- `solver`: 닫힌 method/max_step_seconds/max_steps/roundoff_rule.
  `rk4-fixed-v1`, `64-ulp-per-operation-v1`과 명시적인 정수 예산만 허용한다.

구간/사건/출력 시각은 UTC POSIX whole seconds다. 사건과 forcing/출력 경계를
넘는 step은 허용하지 않는다. 경계까지 이전 forcing으로 적분하고 사건을 적용한
뒤 새 forcing/entry/RGR를 사용한다. 출력은 사건 후 상태다.
초기 시각에도 같은 규칙을 적용해 사건 전 seed와 사건 후 첫 출력의 수지를 대사한다.

## 첫 구현의 자원 경계

첫 적분은 **최대 24시간의 생식기 연구 구간**이다. segments/events는 각 128개,
output_times는 512개, max_steps는 10,000 이하, max_step_seconds는 1–3,600이다.
실제 필요한 경계 분할 step 수를 미리 계산하고 예산 초과 시 실행 전 거부한다.
새 dependency/병렬 solver·항상 켜진 server는 추가하지 않고 WSL2에서 한 과정으로 확인한다.
이 경계는 전체 작기 수용을 뜻하지 않는다. 실제 참조의 47,809 시점·166일은
`crop-cycle-capacity`의 bounded forcing/연속 상태·출력 페이지/재시작 계약으로 후속 검증한다.
임의 forcing 축약이나 해상도 변경으로 완료를 주장하지 않는다.

## 상태·누적 외부 수지

buffer/leaf/stem_root, T24/Tsum와 50개 N/C를 RK4 상태로 사용한다.
RGR/S/W1/forcing은 구간 입력이며 해당 시각의 coupled RHS에 전달한다.
Tsum은 동일한 piecewise constant canopy temperature의 정확한 Fraction 적분을
사용한다. T24는 1차 filtered 온도 상태이며 실제 rolling average로 표시하지 않는다.

RK4의 동일 가중으로 photosynthesis/growth respiration·leaf/stem/fruit 유지 호흡,
leaf/stem 연속 제거·terminal C/N·entry N을 누적한다. 관리 제거 C/N은 사건 시 한 번 더한다.
임의 terminal C→생과 kg/수확·판매 환산은 없다.

    total_C = buffer+leaf+stem_root+sum(C_j)
    total_C-initial_C-cumulative_photo+cumulative_growth_respiration
      +cumulative_all_maintenance+cumulative_continuous_removal
      +cumulative_terminal_C+cumulative_event_C = 0
    sum(N_j)-initial_N-cumulative_entry_N+cumulative_terminal_N+cumulative_event_N = 0

각 step·경계/사건·출력에서 두 수지를 검사한다.
carbon/number scale은 각각 초기/현재 total 및 관련 누적량의 절대값과 1의 최대다.
budget은 `64*(accepted_steps+accepted_events+1)*ulp(scale)`이며 농장 정확도 기준이 아니다.
RHS 및 RK4 모든 trial/마지막 상태와 누적량의 유한/비음수·구획 C/N 조건을 검사한다.
음수·수지/원식 영역·양의 유량 underflow를 clipping으로 숨기지 않는다.

## 결과·오류와 재현

잘못된 입력/시간/예산은 preflight exception으로 거부한다.
실행 중 실패는 `status=hold`로 phase/time/reason·마지막 확인된 상태를 기록한다.
미확인 전체 미래 sample을 채우지 않는다. 완료/hold 모두 immutable input/solver와
model/profile/policy/code hash·Python version/time 규칙·origins/IDs를 manifest로 묶는다.
결과 hash는 실제 sample·누적 수지/사건 journal·hold와 manifest를 포함한다.
같은 지원 환경/입력에서 동일 결과와 hash를 재현해야 한다.

완료 sample에는 실제 계산 시각·기관/N/C 상태·파생 fruit/LAI·누적 수지/잔차·예산을
단위와 함께 넣는다. 연구 출력일 뿐 accepted Run/G1·실제 품종/생과/자원·경제 게시가 아니다.
새 결과/DB/API/3D는 이 단계 수용 뒤 새 계약으로 연결한다. 기존 저장 v1은 변경하지 않는다.

## 수용 기준

1. 고정 독립 Decimal coupled RHS/RK4와 일정 day/night forcing의 기관/N/C·누적량을 대사한다.
2. T24=Tcan인 일정 온도에서 N의 선형 50단 이동 해석해를 독립 계산해 대사한다.
   온도 필터/온도 합도 가능한 독립 해석해/정확 적분과 확인한다.
3. 간격 반감 시 coarse/fine/reference의 실제 오차 감소를 확인하고 각 오차/hold를 기록한다.
4. 구간/출력/초기·마지막 사건과 N/C 같은 비율 제거·누적량/두 보존을 확인한다.
5. 입력/프로필 불변·재현/manifest hash, 영역/고갈·빈 sink/entry·음수/비유한,
   시간/길이/step 예산·초과 제거와 실패 시 마지막 확인 상태를 검사한다.
6. 집중 regression과 changed files/hash/links를 확인한다. 실제 수행한 검증만 체크한다.

초기/자동 착과·실제 품종 forcing/QC와 국내 독립 농장 자료는 별도 병행 경로다.
전체 작기·미래 생산/마진·추천 게시는 기존 G0–G4 증거를 추가로 요구한다.
