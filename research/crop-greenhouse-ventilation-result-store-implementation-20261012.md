# 환기 결과 등록·현재 조회·호출자 거래 — 2026-10-12

상태: 고유20그룹·최종 보존 통과 뒤 로컬 수용. 새 모델의 원 계산 파일을 실제 SCRAM DB에 등록·재조회하는 소프트웨어 범위다.
사용자5173/5174의 기존 모델·결과·서비스는 유지한다. 새 모델/API/worker/UI는 아직 배포하지 않았다.
실제 농장 Run/국내 독립 검증 자료0, G0–G4 `not_assessed`와 실제 품종/생산/미래 마진/추천 보류를 유지한다.

## 구현

[서버 모듈](../backend/app/crop_greenhouse_ventilation_result_store.py), [검사](../backend/tests/test_crop_greenhouse_ventilation_result_store.py),
[계약](../contracts/crop-greenhouse-ventilation-result-store-v1.md)은 수용한 새 DB/명시 권한과 exact 새25장부 custody를 사용한다.
별도 result ID/HMAC/lock domain으로 원 farm/source/context/UTC/evidence·서명 intent/HEAD/proof/root와 current code/policy를 결속한다.
`put`은 completed/hold의 원 root만 등록한다. 같은 요청 재시도는 최초 bytes/recorded_at을 보존하고 ready/yielded를 계산·승격하지 않는다.
`get/page/summary`는 현재 같은 tenant/farm·계정/등록/원 입력/검토/자료 권리와 원 파일을 반환 전후 검사한다.
조회9진입점(Context/UTC 준비·복원·RHS·환기·적분·관리·start/advance)은0이다. 페이지/metadata 상한과 원 UTC 정밀도를 유지한다.

`_put_in_transaction`은 실제 열린 authority Connection·SCRAM/endpoint/현재 grants·INTRANS를 검증하고 내부 savepoint로 호출자 기록과 함께 저장한다.
호출자 오류·늦은 철회는 결과와 호출자 기록을 함께 rollback하며 부모 거래의 사용 가능성과 원 예외 객체를 보존한다.
context 뒤 외부 rollback도 결과를 취소한다. 이 hook만으로 worker 임대/종료 fence·HTTP/UI의 수용을 주장하지 않는다.
새3 core만 추가했고 기존241파일은 보존했다. 이전 서명 결과를 새 코드/모델로 자동 채택·재서명하지 않는다.

## 실제 검증

[서명 참조·원 종료/자원 영수증](artifacts/crop-greenhouse-ventilation-result-store-reference-20261012.json):새19/기존1 = 고유20그룹.
여섯 guard는 순차 실행했으며 모든 guard에서 core3 bytes가 같았다. 전체 backend/CI 실행 결과로 합산하지 않는다.

| 범위 | 원 도구 세션 | guard wall(초) | 통과 |
| --- | --- | --- | --- |
|새/기존 정상·fresh|`21351`|241.865|2그룹·원 bytes/최초 시각/페이지/UTC·조회0|
|권한·미완료·busy·늦은 쓰기 철회|`51254`|166.171|4그룹·commit 전0행/후1행 감사 보존·접근 거부|
|현재 철회·서명 혼합·hold·충돌|`90192`|294.617|4그룹·다른 farm/source/HEAD·유효 HMAC 변조·원 hold|
|호출자 commit/rollback|`76879`|233.535|4그룹·외부 비가시성·원 예외·부분 결과0|
|호출자 기록 뒤 늦은 변경|`65801`|168.297|3그룹·rights/scope/resolver·작업 기록과 결과 rollback|
|연결 신원·다른 모델·hold|`84084`|196.935|3그룹·idle/autocommit/aborted/closed/admin/worker/tenant 거부·공존|

정상 metadata는35,423bytes다. 원16걸음·3시점/3사건과 마이크로초 UTC를 대사했다.
새/기존 정상 모두 별도 exec의 실제 SCRAM·원 raw SHA/최초 recorded_at/원 페이지/summary/UTC·검토 철회와 조회 수치0을 통과했다.
새 정상 payload SHA는 `85ddc79dda17844e061fda694076f8138283966cd5ed244a4004ea982c32b0e0`다. rows1·jobs/기존 Run의 관측 count와 FD를 보존했다.

서명/HMAC이 유효해도 현재 binding/원 progress/SQL 컬럼·source/context/time/농장 혼합을 거부했다.
현재 철회·잘못된 페이지·같은 revision 충돌·실제 advisory lock/busy와 forced rollback을 확인했다.
등록 전 철회는0행, commit 후 철회는private 감사1행을 보존하고 응답/접근을 거부했다. 늦은 page 권리 변경도 반환 전에 거부했다.
실제 hold의 마지막 확정 값·실패 UTC·checkpoint None을 정상 완료로 바꾸지 않았다.

호출자 거래는 uncommitted 결과가 다른 연결에서 보이지 않고, put/hook/retry가 최초 bytes/recorded_at을 공유했다.
inside-hook/after-hook/caught-inside-hook의 원 예외·외부 rollback·savepoint 복구와
호출자 기록 뒤 권리/계정 scope/resolver 변경3종의 결과·작업 기록 동시 rollback을 확인했다.
연결 identity는 실제 authority/SCRAM/명시 endpoint와 현재 grants에 결속된다. idle/autocommit/aborted/closed/admin/worker/foreign tenant7종을 거부했다.

기존22장부 모델을 같은 fixture에서 별도로 실제 계산·서명 등록하고 원 store로 원 bytes/시각을 재조회했다.
새25장부 행과 각각1행 공존·상호 ID/authority 거부·별도 HMAC/lock domain·기존 행 불변을 확인했다.
이는 이번 fixture에서 생성한 두 모델의 signed 행 시험이며 과거 배포 행의 migration/재서명 시험은 아니다.
기존 두 cycle schema-only 행도1행씩 보존했다. 실제 사용자 원 모델은 원 frozen source/DB를 유지한다.

## 자원·보존·CLI·남은 작업

모든 guard 실제0·FD4→4·scratch schema/role/소유 PG/임시 PG/passfile 잔여0이다.
.25초 최대 단일 RSS143,859,712bytes/소유+보호 합988,286,976bytes로512MiB/1GiB 안이다.
최종 보존 원5453의 persisted 실제0 영수증을 재확인했다(이전 wait 뒤 handle 닫힘). 원본2,148·기존241파일·accepted source1,911/원 자산171·현재5174 자산171/설정·두 HTTP200/4보호 root·권리/키/접속 안내·로컬 링크2,024를 대사했다. guard0.603초·FD4→4·소유 잔여0이다.
새 production schema/roles migration·사용자 서버 재기동·token/권리 변경을 수행하지 않았다.

현재 native Codex CLI `gpt-6.1-sol`/`xhigh`의 실제 turn context `2026-10-11T15:40:04.302Z`·raw-line SHA/decision ID와 실제 출력 core SHA를 영수증에 기록했다. 재귀 CLI0이다.
새 농업 원문/계수/자료 권리를 채택하지 않았고 source review SHA를 유지했다. proposal/fixture는 자료·관문 승인이나 실제 품종 보정이 아니다.
전체 CI/remote·새 HTTPS/worker/typed web/WebGL·전체 작기 재계산은 미실행이다.

다음 한 단계는 새 결과의 typed 공개 query다:원108상태/25연속/6사건/10수지·환기 진단/원 UTC/manifest를 혼합 없이 직렬화하고 현재 권리 아래 조회 수치0·반환 전후 변조/철회·2MiB를 검증한다.
그 뒤 실제 보호 HTTPS→자동 worker/typed web/같은 UTC3D→사용자 적용이다. 상위 API/worker/UI는 미수용이다.
남은4–8집중작업시간은 API1–2·worker/web2–4·사용자 적용1–2의 잠정 분해이며 전체 제품 완료 시각은 아니다.
독립 농장 자료0과 온실/자원·경제/최종 UI·G0–G4는 남아 있다.
