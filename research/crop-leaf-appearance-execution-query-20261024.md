# 자동 출현 작업의 현재 조회와 독립 재생 — 2026-10-24

상태: [실행 계약 E3](../contracts/crop-leaf-appearance-execution-v1.md)의 **합성 소프트웨어 수용**.
[E2 실제 worker](crop-leaf-appearance-execution-worker-20261024.md) 다음의 status/manifest/frame/replay 조회다.
기존 자동 consumer 등록·보호 API/runtime·같은 job3D는 후속이다.
[사용자 저장 3D](http://localhost:5176/leaf-appearance-replay.html)는 유지하며 새 조회는 사용자 runtime에 미배포다.

## 구현

LeafAppearanceExecutionQuery는 한 SQL statement의 같은 snapshot으로 원 job/publication/events/outcomes/invocations를 읽는다.
원 job/input·현재 attempt/시작/성공·worker 판본·opaque 참조와 CLI 비위조 증거를 대사한다.
원 signed authority의 _load를 전후 실행하고 그 사이 원 manifest/frame reader·source 결속과 현재 권리/검토를 검증한다.
job input의 intent HMAC/현재 resolver 원 bytes도 조회 양 끝에서 확인한다.
미완료 status는 현재 입력을 전후 대사하며 원 DB 묶음이 바뀌면 Pending으로 재조회한다.

새 manifest의 sample_count로 재생하며 선택 frame과 마지막 frame의 원 기간은 signed._frame_scope로 확인한다.
status/manifest도 마지막 시점이 원 기간 끝에 해당하는지 검사한다.
원 result/root/calculated_at·parent/UTC/기관 ID와12frame/47면적을 재계산 없이 유지한다.
등록 읽기 scope는 요청 내부에 한정하며 요청 간 권리 cache를 만들지 않는다.
응답은 닫힌 leaf-appearance-execution-read-v1·합성 FLAGS/2MiB 이내이며 frame만0이상 정수 index를 받는다.
현재성 위반에는 부분 응답이나 이전 결과 fallback 없이 보류한다.

## 통과한 검증

- **신규 순수25:** 원 게시/attempt·시작/종료·parent/result 결속과 fake CLI/관문 표기 변조,
  새 sample_count·네 조회 모드·선택 frame/마지막 시점의 원 기간을 확인했다.
  최초 모듈 부재의 예상 RED16오류를 보존했고 기간 경계9개를 추가한 뒤25개가 통과했다.
- **실제 SCRAM 정상1:** queued부터 완료 네 조회 모드와 첫/마지막 frame,
  원12frame/47면적·UTC/기관 ID의 전체 bytes/최초 시각과 원 parent18/signed47파일을 대사했다.
  **52개 생장/CLI 진입·8개 작업/객체 쓰기 진입·지속 SQL 쓰기는0**이었다.
- **현재 변경1:** foreign tenant·양쪽 권리/검토·세 원 입력 bytes와 읽기 scope 변경을 거부했다.
  복원 뒤 같은 원 결과를 반환했고 조회의 계산·쓰기0과25표 원 행 SHA를 보존했다.
- **늦은 변경1:** 마지막 frame을 읽은 뒤 잎 권리/부모 권리/잎 검토/부모 검토/resolver source의
  **다섯 경우** 모두 전체 replay가 보류됐다. 조회의 계산·쓰기0과25표 원 행 SHA를 보존했다.
- **독립 fresh1:** 실제 SCRAM·네 조회 모드/첫·마지막 frame과 원12frame,
  같은 job/result/root/calculated_at·parent 및 양쪽 검토 철회를 확인했다.
  **32개 금지 모듈의 import 시도0·13개 CLI/작업/객체/파일쓰기 진입0·지속 SQL 쓰기0**이었다.
  seed/pytest/HTTP app import0·FD4→4·원 DB/parent18/signed47파일을 보존했다.
- **동시 변경2:** 독립 연결의 실제 cancel 도중 조회는 Pending, 다음 조회는 현재 canceled/결과 없음이었다.
  첫 job statement 뒤 실제 worker가 완료된 경우에도 같은 snapshot의 원 queued와 새 publication을 섞지 않고 Pending이었다.
  이 두 시험의 명시 actor 쓰기는 조회의 쓰기0 계측과 구분한다.
- **게시 불변성1:** 별도 fixture 소유자의 실제 UPDATE로 관문 표기를 바꾸려던 시도가 DB 불변 trigger에 거부됐다.
  원 결과와 not_assessed를 다시 조회했고25표 원 행 SHA·계산/쓰기0을 보존했다.

최종 고유 수용은 **순수244(신규25/관련219)+실제 SCRAM7(독립 fresh 포함)=251개**다.
다섯 늦은 변경이나 fresh의 네 모드를 별도 검사 수로 중복 합산하지 않는다.
예상 RED 외의 실패/생산 코드 수정은 없었다. 모든 native는 사용자 DB와 분리된 scratch PostgreSQL에서 순차 실행했고,
소유 schema/role0·passfile/짧은 임시 디렉터리 제거와 잔여 프로세스0을 확인했다.
전체 backend/새 hosted CI·HTTP/TLS/브라우저는 이번에 실행하지 않았다.

source는 `147ec8da4a37a68bd6ed9df9e28188b96d5b9bd5`다.
native gpt-6.1-sol/xhigh의 실제 turn_context 시각/원 LF SHA·재귀 CLI0,
최종4소스 지문·원 로그/종료와 각 시험 증거는 [기계 기록](artifacts/crop-leaf-appearance-execution-query-20261024.json)에 보존했다.
기존 수치 모델/원 입력·서명·DB 스키마/역할·사용자 웹/키/서비스는 변경하지 않았다.

## 자원·관측과 다음 단계

정상 native251.359초였다. 내부 단일 조회는11.37–11.85초, replay 응답은69,478bytes였다.
이는 단독 내부 관측이며 HTTP30초/U1·계산 중 동시 조회/동일 재접수나 공통 호스트 용량 수용이 아니다.
8개 검증 단계의 최대 PID104,808,448/보호+소유 합537,145,344bytes였다.
.25초 설정·512MiB/PID·1GiB 합산/600초/4MiB 로그 안에서 보호3root·원2,504항목/현재 소스·잔여0·FD4→4를 보존했다.
Windows Chrome을 이 WSL 합산에 포함한 것으로 표시하지 않는다.

현재 deterministic_work.WORKERS는 새 appearance worker/outcome을 등록하지 않았다.
다음은 기존 자동 consumer에 정확 appearance input_version/worker/outcome을 명시 등록하고,
실제 discovery→1계산/원자 완료·같은 원12frame/47면적·다른 queued 모델 보존/완료 재선택0과
현재 권한·소유 정리를 검증하는 자식이다. 새 큐/서비스는 필요하지 않다.
이후 보호 API/owned runtime→같은 job3D·메뉴/reload 복원을 잇는다.

E3의 이전80–160분 예상은 위 실적으로 대체한다.
다음 consumer는 기존 등록/검사15–30분 + 실제 discovery/권한·회귀15–30분 + 기록5–15분 =
**35–75집중분**의 낮은 신뢰 작업량이다. 후속 API/runtime/UI와 자료 확보 시간은 포함하지 않는다.
실제 품종/국내 독립 작기0, 관리·생산/자원/Decimal 경제·거시/수급·자율 비교,
R2/첫 cold 경고·실제 runtime CLI G1/G0–G4와 전체 제품 날짜 미정·goal 미완료를 유지한다.
