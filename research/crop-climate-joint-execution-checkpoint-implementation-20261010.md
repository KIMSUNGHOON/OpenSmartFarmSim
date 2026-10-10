# 공동 작물·기후 checkpoint 수용 — E2

2026-10-10 KST. [실행 계약](../contracts/crop-execution-link-v1.md)의 E2 내부 서비스를
core `af93e83`으로 로컬 수용했다. 변경은 새 service/test와 실행 계약의 세 파일이다.
[실행 증거](artifacts/crop-climate-joint-execution-checkpoint-reference-20261010.json)에
각 실행의 코드 pin·명령·실패·실제 종료·검사 결과와 자원/정리를 보존했다.

## 구현과 사용자 확인 범위

[CheckpointStore](../backend/app/crop_climate_joint_execution_checkpoint.py)는 현재 simulation 임대가
원 서명 HEAD/proof와 확정 counts/계산 UTC를 기존 job_events에 수용하도록 한다.
닫힌 metadata는 8KiB 이하이고, 단조 publication_sequence와 별도 DB recorded_at을 기록한다.
같은 HEAD의 재확인은 같은 사건과 최초 시각을 반환한다. heartbeat로 진척 시각을 바꾸지 않는다.
이력 상한은 기존 custody commit 상한에서 유도하며 원 서명 계보·현재 입력/농장/권리를 대사한다.
현재 임대·취소·권리를 삽입 전후 재검사하고 늦은 거부는 사건을 rollback한다.
job 완료나 결과 등록·수치 계산은 이 서비스의 작업이 아니다.

**현재 localhost:5173은 완료된 합성166일의 생장/수확을 조회·재생한다.**
E2를 현재 서버의 worker/API/UI에 조립하지 않았다. 진행 정보 자동 갱신과 계산 중 새3D는 미구현이다.
첫 화면 연결은 진행 정보 갱신 후 terminal 결과의 같은 UTC3D 선택이며,
계산 중 prefix3D는 별도 계약/검증을 거친다. 이번 수용으로 기존 사용자 화면을 교체하지 않았다.

## 집중 검증

[새 검사](../backend/tests/test_crop_climate_joint_execution_checkpoint.py)13개와
기존 접수9/순수 JobStore 입력2개를 합쳐 **고유24개**를 확인했다.
실제 PostgreSQL16.15/SCRAM authority를 사용했다. 마지막 오류 분류 수정 뒤에는 정상 경로·
동시 잠금/재시도·fresh 복원과 회귀를 집중 검사했다. 최종 module SHA에서13개 전체를 반복하지 않았다.
수정 전 통과한 경로의 원 코드 pin을 보존했고 AST 대조로 바뀐 제품 메서드가 `_lease`/`_session`,
바뀐 시험이 동시 확인 하나임을 확인했다. 입력·권리·서명/이력·snapshot·거래 guard는 동일하다.

| 확인한 경로 | 수용 근거 |
| --- | --- |
| 정상/재시도/heartbeat | 같은 HEAD는 같은 event/time, job.updated_at의 heartbeat와 별도 |
| 원 결과 순서 | 정상 completed와 수치 hold의 원 HEAD/proof·counts/UTC, 단조 sequence; 실패 trial 행 비게시 |
| 임대/취소 | 잘못된 인자/시도/token·만료·취소 거부; 새 시도도 최초 사건 유지 |
| 늦은 변경 | 삽입 뒤 권리·scope·resolver·임대 만료·취소의5경우 rollback, 원 임대 복구 |
| 현재 자료/접근 |11scope 각각·다른 tenant·권리/검토 철회·source/HEAD/proof 변조 거부; create 권한은 요구하지 않음 |
| 혼합/이력 |6종 잘못된 envelope, bool count/중복 sequence를 넣은 잘못된 이력 거부 |
| 실제 중단/복원 | HEAD 뒤 DB 사건 전 producer SIGKILL(-9), 새 임대2/fresh exec 원 HEAD 수용·동일 event/time |
| 퇴행 거부 | 서명된 이전 HEAD로 되돌려도 새 DB 사건0; 원 HEAD 복구 후 최초 사건 유지 |
| 동시 요청 | 실제 행 잠금/5초 query timeout은 typed pending; 재시도1event/동일 최초 시각 |
| 계산 분리 | 확인 중10종 Context/복원/RHS/적분/사건/custody.advance/결과 등록0; 준비 fixture 계산은 별도 |

## 원 실패와 수정

첫 normal-v1의 구문 오류를 수정했다. normal-v2/diagnose-v1은 farm binding의 `m²`를
ASCII escape로 재인코딩해 원 UTF-8 SHA와 달라진 오류다. E1의 원 canonical 함수를 사용하도록
수정했으며 원 단위/UTF-8 SHA를 검사했다. normal-v3은 통과했다. 당시 잘린 도구 출력은
원 terminal 파일에서 child 종료0을 복구했으며 controller 종료는 다시 관측했다고 주장하지 않는다.
최종 제품 코드의 정상 경로는 concurrent-v2에서 별도로 통과했다.

concurrent-v1/diagnose-v2는 같은 job 행을 기다리던 두 번째 SQL이 기존5초 statement_timeout에
걸리는 실제 실패다. 잠금 조회의 QueryCanceled를 일시 JointCustodyPending으로 분류하고,
파일 session 종료에서도 유형을 보존했다. DB 제한이나 임대 시간을 늘리지 않았다.
concurrent-v2의 fault 주입은 농장 검증의 별도 research job 잠금까지 건드려 실패했다.
주입 대상을 해당 simulation job으로 제한해 concurrent-v3을 통과했다. 제품 코드는 v2/v3에서 같다.
실제 SCRAM 동시 잠금과 session 내부 pending rollback 모두 확인했다.
마지막 fresh-v2와 regression-v1도 종료0이다. 모든 원 실패/소스/로그 SHA를 artifact에 남겼다.
late-v1이5경우를 통과했고 latelease-v1의2경우는 중복 실행이며 고유 검사 수에 추가하지 않았다.

## 자원·보존과 남은 의존성

모든 실행에서 원본2,148항목·repository source·고정 사용자 source/assets와 보호 controller/service/PG를
보존했다. 5173은HTTP200, controller FD는4→4였다. .25초 표본의 최대 단일138,743,808/
소유+보호 합434,565,120bytes로512MiB/1GiB 안이다. child nice19와 PID/start/boot·pidfd 소유 정리를
사용했고 소유 non-zombie/PG·임시 PG directory·passfile 잔존0, 검사 뒤 schema/role0을 확인했다.
전체 backend/web·빌드·전체166일·새 hosted CI는 실행하지 않았다. push hold를 유지했다.
최종 점검850196에서 core3 SHA·로컬 파일 링크1,537개·비밀 패턴0·보호3 identity/원 HTML HTTP200을 확인했다.
문서 anchor는 검사하지 않았으며 별도 identity 점검에서 원 시험 controller17개가 모두 종료 상태임을 확인했다.

개발 판단은 native Codex CLI gpt-6.1-sol/xhigh의00:57:55.507Z와01:13:58.871Z context에서 수행했다.
원 LF 행 SHA는 artifact에 기록했으며 recursive CLI와 새 제품 runtime CLI 실행은0이다.
native 시작→마지막 회귀 terminal은2,485.837초(약41분), 문서/commit은 별도다.

다음 한 단계는 E3 결과 transaction hook이다. 기존 put과 caller 소유 transaction의 검증/원 metadata·
최초 시각을 일치시키고 rollback/늦은 권리 거부 시 부분 row0을 실제 SCRAM으로 확인한다.
코드 pin 변경의 판본 경계를 명시하고 기존 불변 결과/frozen reader를 보존한다. 이후 E4 worker→
보호 API→typed client/UI→실제 기동 검증으로 진행한다. E3은 잠정0.75–1.5집중시간이며
E1–E9의10–18집중시간 전체 추정을 단일 단계 속도로 환산하지 않는다.
실제 품종/농장 작물 Run과 독립 국내 자료는0건, G0–G4 not_assessed·생산/미래 마진/추천 hold다.
외부 자료 확보와 전체 U3/생산 서비스 완료 날짜는 이번 소프트웨어 관측으로 확정하지 않는다.
