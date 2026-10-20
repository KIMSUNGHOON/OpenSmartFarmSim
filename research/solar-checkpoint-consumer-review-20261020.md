# 제품 checkpoint 소비·검증 경계 — 2026-10-20 KST

[기계 증거](artifacts/solar-checkpoint-consumer-review-20261020.json) · [실제 진단 코드](solar-checkpoint-consumer-probe.py) · [후속 최소 변경 계약](../contracts/solar-confirm-registration-lifetime-v1.md).

## 확인한 소비자

제품4파일의9개 method를 현재 source에 대조했다. 저장 loader의 반환은 다음8칸이다.

| 칸 | 자료 | 실제 소비 |
|---|---|---|
|0|header|세션의 입력 결속, progress의 context/time hash, writer 재개 binding 확인|
|1|context|progress의 planned_steps, advance의 원 프로그램/재개 검증|
|2|commit digest 목록|writer 재개의 append/finalize 이력|
|3|SHA와 수치 `value`를 가진 checkpoint|advance restore, writer의 supplied checkpoint 원 canonical 비교, progress|
|4|마지막 원 source|status/steps/last_confirmed/hold, writer의 다음 append 상태|
|5|원 시각 묶음|progress 및 packet의 computed_through_utc|
|6|페이지 index|공개 artifact reader의 페이지 선택; 위 재개/progress는 반환 index를 직접 사용하지 않음|
|7|samples/events counts|writer 누적, progress/packet과 worker 진행 판단|

`_snapshot`은8칸의 반환을 버리지만, fresh `_load`의 검증 효과를 소비한다. 이 호출은 선택 HEAD와 서명 이력, header/context·프로필·commit/page 원문/보안/SHA/canonical, source/bound result·checkpoint hash·prefix·UTC를 다시 확인한다. terminal이면 별도의 root/summary 경로도 있다. 반환값 미사용만으로 읽기나 검증을 제거할 수 없다.

checkpoint packet은 **25개 metadata 필드**다. 수치 `value`, `checkpoint`, `last_confirmed`, `times`, `hold`는 없다. `rights_or_gate_approval=False`이며 수치 재개나 현재 권리 승인으로 대체할 수 없다. worker `_confirm`은 이 metadata를 받고, 수치 재개는 기존 저장 원 checkpoint를 다시 읽는다.

## 실제 DB 관측

소유 SCRAM fixture에서 step1/원 UTC `2026-10-01T00:00:02.123456Z`의 실제 `confirm`을 실행했다. 마지막 v2의 **고유1검사**이며 초기 v1은 재구성 관측을 추가하기 전 기록으로 합산하지 않는다. API/worker 전체 실행이나64단계 성능 검사가 아니다.

관측 순서는 다음과 같다.

1. unlocked lease → 입력/첫 current → 첫 guarded progress/full load → DB history.
2. `_snapshot`의 fresh full load/proof → descendant → unlocked lease → 중복 확인 또는 DB insert.
3. 늦은 current → 마지막 guarded progress/full load와 원 bytes equality → locked lease → 입력/history fence → transaction commit.

한 번의 정상 확인에서 fresh session/storage load가 각3회였다. 세 결과의 HEAD·8칸·counts는 같았다. public progress는36,157bytes, packet은1,465bytes이며 두 progress bytes가 같았다. 이는 해당 작은 합성 사례의 크기이고 전체 작기/속도 수용이 아니다.

같은 확인에서 **별도 등록 owner2개와 실제 재구성2회**를 관측했다. 첫 `_current`의 owner와 서버 읽기 세션 owner가 다르며 둘 다 종료 뒤 닫혔다. 이 확인 작업 안에서 기존 등록 읽기 scope를 소유하도록 좁힐 수 있는지가 다음 후보의 근거다.

## 같은 HEAD의 늦은 파일 변경

새 저장 prefix마다 첫 progress 뒤 중간 `_snapshot` 직전 또는 마지막 progress 직전에 실제 page bytes를 변경했다. 두 경우 모두 HEAD/서명 metadata는 그대로였지만 confirm이 hold했고 DB checkpoint event는 이전 그대로였다. 마지막 경우는 transaction 안의 새 게시가 rollback됐다. 매번 원 page bytes/권한을 복원한 뒤 fresh confirm이 정상 게시했고 공개 result publication은0이었다. 진단 중 수치 계산은 금지했고 실제 호출0이었다.

따라서 중간 load나 마지막 progress를 이전 packet/HEAD 일치만으로 대체하지 않는다. 같은 HEAD가 현재 파일 내용과 최종 게시 가능성을 보장하지 못한다.

## 결정과 다음 한 단계

`crop-solar-checkpoint-consumer-validation-boundary`의 소비 필드·불변 bytes·현재/늦은 권리·HEAD/ancestry/lease/cancel·오류/게시 순서 대조를 완료했다. **제품 변경0**이며 기존 JSON 재사용 후보의 미채택은 유지한다.

다음 `crop-solar-confirm-registration-lifetime-candidate`는 [별도 계약](../contracts/solar-confirm-registration-lifetime-v1.md)의 **한 confirm 안 등록 재구성2→1 후보**만 평가한다. 세 fresh 저장 검증과 현재 원천/권리 검사를 유지한다. 원 workload의 bytes/UTC·lookup/트랜잭션/오류·자원·정리와 실제 비용을 먼저 대조한다. 이 관측만으로 scope 확장이나 속도 개선을 수용하지 않는다.

## 보존과 한계

최종 v2: pytest1통과/48.78초, controller50.718125초, 단일/합 최대 RSS145,444,864/1,058,287,616bytes. FD4→4·원5root/2,148항목·두 frozen UI/source/자산·소유 PG/비좀비/임시/passfile 잔여0을 확인했다. 수용 수는 원 로그에 결속하며 이전82/176 또는 두 fault vector를 더하지 않는다.

native CLI `gpt-6.1-sol`/`xhigh`의 실제 문맥·원행 SHA와 source/출력/terminal SHA를 기록했다. 재귀 CLI/하위 agent/새 framework·자료 채택0이다. 전체 backend/browser CI·원64·새 DOM/WebGL·실제 농장 검증은 실행하지 않았다. 새 Solar는 미배포이며 기존 정상64→hold/취소→계산 중WebGL→WSL 적용 순서를 유지한다. 전체 완료일과 실제 국내 농장/경제·시장 자료 확보일은 미정이고 goal은 active다.

## 사용자 진행 정보 게시

[게시 영수증](artifacts/solar-checkpoint-consumer-status-publication-20261020.json): 두5173/5174에 동일 최신 기록·HTTP200/no-store를 확인했다. 현재 진단과 후속 후보를 표시하며 원 HTML/환기2,173파일을 유지했다. UI 코드·DOM/WebGL 재검사는0이다. 기존 환기 배포 표시를 유지하며 새 Solar 배포는 아니다. 관련 로컬 링크2,726개·app261/원본·5root/소유 정리를 함께 확인했다.
