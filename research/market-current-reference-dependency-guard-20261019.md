# 기본 조회 의존성 guard 구현 — 2026-10-19 KST

상태: **독립 guard와 검토한 default DTO 재구성의 조건부 동등성을 고유37검사로 로컬 수용**.
[구현](../backend/app/market_reference_dependencies.py) ·
[검사](../backend/tests/test_market_reference_dependencies.py) ·
[기계 증거](artifacts/market-current-reference-dependency-guard-20261019.json) ·
[선행 대조/반례12](market-current-reference-receipt-equivalence-20261019.md) ·
[v4 계약](../contracts/market-current-reference-receipt-agreement-v4.md).

제품 verifier의 getter 생략 경로는 아직 없다. 기존 v2/primitive34/HTTP58/primitive48의
코드·시험 pin을 보존했다. 이번 변경은 새 guard 모듈·전용 검사·문서/진행 기록이다.
현재 native Codex CLI `gpt-6.1-sol/xhigh`의 실제 문맥 시각/해시·코드/출력 해시를 기록했다.
재귀 CLI나 하위 에이전트를 사용하지 않았다.

후속 [보호 연결 비용 평가](market-current-reference-agreement-cost-evaluation-20261019.md)는
원 수치·UTC/감사183을 보존했으나 두 실제 구간에서 약18.8%/17.4% 느려 후보를 미채택했다.
이 guard37의 독립 수용은 유지하며 제품 통합은 보류한다. 현재 다음 단계는 해당 기록과
[구현 순서](../tasks/plan.md)의 연결 수명 후보 평가다. 아래 다음 단계 문구는 비용 측정 전의 계획이다.

## 구현

`scope(owner, witness)`는 최초 full 등록 조회가 끝난 같은 `RegistrationRead` 수명에 진입한다.
지원하는 기본 프로필에는 private guard를 주고, 초기 미지원 프로필에는 `None`을 주어 기존 v2를
실제로 실행할 수 있게 한다. 허용되는 현재 권한 결과를 반환하거나 저장하지 않는다.

- source/view/candidate의 기본 클래스·메서드·코드/기본값, 가져온 함수 참조와 검토한 app9파일을 고정한다.
- 36개 도달 가능한 모델의 core schema·field/config·native compiled validator/serializer와
  관련 canonical/JSON/copy 함수·사용 자료형의 복사 처리표를 구조적으로 대사한다.
  연구 helper의 `repr` 출력은 사용하지 않는다. 불명 객체·검토 범위 밖 callback·plugin은 초기 비적격이다.
- 저장소 `uv.lock`과 설치 Pydantic/core 판본을 비교한다. 이번 실제 환경은 Python3.12.3,
  Pydantic2.13.5/core2.46.5다. 지원 언어 계열은3.12이며 판본/파일·Decimal 설정 변경을 감지한다.
  잠금 파일이나 패키지를 변경하지 않았다.
- 스냅샷은200,000노드·text/bytes2MiB 한도다. 구조 비교 중 원 객체를 유지해 일시 객체 ID 재사용을 막는다.
  클래스/compiled 객체의 프로세스 내 identity는 내부 결속에 쓰며 공개 영수증/증명 토큰으로 직렬화하지 않는다.
- 같은 owner/등록/Task/thread/ContextVar token과 실제 binding을 확인한다.
  guard 검사 자체의 SQL은0이고, 현재 farm/tenant/scope 검증은 계속 호출한다.
- 도중 변경·중첩·복제·이른 닫힘·예외/취소는 현재 등록을 poison/hold한다.
  종료 시 상태·binding·owner/등록 참조·token을 해제한다. 닫힌 guard 재호출이 정상 등록을 다시 poison하지 않는다.

검토 범위는 이 default 코드·모델·자료형과 명시적인 동적 경계다.
임의 Python 확장·callback이나 모든 프로세스 메모리 변경에 대한 일반 증명을 제공하지 않는다.
초기 비적격 프로필을 지원하는 기존 경로는 유지된다.

## 최종 같은 source의 검증

| 실행 | 고유 검사 | 범위 | guard 초 |
| --- | ---: | --- | ---: |
|55597:0|14|정상 full 조회·정리/재진입·초기 미지원3종/기존 경로·잘못된 owner·역할 감사·실제 HTTP principal 만료·SQL0·잠금 판본2·취소·원문 지문 결합|149.018|
|85388:0|16|함수/registry/정책·validator/serializer·core schema/field/config·Decimal·코드/기본값/alias·패키지·JSON helper/copy 처리표 도중 변경|192.943|
|8048:0|7|중첩·복제 Context·thread/Task·복제 닫힘·이른 닫힘·예외|85.737|

합37개(실제 등록 경계35/잠금 상태2)이며 guard 합427.697초(약7.1분)다.
세 배치는 같은 app/시험 SHA를 사용했다. 초기 실패·이전 source의 성공 검사는 더하지 않았다.
5root·원본2,148항목·두 UI source/assets·512MiB/PID·합1GiB,
FD4→4와 소유 프로세스/PG/임시/passfile0을 보존했다.
수용 배치 합 RSS 최대1,011,138,560bytes·단일147,136,512bytes다.

기존 authority provider 구성과 실제 `current_principal/BearerRegistry` 구성을 확인했다.
HTTP 구성은 연결된 job store와 source/hold/context의 같은 제공자 결속을 유지했다.
실제 HTTP listener/자동 worker의 새 guard 배포 또는 전체 동시 실행을 수용한 것은 아니다.

역할을 실제 DB에서 바꾼 시험에서 guard는 SQL0 상태 검사만 하고,
원 full verifier의 현재 역할 감사가 거부했다. 역할 감사는 대체할 수 없다.
초기 plugin wrapper·메서드 wrapper·미지원 metadata에서는 `None`을 받은 뒤 원 verifier가 실제 성공했다.

## 원문 지문과 결합한 조건부 범위

실제 등록에서 source74/candidate34/pin2=110키를 원문 primitive와 함께 읽고,
원 full trace88개를2회 실행했다. 현재 등록 반환값은 같았고36개 모델 상태를 보호했다.
**모든 원 getter를 실행한 결합 검사**이며 반복 DTO 재구성은 아직 생략하지 않았다.

선행12의 일곱 source 유형·172반환 대조와 이번 guard/결합 증거를 근거로,
고정 원문·검토한 default 코드/모델/설정에서의 **DTO 재구성 조건부 동등성**을 수용한다.
전체 getter에는 현재 principal/expiry·권한·역할과 동적 자료 검증이 포함된다.
파생 candidate/scenario/pin의 manifest, held/context·farm/current·취소/임대는 실제 실행해야 한다.
무조건 동등성·원 getter 횟수/타이밍·모든 동시 interleaving 보존·성능 개선은 미수용이다.

## RED와 수정 기록

기계 증거에 실제 tool/terminal 해시와 초기 판본을 분리했다.

- 96447:1: 실제 등록 생성 후 모듈 부재를 확인한 최초 RED.
- 87227:1: 닫힌 guard가 owner/등록을 보유했다. 참조 해제와 닫힌 객체의 재호출 처리를 수정했다.
- 13351:1: 가져온 Python 함수 alias 변경을 놓쳤다. 참조 결속을 추가했다.
- 56583:1: JSON 내부 helper와 복사 처리표 변경을 놓쳤다. 관련 library 상태·파일을 포함했다.
- 76183:2/68204:1: 잠금 시험의 간접 fixture 누락을 수정한 뒤, 실제 잠금 판본 비교 부재를 재현·수정했다.
- 69015:1/14725:1: HTTP 시험의 공유 job provider 결속과 기존 만료 `PermissionError` 기대를 수정했다.
- 61650:0/14172:0: 이전 판본의1/10 성공을37에 더하지 않았다.

모든 초기 실행도 원본/보호 서비스와 상한·정리를 유지했다.
CPython3.12.3 [copy 구현](https://github.com/python/cpython/blob/v3.12.3/Lib/copy.py)과
[JSON encoder 구현](https://github.com/python/cpython/blob/v3.12.3/Lib/json/encoder.py)을 확인해
전이 함수/처리표 범위를 보완했다. 운영 라이브러리를 교체하거나 새 의존성을 추가하지 않았다.

## 다음 한 단계

다음은 같은 보호 수명의 full anchor/현재 참조 검증을 연결하는 작은 단계다.
최초 full trace 성공 전후의 원문 지문이 같을 때만 기대를 고정하고,
매 현재 경계의 fresh 지문·현재 권한/동적 getter·원 canonical digest를 대사한다.
기대는 정확한 guard/등록/trace에 결속한다. guard를 닫거나 바꾼 뒤 bare 등록 값으로 재사용할 수 없다.
초기 비적격은 원 v2, anchor 이후 변경은 poison/hold이며 부분 결과는 게시하지 않는다.
branch 선택에 쓰는 후보 존재/부재도 전후 새 지문으로 확인한다.

먼저 실제 두 계산 구간의 paired 비용과 원 값/UTC·일반 경로를 확인한다.
유용한 개선 근거 후 관련 worker/HTTP 회귀·원 계측 OFF64 정상으로 진행한다.
원 actor/입력/chunk1/조회·retry360/RSS와 G0–G4를 유지한다.
hold/취소→계산 중 WebGL→WSL 용량/사용자 적용은 그 뒤다.

전체 backend/browser·fresh exec/SIGKILL·새 native CI는 재실행하지 않았다.
실제 농장 Run0·자료 권리/독립 현장/미래/비교 검증·새 Solar/실제 생산/경제 추천과 전체 완료일은
미완료/미정이다. 전체 goal은 active다.

## 게시·최종 범위 검토

56780:0에서 최종37·새2파일 해시/문법·기존 primitive48/34/HTTP58와 선행12 source pin,
원 API/worker/header·로컬 링크2,388개를 대사했다.
제품 app의 새 guard 호출은0이며 원 getter를 모두 실행하는 범위를 확인했다.
두 UI의 개발 기록은 HTTP200·동일 원 JSON bytes/no-store, frozen HTML·환기2,173파일 보존이다.
게시 guard2.385초·5root·합 RSS892,502,016bytes·단일141,316,096bytes·FD4→4,
소유 프로세스/PG/임시/passfile0이었다. UI code/DOM/WebGL을 변경하지 않았다.
검토한 조건부 DTO 범위를 실제 getter 생략/전체 성능·생산/추천·G0–G4 수용으로 승격하지 않는다.
