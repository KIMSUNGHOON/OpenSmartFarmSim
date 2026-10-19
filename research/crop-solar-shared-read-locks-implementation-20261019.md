# Solar 읽기 공유 잠금 후보 구현 — 2026-10-19 KST

상태: **구현·20개 고유 검사 통과, 후보 미채택**.
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

모든 현재 source pin이 같으며5root/동적 자식·원본2,148항목·frozen source/assets·두 화면,
512MiB/PID/합1GiB·FD4→4·소유 비좀비/PG/임시/passfile0을 확인했다.
현재 통과 검사의 최대 합 RSS1,033,306,112bytes다.
첫 추가 묶음10219:2는 DB fixture 매개변수가 단독 OS 검사에도 적용된 수집 오류로 실행 검사가0개다.
단독 OS 검사를 분리했고 실패를 수용 수에 넣지 않았다.

**남은 검증:** 실제 작업자 정상/hold·취소/임대 만료/늦은 입력, 진행 query의 현재/잠금/권리/terminal,
prefix의 read session/current/잠금/권리, 최종 검토와 원 계측 OFF64 정상이다.
전체 backend/browser·fresh exec/SIGKILL은 현재 후보에서 재실행하지 않았다.
20개 통과나 통제된 thread 공존을 독립 unpaused64 완료로 표시하지 않는다.
앞선116검사는 sourceeb943d9의 기록이며 이 후보의 새 source 전체 검사 수로 합산하지 않는다.

native `gpt-6.1-sol/xhigh`에서 구현·판단을 수행했으며 재귀 CLI/서브에이전트는 없다.
원 정상22/64 미완료·진단8/64 queued/busy는 현재 변경으로 해결됐다고 주장하지 않는다.
새 Solar 배포·계산 중3D·실제 농장0/권리/독립 G0–G4·전체 완료일은 미수용/미정이며 goal active다.

76973:0에서 현재20검사·후보 미채택/남은 회귀를 두 UI에 no-store 동일 bytes로 게시했다.
현재2app source/syntax·문서 링크2,301개·원 actor/worker/query/probe·HTML/환기 frozen2,173파일,
5root/원본/상한/FD·소유 정리를 확인했다. UI 코드/DOM/WebGL을 변경하거나 재검사하지 않았다.
