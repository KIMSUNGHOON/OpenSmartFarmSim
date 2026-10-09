# 현재 시장 읽기 권한 거부의 CI 시험 기대값

상태: **집중 로컬 수용·수정 판본 hosted CI 미수용**, 2026-10-06 KST.
운영 기반의 완료 범위는 기존 `d19f7c0` 고정을 유지한다.

`d61bcb3`의 [backend 분할2](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37405273500/job/112081329340)는
703개 통과·1개 실패/1,137.44초였다. 기존 tenant/concurrent retry 시험이 `authenticated` 문구를
기대했지만 [선행 읽기 범위](crop-cycle-market-read-scope-implementation.md)가 먼저
`MarketCandidateDenied('market candidate read authority denied')`를 반환했다.
외부 tenant의 읽기는 계속 거부됐으며 산술이나 원천 권리 정책의 변경은 없다.

실제 PostgreSQL 16.15/SCRAM에서 같은 실패1개/0.68초를 재현했다.
`f9c4bc9`은 해당 시험의 import와 기대값만 수정한다. 일반 `ValueError` 대신
정확한 `MarketCandidateDenied`와 전체 메시지를 확인한다. 제품 코드·workflow·gate는 변경하지 않았다.
같은 파일5개/2.81초가 통과했고 두 실행 모두 남은 시험 role/schema/비밀번호 파일0,
PG 정지·private cluster와 admin 비밀번호 파일 제거를 확인했다.
전체 backend 실행이나 수정 SHA의 hosted CI 성공으로 보고하지 않는다.

실제 현재 `gpt-6.1-sol / xhigh` CLI 문맥·로그 해시·원 실패·재현/수정·정리 증거는
[불변 receipt](artifacts/market-candidate-read-authority-assertion-reference-20261006.json)에 있다.
재귀 CLI 실행은0회이고 source 연구나 농장 검증을 새로 승인한 결과가 아니다.
현재 원 `d61bcb3`의 나머지 분할을 보존하며, 전체 종료 뒤 새 판본의 CI를 확인한다.
실제 작물 Run·국내 독립 자료0건과 G0–G4 `not_assessed`를 유지한다.
