# 작물·기후의 현재 농장·자료 권리 연결 — 2026-10-10

## 수용 범위와 산출물

core **c4b8e8ea4f4315734527bd830ddf0ad393dc2f99**의
[150줄 결속 모듈](../backend/app/crop_climate_joint_farm_binding.py), [실제 DB 검사](../backend/tests/test_crop_climate_joint_farm_binding.py),
[계약](../contracts/crop-climate-joint-farm-binding-v1.md)을 로컬 수용했다.
[검증 묶음](artifacts/crop-climate-joint-farm-binding-reference-20261010.json)에 현재 권리·원 실패·fresh exec·정리/자원을 기록했다.
새108상태의 서명 input evidence를 현재 등록 farm/source 권리에 연결한 자식이다.
서버가 서명한 계산 이력·새 결과의 DB 등록/API/3D·실시간 U3는 아직 미구현이다.

기존 `FarmAuthoringService`·authority SCRAM JobStore/전체 grant 감사·기존 crop read/write scope를 사용한다.
신뢰한 서버가 원 directory/evidence bytes와4개 expected SHA를 제공한다. 사용자 요청에서 임의 경로를 받지 않는다.
서명된 원 input evidence를 전후 검증해 context/seed/profile/model·UTC·검토자/결정/증거 ID를 결속한다.
현재 tenant/farm revision/job/hash·source binding·crop/batch/zone/floor/기간/occupancy·availability를 확인한다.
읽기는 research_display, 쓰기는 research_calculation+research_display를 두 번 확인하고 현재 등록/원본/검토/scope를 재검사한다.

별도 DB schema/role/service·운영 기반을 추가하지 않았다. 자료 권리 provider는 기존 형식의 trusted callable이며
시험의 source 권리와 검토 resolver는 소유 합성 기록이다. 실제 농장 동의·외부 자료 G0 승인으로 표시하지 않는다.
profile_applicability는 `unvalidated_for_registered_crop`이며 등록 품종 의도를 검증된 품종으로 바꾸지 않는다.

## 실제 검사·발견한 경계

| 단계 | 원 세션/완료 도구 | 실제 결과 |
| --- | --- | --- |
| 최초 DB fixture 기동 | 71289 / `0b027c` | 종료1·setup error1·본문0·감독2.378초 |
| 첫 정상 권리 경로 | 90433 / `bae47b` | 종료1·정상 경로1실패·감독14.740초 |
| 원 실패 진단 | 33537 / `81f29e` | 종료1·같은1실패의 원 stack·감독15.029초 |
| UTC 수정 후 정상/fresh | 82955 / `97e861` | 종료0·1그룹 통과·pytest18.82/감독19.810초 |
| 현재 권리/닫힌 입력 | 98468 / `f332d0` | 종료0·2그룹 통과·pytest31.92/감독33.372초 |
| callback/설정/기간 경계 | 55560 / `4d7b15` | 종료0·3그룹 통과·pytest45.41/감독47.189초 |
| 별도 증거/원 입력 대사 | 29818 / `f2d9f5` | 종료0·감독1.327초·원 입력 검증 계산0 |

최초 fixture의 pg_ctl 기동은 실패했고 원 임시 server 로그는 cleanup으로 남지 않았다.
긴 workspace TMPDIR 대신 짧은 소유 임시 root를 쓴 후 실제 cluster 기동/SCRAM을 통과했다.
원 startup의 세부 원인을 확정한 것으로 표시하지 않으며 제품 fixture/운영 코드는 변경하지 않았다.
감독의 최초 생성 구문 오류는 실행 전 수정했으며 검사 본문/수용 수에 포함하지 않는다.

원 정상 실패는 `CycleFarmBinding._registration`이 호출하는 whole-second UTC parser에서 확인했다.
새 time binding은6자리 마이크로초를 보존하므로 그 함수 객체를 재사용할 수 없었다.
기존 농장/availability/점유 정책을 유지하면서 원 UTC 정밀도로 비교하는 새 결속을 구현했다.
원 source SHA `8d07251921b699d533a3a05b975d0e981d780ac7f4707dcc188220f1b157ea73`과 실패 로그를 보존했다.
정상 `00:00:00.123456Z`부터32초의 원 시각을 유지하고, 인증된 끝이 crop 종료보다 **1마이크로초 초과**하면 거부한다.
반올림·절단으로 과거 helper에 맞추지 않았다.

수정 후 **고유6개 pytest 그룹을3개 순차 실행으로 수용**했다. 세 실행의 core3 SHA는 같다.
단일6 GREEN 또는 전체 backend 수용으로 표시하지 않는다. 그룹 안의 거부 사례 목록은 검증 묶음에 보존했다.
정상 prepare/read/write·입력 검증2회/권리 관측2회, 각 read scope/쓰기 분리/다른 tenant,
현재 source/검토/권리 철회, 다른 source/context/time/evidence/program/등록/crop/기간/availability,
old schema·비 canonical/중복/NaN/UTF-8/빈/초과, callback 중 선언/원 bytes/source/scope/권리/검토 변경,
서비스/authority/policy/DB identity/code/key ID·expected binding 변경과 exact True/bool 요구를 확인했다.

## 실제 fresh exec·수치/DB·정리

원 정상 binding은6,580bytes다. prepare0.974180초/current0.934661초는 이 작은 합성 입력의 실측이다.
이 값을 전체 작기/API 지연으로 확대하지 않는다. 원 tenant/crop/batch/zone·원 model/profile/검토/UTC를 유지했다.
권리 연결 전후 jobs/events는89/89로 같고 작물 결과/Run은0/0이다.

별도 Python **fresh exec PID1920137 실제 종료0**에서 현재 같은 실제 DB/등록·원 입력/키·provider graph를 새로 만들었다.
fork 상속 서비스로 대체하지 않았다. 원 binding SHA와 bytes가 같고 actual SCRAM/used_password·require_auth를 확인했다.
검토 철회 뒤 현재 조회는 hold였다. context 생성·start/restore/advance·RHS/step/event·UTC binding 생성은 모두0회다.
parent의 각 검사도 같은8종 호출을 금지했고 새 작물 행/Run을 만들지 않았다.

각 DB 실행 뒤 schema/role0·passfile0·임시 cluster directory0·관측한 PG/소유 non-zombie 잔류0을 확인했다.
private 감독은 자기 자식의 subreaper와 기존 pidfd 소유 helper를 사용하며 원 미리보기 PID를 보호했다.
별도 root는 이미 정리된 farm DB를 다시 조회하지 않았다. 실제 정상/fresh/거부 증거와 남아 있는 원 input evidence/hash를 대사했다.
root의 입력 검증8종 호출0·FD4→4이며 이를 새 live farm 권리 판정으로 표시하지 않는다.

선행32 core·9구성 코드·16oracle SHA를 보존했다. 이전82개/993개 수치·저장 회귀와 원166일 RHS/writer/API/WebGL은 재실행하지 않았다.
모든 감독의 source1,734·원본2,148항목·기존 preview source/assets/실제3 PID·frontend200을 보존했다.
FD4→4·0.25초 관측 최대 단일 RSS147,255,296/소유+보호 합567,664,640bytes로512MiB/1GiB 안이다.

설계·판단·구현/검토는 현재 native CLI **gpt-6.1-sol / xhigh**,2026-10-09T18:38:14.702Z에서 수행했다.
원 turn_context 줄(LF 포함) SHA는 `6efed4d37fac19718170eeb328bf21516d12441534b6fae804b4301847145b5b`다.
재귀 CLI0·제품 runtime CLI 추가0회다. 이번 출력은 위 core/계약·검증 묶음이며 관문 승인으로 취급하지 않는다.
관측 exact703e49c Backend37962183498은0–4 success·5 in_progress이며 새 core의 hosted 수용은 없다.
기존 CI를 취소/재시작/새 push로 대체하지 않았다.

## 다음 한 단계·수용 기준·외부 의존성

`localhost:5173`은 기존 완료 합성166일 생장/수확의 실제 DB/API·같은 UTC3D를 유지한다.
이번 새 모델은 UI에 아직 연결하지 않았고 계산 진행률/새 checkpoint 자동 갱신 U3도 미구현이다.
다음은 **서명된 공동 계산 이력→새 DB 결과 등록→현재 권리 API→같은 UTC3D→사용자 실행/U3**다.

다음 `crop-climate-joint-server-custody` core3은 현재 결속을 작은 원 producer의 intent/분할 계산/HEAD/root 전후에 적용한다.
새108상태/UTC/서명 증거의 공식 준비와 원 체크포인트/원량을 고정하고 별도 domain HMAC으로 intent/확정 HEAD를 인증한다.
원475줄 custody는 이전 exact binding/reader/engine 전용이므로 파일 제어/서명 helper의 적용 범위만 검토한다.
실제 작은 정상/hold·현재 계정/source/검토/입력 철회·변조/혼합/재시작/원 prefix·FD/정리/자원을 확인한다.
새 DB schema/role·API/3D와 전체 작기의 수용은 후속으로 남긴다.

잠정 분해는 원475줄/새150줄·저장323줄 대조와 계약0.5–1시간, 구현1–2시간,
실제 producer/권리·HMAC/재시작 검증1–2시간, 증거/기록0.5–1시간의 **3–6집중시간**이다.
이번 실제 DB3회19.810/33.372/47.189초와 fresh exec의 수용을 근거로 하며 다음 producer 비용은 아직 실측 전이다.
계속 작업·새 외부 자료가 불필요한 합성 경로 조건으로10월10일 검토를 목표로 한다. 전체 UI/제품 완료일은 아니다.
실제 품종 입력/농장 Run/국내 독립 자료0건·온실 forcing/물·양분/구매 에너지/Decimal 경제와
G0–G4·생산/미래 마진/추천 hold를 유지한다. 독립 자료·권리 확보는 개발과 병행한다.
