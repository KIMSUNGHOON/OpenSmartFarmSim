# Solar capture Pending의 HTTP 경계 후보 — 2026-10-19 KST

상태: **구현·확장 실제 SCRAM/TLS1검사 통과(503/200/422/403), 미채택**.
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

## 남은 수용

93137:0에서 확장 실제 TLS1도 통과해503/복구200·실제 권리 hold422·scope 거부403·DB 불변을 확인했다.
46.409초·합 RSS1,022,504,960bytes·source/5root/frozen/상한/FD·소유 정리를 보존했다.
이 public1이 같은 private GREEN1을 대체하며 중복 합산하지 않는다.
남은 Solar 읽기 경계7 → worker13 → query13 →
HTTP 오류 분류24 → 검토/로컬 수용 → 변경 source 원 계측 OFF64 순서다.
권리/무결성 hold를 Pending으로 낮추지 않고 조회 계산/SQL 변경0·원 값/UTC·5root/정리를 유지한다.
public1+Solar7+worker13+query13+HTTP24=58건의 대상 회귀 뒤 검토한다. private GREEN과 public1을 중복 합산하지 않는다.
현재 두 파일 source가 바뀌었으므로 이전 read-scope62검사를 이 후보의 신규 통과 수로 합산하지 않는다.
전체 backend/browser·fresh exec/SIGKILL과 새 Solar/계산 중3D/WSL 사용자 적용은 미완료다.
실제 자료 권리·독립 농장/G0–G4·전체 완료일은 미수용/미정이며 goal은 active다.

17427:0에서 확장 TLS1·미채택/남은 회귀와 원39/64·CI 실제status 미확보 상태를 두 UI에 같은 no-store bytes로 게시했다. 현재2파일 pin/3syntax·링크·원 actor/header·frozen HTML/2,173파일·5root/상한/FD/소유 정리를 확인했다. UI 코드/DOM/WebGL은 변경·재검사하지 않았다. 최초69155:1은 상태 이유252자가 기존240자 제한을 넘어 거부됐고234자로 줄였다. 제한은 유지했다.
