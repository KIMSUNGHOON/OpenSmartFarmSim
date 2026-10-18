# 실제 한 advance의 권한 감사 SQL 비용 — 2026-10-19 KST

[기계 증거](artifacts/crop-solar-role-sql-cost-20261019.json) ·
[재구성 감소26검사](farm-registration-read-scope-implementation-20261019.md).

source `c2bc1f6`의 같은 실제 합성16단계 fixture에서 초기/1단계를 준비한 뒤
2단계 advance 한 번을 관찰했다. `psycopg.Connection.execute` 중 실제
`runtime_roles` 호출만 파일/함수/행/statement SHA로 집계했다. SQL 값·매개변수·
접속정보는 게시하지 않는다. 현재 검사·원 수식/입력·상한을 바꾸지 않았다.

| SQL 경계 (`runtime_roles.py`) | 실제 호출 | execute 누적 초 |
| --- | ---: | ---: |
| column 행렬,255행 |528|0.887303|
| table 행렬,238행 |528|0.759208|
| 현재 추가 ACL,196행 |528|0.688298|
| DDL/definer 경로,214행 |528|0.638168|
| dedicated owner 범위,137행 |528|0.374451|

총15개 SQL 위치·**7,920회 execute/4.938623초**, advance 관측9.421724초였다.
실제 원천1,824회의 순서·중복 SHA와 현재 감사528회, 원1→2단계/yielded·16계획과
G0–G4 미평가/권리 승인False를 대사했다. execute 시간만 집계하며 fetch/Python 비용은
제외한다. 한 로컬 표본으로 이전 cProfile 관측과 속도를 비교하지 않는다.
두 행렬은 누적 약1.647초였으므로 이를 줄이는 것만으로 전체64단계 제한을 해결한다고
약속할 근거가 없다. 이번 관찰은 추가 최적화나 권한 캐시를 수용한 것이 아니다.

`62021:0`의 pytest1검사/45.54초·guard47.919초·합 RSS992,739,328bytes였다.
원5root/동적 자식·frozen source/assets·원본2,148항목·512MiB/PID/합1GiB·감독FD4→4,
시험 role/schema/소유 비좀비/PG/임시/passfile0을 확인했다. 이 관찰은26개의 고유
컴포넌트 수용 검사에 더하지 않는다. native 정상·현재 browser/전체 회귀·새 모델 배포는 별도다.

다음 판단은 원 계측 OFF64단계 독립 정상의 실제 결과를 먼저 따른다. 미완료이면 저장 단계와
이번 비용을 함께 보고, current 경계마다 자료/권한/판본 변경을 동등하게 차단하는 가장 작은
개선을 별도 계약/실제 DB·철회·취소·만료·원 값/UTC/정리 검사로 검증한다.
성능 목표를 위해 권한 검사를 생략하거나 원 시간/청크/조회/메모리 한도를 바꾸지 않는다.
실제 농장0·독립 측정/미래 마진/작물 비교·관문·전체 완료일은 보류이며 goal active다.
판단은 현재 native `gpt-6.1-sol/xhigh`에서 수행했고 재귀 CLI/subagent를 실행하지 않았다.
