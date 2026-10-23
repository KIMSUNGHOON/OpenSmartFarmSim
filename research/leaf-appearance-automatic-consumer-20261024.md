# 자동 출현의 기존 consumer 연결 — 2026-10-24

상태: [E1–E3 실행 계약](../contracts/crop-leaf-appearance-execution-v1.md) 이후의 **합성 소프트웨어 수용**.
[현재 조회/독립 재생](crop-leaf-appearance-execution-query-20261024.md) 뒤 기존 discovery와 전경 consumer를 연결했다.
보호 API/owned runtime·같은 job3D는 후속이며 새 연결은 사용자 runtime에 미배포다.
[사용자 저장 3D](http://localhost:5176/leaf-appearance-replay.html)는 그대로 유지한다.

## 구현과 검증

생산 코드 변경은 기존 두 모듈의3줄 등록이다. discovery에 leaf-appearance-execution-input-v1을 추가하고,
DeterministicWorkerLoop에 정확 LeafAppearanceExecutionWorker/LeafAppearanceExecutionOutcome을 등록했다.
비어 있거나 다른 모델/혼합 판본인 구성은 거부하며 기본 구성에서 실행하지 않는다.
기존 operator factory와 작업 표/임대를 사용하고 새 큐/서비스·수치 모델이나 의존성은 추가하지 않는다.

- **신규 순수12:** 구성 생성의 계산0·명시 판본, 빈/미래/다른/이전 잎/혼합 판본 거부,
  안전한 종료 메타데이터와 다른 계열/다른 job/미종결 outcome 거부를 확인했다.
- **기존 제어·관련136:** 기존 잎/형태/CO₂/일사/공동 계산의 등록과 공통 consumer/discovery를 확인했다.
  Python 모듈 entry의 실제 자식 프로세스 시험도 포함하므로 모두 순수 검사로 표시하지 않는다.
  not scram 선택에서 기존 실제 SCRAM18개는 제외했고 통과 수에 더하지 않았다.
- **실제 SCRAM1:** 현재 metadata/simulation_execute 철회를 각각 거부하고 원25표 행 SHA·생장/CLI0을 확인했다.
  복원 후 실제 discovery→수치 producer1회/원자 완료·안전한 종료 사건1개,
  같은 원12frame/47면적·parent/result/calculated_at/서명 결과를 E3 query로 대사했다.
  알 수 없는 판본과 기존 leaf-population 판본의 두 queued 작업은 그대로였다.
  완료 후50+37행을 훑어 **선택0·추가 계산0**을 확인했다.
  새 세 작업과 관련 행을 제외한 **25표 원 행 SHA**와 부모18파일을 보존했다.
  권한 거부 및 후속 조회/discovery의52개 생장/CLI 진입은0이었다.

먼저 미등록 상태의 예상 RED5실패/5통과를 보존했다.
이전 잎 판본/결과 계열의 두 반례를 더한 최종 신규12와 관련136·native1로 **149개 고유 검사**를 수용했다.
예상 RED 외의 실패나 생산 코드 수정은 없었다.
사용자 DB와 분리한 scratch PostgreSQL에서 실행했고 schema/role0·passfile/짧은 임시 디렉터리 제거,
잔여 프로세스0·FD4→4를 확인했다. 이전 E2/E3의8개 소스 지문도 그대로였다.
전체 backend/기존 consumer의 전체 SCRAM/hosted CI·HTTP/브라우저는 이번에 실행하지 않았다.

source는 `1de117c44a925d8e35620bbb2627f778d546ac2b`다.
현재 native gpt-6.1-sol/xhigh의 실제 turn_context 시각/원 LF SHA·재귀 CLI0,
최종 코드/시험과 이전 E2/E3 지문·원 로그/종료 증거는 [기계 기록](artifacts/leaf-appearance-automatic-consumer-20261024.json)에 보존했다.
기존 수치 모델/원 입력·서명·사용자 웹/DB/키/서비스는 변경하지 않았다.

## 자원과 다음 단계

정상 native193.166초, 실제 consumer 단일 관측127.820초였다.
4개 검증 단계의 최대 PID140,087,296/보호+소유 합504,709,120bytes였다.
.25초 설정·512MiB/PID·1GiB 합산/600초/4MiB 로그 안에서 보호3root·원2,504항목/현재 소스·잔여0·FD4→4를 보존했다.
이는 Windows Chrome을 포함한 호스트 용량/처리량이나 HTTP30초/U1 수용이 아니다.

다음은 보호 HTTP의 새6경로·닫힌 typed 요청/응답과 기존 인증/Scope/create_app 조립이다.
같은 jobs/provider/admission/query·farm/parent graph를 검사하고 기본 비활성503·기존 경로/스키마를 보존한다.
실제 SCRAM/TLS의 접수/동일 재시도·충돌·원 완료12frame/47면적·취소,
현재/늦은 인증·권리/입력 변경·조회 계산/쓰기0와 원 행/파일·WSL/소유 정리가 수용 기준이다.
원 body/키/tenant·임의 경로는 받지 않는다. 내부 단독 조회11.37–11.85초는 실제 HTTP30초 예산과 구분하며,
계산 중 동일 재접수/동시 U1 보류를 임의 timeout 증가로 해제하지 않는다.
이후 owned runtime→strict SDK/같은 job3D·메뉴/reload·실제 브라우저를 검증한다.

이전 consumer35–75분 예상은 위 실적으로 대체했다.
다음 API/Scope·typed/OpenAPI 조립40–80분 + 실제 DB/TLS·권한/전송 검사40–80분 + 기록10–20분 =
**90–180집중분**의 낮은 신뢰 작업량이다. 기존6경로의 계약·구현을 재사용하고 새 원 요청/결과 판본과 실제 지연을 확인한다.
후속 runtime/UI·외부 자료 확보 시간은 포함하지 않으며 전체 제품 날짜는 미정이다.
실제 품종/국내 독립 작기0, 관리·생산/자원/Decimal 경제·거시/수급·자율 비교,
R2/첫 cold 경고·실제 runtime CLI G1/G0–G4와 전체 goal 미완료를 유지한다.
