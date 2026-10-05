# 작기 결과 runtime의 진행 증거

상태: **수용 전, 2026-10-06 KST**. 후보
`42523ec8b4c7966e6be592811ac7b8717635aa2f`는 명시 cycle flag/factory 짝과
같은 farm/jobs/principal의 exact store를 기존 runtime에 연결한다. 새 service/queue/schema는 없다.
순수 설정6개·기존 route41개가8.11초에 통과했고 이전 세 crop factory 옵션 시험3개도 통과했다.
실제 runtime/API 부모는 아직 완료로 표시하지 않는다.

최초 실제 SCRAM/Bearer/TLS 시험은 **1실패/496.00초**였다.
[고정 실패 증거](artifacts/crop-cycle-api-runtime-tls-hold-20261006.json)는 원 source hash,
실제 CLI `gpt-6.1-sol / xhigh`, private log hash와 정리를 보존한다.
extra worker SELECT grant의 live audit가 `RolePolicyHold`를 발생시켰고, route의 운영 오류
처리503은 정상 거부였다. 시험의422 기대를 실제 오류 계약에 맞춰503/고정 unavailable code로
수정했다. 작물/입력 근거 hold422와 요청 권한403의 처리는 그대로다.

실패 실행의 runner wall496.476776초, child peak RSS152.292969MiB였으며 역할·schema·
test password·owned server0, PostgreSQL 중지와 private cluster/admin password 삭제를 확인했다.
실패 이후 아직 실행하지 못한 file/DB 변조·두 번째 기동·마지막 row/FD 검증을 통과로 보고하지 않는다.
수정된 전체 짧은 통합 시험을 별도 임시 PostgreSQL/nice10에서 다시 실행 중이며,
새 성공/실패 영수증을 만든다. 기존 실패 증거를 덮어쓰지 않는다.

짧은 통합 시험 통과 뒤에도 실제 등록25시간 결과의 전체 HTTP30초/2MiB 예산은 별도로
측정해야 한다. 그 수용 뒤 client → 같은 ID/UTC 성장 연구3D → 작기 부하 → 근거 있는
생과·자원·경제 순서로 진행한다. 실제 품종/작기 입력·국내 독립 검증 자료0건,
실제 crop Run0건이며 G0–G4/생산 예측·추천은 미수용이다.
