# 수집 시험이 소유한 복사 비밀번호 파일 정리

2026-10-07 KST. [원 증거](artifacts/application-collection-passfile-cleanup-reference-20261007.json)에
실패 CI·동일 순서의 실제 PostgreSQL 재현/수정 검증·코드 SHA·정리 결과를 고정했다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI는 실행하지 않았다.

## 실패와 원인

`2daa99f`의 [Backend 분할1](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37574780524/job/112641108430)은
751개 본문 통과 뒤 현재 조회 module의 종료 정리에서1오류/2354.58초로 실패했다.
스키마·역할은0이었지만, 앞선 수집 시험의 `collection/authority.pgpass`가 남아 있었다.

`scripts/application-collection-fixture.py`는 별도 수집 실행 환경용으로 시험 로그인
비밀번호를 복사한다. `login_scope`는 자신이 만든 원 파일만 정리하므로,
그 복사본은 수집 시험이 정리해야 한다. 뒤의 조회 시험은 같은 pytest 임시 기반
전체에서 비밀파일 잔존을 검사해 이 복사본을 발견했다.

다음 두 기존 시험을 실제 disposable PostgreSQL16.15/런타임 SCRAM에서 순서대로 실행했다.

```text
tests/test_application_collection_fixture.py::test_private_collection_parent_uses_same_login_and_tenant
tests/test_crop_cycle_current_query.py::test_source_withdrawal_inside_final_input_rights_review_cannot_return
```

수정 전 **2통과·종료 정리1오류/75.69초**, pytest 종료1로 동일 문제를 재현했다.
로컬 재현이 남긴 복사본도 해당 경로의 소유를 확인한 뒤 제거했다.

## 수정과 검증

수집 시험의 준비·실행·검사에 `try/finally`를 적용했다. 정상 종료 또는 예외에
그 시험이 소유한 복사본1개만 삭제한다. 수집 fixture의 실행 코드와 기존 검사는 유지했다.
별도 실패 주입 시험은 실행하지 않았고, 예외 경로는 `finally` 구조로 검토했다.

- 수정 후 동일 순서 **2통과/75.53초**, pytest 종료0.
- 전체 임시 기반의 잔존 비밀파일·스키마·역할 모두0.
- 시험 PostgreSQL PID와 data directory 부재 확인.
- 기존 수집 시험의 모든 연산·assertion을 AST로 대사했다.
- 현재 조회 정리 fixture와8개 시험의 bytes는 변경하지 않았다.
- 실행 중인 전체166일의 고정55개 source와 과거 조회/시작 영수증은 보존했다.

새 시험 node·제품 코드·pipeline 변경은 없다. 전체 backend 로컬 재실행과 새 hosted CI
수용은 이번 증거에 포함하지 않는다. 관측 당시 기존 CI의 다른4workflow는 성공했고,
Backend 분할0 성공·1 실패·2/3 실행 중·4/5 대기였다. 기존 실행을 취소하거나 재시도하지 않았다.
수정의 hosted 검증은 진행 중인 기존 CI가 종료된 뒤 별도로 확인한다.

## 다음 단계

이 수정은 전체 작기 계산→저장→같은 UTC3D 검증에 필요한 시험 정리 결함을 해결한다.
운영 기반 `d19f7c0`과 원 수식·실행 한도는 유지한다. 같은166일 실행의 실제 종료·
모든 출력/사건·수지와 복원을 확인한 뒤 전체 저장/조회/3D를 검증한다.
생과 환산·자원·경제 연결과 실제 품종/국내 독립 자료 확보는 계속 남아 있다.
실제 작물 Run·채택 입력·국내 독립 자료는0건, G0–G4는 `not_assessed`다.
