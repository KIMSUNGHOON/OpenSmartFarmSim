# Solar 읽기 공유 잠금 로컬 수용 — 2026-10-19 KST

상태: **55개 고유 검사·검토로 로컬 소프트웨어 수용. 독립 원64 정상·운영 수용은 미완료**.
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
이후55건의 현재 수용 상태 게시와 정확한 feature head의 원 독립 실행을 이어 간다.

약32.1분은 위55검사의 관측된 로컬 guard 시간이다. CI 대기·독립 실행/후속3D와 실제 자료 확보가
미완료여서 전체 완료 날짜는 정하지 않는다. 기존 두 UI는 이전에 수용된 합성 저장3D/환기를 유지한다.
