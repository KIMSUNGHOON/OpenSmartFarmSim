# 소유 생산 batch의 실제 계산·불변 결과 게시 — 2026-10-31

[worker](../backend/app/economic_batch_worker.py)와 [계약](../contracts/economic-batch-execution-worker-v1.md)을
실제 소유 PostgreSQL/SCRAM에서 수용했다.
[전체 기계 증거](artifacts/economic-batch-execution-worker-20261031.json)와
[실제 게시 사례](artifacts/economic-batch-worker-case-20261031.json)를 남겼다.
**원 v10을 실제 lease로 계산하고 전체 결과를 불변 파일/작업 publication에 저장한다.
현재 근거를 검사하는 결과 조회·제품 HTTP/runtime/자동 소비·비용 UI는 후속이다.**

## 실제 동작

정확한 tenant/job UUID·simulation/input_version과 원 입력 bytes를 확인한 뒤 그 작업만 claim한다.
기존 실제 source/서명 hold/context 권한과 최초 source UUID·입력/근거 SHA를 다시 검사한다.
계산 전후·게시 거래와 마지막 기록 뒤 현재 scope/객체·코드/잠금 환경 지문을 검사한다.
원 schema4/v10의 Decimal 계산을 한 번 수행한다. 새로운 단가·계수/수확 사건이나 계산기는 추가하지 않았다.

`economic-batch-calculation-result-v1`은 전체 원 결과/그 SHA와 입력·모든 접수 pin,
job/attempt·코드/잠금 환경 SHA를 담는다. envelope는2MiB까지이며 넘으면 보류한다.
durable 내용 주소 파일 뒤 live lease/cancel과 원 입력·근거를 대사하고,
같은 DB 거래에서 publication/manifest·성공/outcome을 기록한다.
마지막 현재 검사·정확한 terminal/publication·원 lease deadline 검사도 거래 안에서 수행한다.
실패 시 게시/성공은 rollback한다. 파일만 남은 경우는 미게시 bytes이며 성공 조회 대상이 아니다.
기존/공유 파일을 실패 정리로 지우지 않는다.

새 테이블/역할/의존성은0이다. 기존 JobStore의 lease·파일·publication을 재사용한다.
현재 API는 종류별 검증 경로이며 이 새 전체 artifact를 전송하는 raw HTTP 경로를 추가하지 않았다.
새 결과 조회도 소유권·현재 근거/권한을 대사한 뒤 연결해야 한다.

## 검증과 실제 산출물

- **신규24 + 기존249 = 고유273집중 검사**를 최종 같은 production 코드에서 통과했다.
  원 접수23/source20/경제206을 모두 포함한다. 이전24 단독 실행과 반복 사례를 다시 더하지 않는다.
- 실제 claim→한 번 계산→전체 결과/원 SQL publication/terminal·최초 bytes/시각·재호출,
  두 동시 worker의 단 한 번 게시·다른 종류/유효 lease 배제·실제 만료 재임대/이전 token 거부,
  취소/late scope·root/context 변경·코드/환경 지문 fault와 저장/DB fault rollback을 대사했다.
  잘못된 입력/근거는 계산 전 보류했고 한도 fault는 잘라낸 금액을 게시하지 않았다.
- 최초 missing-module RED와 **마지막 근거 조회 중 환경 지문 변경을 놓쳐 succeeded가 된1fail RED**를 보존했다.
  조회 후에도 코드/환경 지문을 대사하도록 수정한 뒤 최종24/273이 통과했다.
  코드/환경·I/O/DB fault는 소유 테스트의 주입 검증이며 실제 배포/G4 증거가 아니다.
- 실제 사례는 원 artifact **10,460bytes**, SHA
  `8fde368e7a03635370548b1eb0325acdee602796788f043b5acbd2c98e8d3ea2`다.
  전체 결과 SHA는 `311ce62528bc20873b83f1b7fcd9d1c12f5ce2c64044d439e0d393a84ae2ebce`다.
  실제 계산1회·원 source/job/input·manifest/최초 게시를 private 원 bytes와 대사했다.
  300자리 독립 Decimal의 자체 숫자 fixture는 비용20원/기간 현금−20원과 일치했다.
  실제 농장 비용·작물 수확·미래 마진의 추정값이 아니다.

PG16.15의 별도 소유 클러스터·16MiB shared_buffers·host SCRAM을 사용했다.
원 사용자 서비스 DSN/비밀번호를 읽거나 접속하지 않았고 각 소유 서버/암호 파일을 정리했다.
최종273은 guard248.392초/PID143,925,248bytes/합계428,769,280bytes,
단독24는157.122초/124,366,848/376,922,112였다.
한 phase/PID512MiB/합계1GiB/600초·소유 잔여0·FD4→4·보호 root/4,500항목을 유지했다.

원721source/1output/private12/external33·추가 review4와 통합6지문을 실제33e737bf Git 판본/현재 파일로 대사했다.
기존 숫자·CAS/GUI·238고정 파일의 실제 HTTP/원 PID·boot/ticks·첫 만료를04:21 UTC에 보존 확인했다.
이전 cold proof 재사용은 신규 계산 수에 넣지 않았다. [현재 저장3D](http://localhost:5184/supply-material-quantities-replay.html)는
17:03 KST 첫 만료를 유지한다. 과거5181의13:34 KST 만료를 연장하거나 복구하지 않는다.
기존 DB/설정·입력v1–v3/worker·API/3D 빌드의 변경/배포0,
전체 backend/frontend suite·새 브라우저/hosted CI 미실행을 유지한다.

native gpt-6.1-sol/xhigh·CLI0.157.1 turn `2026-10-31T04:12:31.198Z`와 판단/출력 지문을 기록했다.
재귀 CLI·새 agent·실제 농장 자료/계수·요금 채택은0이다. G0–G4 미평가·R2 미승인을 유지한다.

## 다음 단계

다음은 `economic-batch-stored-result-query`다. 별도 fresh reader가 실제 작업 입력/근거·
publication/전체 원 결과 SHA·판본·최초 시각과 현재/late 권한을 확인해야 한다.
조회에서는 금액 재계산/SQL 쓰기가0이어야 하며 실행 scope 없이 읽기 scope로 검증한다.
조회 구현1–2h+실제 DB/fresh·변조/권한 검증1–2h=**2–4집중시간 초안**이며 수용 결과 뒤 갱신한다.
그뒤 보호 HTTP/명시 runtime·자동 소비→저장 창·독립 가정 비용의 기간 결속→strict SDK/같은 선택 UI다.

실제 품종/긴 작기·독립 국내 raw0·설비/계량/구매/청구·다회 수확/정산·거시/수급·자율 비교,
최종 제품/배포·G0–G4/R2와 전체 완료일은 미완료/미정이다. 전체 goal active/incomplete다.
