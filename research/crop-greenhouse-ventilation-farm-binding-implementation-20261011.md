# 환기 입력과 현재 등록 농장 결속 — 2026-10-12

**실제 SCRAM 새6/회귀6그룹 통과·최종 보존 확인 뒤 로컬 수용.** [핵심3 계약](../contracts/crop-greenhouse-ventilation-farm-binding-v1.md)/
[기계 증거](artifacts/crop-greenhouse-ventilation-farm-binding-reference-20261011.json).
[입력 증거332검사](crop-greenhouse-ventilation-input-evidence-implementation-20261011.md) 이후의 현재 농장/자료 권한 결속이다.

## 구현

기존 실제 농장 등록·authority JobStore/SCRAM·전체 grant 감사·read/write scopes를 재사용했다.
새 입력 authority/type/schema·권리 선언·binding version/scope로 구 판본을 구분하며 새 DB/schema/role/service를 제품에 추가하지 않는다.
새 context/UTC/초기 상태·25장부 identity·검토/결정/원 source와 현재 farm/crop/batch/zone/floor·점유 기간을 결속한다.
현재 입력/검토 검사와 권리 관측을 각2회 수행하고 원 등록/tenant/scope를 반환 전에 다시 확인한다.
profile_applicability는 `unvalidated_for_registered_crop`이며 등록 품종 의도를 실측 검증으로 표시하지 않는다.
이 호출은 여러 저장소를 하나의 원자 snapshot으로 잠그는 증명이 아니다. 후속 custody가 게시 전후 다시 확인한다.

## 실제 검증

| 범위 | 결과 |
| --- | --- |
| 정상 read/write·fresh |7,385bytes 원 결속 동일·actual SCRAM/used_password/require_auth·fresh exit0 |
| 조회 계산 |context/UTC 생성·RHS/환기/step/관리/start/restore/advance의9항목 모두0 |
| 원 row 보존 |jobs/inputs/작물 결과/Run `[89,89,0,0]`→동일; 새 결과/Run0 |
| 현재 권리 |read/write 구분·9read scopes·다른 tenant·source/review/자료 권리 철회 거부 |
| 닫힌 입력 |18혼합 요청·6raw JSON·원 expected bytes 변경·구 source/rights/authority 타입 거부 |
| 늦은 변경 |rights/review/source/scope/bytes/declaration6개 callback 거부·원 row 동일 |
| 고정 설정 |7참조/정책/코드/key ID·5개 non-True·bool write 정책 거부 |
| 기간 |다른 작기와 종료1µs 초과 거부·원 UTC를 절단하지 않음 |
| 최종 집중 |새6/기존6=12고유 그룹·pytest181.07초·원2839 child/tool0·guard193.493128129초 |
| 정상 smoke |새/기존 정상·fresh2그룹·원36745 child/tool0·37.338827889초 |
| 정리 |양쪽 scratch DB schema/role0·FD4→4·owned PG/임시 PG/passfile 잔존0 |
| WSL |.25초653표본·단일142,290,944/보호 포함 합963,219,456bytes;512MiB/1GiB 이내 |

정상 prepare0.953718924초/current0.946740424초를 관측했다. 특정 작은 합성 등록 농장의 비용이며 운영 SLA가 아니다.
실패 실행0·사용자 서버 중단/교체0·새 API/worker/웹 배포·전체 CI/remote 실행0이다.
원 전체166일 계산/3D를 불필요하게 다시 실행하지 않았다. 기존 [5174 화면](product-ui-current-status-entry-20261011.md)을 유지한다.
실제 native CLI `gpt-6.1-sol / xhigh`, turn `2026-10-11T14:46:56.847Z`,
context SHA `a047cc1744edc79213f0ff537e010aa6d1036c908f0c6554d7a638dd46669798`, 재귀 실행0이다.
농업 식/계수·자료 권리는 [기존 원문 검토](crop-greenhouse-boundary-source-review-20261011.md)를 유지한다.

최종 보존 원80736 child/tool0·0.609091734초:기존238계산·원본2,148·원 source1,911/171자산·현재171자산·두 HTTP200·현재 권리/검토·로컬 링크2,018을 확인했다.
수용 시각: 2026-10-12T00:11:57.614988+09:00 KST.

## 다음 한 단계와 외부 의존성

다음은 **서버 소유의 서명된 checkpoint/HEAD 이력**이다.
새 현재 binding·새 artifact/UTC의 원 bytes/25장부를 다른 signing domain과 trusted resolver로 결속한다.
원 실외 입력을 포함해 context를 준비하고 signed evidence의 초기 RHS+환기 record와 대사한다.
수용: 실제 SCRAM의 분할 계산/원 checkpoint·HEAD/UTC·fresh 재개·읽기 수치0·현재 권리/철회/변조·원본/두 UI/WSL 보존이다.
이후 결과 등록/보호 API→worker/typed web/같은 UTC3D→사용자 적용을 별도 수용한다.
입력/농장 결속을 수용해, 남은 합성 환기 모델 UI 연결은 custody/API2–4 +worker/web2–4 +적용1–2 =잠정5–10집중작업시간이다. 전체 제품 완료 견적은 아니다.

실제 농장 Run/독립 국내 자료0·G0–G4 `not_assessed`·실제 품종/생산·미래 마진/추천 hold다.
새 환기 모델은 현재 UI 미배포다. 이 자식으로 상위 input-custody·API/worker/전체 제품을 완료 처리하지 않는다.
독립 자료 확보는 개발과 병행하며 예측/추천 게시 조건을 낮추지 않는다.
