# Solar 읽기 검증의 짧은 잠금 구간 로컬 수용 — 2026-10-19 KST

상태: **현재62개 고유 검사·검토로 로컬 소프트웨어 수용. 독립 원64·운영 수용은 미완료**.
[계약](../contracts/crop-solar-read-validation-lock-v1.md) ·
[이전 판본의 원22/64·진단15/64/실제 RED](crop-solar-shared-read-locks-implementation-20261019.md) ·
[기계 증거](artifacts/crop-solar-read-validation-lock-implementation-20261019.json).

## 변경

제품 수정은 Solar custody1파일이다. writer의 배타 잠금·수식/입력/worker/query/prefix/원 actor·retry360/RSS는 그대로다.
읽기 세션은 root/intent SH 아래 signed HEAD/proof ancestry·intent/디렉터리·동일 named lock FD·artifact 사용량을 확인한다.
SH를 intent→root 순으로 해제하고 기존 current DB/원천/권리 검사를 모두 수행한 뒤,
root→intent SH/NB를 재획득해 같은 상태인지 확인한다. 바뀐 정상 HEAD/사용량은 Pending,
권리 실패·교체된 lock/디렉터리/원문/변조는 fail closed다. 검증 실패 세션은 재사용하지 않는다.
읽기 prepare/advance/게시/파일 생성 금지와 prefix의 기존 수동 불변 읽기 경로를 유지한다.
권한/자료 검증 결과를 캐시하거나 current 검사를 생략하지 않았다.

## 현재 최종 source 검사

| 검사 | 고유 수 | 실제 도구 |
| --- | ---: | --- |
| 실제 writer step2 진행·stale reader Pending·fresh 원step2/UTC |1|4703:0|
| root/intent SH 재획득 실패·부분 잠금 해제 |2|4703:0|
| 기존 FD가 살아 있어도 named root/intent lock 교체 거부 |2|4703:0|
| 실제 pre-HEAD 게시 실패·같은 HEAD/늘어난 파일 사용량의 stale 응답 거부 |1|4703:0|
| current 도중 권리 철회·응답 거부/두 잠금 해제 |1|4703:0|
| 기존 read/confirm/query 공존·writer 배제/해제·읽기 변경/빠진 파일 생성 금지·독립 OS lock |9|65643:0|
| 기본 파일 보안·원 Cycle 경로·권리 철회 |7|91471:0|
| Solar 권리/서명 변조·늦은 게시 거부·수치 보류·서명 도메인 분리 |4|83327:0|
| 실제 작업자 정상/hold·chunk/terminal 취소·임대 만료/새 시도 인계 |5|72509:0|
| 검증6지점 취소·늦은 입력/임대 변경 차단 |8|97316:0|
| query none/current·heartbeat/새 시도·미확정/실제 EX·권리/직렬화 철회 |6|84216:0|
| query followup EX/해제·HEAD 전진/변조·디렉터리 교체·정상/hold 결과 조회 |7|64938:0|
| prefix 읽기 전용·현재/늦은 권리·취소·선택자/실제 EX 아래 불변 읽기 |5|29446:0|
| prefix 원 페이지/희소 UTC·서명 이력 rollback/fork 거부·정상/hold 종료 |4|48177:0|

41317:1의 실제 writer Pending RED 뒤 같은 private 검사28208:0이 통과했다.
그 GREEN은 artifact 사용량 snapshot을 더하기 전source54350e이므로 현재62건에 합산하지 않는다.
위7건은 최종source5f5bbcc에서245.066초 guard로 통과했다. 최대 합 RSS는 기계 증거를 따른다.
source/원본2,148항목·frozen 두 UI/5root·512MiB/PID/합1GiB·FD4→4·소유 비좀비/PG/임시/passfile0을 확인했다.
이전 shared read55검사는 그 이전 source의 기록이며 이 후보의 현재62검사에 합산하지 않는다.

## 검토·남은 수용

새 경계7와 기존55의 실제 새 source 회귀를 모두 통과했다. 제품 변경은 custody1파일이며
기본 파일 helper/수식/입력·writer EX·worker/query/prefix/API·원 actor/probe/workflow는 그대로다.
현재 권리/원천 검사는 모두 수행하고, named FD·디렉터리/intent·signed HEAD/ancestry와 파일 사용량을
잠금 재획득 후 대사한다. 검증 실패 세션을 재사용하지 않고 부분 응답도 반환하지 않는다.
syntax2파일·git diff와 실제62건/10guard의 동일 최종source5f5bbcc를 검토했고 추가 제품 수정 사유는 없었다.

관측 guard 합계2,083.339초(약34.7분)·최대 합 RSS1,062,330,368bytes다.
5root/동적 자식·원본/frozen/두 UI·512MiB/PID/합1GiB·FD4→4·소유 PG/임시/passfile 정리를 확인했다.
이 수용은 로컬 소프트웨어 범위다. 다음은 변경 source의 원 계측 OFF64 독립 정상이며,
64/start1/CLI0/attempt1/success1·두 actor 종료0·두 전진 prefix·원 수치/UTC·전체 owned 정리 증거가 필요하다.
그 뒤 독립 hold → 실제 HTTP 취소 → 계산 중 WebGL → WSL 용량/사용자 적용을 검증한다.
전체 backend/browser·fresh exec/SIGKILL은 현재 source에서 재실행하지 않았다.
원 입력64/chunk1/조회·retry360/RSS를 바꾸거나 같은 실패 source의 정상/진단을 반복하지 않는다.

현재 native Codex CLI gpt-6.1-sol/xhigh에서 구현/판단했으며 재귀 CLI/서브에이전트는 없다.
현재 수치 소프트웨어 범위다. 실제 농장0/자료 권리·독립 G0–G4·새 Solar 배포·전체 제품 수용은 미완료다.
55기존 회귀의 직전 guard 합계는 약32.1분이었으나 새 source 비용/독립 실행/외부 자료 확보가 미완료여서
전체 완료 날짜를 확정하지 않는다. goal은 active다.

92807:0에서 중간7검사·미채택 상태를 두 UI에 같은 no-store bytes로 게시했고, 현재source/2syntax·2,303링크·원 actor/header·frozen HTML/2,173파일·5root/원본/상한/FD/소유 정리를 확인했다. UI 코드/DOM/WebGL은 변경·재검사하지 않았다.

3518:0에서62건 로컬 수용/남은 원64·후속 조건을 두 UI에 같은 no-store bytes로 게시했다. 현재 source/syntax/링크·원 actor/header·frozen HTML/2,173파일·5root/상한/FD/소유 정리를 확인했다. UI 코드/DOM/WebGL은 변경·재검사하지 않았다.
