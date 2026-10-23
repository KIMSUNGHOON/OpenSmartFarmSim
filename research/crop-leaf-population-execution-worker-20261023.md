# 잎 계산 worker와 원자적 완료 게시 — 2026-10-23

상태: [실행 계약 E2](../contracts/crop-leaf-population-execution-v1.md)의 **합성 소프트웨어 수용**.
[E1 접수](crop-leaf-population-execution-admission-20261023.md) 다음이며 E3 현재 조회와
기존 자동 consumer·보호 HTTP/runtime·제품3D 연결은 후속이다.

## 구현

`LeafPopulationExecutionWorker(service,tenant_id=...,lease_seconds=600).run_once(job_id)`는
해당 tenant/명시 leaf input_version의 simulation만 claim한다.
현재 원 입력/parent·binding과 live lease를 확인하고 실제 signed leaf producer를 job 잠금 밖에서 실행한다.
시작 이벤트의 planned_outputs는 현재 binding에 결속된 **원 부모 manifest**에서 읽는다.
잎 program에 없는 출력 시점이나 임의 진행률을 만들지 않는다.

원 signed 결과/binding과 현재 입력·권리/lease/cancel을 게시 전후에 검사하고,
같은 DB 거래에서 publication·결과/완료 이벤트·attempt outcome·terminal을 저장한다.
generic artifact는 원 job/input에 결속된 새 leaf 판본의 **371bytes opaque 참조**다.
완료 재실행은 계산하지 않고, 취소/만료/늦은 철회 때 private signed/opaque 파일이 남아도
결과 참조를 게시하지 않는다. 새 결과 표·역할/큐와 가짜 CLI invocation은 추가하지 않는다.
이 v1은 계산 중 프레임/수치 checkpoint 재개를 제공하지 않는다.

## 통과한 검사

- **참조9:** job/input/result·scope/판본·닫힌 필드·정규 바이트와4KiB 상한,
  원 artifact SHA/attempt·gate 표기를 확인했다. 먼저 새 모듈 부재 RED를 보존했다.
- **실제 SCRAM 정상1:** 별도 farm/완료 parent 아래 실제 leaf 수치 producer1회,
  원 root `9b156ea33c87af66681a05df3a6630ae85c8f346a57d3d81b2c3f5c4525fc077`과
  **원12frame/52면적·UTC/ID**의 전체 frame bytes를 대사했다.
  parent job/result/최초 계산 시각과 계획12출력, publication/ref/code와 실제 완료를 확인했다.
  같은 접수와 완료 worker 재실행은 추가 계산0이며 다른 queued 모델을 보존했다.
  새 두 job과 연관 행을 제외한 **25표 모든 원 행 SHA**, 부모18파일을 보존했고 leaf44파일을 확인했다.
  실제 leaf attempt의 CLI invocation은0이다.
- **현재 권리 보류1:** 접수 뒤 계산 권리 철회 시 hold/결과 참조·게시0,
  **49개 생장/producer/CLI 진입0**을 확인했다.
- **늦은 변경5:** 실제 private signed 계산 뒤 cancel/lease_expired,
  publication INSERT 뒤 leaf 권리/parent 권리/leaf 검토 철회를 적용했다.
  cancel은 canceled, 세 철회는 hold, 만료된 lease는 unclosed로 남으며
  **publication/성공 이벤트·generic 결과 참조 모두0**이었다. 부모18파일을 보존했다.
  unclosed는 완료나 자동 재개 수용으로 표시하지 않는다.

최종 수용은9+7=**16개 고유 검사**다. 각 native 실행의 소유 schema/role0·짧은 임시 디렉터리 제거와
guard FD4→4·소유 child0을 확인했다. 시험은 사용자 DB와 분리된 scratch PostgreSQL을 사용했다.
E1 생산/시험 source와 이전 계산 모델을 변경하지 않았다.

첫 정상 native는 기존 lease_renewed 이벤트1개를 시험 기대값에서 빠뜨려 실패했다.
이벤트 기대6→7과 실제 갱신1건 검사를 고쳤고 **worker/참조 생산 코드는 바꾸지 않고** 전체 정상 경로를 다시 통과했다.
첫 실패/로그·정리와 최종 통과를 [기계 증거](artifacts/crop-leaf-population-execution-worker-20261023.json)에 보존했다.
실패 실행을 통과 수에 합산하지 않는다. 전체 backend 회귀/hosted CI·E3 fresh/HTTP/브라우저는 이번 범위에 없다.

## 자원과 다음 단계

정상 native248.896초, 실제 worker 단일 관측134.798초였다.
성공 단계의 최대 PID108,838,912bytes/보호+소유 합386,654,208bytes로
.25초 표본·PID512MiB/합1GiB·단계600초 안이었다.
원2root/2,148항목·기존 저장/배포 파일을 보존했고 병렬 DB 검사는 실행하지 않았다.
이는 Windows Chrome이나 공통 WSL 용량/처리량 수용이 아니다.
정확 native gpt-6.1-sol/xhigh와 재귀 CLI0은 기계 증거에 기록했다.

다음 **E3**는 같은 job/input/publication/outcome/events·원 signed 결과를 대사하는
status/manifest/frame/replay 조회다. 원 result/root/calculated_at·parent/UTC/12frame을 유지하고,
현재/늦은 권리·원본/게시 변경을 거부하며 별도 fresh의 생장/producer/worker import·계산/CLI/쓰기0을 요구한다.
현재 signed replay24.58초/E1 입력 read12.70초가 관측되었으므로 중첩 검증 비용과 HTTP30초 예산도 실측한다.
원 현재성 검사를 유지하면서 검증 경계를 설계하며, 처리 시간 미확인을 U1 통과로 표시하지 않는다.

현재 기존 `deterministic_work.WORKERS`는 새 leaf worker/outcome을 등록하지 않았다.
따라서 이 수용은 **명시 run_once worker**이며 무인 consumer/runtime 완료가 아니다.
E3 뒤 기존 foreground consumer에 정확 판본/worker/outcome을 등록하고 실제 discovery→1계산·
다른 queued 작업/완료 재선택0을 검증하는 의존성을 계획에 명시했다. 새 큐나 서비스는 필요하지 않다.

E2의 이전1.75–3.5h 계획은 이번 수용으로 대체한다.
E3 계약/구현45–90분 + 실제 DB/독립 조회·변경60–120분 + 기록15–30분 =
**2–4집중시간**의 낮은 신뢰 작업량이다. HTTP 예산과 현재성 경계의 실제 검사 뒤 갱신한다.
제품 전체 날짜가 아니며, 이후 consumer·보호 API/runtime→같은 job3D/메뉴·재접속 복원을 잇는다.

[사용자 화면](http://localhost:5176/leaf-population-replay.html)은 기존 저장 합성3→6잎 재생이다.
이번 worker는 사용자 runtime에 미배포이고 새 leaf 자동 실행으로 표시하지 않는다.
실제 Axiany 계수/초기관측·독립 현장 작기0, 생산·자원/경제·자율 선정·최종 사실감/첫 셰이더 경고,
G0–G4 및 전체 제품 완료 날짜 미정을 유지한다.
