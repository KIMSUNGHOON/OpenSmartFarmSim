# 계산 중 여러 저장 시점의 실제 갱신 관측 v1

상태: **2026-10-11 [A1 계약/128초 입력 재현](../research/crop-climate-joint-prefix-advance-input-20261011.md) 수용. [A2 실제 연속 갱신/사용자 연결](../research/crop-climate-joint-prefix-advance-browser-20261011.md) 수용: running 원5시점→terminal 원9시점/3사건·재접속/원본·두 주소 복구.**
선행 [P6b 사용자 활성화](../research/crop-climate-joint-prefix-user-activation-20261011.md)는
32초 입력에서 running 원 저장1시점→terminal 원3시점을 확인했다.
이 자식은 [확정 prefix 계약](crop-climate-joint-prefix-view-v1.md)의 원값/권리 경계를 유지하면서
같은 실행의 서로 다른 계산 시점이 실제 화면에 갱신되는 증거를 추가한다.

## 입력 판본과 계산

원 normal의 scenario·4개 profile·notice·UTC origin·2초 격자·관리 사건0/8/16을 그대로 사용한다.
새 사용자 소유 합성 판본은 종료 step16→64, 출력 `[0,8,16]`→`[0,8,...,64]`만 확장한다.
기간은32→128초이며 같은 관리 사건의 원 시각은 바꾸지 않는다.
새 source/context/time-binding/evidence SHA·검토/결정 ID와 권리 선언을 만들고 기존 판본을 보존한다.
입력의 존재나 새 서명은 현장 자료 승인/품종 보정이 아니다.

서버 채택 전에 같은 원 context의 일괄 계산과 chunk8 복원 계산을 별도 실행해
모든 sample/event·마지막 상태/checkpoint bytes·원 UTC가 같은지 대사한다.
수치 hold가 발생하면 정상 입력이라고 게시하지 않는다. 기존 모델의 수지/물리 범위 검사도 유지한다.
이 비교는 새128초 입력의 소프트웨어 재현 검증이며 독립 농장 검증이나 정확도 증거는 아니다.

기존 사용자 DB/키를 사용하는 새 입력은 reviews/rights/runtime의 **새 판본과 활성 포인터**로 연결한다.
기존 항목·입력 파일·작업·결과·키는 보존한다. API/worker가 시작 시 resolver를 고정하므로
새 입력 연결은 유지보수 창에서 정상 재기동해야 한다. 같은 파일 재접수는 같은 실행으로 연결한다.
적용이 실패하면 기존 입력/권리 판본과 원 frozen 제품으로 복구하고 실패 원인을 남긴다.

## 실제 브라우저 수용

기존 [reference MJS](../research/crop-climate-joint-prefix-browser-reference.mjs)의 `live-advance`를 사용한다.
실제 SCRAM·TLS·자동 worker(chunk8)·제품 UI를 사용하고 기존 정상/hold/취소 검증을 대체하지 않는다.

1. 빈 상태의 장면 없음→새 입력 접수→같은 실행의 확정 prefix를 순차 조회한다.
2. 서로 다른 **원 UTC2개 이상**의 WebGL 장면을 계산 중 관측한다.
   selector만 달라지고 선택 UTC가 같은 경우는 추가 갱신으로 세지 않는다.
   UTC·publication sequence가 전진하고 원 작물/기후/구획 수치도 바뀌어야 한다.
3. 각 장면의 LAI·50과실 C/개수·온도·표/그래프/사건은 같은 selector의 원 HTTP200과 대사한다.
   관측한 벽시계 UTC는 계산 시각과 별도 기록한다. 실제 DB의 최종 상태/종료 시각과 대조해
   관측들이 terminal 이전이었는지 확인한다.
4. 완료 결과의 같은 원 sample/event·binary64/UTC와 재접속 시 같은 결과를 확인한다.
   첫 장면과 전진한 장면의 실제 원 PNG/응답 SHA를 기록한다.
5. 기존 두 주소·작업/결과/파일/키·권리와 새 작업/결과의 결속, 실제 도구 종료·FD/소유 정리를 대사한다.

현재 reader의 순차 조회/10초 대기와 오류 backoff를 유지한다. 작업자를 멈추거나
인위적인 sleep·저예산 전환·가짜 checkpoint·보간 장면으로 관측 시간을 만들지 않는다.
더 긴 **실제 계산 구간**이 필요한 경우 입력 판본/재현 검증을 먼저 갱신한다.
관측 시간 초과만으로 새 작업을 접수하지 않는다. 원 작업의 실제 상태부터 확인한다.

## 자원과 후속

기존512MiB 단일/1GiB 합산·0.25초 관측과 정확한 프로세스 identity 보호를 적용한다.
P6b의 browser 합산1,010,683,904bytes는 legacy 정지 상태의 관측이므로
두 사용자 서버와 브라우저를 그대로 병행하는 용량 증거가 아니다.
검증 전 기존 서비스와 입력/권리 판본의 복구 절차를 준비하고, 필요한 유지보수 뒤 두 주소를 복구한다.
이 수용은128초의 실제 저장값 갱신으로 한정한다. 전체 작기·가변 기상/온실 경계·물/양분/구매 에너지·
생산량/Decimal 경제·최종 U3/통합 UI와 실제 자료/관문은 별도다.

작업과 잠정 시간은 [U3 할 일](../tasks/todo.md#최종-제품-ui-통합-2026-10-09)과
[계획](../tasks/plan.md#joint-prefix-view-20261010)을 따른다.
