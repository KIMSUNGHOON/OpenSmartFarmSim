# 기본 조회의 조건부 동등성·반례 조사 — 2026-10-19 KST

상태: **연구 대조·반례 고유12검사 수용. 운영 의존성 guard·전체 동등성·verifier 통합은 미구현/미수용**.
[연구 helper](market-reference-receipt-equivalence.py) ·
[실제 DB 검사](../backend/tests/test_market_reference_receipt_equivalence.py) ·
[기계 증거](artifacts/market-current-reference-receipt-equivalence-20261019.json) ·
[v4 계약](../contracts/market-current-reference-receipt-agreement-v4.md).

기존 [primitive48](market-current-reference-receipt-primitive-20261019.md)과 v2/primitive34/HTTP58의
코드·검사 pin은 그대로다. 새 연구 helper를 부르는 제품 경로는 없다.
현재 native Codex CLI `gpt-6.1-sol/xhigh` 문맥 시각/원 해시와 실제 산출물을 기록했다.
재귀 CLI·하위 에이전트·변경 없는 native64 반복은 없다.

## 코드에서 확인한 의존성

순수성의 후보 범위는 **고정된 원문에서 DTO를 재구성하는 부분**이다.
전체 getter는 현재 주체·scope·실제 DB 조회·현재 역할 감사에 의존한다.

| 경로 | 원문/설정 의존성 | 유지해야 하는 현재 검증 |
| --- | --- | --- |
| source7종 및 scenario/shock pin | source row의 kind/ID/revision/job/raw/hash/version/admission/authority, joined job stage/input/hash, `_KINDS`와 모델·canonical JSON 코드 | source/view/candidate의 현재 tenant·scope, 같은 owner/connection, 실제 역할 감사 |
| candidate input | 후보 raw/hash/identity, `_parse`/`_checked_input`, `OwnedEconomicRecord` validator/serializer | 현재 candidate 권한, 후보 존재 시 우선 선택, 부재일 때 source fallback |
| source scenario fallback | candidate pin 부재와 source 원문, `OwnedScenarioPin`/`JointShockPin` 재구성 | pin 존재 여부를 새로 확인; 파생 후보가 있으면 실제 후보 검증 수행 |
| 파생 candidate/scenario/pin | pin3원문·identity/해시와 manifest에 든 별도 candidate input 행 | `_checked_candidate`의 현재 manifest 검증을 실제 실행 |
| tenant/held/context | 현재 principal·Bearer clock, hold/context 권리·서명·현재 참조 | 현재 getter와 상위 farm/current 경계를 실제 실행 |

검토한 app 파일은 source/candidate/view, economic contracts/economics,
jobs/market/market scenario/provenance의9개다. 함수·코드/기본값, registry/정책,
도달 가능한 모델의 core schema/validator/serializer/field/config, canonical 함수,
Python·Pydantic 버전과 Decimal 설정을 대조했다.
자료 권리·인증·역할 또는 gate 결과를 이 목록에 캐시하지 않는다.

연구 helper의 `envelope()`는 프로세스 내부 identity/repr 비교를 사용한다.
**운영 guard나 이식 가능한 증명 토큰으로 사용할 수 없다.**
현재 코드의 조건을 확인하는 도구이며 임의 callback/closure/plugin에 대한 완전한 의존성 탐지기는 아니다.
실제 기본 HTTP/자동 작업자 구성에서 지원 조건을 강제하는 코드는 후속 구현이다.

## 최종 실제 DB 대조 — 48629:0

`12 passed in 137.09s`, guard144.319초다. 앞선52409:0의7개는 더하지 않았다.
같은 실제 SCRAM/read-only Read Committed/전후 역할 감사와 primitive를 사용했다.
전체 getter를 계속 실행했고, 반복 재구성을 생략한 제품 경로는 없다.

| 관측 | 실제 결과 |
| --- | --- |
| 원 registration trace |88논리 참조를 원 verifier로2회 실행·동일 digest/중복 순서 |
| 닫힌 키/계획 | source74·candidate34·pin2=110키, 순수 후보76/dynamic12인덱스 |
| source7종 |86합성 record에서172개 원 반환값 대조·두 source pin 경로·같은 지문 |
| 함수/registry/validator/serializer/정책 교체 | 원문 지문은 같아도 원 verifier가 거부; 연구 envelope는 변경 감지 |
| Decimal 설정 변경 | 이번 원 반환값은 같았고 envelope는 변경 감지; 기존 registration의 설정 경계 유지 필요 |
| candidate 우선 경로 | 사용하지 않는 source를 변경해도 같은 candidate 반환·source getter0·source key0 |
| 미지원 조회 | closed planner가 거부하여 기존 경로를 유지할 조건을 확인 |

두 번의 동일 반환값과 합성 표본은 모든 농장에 대한 무조건 동등성 증명이 아니다.
원문·코드·모델/정규화·설정이 고정된 범위에서의 대조이며, 현재 권한 검증은 별도로 실행했다.
source metadata처럼 DTO가 직접 반환하지 않는 필드까지 지문에 포함하는 경우의 보수적 hold도
후속 프로토콜에 명시해야 한다. 기존 getter 횟수/타이밍/모든 동시 interleaving의 보존을 주장하지 않는다.

## 반드시 유지할 반례

### manifest 입력

합성 pin의 manifest에 명시 trace 밖의 candidate input을 연결하고 원 후보 검증이 성공함을 확인했다.
그 별도 입력의 raw/hash만 변경하면, 명시 trace의 source/candidate/pin 지문과 연구 envelope는
전부 그대로여도 실제 `get_market_candidate`가 거부했다.
실험 중 pin/명시 입력의 지문 대사는 통과했다. 따라서 해당 지문들만으로 후보 검증을 대체할 수 없다.
**파생 candidate/scenario/pin의 현재 manifest 검증을 유지한다.**

### 인증 만료

실제 `BearerRegistry/current_principal`과 제어된 clock으로 같은 함수·DB 상태에서 만료를 만들었다.
연구 envelope는 같았지만 현재 principal은 사라지고 원 verifier/outer scope는 거부했다.
인증 결과나 만료 전 권한을 재사용할 수 없다. 원문 지문은 권한 영수증이 아니다.

## 수용 범위와 다음 구현

`market-current-reference-receipt-equivalence-v4` 전체는 아직 체크하지 않는다.
이번 연구 산출물은 지원 조건과 거부해야 할 반례를 고정한다.
다음은 **실제 default HTTP/자동 작업자 경로의 의존성 guard**다.

1. 지원하는 store/view/source 함수·클래스, 모델/compiled validator/serializer·전이 코드와
   정책/정규화/Decimal·고정 라이브러리 판본을 현재 실행 수명에 결속한다.
2. 초기 미지원 callback/closure/plugin/모델/스키마는 기존 v2로 처리한다.
   anchor 이후 변경은 현재 작업을 poison/hold하고 중간 결과를 내보내지 않는다.
3. 실제 worker/API 구성에도 적용되는 것을 확인한다. fixture 전용 특례를 제품 조건으로 도입하지 않는다.
   principal/권한·역할·farm/current·취소/임대와 파생 manifest 경계는 실제로 실행한다.
4. 이 guard와 조건부 동등성을 수용한 뒤에만 full anchor/현재 지문을 연결한다.
   원 수치/UTC·worker/HTTP 회귀·paired 실제 비용을 통과한 경우 채택한다.

그 다음 원 계측 OFF64 정상→hold/취소→계산 중 WebGL→WSL 용량/사용자 적용이 남았다.
이번 연구의 속도 개선·현재 native64 정상·새 Solar/계산 중3D·실제 농장/관문은 미수용이다.
실제 농장 Run0·자료 권리/독립 현장/미래/비교 검증과 전체 완료 날짜는 미완료/미정이다.
전체 goal은 active다.

## 자원·근거

5root·원본2,148항목·두 UI source/assets·512MiB/PID·합1GiB를 보존했다.
실제 합 RSS1,027,694,592bytes·단일141,316,096bytes·FD4→4,
소유 프로세스/PG/임시/passfile0을 확인했다. 전체 backend/browser·fresh exec/SIGKILL은 재실행하지 않았다.

Pydantic 공식 [BaseModel 속성/검증·직렬화](https://docs.pydantic.dev/latest/api/base_model/)와
Python3.12 [Decimal context](https://docs.python.org/3.12/library/decimal.html)를 확인했다.
검증기/직렬화기·context가 별도 상태라는 API 근거다. 운영 동등성을 해당 문서가 보증하는 것은 아니다.
실제 의존성 판본은 저장소 잠금/설치 상태로 확인해야 하며 최신 문서로 패키지 잠금을 변경하지 않았다.
DB 원문을 자료로 채택하거나 농업/경제 계수·가격·예측을 추가하지 않았다.

## 게시·최종 검토

16497:0에서 연구 helper/시험2파일의 해시·문법과 검토한9개 파일·기존 primitive48/34/HTTP58 pin을
대사했다. 문서 로컬 링크2,375개·원 API/worker/header와 전체 동등성 미체크 상태를 확인했다.
두 UI 개발 기록은 HTTP200·동일 원 JSON bytes/no-store이며 frozen HTML·환기2,173파일을 보존했다.
게시 guard2.649초·5root·합 RSS900,395,008bytes·단일141,316,096bytes·FD4→4,
소유 프로세스/PG/임시/passfile0이었다. UI code/DOM/WebGL은 변경하지 않았다.
검토에서 연구 helper의 identity/repr 관측을 운영 guard로 사용하지 않고,
전체 동등성/성능/관문으로 승격하지 않는 범위를 확인했다. 새 native CI는 실행하지 않았다.
