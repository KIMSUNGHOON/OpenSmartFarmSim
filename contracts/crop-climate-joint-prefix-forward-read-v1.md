# 계산 전진 중 선택한 불변 판본 읽기 — v1

상태: **P6a2b1 구현 전 계약**. 2026-10-11.
근거는 [v3의 요청별 실제 분류](../research/crop-climate-joint-prefix-progress-diagnosis-20261011.md)다.
기존 [prefix 계약](crop-climate-joint-prefix-view-v1.md)과 [임대 갱신 계약](crop-climate-joint-prefix-progress-guard-v1.md)을 확장한다.
이 문서는 동시 전진의 비교 근거만 정하며 공개 DTO·writer/수치·입력/결과 형식은 변경하지 않는다.

## 구현 범위

core는 `crop_climate_joint_prefix.py`와 `api_crop_climate_joint_prefix_routes.py`, 검증은 대응 test2파일이다.
현재 v3의 exact HEAD/latest 비교는 선택한 판본 자체가 유효해도 정상 append가 발생하면 조회를 폐기한다.
선택한 DB 수용 판본의 불변성과 지금의 작업/자료 권리를 각각 검사해 같은 원 snapshot을 반환한다.
reader 내부 판본/source hash를 갱신하고 기존 공개 projection/schema/client 경계를 유지한다.
새 cache/queue/schema/서비스나 worker 지연은 필요하지 않다.

## 전진을 허용하는 증거

아래를 모두 증명한 **선택 사건이 있는 active 조회**만 대상으로 한다.

1. job 전후 비교는 v3의 같은 state/attempt/token/input·모든 나머지 필드와 UTC 임대 갱신 조건을 그대로 사용한다.
   links/publications/outcomes/terminal 변화도 허용하지 않는다. 새 DB 컬럼을 무시하지 않는다.
2. 선택한 DB 사건의 전체 row(event ID/attempt/reason/최초 시각)가 현재 거래에서도 정확히 같다.
   이전에 관측한 latest 사건도 그 선택자로 다시 읽어 전체 row를 대사한다. 삭제/교체/변조는 거부한다.
3. 새 latest는 실제 `_history`의 연속 publication/custody sequence·같은 input/attempt 검사를 통과해야 한다.
   이전 latest보다 뒤로 가지 않고, 같은 sequence이면 전체 row가 같아야 한다.
   전진이면 실제 선택한 판본과 같은 intent/binding/원 입력 및 검증된 signed ancestry에 속해야 한다.
4. 조회 중 관측한 private HEAD의 실제 검증된 proof/hash/sequence도 보존한다.
   다음 현재 HEAD는 그 HEAD·선택 사건·전후 latest의 검증된 후손이어야 한다.
   단지 commit 수가 증가하거나 선택한 옛 판본을 포함한다는 이유만으로 다른 fork 또는 private rollback을 허용하지 않는다.
5. `_Session`의 실제 HMAC/서명 이력·디렉터리/intent·현재 입력/자료 권리·계정 검사를 전후 유지한다.
   immutable page는 선택한 signed HEAD에서 읽고 모든 원 값/UTC/수지를 기존 reader로 검사한다.

전진 판정에 필요한 server witness는 선택 사건·관측한 HEAD proof·검증된 bundle과 원 payload hash에 결속한다.
public payload나 생성된 설명에서 내부 witness를 복원하지 않는다. 실제 token/row/key는 공개하지 않는다.
후검사에서 새 latest의 수치/시각을 원 snapshot에 덧붙이지 않는다. job/observed_at도 실제 확인한 probe를 사용한다.

## 변경하지 않는 전환

선택 사건이 없는 none/closed 응답은 기존 비교를 유지한다. 첫 수용 사건이 생기면 다시 조회한다.
queued→simulating·취소·attempt/token/input·종료/결과 연결 변화는 기존 Pending/closed 전환을 따른다.
page의 선택자 충돌/범위 오류와 현재 권리 거부를 재시도 가능한 계산 전진으로 숨기지 않는다.
현재 E6 진행 DTO·writer 잠금/임대·수치 결과를 바꾸지 않는다.

## 수용 기준

- v3에서 실제 **독립 프로세스**의 private advance와 advance+DB confirm이 조회 중/직렬화 후 발생하는 red를 보존한다.
  새 reader는 같은 선택 사건의 page canonical bytes/hash·binary64/UTC·최초 수용 시각을 그대로 반환해야 한다.
- private HEAD만 전진, DB latest 전진, 같은 sequence, 두 경로의 반복 갱신을 구분한다.
  forward 검증이 실제 source/권리·HMAC/현재 계보를 호출했음을 확인한다.
- signed rollback(특히 처음 본 private HEAD보다 뒤지만 selected보다 앞인 경우), fork/변조,
  선택/종전 latest 사건의 삭제·reason/최초 시각 교체, 역행/비공개 필드/취소/종료·늦은 철회를 거부한다.
- 기존 원 페이지/empty/sparse/older accepted/fresh·권리/취소·schema/기본 비활성 계약을 집중 회귀한다.
  원 모델/입력/custody/checkpoint/result pin과 조회 계산/게시/쓰기0을 보존한다.
- 실제 unpaused 정상/hold/cancel의 공개 summary→같은 selector events/samples를 검증한다.
  정상에서는 **계산 중 page200과 원 값**을 확인하고 원 terminal 응답을 대사한다.
  내부 DB 선택자 직접 발견 진단을 공개 discovery 성공으로 세지 않는다.
- WSL 상한·두 사용자 서비스/원본·FD/소유 정리·실제 원 handle 종료를 확인한다.
  이 자식의 수용은 P6 실제 WebGL/사용자 활성화 수용을 대신하지 않는다.

작업 순서/일정은 [계획](../tasks/plan.md#joint-prefix-view-20261010)과 [할 일](../tasks/todo.md#joint-prefix-view-20261010)을 따른다.
제품 주장과 현장 자료의 조건은 [PROJECT_SPEC](../docs/PROJECT_SPEC.md)에 유지한다.
