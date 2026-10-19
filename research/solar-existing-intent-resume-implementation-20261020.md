# 기존 일사 계산 이력의 비생성 재개 — 2026-10-20 KST

[기계 증거](artifacts/solar-existing-intent-resume-implementation-20261020.json) · [계약](../contracts/solar-existing-intent-resume-v1.md) · [선행 비용 후보](solar-validation-cost-candidates-20261020.md).

## 검토에서 구현으로

원 source8b5afe5의 `_open` 호출자7곳과 파일 부작용을 대조했다. 기존 write 진입은 잠금 파일·디렉터리를 생성할 수 있고, 검증 직후 `intent.json`을 삭제하면 `_immutable`이 같은 서명 원문을 다시 쓴다. 실제 SCRAM의 소유 합성 fixture에서 삭제·권리 철회를 주입해 재생성을 확인했다. **원래 다음 guard는 수치 계산을 차단했다.** 이를 원 제품의 무권한 게시 취약점으로 보고하지 않는다. 기존 경로 그대로 첫 검증만 제거하는 후보는 기각했다.

구현은 `SolarServerCustody.advance`에서만 선택하는 비생성 경로다. 잠금·intent·proofs/artifact·HEAD가 모두 있는 기존 이력만 선택하고, 기존 잠금은 `O_CREAT`/`O_TRUNC` 없이 열며 디렉터리는 생성하지 않는다. 서명/canonical 원문과 바인딩을 대조하고 비공개 HEAD 원문을 잡는다. **원래 `advance`의 첫 full current guard 뒤**, 같은 HEAD인지 확인한 다음 기존 loader·준비·복원·계산·게시로 간다. 선택 뒤 파일이 사라지면 수리/생성 경로로 돌아가지 않는다.

첫 등록 정보 구성이 첫 advance guard로 옮겨지고, 그 닫힌 진입 경계의 warm 검증 한 번만 줄었다. 물리·경제 원천/권리의 전체 검증과 나머지 현재 검사 순서·SQL을 대사했다. HEAD는 같은 작업의 파일 변경을 검출하는 비공개 값이며 권한 결과 cache가 아니다. 현재성·경제 권리·수치·게시 guard를 통째로 생략하는 구현은 없다.

| 제품 호출자 | 현재 진입 |
|---|---|
| `advance` | 완전한 기존 이력만 비생성 선택; 첫 full guard 전 이력 소비/계산/쓰기 없음 |
| worker `_adopt`, result `_session`/`_read` | 기본 eager 진입 유지 |
| `inspect`/`page`, checkpoint `_session` | 기존 read-only deferred 옵션과 첫 progress full guard 유지 |
| 신규/불완전 이력 | 기존 eager 경로; 선택 뒤 손실은 중단 |

`entry_guard=False`는 여전히 read-only 전용이다. 새 비공개 옵션은 exact bool·write/eager 조합만 받는다. 공개 요청·응답, 수식/계수·프로필, actor/입력·원64 예산을 바꾸지 않았다. 소프트웨어 pin이 달라진 기존 판본의 이력을 자동 변환하는 작업은 이 수용에 포함하지 않는다.

## 최종 같은 source의 로컬 수용

backend app261파일 집계는 `a18da9558cd83d62edd1fb9a64ea8829ee59fd9da08b72cbce380d23229daa32`다. app 파일1개만 바뀌었고 나머지260개와 핵심 method12개의 AST가 원 source와 같다. 실제 세 method와 사설 후보의 AST, 두 보안 helper의 명시적 alias/name 정규화 후 AST를 대조했다.

**기능71 + 최종 제품 paired1 = 고유72검사**를 같은 app source로 수용했다. 이전 source의64를 재실행 없이 더하지 않았으며, 원 독립64단계 관문과 다른 수다. 원 source의 부작용 반례1·사설 비용 trial1도72에 넣지 않았다.

| 검사 | 건수 | 확인 |
|---|---:|---|
| 새 재개 경계 |7| 비생성 진입·strict 옵션·default/new eager, 부재6/현재 권리4/HEAD3/실제 lock4 fault vector·원 이력 bytes/닫힌 scope |
| 새 잠금 파일 보안 |1| 두 잠금 위치의 symlink/hardlink/nonempty/mode8 vector·생성/소비0 |
| 기존 소유권·읽기 경합 |4 + 7| 기본/current/prepare 이후 철회·읽기/확정 공존·쓰기 배제/해제 |
| worker |13| 정상/수치 hold 원 값·원자 완료, 취소/임대/재개, 검증 중 취소·입력 변경/만료 |
| query |13| 원 counts/UTC/최초 시각·현재/늦은 권리, snapshot 변경/디렉터리·원 완료/hold의 별도 reader·조회 계산/SQL 변경0 |
| HTTP/TLS/fresh |24 + 1 + 1| 인증/고정 실패·실제 SCRAM/TLS503→200·별도 exec 원16걸음/행·UTC/재개·읽기 계산0 |
| 실제 제품 비용 |1| 원 quanta ABBA·cold 구성 이동/남은 전체 검증과 SQL 차이 대사 |

query7의 잠금 해제2·snapshot 변경2·디렉터리1·terminal2가7건이다. 초기 진행 메시지의 snapshot 변경3건 표현을 최종 로그의2건으로 정정한다. fault vector 수를 pytest 건수에 더하지 않았다.

## 실제 비용

사전 기준은 평균 wall 감소2% 이상과 두 짝 모두 감소다. 사설 trial은 평균3.3782%였으며, 최종 제품 source는 별도로 다음을 확인했다. baseline은 같은 최종 source의 입력/pin 아래 원8b5afe5 method 본체만 복원한 비교다.

| ABBA 짝 | 기존 wall초 | 제품 wall초 | 감소율 |
|---|---:|---:|---:|
| 첫 짝 |7.939854|7.560805|4.7740%|
| 둘째 짝 |8.144813|7.707018|5.3751%|

평균 감소는 **5.0784%**다. 감사315→301·SQL11,723→11,125·원천2,736→2,584·full current18→17을 대사했다. 최초 cold 구성을 보존하고 warm 검사 한 번의 정확한 SQL 차이만 확인했으며 나머지 current 검사의 순서/SQL은 같았다. 원 checkpoint counts와 UTC04/06/08/10.123456Z를 유지했다. 이전 개선율과 합산하거나 원360초 처리량으로 환산하지 않는다.

## 실패·자원·보존

- 첫 사설 trial은 cold 구성 위치까지 SQL이 같다는 잘못된 시험 가정으로 미수용이었다. 다음 시도는 fixture 지역 이름 충돌로 계측 전에 실패했다. 원 증거를 보존하고 수정했으며 좋은 수치를 고르기 위한 반복은 하지 않았다. RED는 새 옵션이 없는 코드의 `TypeError`였다.
- 잠금 파일 검사에서 OS의 mode 거부 `PermissionError`를 시험이 너무 좁게 예상했다. root lock/mode일 때만 해당 거부를 허용하도록 시험을 고쳤으며 제품의 거부 동작은 바꾸지 않았다.
- 묶음 회귀 두 번은 합 RSS1,076,113,408/1,084,600,320bytes로 감독 중단됐다. 상한을 올리거나 기존 서비스를 멈추지 않았다. 해당 묶음의 일부 성공은 수용에 더하지 않았다. 두 번째 중단의 소유 PG/backend·자식 잔여0을 재확인하고, 남은 인증 파일4개를 내용을 읽지 않고 삭제했다. 임시 DB 디렉터리도0을 확인했다. 실패 기록은 수정하지 않았다.
- 같은 원 사례를 별도 프로세스/DB로 나눠27개 실행에서72건을 완료했다. 입력·assertion·상한은 유지했다. 통과 실행의 단일/합 RSS 최대170,864,640/1,060,302,848bytes·FD4→4·5root/원본2,148/두 frozen source·자산·소유 PG/임시/passfile0을 대사했다. 실제 guard합1,451.214371초는 시험 소요이며 제품 완료 일정이 아니다.

실제 native CLI `gpt-6.1-sol` / `xhigh` 문맥/원행 SHA·원 source/receipt/probe/종료 SHA를 기계 증거에 결속했다. 재귀 CLI/하위 에이전트·새 라이브러리/수치 프로필·자료 채택은0이다. 전체 backend/browser CI나 계산 중3D/WSL 사용자 적용을 이번72로 수용하지 않았다.

## 다음 관문

기존 [CI39280701330](solar-current-guard-native-normal-20261020.md)는 source8b5afe5·원360초 미완료·저장41/64의 최종 실패다. 다음은 새 source의 **계측 OFF 원 actor/input64·chunk1·poll/retry360·RSS**, start1/CLI0/attempt1/success1·두 전진prefix/원 값/UTC·actor0/0·DB/소유 정리다. actor source hash 두 값과 전체 원 관문을 유지한다.

원 정상 뒤 독립 hold→실제 HTTP취소→계산 중WebGL→WSL 용량/사용자 적용으로 간다. 새 Solar 미배포·실제 농장 Run0·국내 원 실측/독립 작기·G0–G4 보류·전체 완료일 미정·goal active를 유지한다. 새 CI 접수/종료는 별도 관측으로 기록한다.

최종 게시 `focused-solar-existing-resume-final72-status-v1`는 자식0·guard1.637172초였다. 같은 app72/원 actor source 두 hash·관련 링크2,724개와 두 HTTP200/동일bytes/no-store·frozen HTML/환기2,173파일·5root/원본2,148/FD4→4/소유 정리를 확인했다. 진행 기록은2026-10-19T18:31:56.772848Z이며 UI 코드·DOM/WebGL을 다시 검증한 것은 아니다.

수용 source commit은 `aeb7a901e0860ffcacc2a0adf2469a6cb882e315`다. 새 [CI39303668519](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39303668519) / job118235091581를 한 번 접수했다. 2026-10-19T18:35:39.802746Z API 관측은 run/job `in_progress`·고정 PostgreSQL 빌드 중·원 계산 step `pending`이다. head/source·계측 OFF·원 actor/input/예산을 대사했다. 이는 계산 진행/완료나64 정상 수용의 증거가 아니며 같은 실행을 추적한다.

CI 현황 게시 `focused-solar-existing-resume-CI-status-v1`도 자식0·guard1.630606초/동일 app72·원 actor/링크·두 HTTP/정리 검증을 통과했다. 진행 기록은2026-10-19T18:37:10.697216Z이며 새 UI/DOM/WebGL 수용은 아니다.

후속 [원 독립 정상 최종 결과](solar-existing-intent-resume-native-normal-20261020.md)는 CI39303668519/sourceaeb7a90의 원360초 미완료·저장 metadata41/64다. 원64 정상/배포는 여전히 미수용이며 다음은 이력 길이별 검사 비용 관측이다. 위 접수/대기 문단은 당시 기록으로 보존한다.
