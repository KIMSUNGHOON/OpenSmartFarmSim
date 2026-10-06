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
수정된 전체 짧은 통합 시험은 별도 임시 PostgreSQL/nice10에서 **1통과/559.86초**였다.
[새 영수증](artifacts/crop-cycle-api-runtime-short-reference-20261006.json)에 실제21응답·
최대27.871882초/18,718bytes·120걸음/원3시점/사건0개·정상/빈 hold와 서버2회 종료를 고정했다.
file/DB HMAC 변조·현재 입력/source 철회·DTO 뒤 철회·live grant drift·재기동을 검증했다.
child peak157.035156MiB, custody FD/역할/schema/test password/server0와 임시 PG 삭제를 확인했다.
순수47개/기존 옵션3개와 합쳐 고유51개 분할이며 단일51 GREEN은 아니다.
원 사건0개인 짧은 시험이므로 실제 nonempty event 페이지는 다음 긴 결과에서 검증한다.
기존 실패 증거를 덮어쓰지 않았다.

등록25시간의 첫 실제 긴 시험은 **1실패/2616.58초(43분36초)**였다.
[새 고정 실패 증거](artifacts/crop-cycle-api-runtime-long-tls-hold-20261006.json)의
`654929f`에서11,400걸음 completed와 DB put까지 진행했고, 첫 SSL handshake에서
시험 인증서 만료로 실패했다. 공유 `tls_files`는10분 유효하며 계산 전에 발급됐다.
HTTP header/body를 받기 전 실패라서 전체 응답0개, 원 페이지 대사·재기동·30초 예산은 미측정이다.
독립 control flow 계산과 API 원값 대사 완료도 구분한다. worker/HTTP 예산 초과로 보고하지 않는다.
runner2617.197402초/child peak126.394531MiB, 역할/schema/test password/server0와
PostgreSQL 중지·private cluster/admin password 삭제를 확인했다.
수정 후보는 같은 시험의 기존 TLS fixture를 계산·DB put 이후 `request.getfixturevalue`로
발급한다. shared fixture·10분 유효기간·SSL 검증·HTTP30초/2MiB·worker128전이는 그대로다.
제품 소스/계수·서버 저장 알고리즘을 변경하지 않았으며 수정된 실제 긴 시험의 완료 증거는 아직 없다.

계산 뒤 TLS를 발급한 수정 판본의 같은 긴 시험은 **1실패/2789.54초(46분29초)**였다.
[별도 HTTP 실패 증거](artifacts/crop-cycle-api-runtime-long-http-hold-20261006.json)는
`c27d8c5`의 source3개와 실제 CLI·로그 해시, runner2790.037117초/child peak139.65625MiB를
보존한다.11,400걸음과 DB put, 검증 TLS의 첫 summary/30초·2MiB/FD·27시점/5사건 수 확인을
통과한 뒤 페이지 응답의 status line을 기다리다가 socket30초 읽기 시간 초과로 실패했다.
실패 페이지 종류/offset·부분 응답 개수/시간/bytes는 기록되지 않아 특정 페이지로 단정하지 않는다.
원 페이지 전체 대사와 재기동은 미완료이며 성공 전용 decoded JSON도 생성되지 않았다.
역할/schema/test password/server0와 PostgreSQL 중지·private cluster/admin password 삭제는 확인했다.
인증서 만료와 별개의 응답 예산 실패다. 기존30초/2MiB를 유지하고 custody/API 페이지 읽기 작업을
진단하며, 다음 실제 시험에는 실패 직전 부분 호출 근거도 보존해야 한다.

짧은 통합 시험 통과 뒤에도 실제 등록25시간 결과의 전체 HTTP30초/2MiB 예산은 별도로
측정해야 한다. 그 수용 뒤 client → 같은 ID/UTC 성장 연구3D → 작기 부하 → 근거 있는
생과·자원·경제 순서로 진행한다. 실제 품종/작기 입력·국내 독립 검증 자료0건,
실제 crop Run0건이며 G0–G4/생산 예측·추천은 미수용이다.
