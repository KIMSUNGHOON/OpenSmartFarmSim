# 현재 참조 묶음 이후 남은 청크 비용 — 2026-10-19 KST

[선행96검사·원 독립25/64 미완료](market-current-reference-bundle-implementation-20261019.md) ·
[관측 계약](../contracts/crop-solar-current-binding-cost-v1.md) ·
[기계 증거](artifacts/crop-solar-reference-bundle-remaining-cost-20261019.json).

현재 구현으로 기존 소유 합성16단계 fixture의 초기0/1단계를 계산한 뒤 실제1→2단계를
한 번 계측했다. 독립64단계 입력이나 원 actor를 바꾼 실행이 아니다. `18369:0`에서
관측1검사를 통과했다. 기존96개의 고유 컴포넌트 검사 수에는 더하지 않는다.

| 경로 | 실제 호출 | 포함 시간(초) |
| --- | ---: | ---: |
| custody advance |1|11.199337|
| 현재 binding |12|10.780705|
| 등록 입력 현재 조회 |24|9.137400|
| 반복 원천 검증 묶음 |23|6.112977|
| 전체 role 감사 |298|4.405697|

벽시계11.200956초·DB 연결144회·SQL execute8,976회/누적5.208178초였다.
시간은 중첩·profiler와 계측 overhead를 포함하므로 합산하거나 native 처리량으로 해석하지 않는다.
실제 원천1,824회/중복 순서 SHA·current12/등록24/재구성1,
원 UTC `00:00:02.123456Z`→`00:00:04.123456Z`·1→2/yielded와
이전 확정 proof3개의 dev/inode/mode/크기/시각/hash·directory identity를 확인했다.
SQL·매개변수·개인 자료나 접속정보는 기록하지 않았다.

## 남은 감사 위치와 다음 작은 수정

| 실제 role 감사 호출자 | 호출 수 |
| --- | ---: |
| JobStore.connect |72|
| MarketCandidateStore._reference_guard |82|
| ThermalRunStore.connect |48|
| MarketCandidateStore.read_scope |48|
| connect_market |24|
| MarketSourceStore.read_scope |24|

현재 순수 원천 검증에서도 source·candidate·reference scope의 감사가 겹친다.
다음은 [v2 후보 계약](../contracts/market-current-reference-audit-scope-v2.md)에 따라
**같은 순수 검증 작업을 소유한 source scope의 실제 전후 감사로 내부 중복을 합치는 최소 변경**이다.
일반 조회·부적합한 공유 바인딩의 감사와 각 읽기의 현재 principal/pointer/세션·원문/권리를 유지한다.
모든 getter/중복을 실제 같은 순서로 실행하고 최종 실제 감사 전 결과를 내보내지 않는다.
현재 v1은 유지하며 새 후보는 미구현·미수용이다. 원 실제 값/UTC·늦은 변경/수명/정리와
paired 비용이 유용함을 입증한 뒤에만 채택하고, 그 뒤 원 계측 OFF64 정상을 별도로 검증한다.
감사 횟수 감소만으로 native 완료나 속도 개선을 약속하지 않는다.

guard47.138초·합 RSS1,020,993,536bytes·FD4→4·소유 비좀비/PG/임시/passfile0,
원5root·2,148항목·frozen source/assets·두 UI와512MiB/PID/합1GiB를 유지했다.
제품 코드는 변경하지 않았다. 판단은 현재 native `gpt-6.1-sol/xhigh`에서 수행했으며
재귀 CLI/서브에이전트는 없다. 현재 backend/browser 전체 회귀는 실행하지 않았다.

원64 정상·계산 중3D/WSL 용량·새 Solar 배포는 미수용이다. 실제 농장 Run0·권리/관문 승인False,
G0–G4 미평가·독립 현장/미래 생산·경제/후보 비교 자료와 전체 완료일 미정·goal active를 유지한다.

46734:0에서 실제25/64 미완료·남은 비용/다음 후보를5173/5174에 no-store 동일 bytes로 게시했다.
현재 source pin/문서 링크·원 actor/query/probe·HTML/환기 frozen2,173파일/5root/원본/상한/FD·소유 정리를 확인했다.
UI 코드·DOM/WebGL은 변경하거나 재검사하지 않았다.
