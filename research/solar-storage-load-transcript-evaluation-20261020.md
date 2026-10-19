# 반복 저장 load 검증 기록 후보 평가: 미채택 — 2026-10-20 KST

[기계 증거](artifacts/solar-storage-load-transcript-evaluation-20261020.json) · [선행 이력 길이 관측](solar-history-validation-cost-review-20261020.md).

## 경로와 사전 기준

원 `_Session.advance`는 최초 `_load` 뒤 prepare/current guard와 checkpoint 복원을 수행하고, writer `_resume`에서 다시 `_load`한다. 그 사이 외부 resolver와 현재 검사가 있으므로 앞선 결과를 그대로 재사용할 수 없다. writer는 반환된 commit 목록/counts를 자기 상태로 받아 갱신하므로 가변 DTO를 공유하는 것도 부적합하다. source5파일의 bytes/AST와 실제 소비 순서를 대조했다.

사설 후보는 최초 검증 결과를 같은 프로세스의 비공개 복제 bytes로 보관하고, 두 번째 읽기에서 **원래의 모든 `_blob` 호출·현재 파일 읽기/SHA·파싱/canonicality·참조 한도·헤더/notice/profile 검증**을 실행했다. 결과는 새로 복제하며 HEAD와 의존성을 재확인했다. 현재 농장/경제 권리 검증은 원 경로에서 모두 수행했다. 권한 승인 결과를 보관하는 후보는 아니다.

복제는 내부에서 만든 값에만 Python marshal을 사용한 비용 실험이다. 외부 bytes나 영속/public 포맷으로 사용하지 않았다. [Python 공식 문서](https://docs.python.org/3.12/library/marshal.html)의 타입/버전 및 신뢰 경계를 참고했다. 새 패키지나 실제 자료를 채택하지 않았다.

판정 전에1차 독립 loader의 평균20% 이상/두 짝 개선, 후속 실제 quantum의 평균2% 이상/두 짝 개선을 정했다. 1차는 capture 비용을 제외하므로 후속에는 capture·의존성 대조·복제 비용까지 반드시 포함하도록 했다. 비용 시험 자체를 보안/제품 수용으로 취급하지 않았다.

## 독립 loader: 비용 기준 충족, 제품 수용 아님

원 CASE6/64·chunk1·41단계 이력의 ABBA에서 기존232.774/241.079ms, 후보138.846/139.848ms를 관측했다. 평균41.1855%, 짝별40.3513/41.9909% 감소다. 원 `_blob`95회를 모두 실행했고 복제는199,257bytes였다.

현재 한도·같은 함수 객체의 code 변경·notice 원천·가변 반환 DTO·단일 소비·원문 변경의6개 vector를 확인했다.6개를 별도 pytest6건으로 세지 않았다. 사설 fingerprint의 solar clock alias·기본 artifact/input JSON helper·완전한 폐쇄성/불투명 소유권은 미입증이다. 이는 제품 취약점 보고가 아니며 사설 후보의 미수용 범위다.

## 실제 늦은 quantum: 비용 기준 미충족

같은 원 CASE6/64/chunk1·현재 source로42–45단계의 `worker._before → server.advance → worker._confirm`을 비교했다. 준비용41단계 이력은 원 수치 청크·서명 publisher/guard로 만들었다. 준비 경로는 원 독립 API/worker 실행을 대체하지 않으며, 아래 구간은 원 함수/입력/수치·UTC 그대로 측정했다. capture와 의존성 대조·fresh 파일 검증/복제 비용을 포함했다.

| 짝 | 기존 wall초 | 후보 wall초 | 감소율 |
|---|---:|---:|---:|
|첫 짝(42→43)|8.969867|9.110312|−1.5657%|
|둘째 짝(45→44)|9.266716|9.098380|1.8166%|

평균 **0.1529%로2% 기준 미달이며 첫 짝은 느렸다.** 원 quantum마다 SQL11,125/권한 감사301/원천2,584·full current17, 원 checkpoint bytes/counts와 UTC `00:01:24.123456Z`–`00:01:30.123456Z`(2초 간격)를 대사했다. 후보의97/99개 원 blob 읽기와199,323/199,389bytes 복제가 실제 사용됐고 fallback은0이었다. 초기 loader의41%를 전체 성능으로 확대하지 않는다.

후보는 **미채택**이며 제품 app261파일/집계a18da9는 그대로다. 추가 보안 회귀·제품 구현·변경 없는 독립64 재접수는 하지 않았다. 위 동시 API 없는 비교도 원64 정상 관문이 아니다.

## 자원·실패와 다음 단계

새 독립 trial1/실제 quantum trial1의 고유2건을 완료했다. guard합157.377121초·단일/합 최대 RSS141,316,096/1,008,947,200bytes·FD4→4·5root/원본2,148/두 frozen source/자산·소유 PG/임시/passfile0을 확인했다. 원 상한을 유지했다. 첫 사설 snapshot은 비용 측정 전 imported dataclass 기본값 MISSING의 비지원 상태로 실패했다. 해당 기록을 보존하고 검토한 함수 정의와 imported alias를 구분한 새 v2에서 시험했다. 실패/기존72/선행 이력 관측2를 새2에 합산하지 않았다.

실제 native CLI `gpt-6.1-sol` / `xhigh` 문맥·사전 기준·source/probe/원 증거/종료 SHA를 기계 기록에 결속했다. 재귀 CLI/하위 에이전트·새 CI 접수·제품 변경은0이다.

다음 한 단계는 현재 권한 감사의 마지막4개 SELECT에 대해 **다중 결과 전달의 동등성**을 검토하는 것이다. [PostgreSQL simple-query 문서](https://www.postgresql.org/docs/16/protocol-flow.html#PROTOCOL-FLOW-SIMPLE-QUERY), [Read Committed](https://www.postgresql.org/docs/16/transaction-iso.html#XACT-READ-COMMITTED), [Psycopg 다중 문장](https://www.psycopg.org/psycopg3/docs/basic/from_pg2.html#multiple-statements-in-the-same-query)과 설치 source를 대조해야 한다. 여러 독립 SQL을 한 query string으로 보내는 경로의 snapshot·결과/오류 순서·안전한 인자·transaction 정리·기존 고정 응답을 먼저 확인한다. 이전15→4 SQL 병합이나 pipeline wrapper를 재적용하는 작업은 아니며 아직 새 전달 경로를 승인하지 않았다. 동등성 근거가 없으면 비용 trial을 하지 않는다.

원 독립 정상64→독립 hold→실제 HTTP취소→계산 중WebGL→WSL 용량/사용자 적용 순서, 새 Solar 미배포·실제 농장 Run0·국내 원 실측/독립 작기·G0–G4 보류·전체 완료일 미정·goal active를 유지한다.

최종 게시 `focused-solar-transcript-rejected-final-status-v2`는 자식0·guard1.377465초였다. 새 링크2/앞선 보고서6/관련 문서2,743개의 중첩 수는 합산하지 않았다. 원 actor/같은 app/기존72·이력2/새 trial2의 증거를 대사하고 두 HTTP200/동일bytes/no-store·frozen HTML/환기2,173파일·5root/원본2,148·FD4→4·소유 정리를 확인했다. 첫 게시 검증은 이전 helper의 완료 전 checkbox 기대가 남아 게시 전에 실패했다. 새 helper에서 완료 증거에 맞는 checked 상태를 확인했으며 나머지 guard는 유지했다. 실패는 수용에 포함하지 않았다. 진행 기록은2026-10-19T19:19:51.747243Z이며 UI 코드/DOM/WebGL 재검증은 아니다.
