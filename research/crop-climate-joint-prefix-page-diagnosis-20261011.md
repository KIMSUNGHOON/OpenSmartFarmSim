# 확정 생장 페이지503의 실제 분류 — 2026-10-11

**P6a1 원인 분류를 수용했다. 제품 reader 수정·실제 계산 중 WebGL·사용자 prefix 활성화는 아직 미수용이다.**
[기계 증거](artifacts/crop-climate-joint-prefix-page-diagnosis-reference-20261011.json)의 SHA-256은
`36cb4052f6d0ed6982b7a1625020ac6a44296eac7b48e6543714d1071325fb10`다.
이전 goal turn은 corebb67a60/c3faf55·실제 event200·두 화면 복구의 **progress**로 분류했다.
이번 판단은 실제 native Codex CLI `gpt-6.1-sol`/`xhigh`의2026-10-11T03:52:23.310Z turn context에서 수행했고 재귀 CLI는0이다.

## 실행 범위

[이전 실제 브라우저 v9](crop-climate-joint-progress-prefix-retry-20261011.md)는 accepted summary/event200 뒤 samples503과 running WebGL assertion 실패를 기록했다.
v9에는 내부 예외 위치 기록이 없으므로 그 단일 응답의 원인을 사후 확정하지 않는다.
같은 `c3faf55` reader/runtime 소스로 별도 임시 DB·실제 SCRAM/검증 TLS·chunk8의 독립 자동 작업자에서 순차 조회를 재현했다.
API 스레드에만 예외/함수 소요 시간과 DB/HEAD 메타데이터 차이 기록을 넣었다. 작업자는 tracing·pause·계산 지연 없이 실행했다.
원 입력/권리 검증·수치 계산·게시 코드와 HTTP 응답은 수정하지 않았으며 API mock/가짜 frame은0이다.

| 실행 | 실제 관측 | 종료 |
| --- | --- | --- |
| v1 예외 위치/시간 | accepted summary2회·event200 1회·sample200 0회·503 6회 |작업 succeeded·worker0·pytest/guard0 |
| v2 HTTP/DB/HEAD 차이 추가 | accepted summary1회·같은 selector event200/sample200 각1회·503 6회 |작업 succeeded·worker0·pytest/guard0 |

이는 **같은 합성 모델 시나리오의 진단2회**이며 새 회귀2개나 실제 UI 통과로 세지 않는다.
v2의 두 페이지는 작업 상태 `simulating`에서 받은 이전 수용 판본이다. 당시 파일 HEAD에는 이미 terminal artifact가 있었으며 실제 수치 적분이 계속되는 장면을 관측한 것은 아니다.
원 terminal 값과의 binary64/UTC 대사와 브라우저/WebGL은 이번에 실행하지 않았다.

## 보류를 일으킨 지점

| 현재 코드 | 실제 차이 | 분류 |
| --- | --- | --- |
| [prefix reader read:250](../backend/app/crop_climate_joint_prefix.py#L250) | queued→simulating, attempt/lease 변경 |작업 수명 변경; 보류 유지 대상 |
| 같은 DB bundle 검사 | state/attempt/input을 유지하고 `lease_until`, `updated_at`만 변경 |임대 갱신도 전체 행 불일치로 거부 |
| [read:261](../backend/app/crop_climate_joint_prefix.py#L261) | DB probe 뒤 현재 HEAD가 commit1→2로 전진 |정상 private tail 전진도 전후 HEAD 불일치로 거부 |
| [HTTP 후검사:34](../backend/app/api_crop_climate_joint_prefix_routes.py#L34) | 같은 simulating 작업의 `lease_until`, `updated_at` 변경 |직렬화 후 public job.updated_at 비교에서 거부 |
| DB bundle 검사 | simulating→succeeded와 lease 해제 |종료 전환; 보류 유지 대상 |

v1의 두 samples503은 각각 final HEAD 변경과 DB bundle 변경에서 발생했다.
v2는 초기 lease-only 변경과 HTTP 후검사, 정상 HEAD 전진, 실제 시작/종료 전환을 별도로 기록했다.
예외 전파의 반복 기록과 정상 `StopAsyncIteration`을 별도 root failure로 세지 않는다.
수치 오염이나 방정식 실패를 관측한 것은 아니다. 두 작업은 모두 첫 시도에 정상 종료했다.
v9의 원 응답을 이 위치 중 하나로 단정하지 않고 재현 경로의 직접 증거로 사용한다.

## 조회 시간

v1의 성공 HTTP는 약5.86–10.45초, v2는 약6.11–11.26초였다. API tracing을 포함한 진단 측정이며 무계측 성능 보장이 아니다.
v1의 query `_current`는50회·각 최대1.235초였고 custody `_guard`는21회·각 최대1.155초였다.
같은 실행의 storage `_load`는6회·최대0.0225초였다. 현재 비용의 대부분은 반복된 입력/권리 검증 경로에 있다.
기계 기록의 함수 시간은 **inclusive**이므로 상위/하위 함수 시간을 더해 전체 시간으로 보고하지 않는다.
다음 수정은 검증 호출을 줄이는 성능 최적화부터 시작하지 않는다. 먼저 무관한 임대 갱신과 실제 결과 무효화를 구분한다.

## 보존·자원과 공개 reference

두 사용자 서비스를 중지하지 않고 보호 root4개와 그 동적 자손을 포함해 검사했다.

| 범위 | wall | 단일/합산 최고 RSS(bytes) |
| --- | --- | --- |
| 실제 진단 v1 |112.514초 |151,101,440 /1,069,514,752 |
| 실제 진단 v2 |117.263초 |151,023,616 /1,059,700,736 |
| 공개 reference collection |2.167초 |136,744,960 /705,585,152 |

모두 단일512MiB/합산1GiB 상한 안에서 실제 exit0이었다. v1의 합산 여유는 약4MiB였으므로 후속 native 검사도 순차 실행한다.
원본2,148항목·두 frozen source/자산·보호 프로세스 보존, FD4→4·소유 프로세스/PG/passfile 잔여0을 확인했다.
사용자 저장소에 새 작업을 접수하지 않았고 두 진단 작업은 별도 임시 DB에서 종료·정리했다.

[공개 진단 reference](crop-climate-joint-prefix-page-diagnosis.py)는 실제 v2 private 파일에서 workspace 경로 산출1곳만 바꿨다.
정규화한 source bytes 동일·현재 ROOT 경로 일치·실제 pytest collect1개/exit0을 확인했다.
**공개 파일 자체의 native 실행은 재실행하지 않았다.** 실제2회의 원 source SHA와 복사 후 diff/collection 증거를 구분해 기록했다.
이 reference는 조사 도구이며 제품 기능이나 상시 CI 시험으로 수용하지 않는다. 실제 데이터/자격증명은 공개하지 않는다.

## 다음 한 단계

[P6a2a 설계](../contracts/crop-climate-joint-prefix-progress-guard-v1.md)는 **prefix의 임대 갱신만 구분하는 버전 고정 snapshot guard**다.
reader/HTTP2 core와 대응 reader/HTTP test2파일을 대상으로 한다. 실제 독립 heartbeat를 조회 중과 직렬화 후에 일으키는 red/green을 먼저 확인한다.
같은 입력/attempt/lease token/state/선택 판본과 모든 다른 job 필드를 고정하고, 정상적인 두 시각의 단조 전진만 허용한다.
취소·재시도·종료·입력/선택/권리/서명 변화는 계속 거부한다. 현재 E6 진행 DTO와 writer/수치/입력/결과 형식은 변경하지 않는다.
HEAD 변경 검사는 이 자식에서 유지한다. P6a2a 뒤 실제 trace가 여전히 HEAD 전진 때문에 화면을 막으면 별도 P6a2b로 분해한다.

다음 자식의 구현/집중 회귀는 **1–2집중시간 잠정**, 연속 작업 시2026-10-11 KST 범위다.
그 뒤 실제 P6 전체 경로0.5–1.5시간·P6b0.5–1시간은 앞선 관측에 근거한 잠정 범위이며, HEAD 후속 수정 여부는 아직 미확정이다.
계산 중3D의 완료 날짜는 P6a2a의 실제 재검증 뒤 갱신한다. 독립 농장 자료·전체 작기/생산량·자원·경제·최종 UI 완료일은 이 단기 조사로 확정하지 않는다.
두 화면의 접속 방법은 [기존 안내](../web/README.md#joint-execution-user-preview)를 유지한다.
운영 기반 완료 범위·원본/권리·remote hold는 유지했다. 실제 crop Run0/독립 현장 자료0, G0–G4 `not_assessed`, 생산/미래 마진/추천 hold다.
