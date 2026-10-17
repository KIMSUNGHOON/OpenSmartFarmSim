# 독립 일사 계산의 실제 단계/시간 계측 — 2026-10-17

[기계 증거](artifacts/crop-solar-worker-progress-diagnostics-20261017.json) ·
[수용 계약](../contracts/crop-solar-worker-progress-diagnostics-v1.md) ·
[관찰 header](crop-solar-worker-progress-trace.py).

원 정상64걸음이360초 안에 끝나지 않은 이유를 조사한다. 원 입력·chunk1·조회 주기·
권리/취소/임대·판정·360초 계산/600초 감독·512MiB/PID·합1GiB를 유지했다.
관찰 header는 명시 진단 모드에만 주입하며 정상 실행 수용을 금지한다.

## 구현과 집중 검증

실제 메서드 진입/종료의 monotonic 시간과 반환 checkpoint/progress의 허용 metadata만 수집한다.
마지막 확정 값은 `_confirm`의 반환값이다. locals·입력/환경/예외 메시지·물리 상태값을 기록하지 않는다.
최근32사건/동시16단계/최근16예외·64KiB와 atomic replace를 적용했다.
중첩 포함 시간과 관찰 비용이 들어가므로 누적 시간을 합산하거나 제품 처리량으로 해석하지 않는다.

- 8820:1에서 관찰기 미구현의3실패를 보존했고,8887:0에서 비밀값 제외·유한 기록·
  실제 PIDfd SIGTERM 뒤 완결된 진행 파일 보존3검사를 통과했다.
- 90305:0에서 기존 web/native workflow 단계·원 prototype 보존, 통제된 예외 메시지 제외·
  실제 자식 종료7 거부·소유 정리를 확인했다.
- 모두 새5root/원2,148항목/기존 frozen source·자산·두 화면·한도·감독FD4→4·시험 소유/PG/임시/passfile0을 보존했다.

## 첫 실제 진단

[CI39031782329](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39031782329), sourcebe08f07은
실패로 종료했다. **마지막 반환 확정 checkpoint는3/64걸음·yielded·
2026-10-01T00:00:06.123456Z**다. 소프트웨어 합성 계산의 단계이며 농장 생장/생산 예측이 아니다.

| 관찰된 구간 | 완료 return 사건 | 중첩 포함 누적 초 | 단일 최대 초 |
| --- | ---: | ---: | ---: |
| worker `_before` |6|23.048|4.070|
| worker `_adopt` |1|7.512|7.512|
| worker `_confirm` |4|104.758|26.421|

advance의 외부 서버와 내부 Session이 같은 이름으로 합쳐져 그 누적값은 위 표에서 제외했다.
최근 사건에서는 내부 약40.506초를 감싼 외부 약44.282초가 별도로 관찰된다.
누적 기여율은 계산하지 않았다. 마지막 관찰 시각에는 advance가 실행 중이었고 worker 최종 outcome은 없다.
누락된 반환/완료 단계나 원 성능을 추정하지 않는다.

감독377.527초·자식1·원 시간 상한 종료·단일133,459,968/합376,705,024bytes,
FD7→7·소유 비좀비/임시0이다. 정상/DB 정리 proof는 없고 두 actor는-15로 정리됐다.
artifact12100682772/9,596bytes의 실제 run/head/ZIP digest·안전 경로와 header/actor/prototype hash를 대사했다.
hosted에는 로컬5root가 없으므로 이 자원 수치로 WSL 동시 용량을 수용하지 않는다.

## 실제 관측으로 고친 계측기와 다음 검사

원 progress는 root에 steps/status를 두고 checkpoint에는 별도 hash를 둔다.
v1은 그 hash를 먼저 선택해 `last_advanced`를 놓쳤다. 원 증거의 None은 그대로 보존했다.
또 외부/내부 advance 이름을 구별해야 한다.
두 실제 형태를 재현한35887:1에서2실패/기존3통과를 확인했고,
수정 후 **81261:0의5검사**를 통과했다. 누락 값을 소급 생성하지 않았다.

v2는 클래스별 단계 이름, root progress 우선과 원 times의 UTC를 사용한다.
검증/저장 경로의 guard/load/progress/prepare·farm current/input/registration·등록 조회·
입력 증거 verify와 모델 context/restore/chunk의 **시간만** 더 관찰한다.
물리 코드·계수·입력·현재 권리·cache·실행/자원 상한을 바꾸지 않았다.

## 실제 세부 진단과 좁힌 다음 경계

[CI39032832587](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39032832587),
source20d2d0f는360초 계산 상한에서 실패했다. 마지막 확정은 **16/64걸음·yielded·
2026-10-01T00:00:32.123456Z**, 마지막 advance 반환은17걸음·00:00:34.123456Z다.
두 값은 구분하며 미확정 걸음을 확정 진척으로 표시하지 않는다.

| 관찰된 구간 | 완료 return 사건 | 중첩 포함 누적 초 |
| --- | ---: | ---: |
| farm current |362|339.428|
| 농장 등록 읽기 |726|290.968|
| worker confirm |17|116.247|
| 모델 chunk |18|0.717|
| 모델 context 준비 |18|0.129|
| 모델 checkpoint 복원 |17|0.163|

등록 읽기는 current 안에 포함된다. 합산·기여율·원 처리량 또는 v1 대비 속도 개선을 주장하지 않는다.
관찰기 구현도 달라졌고 관찰 자체 비용이 포함된다.
종료 시 confirm→current→입력 증거 verify가 실행 중이었다. worker 최종 outcome은 없다.
감독374.858초·자식1·단일134,344,704/합370,135,040bytes·FD7→7·소유/임시0이며
정상/DB 정리 proof는 없다. 두 actor는-15다. artifact12101665601/14,070bytes의
run/head/ZIP digest·안전 경로·prototype/header/actor hash를 대사했다.

다음은 농장 등록 내부의 조회·현재 연구/맥락 검증·경제 참조·입력 compiler **시간만** 구분하는 단계다.
실제 자료를 반환하는 내부 함수를 재현한76226:1에서 신규1실패/기존5통과를 보존했고,
75150:0에서6검사를 통과했다. 반환 원문 미노출·확정 단계 불변과 기존 bounded/SIGTERM 검사를 포함한다.
새5root/원2,148항목·두 UI/소스·자원 상한·FD/소유/PG/임시/passfile0을 보존했다.

## 등록 내부 진단 완료와 선택한 수정

[CI39033602306](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39033602306),
source98bd4dc도 원360초 계산 상한에서 실패했다. 원 반환 확정/advance는 **15/64·yielded·
2026-10-01T00:00:30.123456Z**다. 관찰 메서드가 추가돼 이전 진단과 처리량을 비교하지 않는다.

| 관찰된 구간 | 완료 return 사건 | 중첩 포함 누적 초 |
| --- | ---: | ---: |
| 등록 `_prepare` |674|269.181|
| 경제 pin 검증 |674|159.035|
| 별도 hold 조회 |674|33.791|
| context 조회 |2022|49.780|
| 등록 `_find` |1348|33.540|
| 입력 compiler |674|3.080|
| 모델 chunk |17|0.721|

중첩 시간은 합산하지 않는다. 실제 SolarCustodyPending3사건도 관찰됐으며 최종 outcome은 없다.
감독376.526초·자식1·단일134,590,464/합375,115,776bytes·FD7→7·소유/임시0,
정상/DB 정리 proof 없음·두 actor -15다. artifact12101323115/19,919bytes와 실제
run/head/digest/안전 경로·header/actor/prototype hash를 대사했다.

다음 변경은 [현재 참조를 경제 pin과 같은 읽기 범위에 묶기](farm-pinned-context-reader-implementation-20261017.md)다.
이미 검증된 source-owned reader를 재사용하며 current 원 행/서명·권한·부적합 fallback을 유지했다.
실제 조합 조회 연결4→1·검증 순서/원 값 동일과14검사를 확인했다. 컴파일/cache·수식·상한은 바꾸지 않았다.
이 측정/진단 단계는 완료했지만 정상 실행·WSL 용량·S3/S4·새 Solar 적용·실제 자료/G0–G4는 미수용이다.
현재 native gpt-6.1-sol/xhigh 문맥의 실제 context/hash를 기록했다. 재귀 CLI·새 agent는 없다.
