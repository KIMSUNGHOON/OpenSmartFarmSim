# 공동 작물·기후 임대 worker — E4 로컬 수용

2026-10-10 KST. core `6cf4eaf`의 worker/test/실행 계약 세 파일을 수용했다.
[실행 증거](artifacts/crop-climate-joint-execution-worker-reference-20261010.json)는
400,664bytes, SHA-256 `b0911c96b274bd6cb8718f7d86ecb9c94d4321ad31fafb8babd8269b8c432514`다.
대상은 원32초·16걸음·108상태·명시 상수 입력의 합성 연구 실행이다.

## 실행과 저장

[`JointExecutionWorker.run_once`](../backend/app/crop_climate_joint_execution_worker.py)는
E1 job의 현재 임대·불변 입력·현재 농장/자료 권리를 확인하고 E2에 진행을 수용한다.
계산은 원1–128 예산의 구간으로 나누며 구간 전 임대를 갱신한다.
중단 뒤 원 HEAD가 있으면 Context/복원/RHS 호출 없이 먼저 수용한다.
구간 도중 취소/만료 뒤 생긴 private HEAD는 작업 진행이나 결과로 자동 게시하지 않는다.

E3 hook의 같은 conn에서 결과 registry·결과 연결 사건·terminal event/outcome을 작성한다.
hook 종료의 권리 검사 뒤 같은 외부 거래에서 현재 실행 권리/입력·임대를 다시 확인하고,
마지막 DB clock/취소 fence로 상태를 갱신한다. 이 뒤 실패도 외부 거래 전체를 되돌린다.

기존 DB는 `succeeded` iff 일반 publication1을 강제한다. 초기 수치 hold의 일반 publication은
실제 deferred `CheckViolation`으로 commit이 거부됐다. 이를 진단해 성공에는 일반 publication을,
수치 hold에는 publication0과 닫힌 `joint_execution_result_registered_v1` 사건을 사용하도록 보완했다.
두 경우 모두 등록 연구 결과와 작업의 연결을 같은 거래에 저장한다. DB schema와 일반 조회 계약은 유지했다.
현재 권리/자료 거부에는 새 결과 연결이 없다. [닫힌 연결 객체와 후속 reader 조건](../contracts/crop-execution-link-v1.md)을 명시했다.
성공 packet의 content-addressed 파일은 rollback 뒤 비공개 잔존할 수 있으며 선택 가능한 DB 연결은 없다.

## 실제 검증

신규24개와 관련 기존4개, **고유28개**를 실제 PostgreSQL/SCRAM에서 통과했다.
최종 수용27묶음은 모두 child/root 종료0·실패/skip0이며 제품 source SHA가 최종 코드와 같다.
정상 검사는 마지막에 구간/임대 실측을 추가해 재실행했다. 같은 검사 중복은 고유 수에 더하지 않았다.
시험 파일 판본·선택식과 원 로그 SHA는 묶음마다 기록했다. 최종 module 전체를 한 명령으로 재실행한 증거는 아니다.
기본 명령은 `nice -n 19 backend/.venv/bin/python -m pytest -q -p no:cacheprovider --tb=short`에
해당 test와 `-k` 선택식을 붙였으며, 실제 argv·소유 PG 환경·원 로그는 로컬 private 증거에 보존했다.

| 검사 | 확인한 결과 |
| --- | --- |
| queued→완료/hold | 실제 세 구간·원 모든 행/108상태·UTC·실패 trial 정상 행0·별도 exec의 동일 결과/연결 |
| 성공/보류 거래 | 성공 registry1/publication1/link1/outcome1, 수치 hold는1/0/1/1; 같은 job/attempt·packet/root SHA 구분 |
| 실제 crash | HEAD 뒤 DB 사건 전 producer SIGKILL(-9); 새 exec/임대2가 원7걸음을 계산0으로 수용하고9걸음만 계산 |
| crash 원값/UTC 대사 | 정상 기준과 최종108상태 checkpoint·last_confirmed 동일; 원0/8/16시점 UTC를 독립 대사. 구간별 times 목록 길이는 달라도 원 격자/시각은 같음 |
| 임대/취소 | 구간 뒤 만료→새 임대 재개, 구간 직후/완료 직전 취소·새 결과0, 마지막 fence의 거래 안 만료 주입→전체 rollback |
| 오류5지점 | publication/event/outcome/hook 종료/최종 UPDATE 실패 모두 결과·연결·완료0, 원 확정 checkpoint는 유지 |
| 늦은 변경3경우 | 완료 기록 뒤 실행 scope·자료 권리·resolver 변경은 결과/연결/outcome rollback 후 안전한 보류 |
| 재사용/잠금 | 원 완료 결과의 ID/bytes/최초 시각 보존·계산0; 실제 custody 잠금은 일시 재시도 |
| 입력/소유 | 닫힌 입력 거부·다른 stage/version·사전 취소·권한/tenant/ID/고정 authority/bounds 거부; 잘못된 SHA는 DB 접수부터 거부 |
| 기존4개 | E2 최초/중복/heartbeat와 완료/hold sequence2개, E3 원 등록/fresh 조회; 기존 두 결과 테이블 보존 |

초기 실패도 보존했다. 별도 exec 출력의 import 누락, worker 감사 사건을 무변경으로 보던 비교,
수치 hold에 재개용 checkpoint가 있다고 가정한 시험을 수정했다. 원 hold는 checkpoint=null과
last_confirmed/진단을 보존한다. DB publication/state 충돌은 실제 worker 수정이며 원 진단 프레임을 보존했다.
잘못된 입력은 기존 immutable job을 수정하지 않고 새 소유 행으로 시험했다. SHA CHECK를 우회하지 않았다.

## 시간·자원·보존

마지막 정상 worker는79.268초였다. 예산8의 세 advance는13.822/11.115/15.679초,
임대 갱신 간격 최대21.266초·마지막 갱신→완료35.543초였다. 시험의600초 임대 안이다.
`monotonic` 실측이며 임대 허가는 DB clock fence가 판단한다. 이 작은16걸음의 비용을 전체 작기에 외삽하지 않는다.

.25초 표본·child nice19·PID/start/boot·pidfd 정리에서 최대 단일129,622,016/
소유+보호 합451,383,296bytes로512MiB/1GiB 안이었다. controller FD4→4,
소유 non-zombie/PG·임시 PG directory/passfile·schema/role 잔존0을 확인했다.
원본2,148항목·repository source·고정 사용자 source/assets·보호3 identity와5173 HTTP200을 보존했다.
전체 backend/web·새 빌드·전체166일 계산·hosted CI는 실행하지 않았으며 push hold를 유지했다.
최종 core source pin/DB 원 bytes·로컬 파일 링크1,751개·비밀 패턴0·시험 controller34개 종료와
보호3 identity·원 HTML SHA/HTTP200을 확인했다. 문서 anchor는 검사하지 않았다.

native Codex CLI `gpt-6.1-sol/xhigh`의02:19:33.608Z context에서 판단했다.
원 LF 행 SHA는 `65110080441857193861bfa337b77cf733c76a868ba9b08dc47613d4556bd932`다.
recursive CLI와 새 제품 runtime CLI 실행은0이다. native→마지막 집중 terminal은
3,414.796초(약57분)였으며 문서/commit은 별도다.

## 다음 사용자 경로와 외부 의존성

현재5173은 기존 완료 합성166일의 생장/수확 재생을 유지한다. 새 worker는 명시적 내부 호출이며
자동 발견/소비·접수/진행/취소 HTTP·웹 자동 갱신은 후속이다. 계산 중 prefix3D도 별도다.
다음 E5a는 joint 입력 판본의 명시적 발견과 실제 혼합 queue/페이지·권한·조회 계산0을 검증한다.
이어 E5b 자동 소비→E6 현재 조회/HTTP/runtime→E7 typed client→E8 화면→E9 실제 사용자 기동을 연결한다.

[남은 E5–E9](../tasks/plan.md#작물-계산과-ui의-실행-연결--2026-10-10)는 문서/검토 여유를 포함해
6–12집중시간 잠정이다. 전체 U3/최종 UI·forcing 변경/전체 작기 부하·물/양분/구매 에너지/경제 연결과
실제 품종·독립 국내 농장 자료/게시 관문은 별도다. 실제 crop Run/독립 자료0건,
G0–G4 not_assessed·생산/미래 마진/추천 hold를 유지하며 실제 자료 확보일에 근거한 완료 날짜는 아직 없다.
