# 한 checkpoint 확인의 등록 scope 후보 평가 — 2026-10-20 KST

[기계 증거](artifacts/solar-confirm-registration-evaluation-20261020.json) · [선행 소비 관측](solar-checkpoint-consumer-review-20261020.md) · [후보 계약](../contracts/solar-confirm-registration-lifetime-v1.md) · [재현용 후보](solar-confirm-registration-candidate.py).

## 결정

**이 후보를 제품에 적용하지 않는다.** 사전 기준은 원 before/advance/confirm 전체 묶음에서 두 ABBA 짝 모두 감소·평균2% 이상이었다. 실제 한 번의 유효 trial은 평균1.404965%·둘째 짝2.646682% 증가로 기준을 통과하지 못했다. 같은 후보의 시간 비교나 같은 app의 정상 CI를 다시 실행하지 않았다.

후보는 원 confirm의 early lease/입력 뒤 기존 등록 scope를 소유하고, 읽기 서버 세션만 명시적으로 같은 owner에 합류하게 했다. 첫 original current 앞에 guard를 더하고 owner/인자·활성/실패/slot/실행 결속을 검사했다. scope는 jobs transaction commit 전에 닫는다. 원 세 fresh 저장 검증·현재 원천/권리·lease/cancel·서명/이력·최종 입력/history fence를 유지했다. JSON 자료 소유권 재사용은 없다. 제품 app261은 변경하지 않았다.

## 실제 경계 진단

마지막 v2의 **고유1검사**에서 다음을 확인했다. 아래 fault/option 수는 검사 건수에 더하지 않는다.

- 실제 confirm의 재구성2→1, 닫힌 owner·fresh session/storage load 각3회·원 checkpoint metadata/UTC와 같음.
- 같은 HEAD의 page 변경을 중간 snapshot과 마지막 progress에서 차단, DB checkpoint rollback·원 page 복원 뒤 정상 게시, 조회 중 수치 계산0.
- exact-bool 아닌 옵션6개, owner 없는 합류, write 합류, 기본 nested 동작과 다른 farm owner 거부; 올바른 명시 읽기 합류.
- scope 종료 예외·늦은 물리/경제 권리 철회 모두 DB checkpoint rollback, witness/connection 토큰 정리와 복원 뒤 fresh confirm. 공개 result publication0.

초기 v1도 통과했으나 이전 진단에서 복사한 `separate_registration_owners=True`라는 metadata 상수가 잘못 남았다. 실제 assertion/재구성 수는1이었다. 원 파일/출력은 보존하고 v2에서 상수를False로 수정한 뒤 strict/exit/권리 경계를 추가했다. v1을 최종 검사 수에 합산하지 않는다. Task/thread/복제 context·모든 source/연구/snapshot/grant·취소/임대 경계의 전체 신규 회귀는 수행하지 않았고, 비용 기준 미달 뒤 제품 채택 검사로 확장하지 않았다.

## 원 입력의 실제 전체 묶음 비용

원 CASE6/64·출력0…64/8·chunk1을 유지하고 원 writer/custody로41까지 준비한 뒤42–45를 측정했다. 준비 구간은 독립 worker/API 정상 완주가 아니다. 후보 source hash와 ABBA/2% 기준은 실행 전에 고정했다.

| 순서 | 방식 | step | 전체 wall초 | SQL | 등록 재구성 |
|---|---|---:|---:|---:|---:|
|A|기존|42|9.132414207|9,929|4|
|B|후보|43|8.657197244|9,704|3|
|B|후보|44|8.788803786|9,704|3|
|A|기존|45|8.562189819|9,929|4|

짝별 감소율은 **5.203629% / −2.646682%**, 평균은 **1.404965%**다. 재구성1회와 역할 감사15회가 줄었지만 일관된 전체 비용 개선을 입증하지 못했다. SQL225회 감소는 `_database`15·`audit_runtime_roles`135·`_scope`75회뿐이었다. 이를 검증 전체 수용이나 원64 개선율로 확대하지 않는다.

네 묶음 모두 현재 검사15회·같은 원천 선택2,280회/순서 지문·fresh load5회/호출 순서를 유지했다. 독립 순수 계산의 checkpoint 원 bytes·counts·HEAD와 UTC00:01:24/26/28/30.123456Z를 대사했다. 모든 등록 owner가 닫혔고 관찰기는 제거됐다. 결과의 pytest 통과는 원값/계측 수용이며 속도 기준 통과를 뜻하지 않는다.

## 자원·범위

최종 경계1 + 비용1 = **고유2검사**다. 마지막 경계 controller77.194740초·합 최대 RSS1,050,656,768bytes, 비용 controller160.245478초·합1,060,696,064bytes이며 단일 최대145,444,864bytes다. 각 FD4→4·원5root/2,148항목·두 frozen UI/source/자산·소유 PG/비좀비/임시/passfile 잔여0을 확인했다. 초기 pilot와 과거82/176을 합산하지 않았다.

실제 native Codex CLI `gpt-6.1-sol`/`xhigh`의 문맥·원행 SHA와 후보/사설 실행기/사전 기준·출력/terminal/source pin SHA를 결속했다. 재귀 CLI/하위 agent·새 framework/수식/자료 채택은0이다. 전체 backend/browser CI·새 DOM/WebGL·원 계측 OFF64·실제 농장/경제 검증은 실행하지 않았다. 새 Solar 미배포·실제 농장 Run0·전체 완료일 미정·goal active다.

## 다음 한 단계

[기존 동시 진단](solar-current-worker-api-diagnostic-20261020.md)은 HTTP status와 worker의 확정27/64를 남겼지만 API 요청별 latency/CPU/SQL이 없어 동시 실행의 비용 비중을 확정하지 못했다. 다음 `crop-solar-api-request-cost-diagnostics`는 [기존 observer의 작은 확장](../contracts/solar-api-request-cost-diagnostics-v1.md)이다. 제어된 비밀 미노출/유한 기록 검사 뒤 원 actor 본문·입력·조회·상한을 유지한 새 관측1회로 다음 제품 수정 경계를 정한다. client 대기 시간을 server CPU로 표시하지 않으며 기존 정상64→hold/HTTP취소→계산 중WebGL→WSL 적용 관문은 유지한다.

## 사용자 진행 정보 게시

[게시 영수증](artifacts/solar-confirm-registration-status-publication-20261020.json): 두5173/5174의 동일 최신 JSON·HTTP200/no-store, 원 HTML/환기2,173파일·app261/원본·5root/소유 정리와 로컬 링크2,734개를 확인했다. UI 코드·DOM/WebGL 재검사는0이다. 기존 환기 배포 표시를 유지하며 새 Solar 배포가 아니다.
