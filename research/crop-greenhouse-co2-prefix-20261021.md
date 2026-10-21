# CO₂ 확정 구간 원 조회 — 구현/검증 진행

**현재 core13+fences10=고유23검사 수용.** 원 실패10은 합산하지 않는다.
[수정 CI39539414514](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39539414514)의
[14개 원 산출물/기계 증거](artifacts/crop-greenhouse-co2-prefix-fences-20261021.json)를 대사했다.
독립/동시8과 원 조회 부모·공개 투영/HTTP/3D·WSL/사용자 적용은 아직 미수용이다.

[계약](../contracts/crop-greenhouse-co2-prefix-v1.md) · [사전 증거](artifacts/crop-greenhouse-co2-prefix-preflight-20261021.json).

`Co2ExecutionPrefixQuery`를 기존 Solar의 원 조회/현재 권리·서명 이력/owner witness 경계에서
CO₂ authority·HMAC/버전·원109상태/장부/UTC에 연결했다. 수치·저장 커널/기존 공개 경로는 변경하지 않았다.
선택 페이지를 직렬화 뒤 재검사하며, DB 미확정 HEAD는 선택하지 않는다.

사전 단계에서 순수 제어7개와31개 전체 수집·원 계수의128초 밀집65시점 준비를 로컬 통과했다.
첫 missing-module RED를 보존했다. 512MiB/PID·합1GiB/600초·기존5root/원자료2148항목·
원 두 미리보기 source/assets를 유지했고 소유 PG/임시/passfile/process 잔존0이다.
128초 변형은 저장 페이지 계약을 시험하며 독립 물리 검증은 원32초 범위다.

## 실제 core13 수용 / 남은18검사

원 Solar23개를 모두 유지하고 late page1/제어7을 추가한31개다.
`co2-prefix-core`13 → `co2-prefix-fences`10 → `co2-prefix-concurrent`8을 원600초씩 분리한다.
[첫 실제 CI39537144157](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39537144157)의
제어7/실제 SCRAM6=13검사를 수용했다([기계 증거](artifacts/crop-greenhouse-co2-prefix-core-20261021.json)).
source5ce10c6의338지문과10개 curated 산출물을 현재 코드에 대사했다.
원 sparse 시점은 계산 확정14초와 sample8초를 구분하고 관리 사건/원 state·UTC를 그대로 보존한다.
64+1의 원65시점 페이지는1,171,565/18,341bytes로 원2MiB 안이며, terminal checkpoint가 아직
job/result 완료가 아님을 확인했다. none/ready/normal/hold와 조회31계측0·DB 불변·정리를 확인했다.
209.543541204초·단일 PID166,141,952/합283,586,560bytes·FD6→6·소유 process/PG/schema/role/임시/passfile0이다.
현재 늦은 변경/변조10·동시 actor/독립 fresh8은 미수행이며 전체 원 조회 부모는 미완료다.
동시 actor의 의도된 SQL·미리 계산한 HEAD 공개와 제품 조회31계측0을 구분한다.
독립 fresh는 실제 producer 전진 뒤 종료한 별도 reader의 원 선택/UTC·철회 시험이다.
원 wrapper의 자동 worker 문구를 unpaused 동시 수치 계산의 증거로 사용하지 않는다.

다음은 전체31개 수용 뒤 닫힌 공개 투영 → 보호 실행 HTTP/runtime → 같은 UTC3D다.
공통 WSL/사용자 적용·전체 작기/자원/경제/최종 UI·실제 CLI 종단 간·독립 농장 자료/관문은 남는다.
실제 농장 Run0/G0–G4 not_assessed·새 CO₂ 미배포, 전체 완료일 미정·goal active다.

## Fences 첫 실행 보류와 실제 SCRAM actor 수정

[CI39537946934](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39537946934)의 pytest는 종료0이고
10개 산출물/정리를 남겼으나 전체 배치는 미수용이다([실패·수정 증거](artifacts/crop-greenhouse-co2-prefix-audit-scram-fix-20261021.json)).
controller292행에서 감사 행 변경을 시도한 소켓 관리자 연결의 used_password=False를 거부했다.
제품 조회는 실제 SCRAM/31계측0이며 감사 행 수정·삭제6건과 반환값 fault6종도 거부됐지만,
이 사실로 전체 postcheck 실패를 성공 처리하지 않는다. tests/provenance 최종 영수증은 없다.
325.704449701초·단일 PID141,369,344/합227,643,392bytes·FD6→6·소유/임시/passfile/schema·role0이다.

확인한 원인만 수정해 감사 actor를 별도 임시 LOGIN NOINHERIT/NOSUPERUSER role·0600 passfile의
실제 host SCRAM으로 바꿨다. 원 schema owner로 SET ROLE한 identity와 used_password/require_auth를
검사하고, 원 audit trigger를 유지한 채6건을 시험한다. actor/membership은 제품 조회 전에 제거하고
자격증명은 finally에서 지운다. 기존 관리자 비밀번호·제품 권한/모델/원 숫자·검사10개/한도는 그대로다.
엄격 postcheck는 실제 actor 인증·owner identity·정리를 요구한다. 로컬은 수정1건 수집만 통과했고 native 수용은 남는다.

원 core13 이후338지문 중 변경2개는 이 감사 시험과 해당 fences postcheck다.
원 core 선택 시험/나머지 정의와 controller의 fences 분기 밖 AST가 동일함을 검토했다.
336개 source 및 모든 제품 app/수치/저장/기존 API·제어7은 그대로다. 이 변경을 숨기거나 세 배치의
전체338지문이 같다고 보고하지 않는다. 후속 native 결과는 수정 source와 원 core의 이력에 각각 결속한다.

## 수정 fences10 수용 — source1a4a205

실제 host SCRAM의 used_password=True/require_auth·원 owner/session identity를 확인했다.
감사 행 변경/삭제6건과 별도 반환값 fault6종이 거부됐고 actor/membership/passfile은 제품 조회 전에 제거했다.
원 signed rollback/fork·미확정 private tail·이전 선택자/재시도·현재/늦은 권리/농장·취소/범위/원 writer lock·
원 파일 및 조회 뒤 선택 page 변조 거부를 수용했다. 모든 측정 조회31진입점/SQL쓰기0, 실패 파일 복구·소유 정리를 확인했다.
311.382355944초·단일 PID139,165,696/합223,649,792bytes·FD6→6이며 원 한도 안이다.
현재338지문을 모두 대사했고 원 core와336개가 같다. 나머지2개의 감사 actor/postcheck 변경과
core 선택 시험·fences 밖 AST 동일성은 앞선 수정 증거에 결속한다. 제품 코드/수치/저장/API는 같다.
다음은 원 signed HEAD 공개/heartbeat/cancel·witness/provenance/승인과 독립 producer/reader8검사다.
현재까지 고유23=제어7/실제 DB16이며 전체 원 조회31/실제3D·전체 작기/자원/경제/외부 관문 수용은 남는다.
