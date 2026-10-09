# 검증 계산 결과의 현재 농장 조회 — 개발 계약

2026-10-07 KST. native Codex CLI `gpt-6.1-sol / xhigh`에서 판단하며 재귀 CLI0회다.
선행 [조회 타입 계약](crop-cycle-calculation-result-read-context-v1.md)과
[새 signed DB 수용](../research/crop-cycle-calculation-result-publication-implementation-20261007.md) 뒤
`crop-cycle-calculation-current-query`를 구현했다. 아래 작은 조회 범위는
[실제 SCRAM12개](../research/crop-cycle-calculation-current-query-implementation-20261007.md)로 로컬 수용했다.
원 query/서명/행과 원55 source를 보존하고 새 exact 판본만 연결한다.

## 구현과 원 증거 결속

core3파일은 `backend/app/crop_cycle_calculation_current_query.py`,
`backend/tests/test_crop_cycle_calculation_current_query.py`, 이 계약이다.
새 query·실제 SCRAM 시험만 추가한다. 새 서비스/queue/DB 표·solver·권리 정책은 추가하지 않는다.

`CalculationCurrentCycleQuery(store, authority, *, evidence_resolver)`는 exact
`CalculationCycleCropResultStore`와 `CalculationResultEvidenceAuthority`를 받는다.
판본은 `crop-cycle-verified-current-query-v1`이며 query source/dependency·resolver 판본을 고정한다.
DB/server/input/result key는 각각 별개다. profiles/notice는 현재 farm authority와 같아야 한다.

`read(...)`와 `open(...)`은 기존 private `{record,terminal,page,identity}` 의미를 보존한다.
`kind=None`은 summary, samples64/event8·원량/UTC·응답2MiB는 선행 새 reader의 계약을 따른다.
없는 ID는 `None`, 현재 권한 오류는 기존 PermissionError/role 의미, 나머지는 고정 hold다.
`open`이 yield한 뒤에도 같은 결속을 검사하여 API의 향후 투영 후 철회를 반환 전에 거부할 수 있어야 한다.
이 bundle은 공개 DTO나 실제 농장 예측이 아니다.

resolver는 version과 `(tenant, packet)` 인터페이스를 가지며 현재 사설 input directory·원 input/result proof bytes만 반환한다.
packet 변형을 거부하고 결과 경로는 현재 custody root/intent/artifact에서 직접 계산한다.
HTTP 입력에서 경로/키/proof를 받지 않고 resolver가 새로운 계산 이력이나 증명을 발행하지 않는다.
**실제 서버가 계산에 사용한 원 input proof bytes**를 그대로 사용한다. 재발행한 다른 raw SHA의 증명으로 대체하지 않는다.

새 binding의 input9필드는 root/calculation/program/period/plan/profile/normalization/Python과 input_validation이다.
마지막 validation8필드는 새 context SHA·input evidence SHA·원 validated context SHA·engine/input evidence 판본과
calculation/input evidence code·dependency다. 조회 context의 공식 manifest와 원 root metadata에서 결정적으로 구성해
DB binding과 byte 대사한다. CalculationContext/private token을 생성하거나 farm `_input`에 조회 타입을 위장하지 않는다.
원 root·기간/계획·프로필/QC·정규화와 서로 다른 세 SHA의 provenance를 모두 유지한다.

현재 계정/Scope·등록/원천·입력 research_display 권리와 선언 불변성, DB HMAC/column·원 payload·farm을 대사한다.
새 server의 순수 `_proof`/`_selected` 해석만 재사용해 현재 intent HMAC와 선택한 HEAD의 **전체 부모 서명**을 검사한다.
`_Journal`·server `_open`·writer·original parser/context/QC/RHS를 조회 중 구성하거나 실행하지 않는다.
원 intent/binding/context/header/head/proof/artifact·status/걸음/count/commit/실제 파일/bytes를 새 결과 snapshot과 대사한다.
현재 파일·inode/코드/설정·DB/등록/권리를 준비 전후, yield 후에 다시 확인한다. 실패/성공의 모든 FD를 닫는다.
조회는 DB/custody 파일/서명을 쓰지 않는다. 새 결과 증명의 발행은 별도 준비 단계다.

## 다음 한 단계의 수용 기준

1. 실제 SCRAM 등록 농장의 새 서버 계산·signed DB 게시·원 input proof/새 result proof 뒤 summary와 모든 작은 원
   sample/event·121상태/clock/cursor·manifest/validation을 대사한다. RHS/parser/context/QC0·DB/custody 불변성을 확인한다.
2. 없는/다른 ID·tenant/farm·구형 authority/store/proof 혼합과 네 key의 중복, resolver/notice/profile/정책 변경을 거부한다.
   다른 원 input proof SHA·유효 HMAC의 잘못된 validation/context/부모 서명·DB column도 거부한다.
3. 실제 현재 Scope/계정·등록·원천/입력 권리 철회, DB/intent/선택·중간 부모 proof/HEAD/입력/page·inode 변조,
   페이지 준비 후 및 yield 뒤 철회/변경을 거부한다. 잘못된 key/ID는 안전한 거부이며 권리 허용으로 바뀌지 않는다.
4. 정상·수치 hold/확인 과거·서비스 재구성과 실제 별도 프로세스의 재조회, FD/context/cache·PG/DB/역할/비밀 파일 정리를 기록한다.
   fork와 fresh exec를 구분한다. 실제 HTTP/fresh API runtime/WebGL 수용은 다음 단계이며 이 시험을 대신하지 않는다.
5. 원 signed row/이력과55 source를 보존하고 실제 호출/출력·현재 source/CLI·query 비용을 기록한 뒤 자식만 체크한다.
   내부 get39.668745초 관측과 HTTP30초 미수용을 보존한다. 한도를 올리거나 출력을 줄여 통과하지 않는다.

기존 이식/검토·실제 시험의3–6집중시간 잠정은12통과/1,079.43초·종료0과 위 수용 기록으로 대체한다.
정상120걸음/3시점·사건 포함120걸음/3시점/3사건·수치 hold60걸음/1시점/1사건,
원량/UTC/검증 SHA·현재 철회/변조·fork·63 source/FD/PG/DB/비밀 정리를 확인했다.
farm query fresh exec·새 HTTP/전체166일/3D는 수행하지 않았다. 다음은
[새 공개 투영3 core파일](api-crop-cycle-calculation-projection-v1.md)과 명시적 설정/factory·실제 TLS다.
별도 등록 prefix 누적 비용 측정은 읽기 개발과 병행한다. 전체166일/등록/HTTP30초·동일 UTC3D는 두 경로의 증거가 모두 필요하다.
이후 수확/생과 → 물/양분·구매 에너지 → Decimal 경제로 연결한다.
실제 품종 입력·국내 독립 검증 자료·실제 작물 Run은0건, G0–G4는 `not_assessed`다.
