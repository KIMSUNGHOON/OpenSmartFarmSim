# 검증된 Solar 입력의 결속 메타데이터 — 2026-10-19

[기계 증거](artifacts/solar-input-binding-metadata-20261019.json) · [내부 계약](../contracts/solar-input-binding-metadata-v1.md) · [선행 기각/원 CPU 관측](current-read-session-projection-evaluation-20261019.md).
현재 native Codex CLI `gpt-6.1-sol` / `xhigh`의 실제 turn_context 시각/해시를 기록했다. 재귀 CLI/하위 에이전트는 실행하지 않았다.

## 변경과 판단

한 실제 before→advance→confirm 관측에서 입력 검증41회, 검토82회, 현재 파일83회, software pin305회, 권리40회를 확인했다. 전체 record getter42회는7,667,856bytes를 읽었고, farm binding의 별도 전체 영수증 decode40회는7,465,640bytes를 읽었다. 두 준비 조회와40개 소비를 구분한다. 이 계측의 중첩 시간은 합산하거나 처리량으로 해석하지 않는다.

매번 모든 원 검증을 통과한 뒤 작은 결속 정보의 canonical bytes를 만든다. 새 getter는 같은 authority token·bytes/크기 경계를 확인하고 새 객체를 반환한다. 소비자는 여전히 매번 verify를 실행하며 원14개 출력만 조립한다. 원 전체 record/bytes/getter, 서명·schema·검토·현재 파일/해시·software pin·권리 검사와 공개 wire/DB 계약은 유지했다. 제품 변경은 두 모듈이며 새 의존성이나 교차 호출 cache는 없다.

## 최종 source 검증

**새7 + 소비/입력 증거74 + 실제 제품 paired1 + worker 정상/보류2 + 현재·늦은 권리4 = 고유88**을 로컬 소프트웨어 범위로 수용했다. 모든 stage의 backend app261파일 집계 SHA가 같다. 이전46/58, 사설 시험·계측, RED와 수정 전 소비자1건은 더하지 않는다.

- 새7: signed/full record와 결속 정보 일치, nested mutation 격리·불변 bytes·token/형식/크기 거부·권리 승인False.
- 소비/입력 증거74: 원14필드/전체 record 의미·중복 decode 제거, 원11프로그램/UTC·조회 재계산0, 위조25·현재 파일16·검토6/도중 변경8·software pin6·fresh Python1. 소비자 시험은 과거 Git 객체 없이 실행하도록 수정한 최종본이다.
- 정상/보류2: 실제16단계·start1/restore2, 모든 sample/event 원 값·UTC·checkpoint/counts·원자 결과/정상 게시1·보류 게시0·조회 계산0.
- 권리4: 현재 농장 권한/검토/원천, callback 도중6종 변경, 읽기 scope/늦은 철회, 직렬화 도중 원천 철회 차단·쓰기/계산0.
- 모든 stage: 보호5root·원본2,148/두 frozen UI,512MiB/PID·합1GiB, FD4→4·소유 PG/임시/passfile 잔여0. 해당 DB stage의 schema/role 잔여0을 확인했다.

| stage | 검사 | guard초 | 합 RSS 최대bytes |
|---|---:|---:|---:|
| focused-input-binding-metadata-green7-v1 | 7 | 2.137818 | 944,877,568 |
| focused-input-binding-evidence-regressions-v1 | 74 | 19.996740 | 1,005,465,600 |
| focused-product-input-binding-metadata-cost-v1 | 1 | 67.960681 | 1,004,150,784 |
| focused-input-binding-worker2-v1 | 2 | 129.181857 | 1,015,058,432 |
| focused-input-binding-current-rights4-v1 | 4 | 62.317399 | 1,031,585,792 |

## 실제 비용과 범위

| ABBA | 기존 full-record 소비 | 현재 제품 |
|---|---:|---:|
| 첫 짝 wall초 | 8.990801 | 8.884360 |
| 둘째 짝 wall초 | 9.184106 | 8.727891 |
| SQL / 역할 감사 / 원천 읽기 | 12,919 / 343 / 3,040 | 동일 |

평균 감소는 **3.0958%**, 짝별 감소는1.1839%/4.9674%다. 실제 최종 제품 메서드와 이전 `ffad57c`의 AST를 같은 작업에서 ABBA로 실행했다. 이전 함수도 현재 영수증의 코드 identity를 사용했고 검증 prefix/decorator의 AST 동일성을 대사했다. 계산 단계2→5의 counts/UTC04/06/08/10.123456Z를 유지했다. 이 비교에는 Python call profiler가 없고 SQL 관찰만 있다. 원천 순서 trace는 이 paired에서 측정하지 않았다.

앞선 사설 unprofiled 후보3.5128%와 구분한다. 별도 사설 call 계측의 네 ABBA 행에서 verify41/review82/current files83/pins305/rights40이 같았다. 이를 최종 제품의 독립 처리량 수용으로 바꾸지 않는다.

정확성·단순성·모듈 경계·현재성/오류 거부·실제 비용을 검토했다. 필수 검토 발견은 소비자 시험의 과거 Git 이력 의존성이었고 최종74검사 전에 제거했다. 전체 backend/browser·원 독립64·새 SIGKILL/전체 HTTP 회귀는 이번 source에서 실행하지 않았다. 기존 UI 코드는 변경하지 않았다.

## 후속 원천 비용 관측 — 수용88과 별도1

같은 app source의 원 quantum을 한 번 더 관측했다. 모든 원 메서드/결과를 유지하고 profiler를 복원했다. 원 step2/UTC04.123456Z, SQL12,919/감사343/원천3,040을 확인했다. 원천 읽기는 경제 입력1,360, 권리1,400, 경제 시나리오80(일반/핀 각40), joint shock80(각40), 정산 적용40, 정산 증거80이다.

선택한 중첩 호출만 뺀 CPU 관측은 source canonical3,040회/1.131초, model validate3,040회/0.719초, model dump6,080회/0.081초다. 전체 SQL execute는12,919회/포함wall7.018초·clientCPU4.471초다. 전체 quantum은wall22.163초로 profiler 오버헤드가 포함됐다. 이 수치의 비율을 실제 처리량·DB 서버 CPU·각 후보의 기대 이득으로 해석하지 않는다. 다음은 남은 원천/SQL 호출의 실제 기여도를 낮은 오버헤드로 좁힌 후 작은 후보를 정하는 것이다. 권한이나 변경 가능한 검증 결과를 재사용하지 않고, 기각된 getter 대체·세션3→1·역할15→4/pipeline/ACL/v4 후보는 반복하지 않는다.

원64/chunk1/조회·retry360초/RSS 정상→독립hold→HTTP취소→계산 중WebGL→WSL 용량/사용자 적용 순서를 유지한다. 이전 독립 CI39249166964는33/64로 미완료이며 현재성/정상 승인 자료가 아니다. 새 Solar 미배포·실제 농장 Run0·실제 자료 권리/독립 농장/미래/대응 비교·G0–G4 보류와 goal active를 유지한다. 이번88의 guard합281.594초는 실제 검증 작업량이며 전체 완료 날짜 추정이 아니다. 원 독립360초 수용과 외부 자료 확보 일정이 없어 전체 제품 날짜/잔여 시간은 미정이다.

최종 게시 `focused-input-binding-final88-status-v1`은 자식0/guard1.365544초였다. app261파일/새 tests SHA·로컬 링크2,387개·원 actor 해시와 두 HTTP200/동일 bytes/no-store·frozen HTML/환기2,173파일·5root/FD/정리를 확인했다. 진행 기록은2026-10-19T14:35:57.727475Z이며 새 Solar 배포 승인이 아니다. DOM/WebGL은 재실행하지 않았다.
