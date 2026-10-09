# 수확 보존 자격증명 시험의 잔여 파일 정리

2026-10-09 KST. [8dd386d CI 실패](crop-result-ci-terminal-20261009.md)의 분할1 원 로그는
`test_registry_credentials_are_private_and_cannot_overwrite_existing_file`의 `reader.pgpass` 하나를
뒤의 로그인 감사가 검출했다고 기록한다. [계약](../contracts/crop-harvest-storage-test-cleanup-v1.md)과
[원 종료·source·정리 영수증](artifacts/crop-harvest-storage-test-cleanup-reference-20261009.json)에 따라
**해당 단위 시험의 파일 누수만 로컬 수용**한다.
native Codex CLI `gpt-6.1-sol / xhigh`의 실제 turn/output을 기록했고 재귀 실행은0회다.

## 같은 순서의 실패와 통과

별도 소유 PG16.15/SCRAM과 같은 pytest/basetemp에서 원 자격증명 시험 다음
`test_actual_scram_and_server_audit_need_no_host_config_file`을 실행했다.
원82435는 종료1/2.897초,2통과·정리1오류로 **같은 경로의 passfile1**을 재현했다.
schema/role0 뒤 기존 전역 감사가 파일을 검출한 원 실패를 private 영역에 보존했다.

자격증명 시험에 `finally`를 추가해 자신이 만든 파일만 제거했다.
0600·기존 파일 덮어쓰기 거부·원 bytes 검사는 유지하며 제품 `pgpass()`는 변경하지 않았다.
전역 감사·다른 시험 파일·역할/schema 정리의 범위도 변경하지 않았다.

수정 후 두 모듈의 **17개 검사**와 생성 후 파일 권한 단언 실패 대조가 통과했다.
원86839는 종료0/3.650초이며 정상/실패 대조 모두 남은 passfile0이다.
기존 HBA 시험이 loader/runtime/TLS의 세 정리 감사를 실행해 schema/role/passfile0을 확인했다.
이 세 감사는 원 소스의 단언/실제 pytest 통과로 확인했으며 이번 실행의 별도 JSON 출력은 없다.
실제 SCRAM 접속과 host 설정 파일을 읽지 않는 검사도 유지했다.

원120초 상한, 시험 PG1개 정지·남은 pidfile0·소유 비좀비0과1,561 source/dist·보호4 identity를 확인했다.
표본 단일 RSS128,991,232bytes·전체 계산/미리보기 포함 동시 합630,591,488bytes다.
512MiB/1GiB 안이며 WSL 전체 메모리 측정은 아니다. 원 실패와 통과의 PG는 각각 별도다.

## 남은 범위

분할5의 `DROP OWNED` 교착과 그 잔여 감사는 이 파일 누수와 다른 문제로 남긴다.
수정 후 hosted PostgreSQL18·전체 Backend/독립 Linux UID는 아직 수용하지 않았다.
전체166일 복구 대사/게시/보존·UI 목록/브라우저/실시간 U3와 실제 품종·독립 농장 자료도 남아 있다.
실제 작물 Run0건과 G0–G4 미평가·생산/마진 예측·추천 hold는 유지한다.
