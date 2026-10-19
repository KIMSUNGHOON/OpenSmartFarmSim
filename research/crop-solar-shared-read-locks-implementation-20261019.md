# Solar 읽기 공유 잠금 로컬 수용 — 2026-10-19 KST

상태: **55개 고유 검사·검토로 로컬 소프트웨어 수용. 원 독립64는22/64·시간 제한으로 미완료**.
[계약](../contracts/crop-solar-custody-shared-read-locks-v1.md) ·
[실제 진단](crop-solar-audit-scope-v2-worker-api-diagnostic-20261019.md) ·
[기계 증거](artifacts/crop-solar-shared-read-locks-implementation-20261019.json).

## 변경

공통 `_file`의 기본 배타 잠금은 유지한다. 명시적 shared read는 같은 기존 lock 파일을
읽기 전용으로 열고 `LOCK_SH|LOCK_NB`를 사용한다. 파일을 만들지 않는다.
Solar `_open(write=False)`만 root/intent shared lock을 선택하고, write=True는 원 배타 잠금이다.
읽기 intent는 원 bytes 비교로 확인하고 `_immutable`의 파일 생성 경로를 사용하지 않는다.

읽기 세션의 prepare/advance/HEAD·proof 게시를 실제 수치/파일 작업 이전에 거부한다.
기존 prefix의 수동 read session도 읽기 모드다. 권리/원문/코드 pin·HMAC·ancestry·원 값/UTC와
기존 모든 current 검사는 유지한다. 원 worker/query/probe·수식/입력·retry/360초/RSS를 바꾸지 않았다.

## 실제 검증과 한계

11456:1에서 실제 읽기 세션이 열린 동안 다른 실행 문맥의 checkpoint 확인이
`SolarCustodyPending`으로 실패했다. 부모 문맥의 예외 변환을 피하도록 테스트가 자식 오류를
부모 종료 뒤 다시 내보낸 RED다. 2892:0에서 같은 검사와 원 head/proof/UTC가 통과했다.
이 검사는 아래9건에 포함되므로 중복 합산하지 않는다.

| 현재 source의 검사 | 고유 수 | 실제 도구 |
| --- | ---: | --- |
| 실제 reader/confirm·조회/중복 확인 공존, 독립 process/open description, writer 배제/해제, 읽기 변경/빠진 파일 생성 금지 |9|76849:0|
| 기존 helper 기본 동작·파일 보안·권리 철회 |7|19041:0|
| Solar 권리/잠금·서명 변조/늦은 게시 거부·수치 보류·서명 도메인 분리 |4|10790:0|
| 실제 작업자 정상 완료/수치 보류·원 결과/UTC·원자 게시 |2|44828:0|
| 청크/terminal 취소·임대 만료와 새 시도의 원 prefix 인계 |3|67846:0|
| 검증 전후·확인·완료/게시의6지점 동시 취소와 결과 미게시 |6|94370:0|
| 잠금 밖 검증 도중 입력 변경/임대 만료 차단 |2|20874:0|
| 진행 none/current·heartbeat/새 시도·미확정/실제 EX 충돌·현재/늦은 권리와 직렬화 철회 |6|60265:0|
| query followup EX/해제·HEAD 전진/변조·디렉터리 교체·정상/hold 결과 조회 |7|34045:0|
| prefix 읽기 전용·현재/늦은 권리·취소·선택자/실제 EX 아래 무잠금 불변 읽기 |5|3791:0|
| prefix 원 페이지/희소 UTC·서명 이력 rollback/fork 거부·정상/hold 종료 |4|8022:0|

모든 현재 source pin이 같으며5root/동적 자식·원본2,148항목·frozen source/assets·두 화면,
512MiB/PID/합1GiB·FD4→4·소유 비좀비/PG/임시/passfile0을 확인했다.
현재 통과 검사의 최대 합 RSS1,047,568,384bytes다.11개 guard 합계1,927.082초다.
첫 추가 묶음10219:2는 DB fixture 매개변수가 단독 OS 검사에도 적용된 수집 오류로 실행 검사가0개다.
단독 OS 검사를 분리했고 실패를 수용 수에 넣지 않았다.

**검토:** 제품 수정은2개 app 파일뿐이다. helper 기본 EX·writer root/intent EX·파일 보안/lock 순서,
현재 권리/원천·HMAC/ancestry/디렉터리 identity 검사를 유지한다. 읽기 모드의 수치/게시/파일 변경을
이전 단계에서 차단했다. 원 worker/query/prefix·수식/입력·actor/probe/workflow·retry/360초/RSS는 그대로다.
별도 open description의 실제 EX를 사용하는 시험 변경으로 이전 배타 reader 가정을 교체했다.
6파일 syntax·git diff 검토와 고유55건의 현재2app pin을 확인했고 추가 제품 수정 사유는 없었다.

**남은 검증:** 원 계측 OFF64 독립 정상 → 독립 unpaused hold → 실제 HTTP 취소 → 계산 중 WebGL →
WSL 용량·사용자 적용이다. 원 actor 종료0/64·두 전진 prefix·원 수치/UTC·전체 owned 정리가 필요하다.
전체 backend/browser·fresh exec/SIGKILL은 현재 후보에서 재실행하지 않았다.
55개 통과나 통제된 thread 공존을 독립 unpaused64 완료로 표시하지 않는다.
앞선116검사는 sourceeb943d9의 기록이며 이 후보의 새 source 전체 검사 수로 합산하지 않는다.

native `gpt-6.1-sol/xhigh`에서 구현·판단을 수행했으며 재귀 CLI/서브에이전트는 없다.
원 정상22/64 미완료·진단8/64 queued/busy는 현재 변경으로 해결됐다고 주장하지 않는다.
새 Solar 배포·계산 중3D·실제 농장0/권리/독립 G0–G4·전체 완료일은 미수용/미정이며 goal active다.

76973:0에서 당시20검사·후보 미채택/남은 회귀를 두 UI에 no-store 동일 bytes로 게시했다.
현재2app source/syntax·문서 링크2,301개·원 actor/worker/query/probe·HTML/환기 frozen2,173파일,
5root/원본/상한/FD·소유 정리를 확인했다. UI 코드/DOM/WebGL을 변경하거나 재검사하지 않았다.

조회 후속 검사의 이전 read=False는 이제 shared이므로, 쓰기 충돌 fixture는 별도 open description의
실제 root/intent 배타 잠금을 잡도록 수정했다. 미확정 descendant와 확인된 최신 HEAD의 잠금 보류를
각각 검사했다. prefix의 기존 무잠금 불변 페이지 읽기도 실제 배타 잠금 아래에서 확인했다.
미확정/실제 EX 충돌은60265:0, followup EX/해제는34045:0, prefix EX는3791:0에서 통과했다.
제품의2개 app 파일은 추가 변경하지 않았다.24986:0에서는 중간39건을 두 UI에 게시하고
source/actor/header·2,301링크·frozen2,173파일/HTML·5root/상한/정리를 확인했다.
8308:0에서55건의 로컬 수용 상태를 두 UI에 게시했고 같은 HTTP bytes/no-store·2,301링크·frozen HTML/2,173파일·5root/상한/정리를 확인했다. UI 코드/DOM/WebGL은 변경·재검사하지 않았다.

로컬 수용 commit `4478d28e8633f5c96be62974234e2d576fa3ed66`의 원 계측 OFF 독립64
[CI39197827938](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39197827938)은 원360초/guard382.741초로 실패했다.
두 actor는 정리에서-15로 종료됐고 resource reason은null이다. 합 RSS364,638,208bytes·단일127,266,816bytes,
FD7→7·소유 비좀비/임시0을 확인했으나 정상/DB 정리 proof는 없다.
종료 뒤 같은 owned cluster의 Read Only/Repeatable Read metadata만22/64·yielded·sequence23,
UTC `2026-10-01T00:00:44.123456Z`·attempt1/simulating이다. 현재 권리/자료 검증이나 정상 수용이 아니다.
원 actor/query/prototype 해시를 대사했고 ZIP은id12163340617/3,286bytes,
SHA256 `01580126142fd287a845cb8c3e2728d2435d4e71657c6e1074448760452e0445`다.
이전 source의22/64와 같은 저장 수만으로 전체 처리량 개선/회귀나 충돌 해결을 주장하지 않는다.
다음은 현재 source의 한 청크 비용과 기존 bounded worker/API 관찰1회다. 새 기반 작업을 추가하지 않고,
현재 실제 단계 시간/예외와 원천/권리/원 UTC를 대사해 다음 수정 범위를 정한다. 같은 원 정상을 재실행하지 않는다.

약32.1분은 위55검사의 관측된 로컬 guard 시간이다. CI 대기·독립 실행/후속3D와 실제 자료 확보가
미완료여서 전체 완료 날짜는 정하지 않는다. 기존 두 UI는 이전에 수용된 합성 저장3D/환기를 유지한다.

## 현재 한 청크 관측 — 76498:0

현재4c4cff8(제품2파일은db75545와 동일)의 실제1→2/원16단계 fixture를 계측했다.
계측 청크9.731752초·전체 guard43.390초, current12/등록24/재구성1·연결144/감사183/원천1,824,
원천 조회 순서 hash `7b1fb256c577daf82221447c22b02c3697f014737e136837f04e0678d41ea401`를 확인했다.
SQL은7,113회/execute3.918210초다. 등록 읽기24회7.606876초·current12회9.300036초는
중첩·계측 overhead를 포함하므로 더하거나 전체 경로 기여율/64단계 처리량으로 환산하지 않는다.
역할 감사 호출자는 job72/thermal48/market24/source24/reference13/candidate2다.
원 UTC02.123456Z→04.123456Z·원 proof3개의 inode/mode/size/time/hash와 directory identity를 보존했다.
5root/원본/frozen·512MiB/PID/합1GiB·최대 합996,966,400bytes·FD4→4·소유 자원/passfile/역할/schema0을 확인했다.
이1건은 진단이며 앞선55건에 합산하지 않는다. 앞선EB의9.707초와 비교한 속도 개선도 주장하지 않는다.

현재 source의 bounded worker/API [CI39198782317](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39198782317)이
완료됐다(실패·관측만 수용). 정확한 head는 `4c4cff80002cc64508dd9af1a3757e5d0ba7bfa9`이며 원 actor 본문/64/chunk1/
조회·retry360/RSS는 유지하고 기존 선택 header만 켰다. 진단은 정상 수용을 금지한다.
현재 등록/current 검사의 반복 비용 관측과 실제 동시 단계/예외를 함께 대사한 뒤 다음 최소 수정을 정한다.

## 현재 worker/API 진단 — CI39198782317

정확한 actor/header·run/head·원 prototype/query hash와 ZIP digest/path를 대사했다.
artifact12162884097/24,715bytes·SHA256 `4dd5e5c21e6f29199ae80543c04382d2dad5add258019c2d35cf93e4fbb27d85`다.
원360초/guard385.006초·자식1/두 actor-15·자원 reasonnull로 종료했다. 최대 합367,403,008bytes,
단일129,609,728bytes·FD7→7·소유 비좀비/임시0이며 정상/DB 정리 proof는 없다.
실제 마지막 확인은15/64·yielded·UTC30.123456Z, 종료 후 metadata도15/64/sequence16/attempt1/simulating이다.
worker-api의 last_adopted/last_advanced/outcome은null이며 그 값을 추정하지 않는다.

| 실제 단계 | call/return | 예외 사건 | 중첩 포함 초 |
| --- | ---: | ---: | ---: |
| adopt |1/1|0|1.855483|
| before |25/25|0|39.327364|
| confirm |16/16|0|123.655036|
| custody_call |34/33|7|323.280593|
| run_once |1/0|0|아직 반환 없음|

이 시간은 겹치고 관찰 overhead를 포함하므로 합산하거나 전후 처리량으로 비교하지 않는다.
남은 active는run_once/custody_call이다. 최근32사건/127drop이며 caught14기록은
writer advance→_open의 SolarCustodyPending7사건이 raise/handler에 각각 기록된 것이다.
confirm의16반환에서는 예외 사건0을 관측했지만 전체 충돌 해결이나 정상 완료를 뜻하지 않는다.
HTTP25건은202×1/200×20/503×4(`solar_execution_unavailable`), accepted prefix14건을 포함한다.
HTTPdrop0, 예외는최근16개(StopIteration12/StopAsyncIteration4)·46drop이므로 전체 무오류를 주장하지 않는다.

현재 증거는 비싼 current 검증과 reader SH가 writer EX를 막는 구간의 재검토를 정당화한다.
다음은 [읽기 current 검증의 잠금 구간 후보](../contracts/crop-solar-read-validation-lock-v1.md)의
실제 writer/reader RED → 짧은 공유 잠금 아래 snapshot capture/재확인 → 현재 권리/HEAD/identity/원 값·UTC 회귀다.
권리/감사 결과를 캐시하거나 검사를 생략하지 않고 writer EX·원 retry360/RSS·수식/입력을 유지한다.
이 후보는 미구현·미수용이며 이전55건의 소프트웨어 수용과 독립 원64 미수용을 구분한다.

## 후속 잠금 구간 후보의 실제 RED — 41317:1

원 source의 실제 reader가 `_load`로 step1을 잡은 뒤 current 검증에서 기다리게 했고,
별도 문맥의 실제 writer `advance(budget=1)`가 SolarCustodyPending으로 거부됐다.
reader를 finally에서 해제하고 thread/context 종료 후 writer 예외를 다시 내보냈다.
따라서 수집/fixture 오류가 아닌 새 요구의 의미 있는 RED다. 새 동작의 GREEN은 아직 없다.
guard35.829초·합 RSS992,784,384bytes·source/5root/원본/frozen/FD4→4·소유 PG/임시/passfile0을 보존했다.
이 실패는 앞선55건의 수용 수에 포함하지 않는다. 제품2개 파일도 추가 변경하지 않았다.

다음 한 단계의 수용 기준은 실제 writer가 검증 대기 중step2를 원 UTC로 게시하고,
그 사이 HEAD가 바뀐 reader는 부분 bytes 없이 Pending, 이후 fresh read는 실제step2와 일치하는 것이다.
짧은 SH capture/재확인·writer EX·현재 권리/원천/identity와 원 retry/시간/RSS를 유지한다.
현재 후보는 설계/RED만 완료했고 구현·관련 회귀·독립 원64/계산 중3D 수용은 남아 있다.

75470:0에서 진단 완료/실제 RED·다음 수용 조건을 두 UI에 게시했다. source/링크·원 actor/header·frozen HTML/2,173파일·5root/상한/FD·소유 정리를 확인했다. UI 코드/DOM/WebGL은 변경·재검사하지 않았다.
