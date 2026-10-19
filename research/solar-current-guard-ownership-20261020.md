# 현재 농장 검증의 호출 위치 정리 — 2026-10-20 KST

[기계 증거](artifacts/solar-current-guard-ownership-20261020.json) · [현재 물리 농장 뷰 계약](../contracts/solar-current-physical-farm-view-v1.md) · [선행 진단/연결 검토](solar-current-validation-boundary-review-20261019.md).
현재 native Codex CLI `gpt-6.1-sol` / `xhigh`의 실제 turn_context 시각·해시를 기록했다. 재귀 CLI/하위 에이전트는 실행하지 않았다.

## 설계 결정과 구현

현재 등록의 full farm/source-binding hash는 경제 계획과 현재 경제 참조/권리까지 포함한다. 기존 `read_registration`과 `SolarFarmBinding._registration`을 계속 사용한다. 별도 물리 전용 reader/권한 판본을 추가하거나 raw row/과거 승인으로 현재 검증을 대신하지 않았다. 경제 자료의 현재 철회도 계속 v1 계산·게시·표시를 차단한다.

현재 source/권리/경제 verifier의 내용은 그대로다. 두 기존 모듈의7줄 추가/7줄 삭제로 중복 호출 위치만 정리했다.

- private prepare closure는 원 Context/record 일치를 확인한 제안을 반환한다. 바로 호출한 `_Session.advance`가 원 full guard를 유지해 start/restore/advance 전에 다시 확인한다. 안쪽의 연속된 post-prepare guard 하나를 제거했다.
- `_open(..., entry_guard=True)`의 기본 즉시 검증은 유지한다. exact-bool·custody `write=False`일 때만 명시적으로 최초 `session.progress()`에 검증을 맡길 수 있다. 호출자는 inspect/page/checkpoint `_session` 세 곳이다. `write=False`는 custody 쓰기/계산 금지이며, 외부 checkpoint DB transaction 전체가 SQL read-only라는 주장이 아니다.
- 직접 binding bytes를 읽는 기존 `_open` 소비자와 result/query session은 기본 즉시 검증을 유지한다. checkpoint는 private signed binding 비교 후 첫 progress full guard를 통과해야 history/DB 쓰기로 진행한다.
- `_Session._guard/_publish/progress/advance`와 checkpoint confirm 본체의 AST는 원 source와 같다. read-lock 재확인, 계산 전후·proof/HEAD 전후·조회 전후·lease/cancel/원자 게시의 원 검증을 유지했다. 권한/검증 결과 cache는 추가하지 않았다.

## 최종 같은 app source 검증

**새 경계4 + 제품 비교1 + worker13 + 읽기 경합7 + query13 + HTTP24 + 실제 TLS1 + fresh producer1 = 고유64 집중 검사**다. 원64단계 독립 정상 실행은 별도 관문이다. 기존88/46·사설 후보/RED·actor 정적 확인은64에 더하지 않았다. 각 stage의 app261파일 집계 SHA를 대사했다.

- 경계4: private 옵션의 형식/쓰기 거부, 기존 binding reader의 즉시 검증, 첫 load 전·반환 전 전체 검증, 준비 반환 직후 물리/경제 권리를 각각 철회하면 continuation0/HEAD0.
- worker13: 실제 normal/hold16단계·start1/restore2·모든 sample/event 값·UTC·원자 게시/보류, 취소·임대/재시도·검증 중 취소·늦은 입력/만료 거부.
- 읽기 경합7/query13: 검증 도중 writer 전진·재잠금 실패/이름 교체·같은 HEAD의 실패 게시·권리 철회에 stale/partial 반환0. 원 checkpoint/counts/최초 시각·중복/새 attempt·정상/hold/fresh, 조회 계산/SQL 쓰기0.
- HTTP24는 endpoint의 고정 실패/후속 account 검증을 확인하는 집중 검사다. 별도 실제 SCRAM/검증 TLS1은 capture 변경503/오류만 반환·복구200/권리422/scope403·DB 불변을 확인했다. 복구200은 checkpoint_status=unavailable, checkpoint/result=null이며 승인된 새 prefix 반환이 아니다.
- fresh producer1: 독립 exec의 원16걸음/2사건·원 모든 값/UTC·선택된 proof/HEAD·원 호출, 완료 inspect/page의 수치 재계산0을 확인했다.
- 보호5root·원본2,148/두 frozen UI,512MiB/PID·합1GiB, FD4→4와 소유 PG/임시/passfile 잔여0을 유지했다. 해당 fixture의 schema/role 정리도 확인했다.

| stage | 검사 | guard초 | 합 RSS 최대bytes |
|---|---:|---:|---:|
| focused-solar-guard-ownership-green4-v1 | 4 | 67.331983 | 1,004,310,528 |
| focused-solar-guard-ownership-product-cost-v1 | 1 | 64.815760 | 1,011,150,848 |
| focused-solar-guard-worker5-v1 | 5 | 225.640481 | 1,066,504,192 |
| focused-solar-guard-worker8-v1 | 8 | 212.885715 | 1,051,271,168 |
| focused-solar-guard-readlocks7-v1 | 7 | 187.721777 | 1,021,480,960 |
| focused-solar-guard-query6-v1 | 6 | 155.637068 | 1,025,417,216 |
| focused-solar-guard-query7-v1 | 7 | 231.072752 | 1,053,388,800 |
| focused-solar-guard-HTTP24-v1 | 24 | 2.392391 | 946,085,888 |
| focused-solar-guard-TLS1-v1 | 1 | 38.870138 | 1,052,479,488 |
| focused-solar-guard-fresh1-v1 | 1 | 41.464727 | 1,049,993,216 |

## 실제 제품 비용

| ABBA | 이전 함수/c0309dc | 현재 제품 |
|---|---:|---:|
| 첫 짝 wall초 | 8.870493 | 7.955378 |
| 둘째 짝 wall초 | 8.867717 | 8.218845 |
| SQL | 12,919 | 11,723 |
| full role 감사 | 343 | 315 |
| 원천 읽기 | 3,040 | 2,736 |

최종 제품의 평균 감소는 **8.8171%**, 짝별10.3164%/7.3172%다. 사설 시험9.2448%와 구분한다. 실제 제품 네 메서드 AST가 사설 후보와 같은 것을 별도 확인하고 최종 module source에서 다시 비교했다. 이전 함수도 현재 코드/영수증 identity를 사용해 같은 실제 작업의 단계2→5·counts/UTC04/06/08/10.123456Z를 대사했다. profiler 없이 SQL 관찰만 사용했다. 원천 순서 trace는 이 비교에서 측정하지 않았고 중복 검증 호출 수가 줄었으므로 원 전체 순서 SHA 동일성을 주장하지 않는다.

2% 이상/두 짝 감소 기준을 통과한 로컬 소프트웨어 관측이다. 원 source/farm/economic/current-rights verifier의 구현은 바꾸지 않았다. 이것을 독립 처리량/원360초나 실제 품종의 생장·수익 검증으로 확대하지 않는다.

RED1은 구현 전 private entry_guard 인자 부재를 확인했다. 순차 실행 도중 결과 요약 helper의 정규식 escaping이 잘못돼 중단됐지만 해당 controller0/실제 worker5 통과·정리 증거는 유효했다. 요약을 수정하고 나머지만 이어 실행했으며 통과5를 재실행/중복 합산하지 않았다. 정확성·단순성·Interface/현재성/권리·실제 비용을 검토했다.

## 원 독립 관문과 다음 작업

원 actor preflight에서 API/worker 본문·단언과 SHA를 대사했다. API는`ab5a93aed402874bb85f723f272feafd64a44b257f6351256fc84b01b4769cba`, worker는`14fe24de5cf95f3f43a955b0e5c042a39d802d3dc3e67c89f6458b33448fade6`이며 전체 값은 기계 증거에 있다. 원 fixture/모델 입력·64/chunk1/poll/retry360/RSS를 바꾸지 않았다. 서로 다른 더 쉬운 물리-only 입력으로 원 실패를 대체하지 않는다.

다음은 위 로컬 수용 source의 **계측 OFF 원 독립64 정상**이다. 원 actor0/0·64/start1/CLI0/attempt1/success1·두 전진 prefix/원 값·UTC·정리를 확인한다. 이전 f403b54/CI39249166964의33/64 실패와 진단 CI39250605987의17/64는 보존한다. 이번64 집중 검사는 독립 정상·전체 backend/browser·배포/G4를 뜻하지 않는다.

독립 정상 이후 hold→실제 HTTP취소→계산 중WebGL→WSL 동시 용량/사용자 적용을 진행한다. 새 Solar 미배포·실제 농장 Run0·실제 자료 권리/독립 국내 품종·현장/미래/대응 비교와 G0–G4 보류, goal active를 유지한다. 코드가 pin된 구 artifact의 배포/이전도 이번에 수용하지 않았다. 검증 guard합1,227.833초는 실제 수행량이며 전체 제품/외부 자료 확보 날짜 추정이 아니다. 전체 완료일과 남은 시간은 미정이다.

최종 게시 `focused-solar-guard-final64-status-v1`은 자식0/guard1.361325초였다. app261파일/새 test·stage별 SHA·원 actor/단언·로컬 링크2,505개·두 HTTP200/동일bytes/no-store·frozen HTML/환기2,173파일·5root/FD/정리를 대사했다. 진행 기록 시각은2026-10-19T15:44:42.529411Z이며 UI 코드/DOM/WebGL은 재검증하지 않았다.
