# 권한 감사 전달·커서 후보 평가: 미채택 — 2026-10-20 KST

[기계 증거](artifacts/solar-role-tail-protocol-and-cursor-evaluation-20261020.json) · [선행 반복 load 후보](solar-storage-load-transcript-evaluation-20261020.md).

## 원 SQL 다중 결과 전달: 반례로 제외

현재 감사의 마지막4개 SELECT는 table/column 유효 권한·grant option·routine 실행·creator defaults를 검사한다. [PostgreSQL simple query](https://www.postgresql.org/docs/16/protocol-flow.html#PROTOCOL-FLOW-SIMPLE-QUERY)는 여러 문장을 전달할 수 있지만 오류/transaction 처리도 확인해야 한다. [Read Committed](https://www.postgresql.org/docs/16/transaction-iso.html#XACT-READ-COMMITTED)의 successive statement 설명만으로 Python의 조기 중단까지 동등하다고 판단하지 않았다.

[Psycopg 다중 결과 설명](https://www.psycopg.org/psycopg3/docs/basic/from_pg2.html#multiple-statements-in-the-same-query)과 설치3.3.6의 `_maybe_prepare_gen → _check_results → _set_results`를 대조했다. 드라이버는 전체 결과의 오류를 먼저 검사하며 `nextset`은 이미 받은 결과를 선택한다. 웹 문서는3.3.7.dev1이고 설치 source/lock SHA는 별도로 고정했다.

실제 SCRAM의 소유 합성 fixture에서 **원4 SELECT와 원 bound 인자**를 안전한 Literal로 구성해 확인했다. 정상 결과4개는 모두 빈 결과였다. 이후 소유 schema 안의 invoker routine·명시적 project-first search_path와 허용되지 않은 DELETE grant를 주입했다. 원문 SQL은 바꾸지 않았다.

| 같은 주입 조건 | 최초 관측 | transaction | 후속 SELECT |
|---|---|---|---|
|원 전체 auditor|`RolePolicyHold/runtime_table_grant_matrix`|`INTRANS`|성공|
|원4문장 simple-query 묶음|뒤 column 문의 `RaiseException/P0001`; 첫 fetch 전 실패|`INERROR`|rollback 필요|

원 auditor는 첫 권한 위반에서 중단했다. 묶음은 뒤 문장의 오류가 먼저 드러나 실패 종류와 transaction 상태가 달라졌다. 이 조건에서 일반 동등성이 없으므로 **전달 후보를 제외하고 비용 trial은 하지 않았다.** 주입/원천을 모두 복원하고 원 auditor 성공을 확인했다. 이는 현재 배포의 취약점이나 원 CI 시간 제한의 원인 보고가 아니다.

## 별도 후보: 원 순서를 유지하는 커서 재사용 — 비용 미충족

위 반례 때문에 SQL은 각각 원 순서대로 실행했다. [Psycopg adaptation 설명](https://www.psycopg.org/psycopg3/docs/advanced/adapt.html#adaptation-configuration)과 설치 source의 cursor 생성·query identity/Transformer·adapter 복사 동작을 대조했다. 같은 물리 연결에서 query별 native cursor를 재사용하는 사설 후보를 평가했다. 모든 원 SQL과 현재 권한 함수를 실제로 다시 실행하며 권한/행 결과를 보관하지 않는다.

adapter map·필요 타입 정보/클래스·함수 metadata·row/cursor factory를 매 호출 대조하고, 소유 연결/구간이 닫히면 cursor도 닫았다. 현재 dumper/loader 변경 시 재생성2회와 다른 row factory의 원 경로 fallback1회를 확인했다. 완전한 의존성 폐쇄·다른 thread/task·오류/수명/보안 수용은 아직 아니며 실제 비용을 먼저 판정했다.

사전 기준은 실제 quantum 평균2% 이상과 두 짝 모두 개선이다. 원 `worker._before → server.advance → worker._confirm`의 ABBA에 cache 생성·metadata 대조·cursor 정리 비용을 포함했다. 두 모드에 같은 auditor wrapper/하위 query observer를 사용했고 원 함수/수치 입력은 유지했다.

| 짝 | 기존 wall초 | 후보 wall초 | 감소율 |
|---|---:|---:|---:|
|첫 짝|7.652470|8.114249|−6.0344%|
|둘째 짝|7.880688|8.215409|−4.2474%|

평균 **−5.1277%로 양쪽 모두 느려 미채택**했다. 후보마다 cursor 생성105/재사용4,410·refresh/fallback0이 실제 발생했다. 원 quantum의 SQL11,125·감사301/원 감사 SQL4,515·원천2,584와 같은 checkpoint counts와 UTC `00:00:04.123456Z`–`00:00:10.123456Z`(2초 간격)를 대사했다. 재사용 건수만으로 개선을 주장하지 않는다. 추가 보안 회귀·제품 구현은 중단했고, 이전 pipeline/15→4 병합/직접 ACL 후보를 다시 적용하지 않았다.

## 보존과 다음 한 단계

새 반례1/실제 비용1의 고유2건이다. guard합77.810431초·단일/합 최대 RSS141,316,096/1,000,112,128bytes·FD4→4·5root/원본2,148/두 frozen source/자산·소유 PG/임시/passfile0을 확인했다. 첫 반례 시험은 native transaction status의 int를 enum으로 취급한 시험 오류로 실패했다. 새 v2에서 enum 변환만 고쳤으며 원 거부와 제품은 그대로다. 실패/기존72/선행 이력2/직전 transcript2를 새2에 합산하지 않았다.

제품 app261파일/집계a18da9는 유지했다. 실제 native CLI `gpt-6.1-sol` / `xhigh` 문맥과 source/lock·사전 기준/probe/종료 SHA를 기록했다. 재귀 CLI/하위 에이전트·새 CI 접수·제품 변경은0이다. 전체 backend/browser 검증이나 원64 정상은 재실행하지 않았다.

다음은 **worker의 미사용 advance 응답 생성 경계**다. 현재 `run_once`는 `server.advance`의 반환을 버리고 즉시 `_confirm`의 checkpoint를 소비한다는 AST를 확인했다. 공개 `advance/inspect/page`의 원 응답을 유지하면서 worker 전용 쓰기 확인 경로를 둘 수 있는지 먼저 검토한다. 수치·private 파일 쓰기·HEAD 게시의 원 current guard, 후속 `_confirm`의 현재 입력/권리·lease/cancel·변경 차단과 원 checkpoint/UTC/원자 DB 게시를 유지해야 한다. 원 actor/input64/chunk1/poll/retry360/RSS와 전체 정상 증명은 바꾸지 않는다. 새로운 경로는 아직 승인/구현하지 않았다.

원 독립 정상64→독립 hold→실제 HTTP취소→계산 중WebGL→WSL 용량/사용자 적용 순서, 새 Solar 미배포·실제 농장 Run0·국내 원 실측/독립 작기·G0–G4 보류·전체 완료일 미정·goal active를 유지한다.

최종 게시 `focused-solar-role-tail-cursor-final-status-v1`는 자식0·guard1.368947초였다. 새 링크2/앞선 보고서3·6/관련 문서2,749개의 중첩 수는 합산하지 않았다. 새2건/과거72·이력2·transcript2의 증거·원 actor/같은 app hash를 대사하고 두 HTTP200/동일bytes/no-store·frozen HTML/환기2,173파일·5root/원본2,148·FD4→4·소유 정리를 확인했다. 진행 기록은2026-10-19T19:39:36.173837Z이며 UI 코드/DOM/WebGL 재검증은 아니다.
