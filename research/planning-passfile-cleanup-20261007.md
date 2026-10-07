# 계획 로그인 시험이 소유한 비밀번호 파일 정리

2026-10-07 KST. [불변 검증 기록](artifacts/planning-passfile-cleanup-reference-20261007.json)에
실패 CI·실제 PostgreSQL 재현·수정 후 정리와 코드 SHA를 고정했다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI는 실행하지 않았다.

## 실패 원인

`2daa99f`의 [Backend 분할4](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37574780524/job/112641108214)는
541개 본문 통과·3,797개 제외 뒤 종료 정리1오류/1,926.68초로 실패했다.
현재 조회 TLS 시험이 가져온 기존 정리 fixture는 전체 pytest 임시 기반에서
비밀번호 파일6개를 발견했다. CI traceback의 경로 목록은 pytest가 일부 생략했다.

앞선 `test_cli_temporal_precision.py`의 세 stage는 `test_planning_roles.py`의
`scope`를 사용한다. 이 fixture는 실행마다 authority/supervisor 파일을 만들고
DB 역할·스키마만 제거했다. 세 실행의 여섯 파일이 뒤 조회 정리까지 남았다.

다음 기존 node를 같은 순서로 실제 disposable PostgreSQL16.15에서 실행했다.
런타임 접속은 SCRAM이며 각 module의 두 임시 cluster를 사용했다.

```text
tests/test_cli_temporal_precision.py::test_signed_server_microsecond_context_is_usable_without_truncation
tests/test_crop_cycle_current_query.py::test_source_withdrawal_inside_final_input_rights_review_cannot_return
```

수정 전 **4통과·종료 정리1오류/64.52초**, pytest 종료1로 동일한 `0 == 6` 실패를 재현했다.
각 stage의 여섯 경로를 직접 기록했고, 소유 경로를 확인한 뒤 해당 파일만 제거했다.
재현에 사용한 두 PostgreSQL 프로세스와 data directory도 종료 후 없었다.

## 수정과 검증

소유 fixture가 생성할 파일을 쓰기 전에 목록에 넣고, DB 정리의 바깥 `finally`에서
그 파일만 삭제한다. DB 정리 실패도 파일 정리를 건너뛰지 않는다.
전체 임시 기반을 지우거나 뒤 조회 검사를 완화하지 않는다.

- 수정 후 같은 순서 **4통과/65.98초**, pytest 종료0.
- 기존 전체 기반 정리 검사에서 비밀번호 파일·스키마·역할 모두0.
- 두 PostgreSQL PID와 data directory의 종료 후 부재 확인.
- 기존 시험 본문과 원 DB 정리 SQL subtree를 AST로 대사했다.
- 현재 조회 정리·TLS 시험·시간 정밀도 시험·로그인 DB fixture bytes 보존.
- 실행 중166일 계산의 고정55개 source SHA 보존.
- 로컬 링크/anchor2,600개·의존성 DAG107/89edge의 비순환과 `git diff --check` 통과.
  선행 수용 영수증을 다시 대사했으며 그 영수증의 과거 시험들을 재실행한 것은 아니다.

첫 AST 진단은 중첩 변경으로 순회 순서가 달라져 실패했고, 원 정리 subtree와
SQL 호출 multiset을 별도로 대사해 통과했다. 첫 CI 경로 전수 조회도 생략된 repr 때문에
실패했으며, 실제 로컬 재현 경로로 소유를 확인했다. 사설 진단 기록을 영수증에 결속했다.

새 시험 node·제품 수식·pipeline 변경은 없다. 별도 DB 실패 주입과 원 TLS 본문 재실행,
전체 backend 로컬 재실행은 하지 않았다. CI의 TLS 본문은 통과했으며 이번 로컬 검증은
그와 같은 정리 fixture를 소비하는 작은 node를 사용했다.
고정된 기존 CI가 끝난 뒤 수정 커밋의 hosted 검증을 별도로 확인한다.

## 남은 범위

이는 전체 작기 계산·저장·같은 UTC3D 검증에 필요한 시험 정리 수정이다.
원166일 실행의 종료·복원·수지와 모든 출력, 전체 등록 농장/조회 성능은 미수용이다.
생과 생산량·자원·경제 연결 및 실제 품종/국내 독립 자료 확보가 남아 있다.
채택 입력·국내 독립 자료·실제 작물 Run은0건이며 G0–G4는 `not_assessed`다.
