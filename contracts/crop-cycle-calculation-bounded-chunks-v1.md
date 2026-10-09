# 원 격자를 보존하는 제한된 계산 묶음 — v1 개발 계약

2026-10-08 KST. 작업 `crop-cycle-calculation-bounded-chunks`.
선행은 [4,096전이 순수 대사](../research/crop-cycle-calculation-chunk-feasibility-observed-20261008.md)와
[공개 provenance 연결](../research/crop-cycle-calculation-prefix-api-bridge-implementation-20261008.md)이다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단하며 재귀 CLI는 실행하지 않는다.

## 정책과 변경 경계

artifact가 요청할 수 있는 `max_transitions`의 상한을128에서4,096으로 바꾼다.
`max_steps` 상한10,000과 입력·모델·적분/출력 격자는 보존한다.
요청 budget은 최대치이며 정확히 그만큼 진행한다는 약속이 아니다.
계산 전에 현재 checkpoint 이후128번째 원 경계의 처리 완료 sequence를 읽고
그 지점까지의 남은 전이와 요청 상한 중 작은 값을 **실효 budget**으로 사용한다.
남은 경계가128개보다 적으면 마지막 원 경계를 사용한다.

원 격자의 경계 i를 처리한 sequence는 `row.steps + i + 1`이다.
현재 checkpoint의 sequence는 적분 걸음 수와 처리한 경계 수의 합이다.
이 관계는 초기·경계 대기 중인 step-end·경계 처리 뒤·forcing/사건이 겹친 상태에서 검증한다.
경계 하나는 출력 하나와 관리 사건 하나를 최대 한 번씩 처리하므로 호출당 두 종류의 행이 각각128개 이하다.
forcing만 있는 경계도 세며 출력이 드문 입력의 처리량에 이 추가 제한이 있을 수 있다.
격자를 건너뛰거나 출력·사건을 버리지 않는다. 최대 한 개의 원 격자 행만 미리 읽으며 RHS 전에 제한한다.

실제 실효 budget을 기존 commit의 `budget` 필드에 기록한다.
독립 delta validator도 그 budget이 현재 checkpoint의 경계 제한 이내인지 확인하고
각 종류의 행이128개를 넘으면 거부한다. writer의 mutable 상태만으로 승인하지 않는다.
단일 page2MiB/128행·delta8MiB·16page/commit·metadata128KiB와 모든 디렉터리/파일/commit 한도는 같다.

첫 core는 artifact module·서버 custody module·새 집중 시험·기존 잘못된 budget 반례와 이 계약이다.
artifact의 물리 형식/참조는 `crop-cycle-verified-artifact-v1`을 유지하되 실제 새 code SHA가 header에 결속한다.
기존 header를 현재 코드로 묵시 채택하지 않는다. DB schema/API/SDK 필드·CLI·CI 설정은 변경하지 않는다.

## 서버 판본과 보존

서버/intent/HEAD proof는 각각 `crop-cycle-verified-server-custody-v3`,
`crop-cycle-verified-server-intent-v3`, `crop-cycle-verified-server-head-v3`다.
HMAC domain은 각각 identity/intent/head의 기존 이름에서 판본만v3로 바꾸고 NUL 종료를 유지한다.
v1/v2 파일·서명·입력·과거 결과는 보존하고 새 코드로 재발급·변환·묵시 재개하지 않는다.
현재 bytes/HMAC 체인, 입력·농장 권리와 candidate 검사 뒤 마지막 guard/atomic HEAD 순서를 유지한다.
terminal 발행의 기존 전체 물리 QC도 유지한다. 조회·완료 재시도에서 RHS를 실행하지 않는다.

## 수용 기준

1. 실제 writer의4,096 요청 거부를 RED로 기록한 뒤 새 경로를 수용한다.
2. 기존6개 정상 프로그램·수치 hold·빈 과거와 조밀한 출력/사건에서 원 수치/UTC·순서·수지·누적을 대사한다.
   실제 engine 호출 전에 실효 budget을 확인하고 요청 dict를 변경하지 않는다.
   각 종류128행·기존 bytes 한도를 지키며 남은 행은 다음 호출에서 한 번만 처리한다.
3. 단계 중간/경계 대기/처리 뒤의 복원, 다른 예산 분할, 별도 Python 재개와 원 checkpoint의 비계보 필드를 대사한다.
   재해시한 과대 budget·128행 초과·잘못된 수치/페이지·원판본 proof는 거부한다.
4. 기존 artifact/prefix/custody의 bytes 변조·현재 권리·늦은 철회·crash/HEAD/fresh Python·자원 반례를 확인한다.
5. 전체 합성 입력의 실제 첫4,096전이를 artifact에 저장하고 고정된128전이32회와
   비계보 checkpoint 전체/원105출력/2사건을 대사한다. 조회 RHS0·원 입력/이력·source/FD/cache를 보존한다.
6. nice19·소유 무거운 작업 하나씩 실행하고 실제 종료/PID identity·로그 SHA·임시 경로 정리를 기록한다.
   작은 회귀 예산600초, 실제4,096 저장 관측 예산240초는 선행190.99초 API 회귀와55.567초 순수 관측에 근거한다.
   관측 만료로 명령을 다시 시작하지 않는다. 보고서·불변 receipt 뒤 이 자식만 체크한다.

다음 단계의 실제 등록 농장/SCRAM에서 큰 묶음 두 번과 재개·권리 철회·저장 비용을 관측한 뒤
전체166일 등록 실행 예산을 정한다. 현재 HTTP30초·worker lease/cancel 설정은 바꾸지 않는다.
전체166일 DB/API/같은 UTC3D·생과/자원/Decimal 경제 연결과 실제 자료 관문은 별도다.
실제 품종 입력/국내 독립 자료/측정 농장 작물 Run0건, G0–G4 `not_assessed`, 예측·추천 hold를 유지한다.
