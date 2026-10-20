# JSON 상태의 사전 조회 표현 — 2026-10-20 KST

[기계 증거](artifacts/solar-json-dictionary-lookup-20261020.json) · [선행 실제 구간 관측](solar-json-residual-whole-profile-20261020.md).

## 판정과 변경

**소프트웨어 검증176개는 통과했지만 원 전체 계산에서 평균5.952327% 느려 제품에 적용하지 않았다.** 제품 app261개/SHA d477b74b…·호출0을 유지한다. 같은 유효한 timing 시험을 반복하지 않았다.

정확한 문자열 모듈 키는 승인한 참조를 한 번 조회해 비교한다. 처음부터 알려진 이름의 문자열 접두사 검사와 중복 사전 조회를 줄였다. Legacy 함수의 globals/builtins 사전 참조는 각 함수 검사 안에서 한 번 읽고, builtin fallback은 globals에 실제로 없을 때 계산한다. `None`과 내부 sentinel 값이 존재하는 경우를 부재와 구분한다. 입력·권리·현재·HEAD·proof의 재사용은 추가하지 않았다.

문자열이 아닌 모듈 키와 문자열 하위 클래스는 원 전체 stamp로 대조한다. 원 stamp가 정렬 오류를 내는 키를 이전 직접 비교가 허용하던 반례를 RED로 확인했다. 이제 동일하게 승인을 거부하고 원 JSON 읽기로 fallback한다. 이 문제는 제품에 연결하지 않은 연구 코드에서 발견했다.

## 최종 같은 source의 검증

새49/기존127 = 고유176개를 CPython3.12.3과 잠금 판본3.12.13에서 각각 통과했다. 선행173개와 비교해 특수 모듈 키2개·globals 부재/명시 None/sentinel1개를 추가했다. 두 키 사례에서 원 읽기의 값과 비소유 결과도 확인했다. 잠금 판본 검사는 현재 설치된 패키지를 사용했으며 clean hosted 설치/전체 CI가 아니다.

원 `_live_stamp`·Legacy `stamp`·`_attested`·`OwnedJSONScope` AST와 source assembly bytes는 그대로다. JSON 고립 참조 두 SHA와 pristine 함수·캡처 중 변경 거부를 유지했다. 관측 위치/감시 항목·가변 내용·helper/codec 변경·원 fallback·소유/예산/수명 검사를 보존했다.

원46commit/59파일의267,526bytes·SHA3136aa28…가 같다. IO104개의 순서·이름·상한·길이·SHA/seen/참조2,314,629bytes, decode104→83·pair46·payload canonical46→0·1MiB/정리가 같다. 실제 DB의 원 CASE6/input64/chunk1 confirm 전체 record·UTC/current6/SQL4,059, 최초/늦은 권리·일시 HEAD 변경6개 보류가 같다. 조회의 수치/CLI0·DB 불변·역할/schema0을 확인했다. 원 독립64 완주는 아니다.

## 원 전체 실행 시간

원64 입력/output0..64/8·chunk1에서41단계 이력을 준비하고42–45의 `before → advance → confirm` 전체를 한 번 ABBA로 측정했다. 후보는 소유 시험 안의 storage loader만 교체했다. SQL/current 함수는 그대로 관측했다. 원 actor·입력·poll/retry360·RSS 상한을 유지했다.

| 순서 | 원 단계 | 전체 초 |
| --- | ---: | ---: |
| 기존 A | 42 | 8.487816670 |
| 후보 B | 43 | 8.975264523 |
| 후보 B | 44 | 9.287453714 |
| 기존 A | 45 | 8.748915018 |

감소율 평균 **−5.952327%**, 짝별 **−5.742912% / −6.155491%**로 사전 평균2% 이상·양짝 양수 기준을 통과하지 못했다. 이전 source의 별도 실측 시간과 직접 비교해 이번 수정의 개선율을 만들지 않는다. 원 checkpoint bytes/counts/UTC·current15/SQL9,929·role273/원천2,280, 후보 각5 scope/pair218·223/fallback0·1MiB/폐기를 보존했다. pytest1통과는 비교·정리 검증이며 성능 수용이 아니다.

## WSL 자원과 범위

초기 native 시험은 합 RSS1,074,987,008bytes로 원1GiB 상한에 따라 중단했고 성공 집계에서 제외했다. 소유 DB·임시 인증/디렉터리·프로세스 잔여0을 확인했다. 시험 수집 뒤·원 fixture 생성 전에 미사용 객체 수집/`malloc_trim(0)`을 적용해 약2.35MB의 수집 임시 메모리를 반환했다. 원 입력/fixture/actor/계산·상한·보호 판정은 바꾸지 않았다. 보호 서비스를 중단하지 않았다.

최종 source의 수용한5실행 최대 합 RSS1,064,226,816bytes/1GiB·단일145,444,864bytes/512MiB, 각 FD4→4·원5root/2,148·두 frozen UI source/자산·소유 잔여0을 보존했다. native guard64.058134초·원 비용 guard157.180942초다. 수집 메모리 반환 증거를 native/비용 각각 기록했으며 앞선 환경과 시간 차이의 원인으로 단정하지 않는다.

## 다음 단계

`crop-solar-json-assembly-observation-boundaries`: 사전 조회 표현은 더 추측해 수정하지 않고, 조립에 추가한 구문별 검사를 원 함수의 외부 호출·자료 노출 지점과 대조한다. 검사 위치/감시 항목을 변경하는 구현 전에 실제 늦은 변경·자기 복원 callback·오류/소유 수명의 동등성을 입증할 계약과 반례가 필요하다. 증거가 없으면 제품의 원 경로를 유지한다. 자료/권리/현재/HEAD/proof cache나 원 actor/입력/상한 변경으로 대체하지 않는다.

비용 수용 뒤 제품 연결/회귀→원 독립 정상64→hold/HTTP취소→계산 중WebGL→WSL 적용 순서다. 전체 backend/browser·새 CI·원64·WebGL은 이번에 재실행하지 않았다. 실제 품종·국내 농장/시설·기후·재배/수확/자원·경제/시장 자료의 권리·독립 검증은 외부 의존성이다. 실제 농장 Run0·G0–G4/미래 생산·마진·최적 추천은 보류이며 전체 완료일/집중시간은 미정이다. native CLI gpt-6.1-sol/xhigh 문맥·source/출력 SHA를 기록했고 재귀 CLI/새 agent0·goal active다.

## 사용자 진행 정보 게시

[게시 영수증](artifacts/solar-json-dictionary-status-publication-20261020.json): 두5173/5174의 같은 최신 JSON·HTTP200/no-store·원 HTML과 환기2,173파일을 확인했다. 176검사/원 비용 미채택·다음 관측 경계 검토와 미완료64/새 일사 배포를 표시한다. UI 코드·DOM/WebGL은 재실행하지 않았다. 기존 환기의 `new_model_deployed:true`를 유지하며 새 Solar 적용이 아니다.
