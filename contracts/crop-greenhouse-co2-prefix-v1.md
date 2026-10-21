# CO₂·일사 계산의 확정 구간 원 조회 — v1

Status: accepted raw-prefix software31 (controls7 / actual SCRAM23 / independent process1).
[Evidence](../research/crop-greenhouse-co2-prefix-20261021.md). Public projection and user activation remain unaccepted.
2026-10-21. native Codex CLI `gpt-6.1-sol / xhigh`의 인터페이스 검토를
[진행 조회 전체 증거](../research/artifacts/crop-greenhouse-co2-execution-query-20261021.json)에 기록했다.
선행은 [현재 진행 조회](crop-greenhouse-co2-execution-query-v1.md),
[worker](crop-greenhouse-co2-execution-core-v1.md), [서명 custody](crop-greenhouse-co2-server-custody-v1.md),
[불변 페이지](crop-greenhouse-co2-storage-v1.md) 기능 수용이다.
[기존 Solar prefix](crop-greenhouse-solar-prefix-v1.md)의 선택/현재성·후검사 경계를 재사용한다.

## 원 조회 경계

별도 `Co2ExecutionPrefixQuery`의 내부 응답은 `joint-co2-solar-prefix-read-v1`,
범위는 `synthetic_joint_co2_solar_confirmed_prefix_only`다. 정확한 CO₂ query/jobs/admission/checkpoint/
custody/result와 현재 code·입력/농장/권리를 요구한다. 새 schema/역할/작업 큐는 추가하지 않는다.
읽기는 create/execute/write 권한, 수치 계산/복원·확인/결과 등록을 요구하거나 실행하지 않는다.

선택자는 DB가 확인한 publication_sequence/head_sha256/proof_sha256의 닫힌 집합이다.
summary는 선택자가 없을 때 최신 확인 사건, 명시 선택자가 있으면 그 사건을 사용한다.
samples/events는 명시 선택자에 결속한다. 최초 DB 확정 UTC/시도와 원 signed HEAD·provenance,
literal 승인 False·not_assessed, 원109상태/44연속·6사건 장부/17수지·관리 전후 진단·UTC를 보존한다.
64 sample/8 event·2MiB 페이지와 기존 내부 envelope 한도를 유지한다.

서명했어도 DB가 아직 확인하지 않은 HEAD는 선택하지 않는다. ready에는 저장 sample이나 계산 시각을
발명하지 않으며 none/closed에는 수치/미래 프레임이 없다. summary/page는 원 offset/total/끝 빈 배열과
선택한 불변 판본을 따른다. 원 quantity를 Solar의108상태/41장부/15수지로 해석하지 않는다.

현재 signed ancestry로 선택 사건·이전 최신 확인 사건·관측 HEAD·현재 최신 확인 사건을 대사한 경우에만
정상 append/heartbeat 중에도 같은 이전 선택자의 원 페이지를 반환한다. 취소/종료·시도/token/input
변경은 재조회이며 rollback/fork/삭제·변조·현재 권리 철회는 차단한다.

서버 내부 owner-bound witness를 유지하고 외부 payload로 재구성하지 않는다. 직렬화 뒤 후검사에서도
선택한 signed snapshot/page를 다시 읽어 selection/binding/manifest/time/summary/page를 대사한다.
이 내부 응답 자체는 원 입력/권리/경로를 공개 API에 표시할 권한이 아니다.

## 수용 순서

1. exact authority·선택자/bounds·UTC/heartbeat 비교와 불변 witness의 순수 제어.
2. 실제 SCRAM의 missing/ready/running/normal/hold/cancel·원 selection/값/UTC/최초 시각·sparse/dense64
   페이지/끝/오류와 private 미확정 HEAD를 검증한다. 조회·복원/확인/SQL쓰기0과 원 결과를 확인한다.
3. 현재/늦은 입력·농장/권리, 이력/서명/페이지/provenance/승인·job/선택 변경과 직렬화 뒤 변조를 검증한다.
   원 불변 행의 변경 거부와 반환값 fault injection, 시험 actor의 별도 변경은 구분한다.
4. 같은 DB/키/파일의 별도 fresh 원 byte/UTC와 독립 writer의 append/heartbeat/private→확인 전진에서도
   이전 선택자가 유지되는지 검증한다. 원 자료/서비스·공통 한도/소유 정리는 실행 계약을 따른다.

전체 원 조회 수용 전 부모를 완료하지 않는다. 이후 닫힌 공개 투영/직렬화 후검사→보호 실행 HTTP/runtime→
typed web/같은 UTC3D→WSL/사용자 적용을 각각 수용한다. 전체 작기/자원/경제·실제 CLI 종단 간·독립 농장
자료/G0–G4/실제 품종 예측·추천·전체 완료일은 별도이며 이번 계획으로 해제하지 않는다.

## 원 범위를 보존하는 검증 배치

원 Solar 고유23개를 모두 CO₂ 원 authority/프로그램에 결속하고, 조회 뒤 선택 page 변조1개와
순수 제어7개를 추가한다. 31개 전체의 수용 전 부모를 완료하지 않는다. 원600초·512MiB/PID·합1GiB와
64/8개·2MiB 페이지를 유지하며 기존 실행2128.864초 증거에 따라 서로 겹치지 않게 나눈다.

- `co2-prefix-core`: 제어7 + 실제 SCRAM6(없는/미시작·running/sparse·ready·dense64+1·normal/hold).
- `co2-prefix-fences`: 실제 SCRAM10(원 rollback/fork·audit·private/confirmed/retry·권리/농장·취소·bounds/lock·tamper·late page).
- `co2-prefix-concurrent`: 실제 SCRAM7(미리 계산한 원 HEAD 공개2·heartbeat/cancel2·witness1·반환값 fault2) + 독립 producer/reader1.

밀집 페이지는 기존 CO₂ `weather-multiple`의 계수/사건/forcing을 유지하고64걸음·매 걸음 출력만
명시한128초 소프트웨어 변형이다. 순수 사전 검사에서65samples/3events·completed를 확인했으며
원32초의 독립 물리 참조를128초 검증으로 확대하지 않는다. 동시 actor는 원 signed descendant 공개나
메타데이터 SQL을 수행하며, unpaused 수치 계산 worker의 동시 처리 증거로 세지 않는다.
