# 공동 작물·기후 결과 저장 거래 — E3 로컬 수용

2026-10-10 KST. [결과 저장 계약](../contracts/crop-climate-joint-result-store-v1.md)의
호출자 거래 hook을 core `c99198c`으로 수용했다. 변경은 기존 store/test와 계약의 세 파일이다.
[실행 증거](artifacts/crop-climate-joint-result-transaction-reference-20261010.json)에
실제 명령·코드 pin·원 종료·관측·자원/정리를 기록했다.

## 구현과 현재 사용자 범위

[ResultStore](../backend/app/crop_climate_joint_result_store.py)의
`_put_in_transaction(conn, tenant, request_raw)`는 호출자가 시작한 authority 거래 안에서
원 completed/hold 결과를 등록하는 내부 context manager다. 기존 put과 같은 `_insert`를 사용해
원 packet·HMAC·참조 컬럼·잠금·충돌·현재 권리 검사를 공유한다.
같은 요청의 두 경로는 동일 bytes/SHA와 최초 recorded_at을 반환한다.

새 hook은 열린 정확한 psycopg Connection·autocommit=False·INTRANS와
SCRAM session/current authority·DB·명시 endpoint·현재 grants를 검사한다.
savepoint 안에서 결과를 등록하고, 호출자가 context 안에서 기록을 추가한 뒤 권리를 다시 확인한다.
호출자 오류/늦은 거부는 이 결과와 같은 savepoint의 호출자 기록을 함께 되돌린다.
호출자가 오류를 잡아 외부 거래를 계속해도 부분 결과는 남지 않는다. 외부 commit/close는 하지 않는다.
기존 put의 commit 뒤 권리 재검사와 private 감사 행 보존 동작도 유지했다.

이 검증에서 함께 작성한 job_event는 거래 경계 시험용이다. **실제 simulation job의 완료·게시·outcome은
아직 결속하지 않았고 E4 worker가 검증한다.** 현재5173은 완료된 합성166일의 생장/수확 재생을 유지한다.
새 실행 API·자동 진행 갱신·계산 중3D는 이번에 연결하지 않았다.

## 집중 검증

[신규10개와 기존9개](../backend/tests/test_crop_climate_joint_result_store.py), **고유19개**를
실제 PostgreSQL16.15/SCRAM에서 통과했다. 11개 실행 묶음 모두 root/child 종료0이고 실패/skip은0이다.
제품 source SHA는 전 실행에서 최종 코드와 동일하다. 기존 검사/fixture13개 정의도 AST 대조에서 동일하다.
초기 정상 검사 뒤 추가한 새 검사를 순차 실행했으며 기존 검사 전체를 보존했다.

| 경로 | 확인한 결과 |
| --- | --- |
| 외부 commit/재시도 | 같은 conn에는 결과1, 다른 conn에는0; 외부 commit 뒤 put/hook의 같은 bytes/최초 시각 |
| 호출자 오류3경우 | hook 내부/종료 뒤 오류는 rollback; 내부 오류를 잡고 외부 commit해도 결과0·거래 사용 가능 |
| yield 뒤 변경3경우 | 권리·쓰기 scope·resolver 변경은 결과와 호출자 event 모두 rollback; 복구 후 정상 등록 |
| 연결/소유 | idle/autocommit/aborted/closed·admin/worker·다른 tenant 거부, 새 결과0 |
| 원 hold/잠금 | 원 terminal progress/counts/UTC·관문 보존, advisory pending은 부분 행0·외부 거래 사용 가능 |
| 구형 저장 판본 | 실제 원 bytes/시각/행 불변, 새 reader와 두 writer는 보류, 원 reader는 동일 재조회 |
| 기존 경로 | 원 등록/fresh exec·권한·잠금/충돌·현재/늦은 철회·변조/혼합·hold·기존2결과 테이블 보존 |
| 계산 분리 | fixture 준비 후8종 Context/복원/RHS/적분/관리/시간 binding 호출0 |

## 이전 판본 보존

SQL/wire schema와 result ID prefix는 v1을 유지한다. 새 storage_code_sha256은 code 객체와
result ID의 해시에 들어가므로 기존 저장 코드와 별도 판본이다. 기존 행의 bytes/HMAC/시각을
수정하거나 새 코드로 자동 재서명하지 않는다. 현재 reader와 두 writer는 구형 code pin을 보류한다.
원 reader는 git `23b9da42f2bce869bab1106bdb53a848650b3f54`에 보존했다.
그 store source SHA는 `87e7e10e8d3476e437f5fec55f0cbc1ab03026a62a62019332ad5f0eab30538c`다.
실제 구형 서명 행을 등록한 뒤 현재 코드의 거부·행 불변과 원 reader의 같은 bytes/최초 시각을 검증했다.
원 reader 검사는 별도 로드한 고정 source를 사용했으며 fresh exec 검사는 기존 정상 경로에서 따로 통과했다.

## 자원·보존·다음 단계

전 실행에서 원본2,148항목·repository source·고정 사용자 source/assets와 보호 controller/service/PG를
보존했다. 5173은HTTP200, controller FD는4→4였다. 최대 단일132,399,104/
소유+보호 합436,658,176bytes로512MiB/1GiB 안이다. .25초 표본·child nice19·PID/start/boot와
pidfd 소유 정리를 사용했다. 소유 non-zombie/PG·임시 PG directory·passfile 잔존0과 schema/role0을 확인했다.
전체 backend/web·빌드·전체166일 계산·새 hosted CI는 실행하지 않았고 push hold를 유지했다.
최종 점검에서 core3 SHA·원 reader source의 git 판본 일치·로컬 파일 링크1540개·비밀 패턴0·
보호3 identity/원 HTML HTTP200을 확인했다. 원 시험 controller11개도 종료 상태다. 문서 anchor는 검사하지 않았다.

native Codex CLI `gpt-6.1-sol/xhigh`의01:43:21.258Z context에서 판단했다.
원 LF 행 SHA는 `dc62a7a80b901aaa26dd1fc9adbced5dfe833a50756dce3ca5d5f48a42504cd0`이며
recursive CLI와 새 제품 runtime CLI 실행은0이다. native→마지막 회귀 terminal은1,682.844초(약28분),
문서/commit은 별도다. 최초0.75–1.5시간 추정을 이 관측으로 갱신한다.

다음 E4는 E1의 같은 job을 실제 임대로 계산하고 E2 진행을 수용한 뒤, E3 context 안에서 결과와
job publication/outcome/완료를 원자 저장한다. chunk 취소/임대 만료·실제 중단 후 원 prefix 재적분0과
원108상태/UTC·현재 권리·부분 게시0을 실제 SCRAM/fresh exec로 확인한다. 잠정1–2집중시간이다.
그 뒤 API/typed client/UI와 실제 기동을 연결한다. E1–E9의10–18집중시간 전체 조건은 유지하며
작은 단계의 속도로 전체 날짜를 환산하지 않는다. 계산 중 prefix3D·전체 U3/생산 서비스 날짜는 별도다.
실제 농장 작물 Run/독립 국내 자료는0건, G0–G4 not_assessed·생산/미래 마진/추천 hold를 유지한다.
