# Solar checkpoint의 등록 읽기 범위 — 2026-10-19

[선행 진단](registration-connection-lifetime-phase-cost-20261019.md) · [기계 증거](artifacts/solar-checkpoint-registration-scope-20261019.json).
현재 native `gpt-6.1-sol` / `xhigh`의 turn_context 시각·해시를 기록했다. 재귀 CLI/하위 에이전트는 실행하지 않았다.

## 변경과 수용 범위

checkpoint `_current`가 기존 server 등록 범위 밖이면 그 호출 안에서만 기존 `registration_read_scope`를 연다. 안이면 기존 witness를 유지한다. 제품 변경은 checkpoint 한 파일의7추가/2삭제이며 새 API/의존성/권한 cache는 없다. 원 트랜잭션과 잠금 해제·현재 권리/원천 검사는 유지한다.

최종 같은 source의 **새6 + 기존 worker13 + paired1 = 고유20검사**로 이 작은 범위만 로컬 수용했다. 본체52/이전 관련58은 재실행 수에 합산하지 않는다. 원 독립64·계산 중 WebGL·새 Solar 사용자 적용 수용은 아니다.

## 기능·보안 검증

- 새6: 새 범위/기존 범위의 동일 witness·두 등록 읽기/재구성1/원천152회 순서·연결 종료; 두 읽기 사이 principal scope/실제 원문/실제 DB grant 변경과 복제 Context 거부. 확인 사건 생성0과 수명 종료를 확인했다.
- 기존5: 정상/hold의 실제16걸음·원 checkpoint/모든 sample/event 값과 UTC·start1/restore2·수량/출처·원자 결과/게시; chunk/terminal 취소; 임대 만료·attempt2 기존 prefix 채택/남은 구간만 계산.
- 기존8: 실제 검증 중6지점 취소가5초 안에 수락되고 checkpoint/결과 부분 게시가 rollback된다. confirm 입력 교체/finish 임대 만료도 거부한다.
- 모든 stage에서5root·원본2,148·frozen 두 UI·512MiB/PID/합1GiB·FD4→4·소유 PG/임시/passfile 잔여0을 확인했다. worker5는 관찰 환경변수 미설정으로 별도 JSON이 없으며 원 module-autouse pytest의 schema/role0 단언과 고정 log/guard로 증명했다. 나머지는 cleanup JSON도 대사했다. 독립 native64의 DB 정리 proof로 대체하지 않는다.

| stage | 검사 수 | guard(초) | 합 RSS 최대(bytes) |
|---|---:|---:|---:|
| focused-solar-checkpoint-scope-green-v2 | 6 | 85.373778 | 1,011,339,264 |
| focused-solar-checkpoint-scope-cost-v1 | 1 | 74.673434 | 1,005,391,872 |
| focused-checkpoint-scope-worker5-v1 | 5 | 255.803535 | 1,061,498,880 |
| focused-checkpoint-scope-worker8-v1 | 8 | 233.152041 | 1,041,784,832 |

## 실제 전체 묶음 비용

같은 실제 작업의 step2→5에서 **baseline/candidate/candidate/baseline**을 실행했다. baseline은 `63b3014`의 `_current` 함수 AST만 사설 시험의 해당 instance에 결합했다. 제품/SQL 결과를 대체하지 않았다. 관찰자는 실제 호출/반환과 연결 정리만 기록했다. 수식은 같은 source다.

| 항목 | baseline | candidate |
|---|---:|---:|
| 두 관측 wall(초) | 10.184751, 10.339553 | 9.787481, 9.718888 |
| 한 묶음 재구성 | 6 | 4 |
| 물리 연결 | 29 | 7 |
| 실제 역할 감사 | 373 | 343 |
| 전체 SQL | 13,321 | 12,919 |
| 원천 읽기/순서 | 3,040 | 3,040(동일 SHA) |

평균 wall 감소는 **4.960%**다. 모든 원 before/advance/confirm 호출을 수행했고 step2/3/4/5의 원 counts·UTC04/06/08/10.123456Z를 대사했다. 재구성 감소에 따라 내부 DB 감사 수는 변했으며, 원 연결 checkout의 현재 audit를 생략한 것은 아니다. 범위 밖 직접 연결은 원 방식이다. 이 작은 로컬 ABBA를 독립 처리량이나360초 수용으로 일반화하지 않는다.

## 검토·제한과 다음 단계

정확성·가독성·기존 모듈 경계·늦은 권리/변경 거부·실제 비용을 검토했다. 첫 두 실행은 selector/path 오류로 검사0이었다. 실제 RED는2회 재구성 단언 실패다. 첫 GREEN의3실패는 실제 거부의 expected 예외 목록 누락이어서 시험을 고쳤고 최종6을 재실행했다. 중간 통과 수는 합산하지 않았다.

전체 backend/browser·새 fresh exec/SIGKILL/독립64는 이 source에서 실행하지 않았다. [이전 정상 CI](registration-connection-lifetime-native-normal-20261019.md)는33/64, 단계 진단은17/64이며 두 결과를 속도 비교하지 않는다. 기존15→4 감사 SQL/pipeline/직접 ACL과 v4 getter 후보는 이미 기각돼 재적용하지 않는다.

현재 약5% 개선만으로 원64/chunk1/조회/retry360/RSS 기준을 통과했다고 볼 수 없다. 후속 exclusive 관측1회를 실제 같은 source에서 마쳤다(아래). 다음은 실제 호출자별 연결 매개변수 조회 비용 대사와 현재 검사 동등성을 보존하는 작은 후보의 비용 비교다. 변경 없는 native64 반복은 하지 않는다. 이후 원 독립 정상→hold→실제 HTTP 취소→계산 중 WebGL→WSL 용량/사용자 적용은 기존 계획을 따른다.

현재20검사의 guard 합은 649.003초다. 이는 이번 작업에 소요된 검증 시간이며 후속 수정의 완료 추정이 아니다. 실제 품종/계수·권리 있는 국내 독립 농장/시장 자료·현장/미래/비교/운영 관문은 남았다. 실제 농장 Run0·G0–G4 미평가·전체 완료일 미정·goal active다.

## 후속 exclusive 비용 관측 — 진단1, 수용20에 합산하지 않음

`focused-checkpoint-quantum-exclusive-profile-v1`은 실제 step2/UTC04.123456Z·원 before/advance/confirm과 profiler 자체 비용을 포함한 wall14.109949초를 관측했다. guard48.648041초·자식0·합982,925,312bytes·5root/원본/두 UI·FD4→4·DB/소유/임시 정리를 확인했다. 모든 함수는 원 실행이며 반환을 대체하지 않았다.

| 함수 | 호출 수 | exclusive초 | inclusive초(중첩) |
|---|---:|---:|---:|
| Psycopg Connection.wait | 13,648 | 3.028975 | 5.460484 |
| JSON iterencode | 12,516 | 0.950168 | 0.996143 |
| ConnectionInfo.get_parameters | 3,963 | 0.729313 | 1.188827 |
| cursor prepared send | 12,302 | 0.472120 | 0.472120 |
| JSON raw_decode | 3,053 | 0.453760 | 0.786611 |

**inclusive는 합산하지 않으며 profiler 포함 wall을 처리량으로 쓰지 않는다.** wait 관측을 네트워크/DB 단일 원인으로 단정하지 않는다. 현재 DTO 검증4,289회도 관측했지만 기본 getter/권리 검사를 생략하는 후보를 새로 수용하지 않았다.

다음 작은 작업은 get_parameters3,963회의 실제 호출 위치별 빈도/비용을 분리하고 필요한 현재 연결 값·인증/factory·세션 설정을 모두 유지하는 후보를 시험 전용으로 비교하는 것이다. 원 감사343·원천3,040/순서·수치/UTC·트랜잭션/수명/늦은 변경 거부와5root/상한/정리를 보존해야 한다. 설정 검사를 cache하거나 결과를 생략하지 않는다. 개선이 일관되지 않으면 미채택하며 독립64/chunk1/조회/retry360/RSS 기준은 유지한다.

최종 상태 게시 `focused-checkpoint-scope-final20-status-v1`은 실제 자식0·guard1.368087초였다. 로컬 링크2,378개·원 actor hash·5173/5174의 HTTP200/같은 bytes/no-store·frozen HTML/환기2,173파일/5root/원본/FD/정리를 확인했다. UI 코드/DOM/WebGL은 변경하거나 재실행하지 않았다.
