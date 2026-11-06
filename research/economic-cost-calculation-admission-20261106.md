# 항목별 비용의 불변 계산 접수 — 2026-11-06

[서버 접수](../backend/app/economic_cost_calculation.py)와 [계약](../contracts/economic-cost-calculation-admission-v1.md)을 수용했다.
[기계 증거](artifacts/economic-cost-calculation-admission-20261106.json)는 원본 manifest와 실제 검사/보존 지문을 결속한다.
**접수 라이브러리 수용이다. 새 trace의 worker/결과 저장·조회·HTTP/runtime/자동 소비·SDK/UI는 아직 연결하지 않았다.**

## 구현과 실제 검증

원 실제 EconomicBatchAuthority/source8/schema4와 EconomicBatchCalculationService의 읽기 전용 참조 준비를 재사용한다.
요청은 scenario ID/revision/SHA와 idempotency key뿐이다. 서버가 tenant/저장소·원 source job UUID/근거 SHA와
고정 trace version/코드·성분 지문을 정한다. 원 참조 입력 전체를 base_input으로 보존하고
새 economic-cost-line-calculation-input-v1과 별도 intent namespace에 기록한다.
프로그램은 읽기 준비/접수/commit 전후에 확인하며 원 JobStore의 job/event와 commit_guard 트랜잭션을 재사용한다.
새 숫자 공식·DB schema/로그인/패키지·HTTP나 worker 분기는 추가하지 않았다. 기존 파일을 수정하지 않고 서버 모듈78줄을 추가했다.

- 신규23 + 기존276 = **고유299검사**를 같은 최종 서버 코드에서 통과했다.
  기존276은 원 batch 접수23·source20·trace/원 batch/경제233이다. 이전 core23은 더하지 않았다.
- 실제 소유 PostgreSQL16.15의 host SCRAM에서 순차/동시 재시도가 한 job/원 canonical bytes·최초 시각을 유지했다.
  같은 키의 다른 revision은 충돌하며 한글 원문과 원 source UUID를 보존했다.
- 읽기4scope와 실행 scope의 현재/commit 철회10사례, 다른 tenant/잘못된 SHA/누락 참조,
  늦은 service/context 교체·코드 지문/지원 version 변경을 거부했다. 새 job/event 행은 롤백했다.
- 준비 결과의 근거를 commit 시 바꾸는 주입과 실제 event 오류에서 롤백했다.
  참조 재대사 주입을 실제 농장 source 변경 시험으로 표시하지 않는다.
- 읽기 준비는 실행 권한 없이 가능하고 원 DB 개수는 불변이다. 반환 dict를 바꿔도 서버 프로그램 지문은 유지된다.
  금액 계산 진입점을 실제로 차단한 접수/재시도도 통과했다. SQL 쓰기는 jobs/job_events INSERT뿐이다.
  같은 키의 원 v10 작업은 별도 queued job이고 새 작업도 queued이며 게시 결과는 둘 다 없다.
- 먼저 새 module 부재의 실제 RED를 기록한 뒤 구현했다. 원 숫자 코드/기존 접수·worker/query/API/runtime/consumer는 변경하지 않았다.

## 자료·자원·보존 범위

native CLI0.157.1의 실제 gpt-6.1-sol/xhigh turn metadata와 판단·출력 파일을 기록했다.
재귀 Codex CLI나 새 리뷰 agent는 실행하지 않았고 부모 native 세션에서 correctness/readability/architecture/security/performance를 검토했다.
이는 자체 QA 자료의 소프트웨어 접수이며 농장 계수/요금·권리/관문 채택이 아니다.

기존 Python 환경과 별도16MiB buffer 소유 PG만 썼고 원 사용자 DSN/비밀번호를 읽지 않았다.
PID512MiB/합1GiB/phase600초 감독에서 원4,500항목/전체 repo source와 보호 외형5175를 보존했다.
최종299검사는172.49초(감독178.73초), 단일 PID 최대146,964,480B·보호/소유 프로세스 합302,149,632B였다.
각 terminal에서 FD4→4·소유 잔여0이며 실제 fixture PG는 정지·임시 디렉터리 제거를 마쳤다.
기존 비용 커널 manifest의 source750/출력2/private22/external20·11월6일 재확인 proof와 통합20의 현재/Git snapshot을 대사했다.
새 manifest는 그 부모 manifest를 SHA로 참조한다. 750개 항목을 복사하지 않으며 기존 지문/수용 이력을 덮어쓰거나 해제하지 않는다.
이번 새 통합2파일은 이전20과 함께 수용 commit의 Git snapshot으로 보존한다.

저장3D의 원 source687/출력4/private745/external46과 만료된5184의238파일·5181의233파일/원 소유 정책·종료를 확인했다.
이번 preview HTTP는0이고 과거 실제 HTTP 검증 지문은 보존했다. 미리보기를 재시작하거나 만료를 연장하지 않았다.
과거 raw 전체 재실행·전체 backend/frontend suite·새 UI/browser·DB 배포·새 trace worker/HTTP 검증은 실행하지 않았다.
독립 국내 raw0·G0–G4 미평가/R2 미승인·전체 goal active/incomplete를 유지한다.

## 다음 한 단계

`economic-cost-line-execution-worker`: 기존180줄 lease/CAS/원자 게시 경계를 공유하되 정확 새 input version만 선택한다.
원 v10/default 동작과 이전 worker의 수용 Git snapshot을 보존하고 숫자 모델/이전 산출물은 덮어쓰지 않는다.
실제 SCRAM에서 한 번의 trace 계산/전체2MiB 결과·입력/코드/성분 지문, 원자 게시/최초 이력,
현재/늦은 근거/권한/코드·취소/만료/재임대/rollback과 기존 worker 회귀를 수용한다.
기존24 worker 검사와180줄 공유 경계·새 입력 계약을 근거로1–2집중시간 초안이며 재작업/CI 대기는 별도다.
그다음 현재 무계산 조회→보호 HTTP/runtime/자동 소비→원 자원 창/독립 비용 기간 결속→strict SDK/같은 선택3D 비용 화면을 진행한다.
후속 query/게이트웨이/UI 공수는 worker 수용 뒤 실제 차이를 반영한다.
실제 품종/한 작기·설비/구매/청구·생산/경제/거시/수급·자율 비교와 외부 농장/권리·R2/배포의 완료일은 자료 일정이 없어 미정이다.
