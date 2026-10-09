# 검증 계산 결과의 인증 경로·OpenAPI — 로컬 수용

2026-10-07 KST. [개발 계약](../contracts/api-crop-cycle-calculation-transport-v1.md)의
route/OpenAPI 자식만 로컬 소프트웨어 범위에서 수용했다.
[고정 영수증](artifacts/crop-cycle-calculation-route-openapi-reference-20261007.json)은 실제 native Codex CLI
`gpt-6.1-sol / xhigh`·재귀 CLI0회·명령/종료/source/로그 SHA와 정리를 보존한다.
실제 설정/runtime/TLS·새 route의 DB 권한·같은 UTC3D와 G0–G4 수용은 후속이다.

## 변경과 검토

[새 인증 경로](../backend/app/api_crop_cycle_calculation_route.py)는 별도 verified result ID를 받는다.
exact 새 store/query·same jobs/farm/principal을 확인하고 기본 비활성은503이다.
한 current query 문맥에서 원 record/terminal/page를 투영·byte 제한한 뒤 문맥의 현재 권리/bytes 검사를
마쳐야 응답한다. threadpool 뒤 인증/tenant도 다시 확인하고 구형 읽기로 우회하지 않는다.
기존64/8 page·엄격한 query/body/ID·고정401/403/404/422/503과 no-store를 유지한다.
응답에는 원 schema/ID/validation·값/UTC와 새 query version/code SHA header가 있다.

[API 조립](../backend/app/api.py)의 AST는 새 import·기본 None인 두 읽기 인자·installer 호출을
제외하면 원 판본과 같다. 운영 runtime은 아직 이 두 인자를 전달하지 않으며 다음 자식에서 연결한다.
기존48 path/148 schema와 나머지 OpenAPI 선언을 모두 대사했고 새 path1개/schema8개만 추가했다.
실제 공식 Python exporter `--write`와 회귀의 credentials 없는 별도 `--check`가 통과했다.
기존 OpenAPI 시험7개 함수 중 새 ID/query를 추가한 권한 시험 하나만 달라졌고 기존 권한 assertion은 유지했다.
계산·저장·현재 조회·원 공개 투영·operator loader/runtime와 선행 시험 **78 source SHA는 전후 같다**.
정확성·가독성·구조·보안·비용을 검토했고 새 서비스·계수·CI/HTTP 한도 변경은 없다.

## 실제 검증

| 실행 | 결과 |
| --- | --- |
| 새 경로 기본 비활성 RED | 404 관측·1실패/0.93초·종료1 |
| 경로 연결 뒤 같은 사례 | 1통과/0.89초·종료0 |
| 새 route 전체 | **63통과/8.77초·종료0** |
| 기존 경로/OpenAPI/runtime·설정 회귀 | **221통과/127.87초·종료0** |

최종 source가 같은 **고유284개 분할 검증**이다. 회귀221개에는 새 OpenAPI operation의 권한 사례도 포함된다.
반복 기본 시험을 더하지 않으며 단일284개·전체 backend 수용은 아니다.
원 수치 artifact를 만든 뒤 parser/context/QC/RHS를 금지하고 ASGI의 정상 summary/samples/events에서
원량·UTC·validation과 한 문맥·bytes 뒤 current check·닫힘·FD12→12를 확인했다.
기록한 정상 공개 JSON은 summary9,489bytes/samples27,842bytes/events53,926bytes다.
이 크기는 canonical JSON 관측이며 실제 TLS 전체 본문/지연 측정은 아니다.

확인 과거 hold는60걸음/1시점/1사건, 빈 hold는0걸음/0시점/0사건이며 원 진단·확인 과거를 보존했다.
알 수 없는/중복 query·비정규 offset/limit·body·구형 ID·누락 권한은 읽기 전에 거부했다.
현재 읽기/종료 시점의 permission·작물 hold·운영 grant 오류·일반 오류와
투영 중 source/credential/tenant 변경에서 stale payload를 반환하지 않았다.
schema-only 기본 시작과 세 별도 Python import 순서에서 새 계산/store/query는 로드되지 않고 FD4→4였다.

route 시험의 custody는 exact 타입 객체에 격리한 읽기 제어 흐름을 붙인 stub이다.
자작 artifact의 수치 계산을 사용했지만 실제 farm/DB 권한이나 네트워크 TLS 증거는 아니다.
기존 회귀의 실제 SCRAM 조립과 새 route의 DB 연결을 구분한다.
nice19·소유 PG3개 순차 실행의 PID/data 부재·비밀번호0개·임시 tree 정리를 확인했다.
새 시험 주 프로세스의 표본 최대 RSS139,796,480bytes는 PG 합산 또는 WSL 전체 peak가 아니다.
계약 수용 절은 시험 후 추가했으므로 영수증 계약 SHA는 시험 당시 판본이다.

## 다음 한 단계와 보류

다음은 [runtime/TLS3 core파일](../contracts/api-crop-cycle-calculation-transport-v1.md)의 명시 조립이다.
원 loader/helper/서명 이력은 보존하고 실제 protected config에서 새 store/query를 `create_app`에 전달한다.
실제 SCRAM/TLS 정상/사건/확인 과거·빈 hold·순차 페이지·재기동·철회/변조/운영 오류·30초/2MiB·정리를
확인한 뒤 API 부모를 수용한다. **남은 작은 API2–3집중시간 잠정**이며 실제 수용 뒤 client/3D 추정을 갱신한다.
전체166일 등록 prefix/복원 비용·생과/자원/구매 에너지·Decimal 경제와 자료 확보는 이 추정 밖이다.

remote `353bffb` Backend는3분할 성공/2진행/1대기 중으로 관측했고 새 push는 없다.
기존 앱 설정 생성 호환 보완·이번 변경의 hosted 수용도 남아 있다.
실제 품종 입력·국내 독립 검증 자료·작물 Run0건, G0–G4 `not_assessed`이며 예측·추천/최종 날짜는 보류다.
