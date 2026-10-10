# 공동 작물·기후 실행 접수 — E1 로컬 수용

2026-10-10 KST. [실행 연결 계약](../contracts/crop-execution-link-v1.md)의 E1을
**소유 합성 입력의 내부 simulation 접수**로 수용했다. core commit은 `9f5c18d`이며 변경 경계는3파일이다.
[실행 artifact](artifacts/crop-climate-joint-execution-admission-reference-20261010.json)에
원 명령·종료/실패·로그/코드 SHA·접수 관측과 보존/자원을 기록했다.

## 구현과 사용자에게 보이는 범위

새 [service](../backend/app/crop_climate_joint_execution.py)는 현재 농장/작물/배치·입력/모델/UTC·권리를
기존 farm binding으로 확인해 불변 simulation job을 만든다. 별도 큐·테이블·운영 서비스는 추가하지 않았다.
서버 소유 resolver가 원 source/proof를 제공하며 사용자 경로/키/원자료를 받지 않는다.
tenant/study/revision의 domain SHA를 기존 멱등 키에 사용한다. 동시 동일 요청도 job/event 하나이고
같은 revision의 다른 내용/resolver는 conflict다. 취소된 작업의 중복 요청은 원 canceled job이며
새 revision만 새 job을 만든다. 접수 중에는 Context/RHS·적분·custody advance·결과 등록을 실행하지 않는다.

현재 authority/principal provider·resolver version과 코드/입력 판본/domain/64KiB 상한을 고정한다.
JobStore transaction의 마지막 guard에서 원 binding/권한을 다시 검사하며 삽입 뒤 철회는
job/event를 함께 rollback한다. 예외는 고정 문구이며 내부 resolver 경로/메시지를 전달하지 않는다.
이 관측은 호출 전후의 현재 권리 검사이며 모든 외부 권리 저장소의 전역 원자 snapshot은 아니다.

**localhost:5173은 기존 완료 합성166일의 생장/수확 저장 결과를 그대로 읽는다.**
새 service는 공개 HTTP/화면에 조립하지 않았고 현재 worker/discovery는 새 입력을 소비하지 않는다.
계산 진행 자동 갱신·서버 취소 UI·완료 result 선택 연결은 후속 E2–E9다.
기존 terminal-only 페이지를 넓힌 계산 중 prefix3D도 이번 수용에 포함하지 않는다.

## 검증과 원 실패

[새 검사](../backend/tests/test_crop_climate_joint_execution.py)9개와 기존 farm binding6/순수 input2개,
**고유17개**를 통과했다. 실제 PostgreSQL16.15의 SCRAM authority 연결을 사용했다.

| 검증 | 확인한 결과 |
| --- | --- |
| 정상/재조회 | 같은 요청3회·새 service도 같은 queued job; 원 binding/input SHA·farm/batch·7,827bytes |
| 멱등/동시성 | 동시 동일 요청1job/1event; 다른 유효 내용1job/1conflict; resolver 판본 충돌 |
| 현재 접근/자료 |11scope 각각·다른 tenant·권리/검토 철회·원 source bytes 변경 거부; 복구 후 접수 |
| commit 직전 변경 | 실제 insert/event 뒤 권리·scope·resolver 변경3경우 rollback, 같은 intent 정상 복구 |
| 닫힌 요청/상한 |7invalid request·6invalid resolver·원문 없는 오류;64KiB 초과 요청/oversized binding fault 거부 |
| authority/pin | 입력 판본/domain/상한/code·principal provider 변경과 nonexact binding 거부 |
| 취소된 의도 | cancel scope 없으면 거부; scope 부여 후 취소·재요청은 원 canceled job; 새 revision만 새 job |
| 접수 계산 분리 | setup 이후10종 준비/복원/RHS/적분/사건/custody/결과 등록 호출0; job publication/attempt 추가0 |
| 회귀 | 기존 farm binding6검사·별도 fresh exec/현재 권리와 순수 canonical input2검사 통과 |

prototype `normal-v1`은1통과/20.650초였으며 이후 contract guard/검사를 확장했다.
최종 제품 source의 `full-v1`은 **8통과/1실패**·root/child1·132.696초였다.
실패는 시험 계정의 cancel scope가 없어서 기존 JobStore가 취소를 거부한 경우다.
권한 없는 취소 거부를 유지하고 명시 scope 부여 뒤 원 취소 이력을 확인하도록 해당 시험만 수정했다.
`conflict-v2`는1통과/8deselected·root/child0·22.880초다.
두 단계의 제품 source SHA는 같다. AST 대조에서 바뀐 정의는 실패한 시험 하나뿐이며
다른8검사/공유 fixture는 동일하다. 다른8통과를 반복하거나 실패를 성공으로 덮어쓰지 않았다.
`regression-v1`은8통과/11deselected·root/child0·93.723초다.
전체 실행 관측4개 중 원 실패1개를 artifact에 보존했다.

모든 단계에서 repository source·고정 사용자 source/assets·원본2,148항목 metadata/SHA를 보존했다.
보호 controller/service/PG identity는 생존했고5173은HTTP200이었다. controller FD는4→4다.
관측 최대 단일139,509,760/소유+보호 합413,671,424bytes로512MiB/1GiB 안이다.
.25초 표본·child nice19·PID/start/boot와 pidfd 소유 정리를 사용했다.
소유 non-zombie/PG·임시 PG directory·passfile 잔존0이며 시험 후 schema/role도0이다.
전체 백엔드/웹·빌드·새 hosted CI·전체166일 계산은 재실행하지 않았다. 기존 코드/화면/의존성은 변경하지 않았다.
최종 `62ccf7` 종료0에서 core3 SHA·로컬 링크1,724개·비밀 패턴0·보호3 identity/원 HTML HTTP200을 확인했다.

## 판단 환경·다음 단계

실제 native Codex CLI turn context `2026-10-10T00:37:33.252Z`의 모델은
`gpt-6.1-sol`, effort는 `xhigh`다. 원 LF 행 SHA는
`18e338f72419abe8eaec0f52015c667db7f9e9b3c597a26d2553b8010bb956c7`이며 재귀 CLI는0회다.
이번 child의 새 제품 runtime CLI 실행은0회다. 기존 CLI runtime의 전체 연결/독립 해제는 후속이며
현재 개발 CLI의 증거로 제품의 실제 판단/자료 채택을 완료 처리하지 않는다.

다음은 E2: 현재 임대가 원 서명 HEAD/확정 counts/UTC를 append-only job event에 수용하고
checkpoint DB 수용 시각을 heartbeat와 구분한다. E3은 기존 결과 저장을 caller transaction에 결속한다.
그 뒤 worker→현재 API/취소→typed client/UI→실제 DB/TLS/browser로 연결한다.
E1의 초기0.5–1.5시간 추정은 native00:37:33Z→회귀 terminal00:50:01Z의748.422초(약13분) 개발/실패 추적·검증 관측으로 갱신한다.
기록/검토·commit은 별도며 E2–E9의10–18집중시간 전체 추정을 이 단계 속도로 단순 환산하지 않는다.
실제 품종/농장 작물 Run/독립 국내 자료0건, G0–G4 not_assessed·생산/미래 마진/추천 hold는 유지한다.
