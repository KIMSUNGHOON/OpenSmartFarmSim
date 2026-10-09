# 권한 서버 시험의 복사 비밀번호 파일 정리

2026-10-07 KST. [불변 검증 기록](artifacts/application-authority-passfile-cleanup-reference-20261007.json)에
실패 CI·실제 PostgreSQL 재현·수정과 source/로그 SHA·정리를 기록했다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI 실행은0회다.

## 실제 실패와 수정

`8d111f1`의 [Backend 분할0](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37604499282/job/112736579454)은
현재 조회 시험의 module 정리에서 실패했다. schema/role은0이었지만 앞선
`test_private_authority_policy_retains_actual_invocation_and_registry_hold`가 만든
`authority/authority.pgpass`와 `supervisor/supervisor.pgpass` 두 복사본이 남았다.
원 `login_scope`는 자신이 만든 파일만 지우므로 복사본은 소유 시험이 정리해야 한다.

다음 두 기존 node를 같은 순서로 실제 disposable PostgreSQL16.15/SCRAM에서 실행했다.

```text
tests/test_application_authority_fixture.py::test_private_authority_policy_retains_actual_invocation_and_registry_hold
tests/test_crop_cycle_current_query.py::test_source_withdrawal_inside_final_input_rights_review_cannot_return
```

수정 전 **2통과·종료 정리1오류/66.85초**, pytest 종료1로 같은 `0 == 2`를 재현했다.
원 준비/실행/검사 전체를 `try/finally`로 감싸 정상·예외 종료에 두 소유 복사본만 삭제했다.
준비 도중 예외도 정리 범위에 들어간다. 기존 모든 연산·assertion의 AST가 그대로임을 대사했다.
뒤 조회의 전체 임시 기반 비밀파일 검사는 유지했다.

수정 후 같은 순서 **2통과/66.25초·종료0**이다. 두 실행의 schema/role 정리와
수정 후 passfile0, 네 실제 PG PID/data·소유 임시 test tree 제거를 확인했다.
실패 재현의 두 잔존 복사본은 경로 소유를 대사한 뒤 해당 두 파일만 제거했다.
현재4 source는 각 실행 전후에 같으며, 원166일55 source도 보존했다.

## 수용 범위

새 시험 node·제품 코드·CI 설정은 추가하지 않았다. 별도 예외 주입·전체 backend 로컬 회귀와
수정 판본의 hosted CI는 실행하지 않았다. 실패한 CI를 취소/재시도하지 않았고
기존 실행 종료 뒤 정상 push에서 수정 판본을 따로 검증한다.

이 수정은 작물 계산·저장·3D 검증을 막은 실제 시험 정리 결함을 해결한다.
운영 기반 `d19f7c0`과 원 수식/한도를 유지하며 생산 예측·추천과 G0–G4는 계속 미수용이다.
