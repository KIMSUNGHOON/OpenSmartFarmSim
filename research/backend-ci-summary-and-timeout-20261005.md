# CI 요약 크기 수정과 기존 HTTPS 시간 초과 조사

날짜: 2026-10-05 KST. 작물 경로 CI의 관측·작은 보고 수정이며 운영 기반 확장이 아니다.
현재 Codex CLI `gpt-6.1-sol` / `xhigh`, 세션
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`, turn `2026-10-04T23:42:35.563Z`에서 수행했다.
재귀 CLI 호출·새 의존성·G0–G4 수용은 없다.

## 실제 실패와 재현

정확한 `e70a7f242d725c0bece9526ff44270caf320c6b6`의
[Backend 실행 37240870201](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37240870201),
파트 3 job `111549167188`은 **531개 통과·1개 실패·2,568개 미선택**,
1,876.90초였다. 기존 `test_authored_assessment_https.py`의 첫 인증된
`POST /v1/assessments`에서 응답 헤더를 읽다가 30초 제한으로 `TimeoutError`가 발생했다.
시작 fixture 253.23초, 실패한 call 31.26초였다. 다른 파트의 실행은 유지했다.
실패 원문은 비공개 `/tmp/ossf-ci-e70-part3-20261005.log`에 보존했다.
이 실패를 작물 수식/3D 결함 또는 단순한 호스팅 부하라고 단정하지 않는다.

동일 테스트를 로컬 `5e710e169e676ea157ef5e3fa29d51e9604766c5`에서 단독 실행했다.
관련 assessment·경제·작성 Run의 제품 코드와 해당 테스트는 실패한 e70 판본과 같다.
작은 임시 PostgreSQL 16.15/SCRAM, 실제 TLS/Bearer, 기존 시험용 CLI를 사용했다.
**1개 통과**, 10개 응답 본문 완료 최대 **22.118초 < 기존 30초**,
fixture 174.68초/call 154.06초, 전체 331.2501초였다.
2026-10-04T23:48:26.775152Z부터 23:53:58.025269Z까지 실행했고
서버·임시 DB·암호 파일을 정리했다. 로그 SHA-256은
`dcb38dbf1f3e3496cc07a0fa4f29eb05470cd65b15fa452e3194d754cc481a98`이다.
로컬 재현은 성공했지만 PostgreSQL 18 호스팅 실패의 원인을 확정하거나
운영 응답 시간/부하를 수용한 증거는 아니다. 호스팅 재시험은 별도 기록한다.
클라이언트 제한·권한 재검사·접수 commit guard·제품 코드를 변경하지 않았다.

## 요약 제한과 수정 수용

같은 job은 2.6MB의 전체 테스트 목록 요약 업로드도 거부당했다.
[GitHub의 단계 요약 제한](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#step-isolation-and-limits)은
1MiB이며, 이 업로드 오류가 job의 통과 여부를 결정하지는 않는다.
따라서 이 수정으로 위 HTTPS 실패가 해결됐다고 주장하지 않는다.

`scripts/backend-ci-partitions.py`는 파일의 **전체** `all_node_ids`/`selected_node_ids`,
전체 목록 SHA-256, 파트 소유·순서·실패 전파와 집계를 유지한다.
요약에는 판본·파트·전체 해시·수집/선택 개수만 기록한다.
관련 집중 **13개/7.73초**가 통과했다. 새 회귀는 실제 별도 pytest 수집으로
1,205개 목록/1,200개 선택·1MiB 초과 manifest가 완전하게 남고,
같은 해시의 요약이 4KiB 미만임을 검사한다. 필터/수집 오류/실패 전파와
저장소 전체 목록 반복 수집의 기존 검증도 통과했다.

최신 수정의 hosted 수용은 후속이다. 기존 운영 기반 고정 범위는 유지하고
다음 초기·착과 정책의 원천/독립 계산 조사로 돌아간다.

## 종료된 e70 CI 기록

Backend는 2026-10-05T00:10:14Z에 **failure**로 끝났다.
다섯 파트 성공/파트3 실패, 합계 3,099개 통과/1개 실패·별도 UID4 통과였다.
전체 3,100개 목록 해시는 여섯 파트에서 같고 DB/password 정리도 모두 성공했다.
집계 job도 실패했다. C0/Web/Application/Authored 네 workflow는 성공했다.
[정확한 terminal 기록](artifacts/crop-coupled-api-web-ci-hold-20261005.json)은 실패를 보존한다.
그 판본 뒤의 UI·startup·CI 요약 수정 수용은 새 정확한 SHA의 CI에서 별도로 확인한다.
이전 실행은 취소/재시작하지 않았다.
