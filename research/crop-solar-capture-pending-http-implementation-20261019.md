# Solar capture Pending의 HTTP 경계 후보 — 2026-10-19 KST

상태: **최종 두 파일·고유58검사·검토로 로컬 소프트웨어 범위 수용**.
[이전62검사와 원39/64·API 단언 근거](crop-solar-read-validation-lock-implementation-20261019.md) ·
[기계 증거](artifacts/crop-solar-capture-pending-http-implementation-20261019.json).

원 CI39204795867/source3d662d2는 API assertion279(status∈{200,503})/worker.wait 시간 초과로
미완료였다. 실제 CI status는 없으며 제어 재현의422를 그 CI의 실제 응답으로 단정하지 않는다.

## 실제 RED/GREEN과 변경

45733:1은 실제 인증 SCRAM DB/검증된 TLS에서 GET이 읽은 HEAD를 current 검증 중 실제 writer가
step1→2·UTC04.123456Z로 전진시켰을 때422 solar_execution_hold를 관측했다.
DB 변경·부분 수치 응답은 없었다. query에서 SolarCustodyPending만 변환한 첫56220:1도422였다.
ResultStore._session은 body 예외를 보존해 server._open 밖에서 다시 내보내므로,
Session의 내부 CycleCustodyPending이 Solar 변환을 거치지 않는 경계를 확인했다.

Session은 자신의 일시 잠금/상태 변경을 SolarCustodyPending으로 내보내고 _open도 이를 보존한다.
Query는 그 typed Pending을 SolarExecutionQueryPending으로 변환한다. 다른 권리/무결성 실패는 변경하지 않는다.
제품 변경은 custody의 예외 유형/통과3줄과 query의 경계 변환2줄이며 원 actor·수식/입력·현재 검사·상한은 유지한다.

2592:0에서 같은 실제 TLS 재현이503 solar_execution_unavailable/부분 수치 없음으로 통과했고,
후속 GET200·unconfirmed checkpoint 없음, DB 불변·원 step2/UTC를 확인했다.
guard46.647초·source/원본/frozen/5root·512MiB/PID/합1GiB·FD4→4/소유 PG/임시/passfile0을 보존했다.
이것은 제어된 소프트웨어 사례이며 원 독립 정상이나 전체 G0–G4 수용이 아니다.

## 최종 source 회귀와 검토

93137:0에서 확장 실제 TLS1도 통과해503/복구200·실제 권리 hold422·scope 거부403·DB 불변을 확인했다.
46.409초·합 RSS1,022,504,960bytes·source/5root/frozen/상한/FD·소유 정리를 보존했다.
이 public1이 같은 private GREEN1을 대체하며 중복 합산하지 않는다.
최종 source의 다음 고유 회귀도 모두 통과했다.

| 경로 | 검사 수 | 실제 도구 종료 | guard 초 |
| --- | ---: | --- | ---: |
| 확장 실제 SCRAM/TLS | 1 | 93137:0 | 46.409 |
| 읽기 current/잠금/HEAD/사용량/권리 | 7 | 24027:0 | 245.290 |
| worker 정상/hold·청크 취소·임대 재개 | 5 | 28741:0 | 309.923 |
| worker 검증 중 취소/입력 변경/임대 만료 | 8 | 15804:0 | 269.764 |
| query 현재/원 UTC/권리/늦은 변경 | 6 | 67673:0 | 177.645 |
| query 잠금/서명 변경/디렉터리/정상·hold 결과 | 7 | 72881:0 | 292.463 |
| HTTP 접수/조회/취소 오류 분류 | 24 | 89032:0 | 2.137 |

public1+Solar7+worker13+query13+HTTP24=58건이다. private GREEN과 public1을 중복 합산하지 않는다.
현재 두 파일 source가 바뀌었으므로 이전 read-scope62도 이 수정의 신규 통과 수로 합산하지 않는다.
합계1,343.631초(약22.4분), 합산 최대 RSS1,041,448,960bytes다. 각 stage에서 두 파일 pin·원본2,148항목·
frozen 자산/5root·512MiB/PID/합1GiB·FD4→4·소유 PG/임시/passfile0을 확인했다.
권리/무결성 hold를 Pending으로 낮추지 않고 조회 계산/SQL 변경0·원 값/UTC를 유지했다.

`gpt-6.1-sol`/`xhigh`의 실제 현재 native CLI 문맥에서 검토했으며 재귀 CLI는 실행하지 않았다.
검토의 문맥 시각/해시는 기계 증거에 기록했다. 정확성은 typed Session→Query→HTTP 경계와 실제 TLS/회귀로,
단순성은 제품5줄 변경/새 추상화 없음으로, 구조는 기존 경계/ResultStore wrapper 보존으로 확인했다.
권리/접근/무결성 실패 유형·current 검사를 유지했고 새 SQL/계산/반복/재시도는 없다.
확인한 범위의 미해결 검토 지적은 없으며 독립 정상의 처리량은 아직 수용하지 않았다.

## 다음 수용과 한계

다음은 변경 source의 원 계측 OFF64 독립 정상이다. 원64/chunk1/조회·retry360/RSS,
64/start1/CLI0/attempt1/success1·두 전진 prefix·원 UTC/수치·두 actor 종료0·FD/역할/schema/소유 PG/임시 정리 proof가 필요하다.
원360초와 준비/정리·CI 대기를 예상하되 성공을 미리 단정하지 않는다.
이후 독립 hold → 실제 HTTP 취소 → 계산 중 WebGL → WSL 용량/사용자 적용 순서다.
전체 backend/browser·fresh exec/SIGKILL과 새 Solar/계산 중3D/WSL 사용자 적용은 미완료다.
실제 자료 권리·독립 농장/G0–G4·전체 완료일은 미수용/미정이며 goal은 active다.

17427:0에서 확장 TLS1·미채택/남은 회귀와 원39/64·CI 실제status 미확보 상태를 두 UI에 같은 no-store bytes로 게시했다. 현재2파일 pin/3syntax·링크·원 actor/header·frozen HTML/2,173파일·5root/상한/FD/소유 정리를 확인했다. UI 코드/DOM/WebGL은 변경·재검사하지 않았다. 최초69155:1은 상태 이유252자가 기존240자 제한을 넘어 거부됐고234자로 줄였다. 제한은 유지했다.

94972:0에서 로컬58 수용과 다음 원64 독립 정상을 두 UI에 같은 no-store bytes로 게시했다.
두 파일 pin/3syntax·2,305개 로컬 링크·원 actor/header·frozen HTML/2,173파일·5root/상한/FD/소유 정리를 확인했다.
합산 RSS888,143,872bytes였으며 UI 코드/DOM/WebGL은 변경·재검사하지 않았다.

## 후속 원 독립 정상의 미완료 — CI39210494752

source `583bd633ba71060df5355961f74d190177a85010`의 trace-OFF 원64 실행은 실패했다.
원 부모의360초 기준 단언이며 guard382.137초·자식1·자원 중단 사유 없음이었다.
API/worker는 소유 정리 과정에서 각각-15로 종료됐고, API의 별도 예외 위치/실제 HTTP status는 없다.
정상 수용 파일과 DB 정리 proof도 없다. 이전 CI39/64는 다른 종료 원인이므로 처리량 개선/악화 비교로 쓰지 않는다.

종료 뒤 같은 소유 cluster의 READ ONLY/REPEATABLE READ metadata는 attempt1/simulating,
24/64/yielded/publication25와 UTC `2026-10-01T00:00:48.123456Z`를 보여줬다.
이것은 종료 뒤 저장 metadata이며 현재 source/권리 또는 계산 결과의 정상 수용 검증이 아니다.
hosted 합산 RSS363,646,976bytes·단일128,987,136bytes·FD7→7·소유 non-zombie/임시0은 확인했다.
WSL5root 용량·DB 역할/schema 정리 proof나 G4로 확대하지 않는다.

artifact12166794422/3,286bytes의 SHA256은
`23fff1f9f19b1509219862ef46f0ba95f873b1478fe7fb2b0fc68358f93f0dc4`다.
run/head/name/digest·허용4파일/경로/용량을 엄격히 검증했다. 실제 HTTP status/code는 미확보다.

다음 한 단계는 [기존 bounded 단계 진단](../contracts/crop-solar-worker-progress-diagnostics-v1.md)의
`phases`를 현재 source에서1회 적용하는 것이다. 실제 current/등록/guard/advance/confirm의 시간과 원 반환
checkpoint/UTC·원 actor/header/run/head/digest·종료/정리를 대사해 다음 최소 수정 범위를 정한다.
원64/chunk1/조회/retry360/RSS·현재 권리/자료 검사·수식은 유지한다. 진단 자체는 정상 수용이 아니다.
같은 미완료 정상 재실행이나 독립 hold/취소/WebGL의 선행 수용으로 대체하지 않는다.
