# 새 잎 계산의 소유 미리보기 조립 — 2026-10-23

상태: **별도 합성 시험 DB의 실행 파일 조립 수용**. 사용자 runtime 배포·제품3D 연결은 아직 후속이다.
[기계 증거](artifacts/owned-leaf-population-preview-20261023.json)에 실제 native Codex CLI
**gpt-6.1-sol / xhigh**의 turn_context 지문과 재귀 실행0을 기록했다.

## 구현

기존 `serve-owned-morphology-preview.py`에 선택적 `leaf_population` 설정을 추가했다.
`owned_leaf_population_preview.py`가 기존 parent query의 같은 jobs/provider/farm·stem 입력 authority를 사용해
현재 leaf 입력/검토·권리, 서명 결과, 접수/query와 정확한 leaf worker loop를 조립한다.
기존 줄기 loop도 유지하며 각 background principal은 원 BearerRegistry의 현재 유효성을 확인한다.
새 큐/표 정의·역할 정책·패키지와 backend/app/OpenAPI 변경은 없다.

설정은 owned-leaf-population-preview-v1의 닫힌 필드 집합이며 원 자료/키는 보호 파일에서만 읽는다.
resolver는 tenant와 정확한 input 참조를 확인하고 매번 원 bytes를 다시 읽는다.
권리는 정확한 선언/원본과 현재 허용 상태·계산/표시 목적을 확인한다.
옵션이 없으면 기존 줄기 전용 미리보기 경로를 유지한다.
설정된 `/leaf-preview-input`은 현재 인증/쓰기 Scope와 양 끝 binding을 검사해 닫힌 요청·표시 이름만 반환한다.
이는 운영자 소유 합성 입력 선택이며 일반 지역/작물 입력 목록이나 승인 자료가 아니다.

## 통과한 검증

| 범위 | 고유 검사 | 실제 확인 |
| --- | ---: | --- |
| 제어 | 12 | 미설정 보존, 부분/미래/추가 설정·잘못된 경로 거부, tenant/원 참조 결속·원 bytes 재조회, 현재 권리 철회 |
| 실제 실행 파일·SCRAM·검증 TLS | 3 | 두 작업자 자동 실행/원 결과·cold restart, 파일 철회/취소, 기본 줄기 모드/SIGINT 종료 |
| **합계** | **15** | 실패와 같은 검사의 반복은 합산하지 않음 |

실제 Python 실행 파일을 별도 자식으로 기동하고 인증서를 검증하는 HTTPS로 접수했다.
leaf 작업은 자동으로 **1개 완료 attempt**를 게시했다. 원 **12시점/52잎 면적의 전체 frame bytes**와
parent 결과를 대사했다. 같은 DB·키로 재시작한 뒤 result/최초 calculated_at/replay가 같았고 추가 POST는0이었다.
양쪽 서버 종료에서 두 loop의 join/종료0을 확인했다. 직접 수치 진입 횟수 계측으로 확대하지 않는다.

현재 권리 파일 철회와 source bytes 변경은422였다. 권리 철회 후 실제 취소가200/canceled였고 결과 참조를 게시하지 않았다.
leaf 옵션 없는 실제 실행은 원 입력/완료 줄기 결과를 조회하고 새 leaf 경로는 노출하지 않았다.
이 기본 모드는 SIGINT 뒤 원 작업자1개를 정리하고 종료0이었다.
각 시험의 새 job 관련 행을 제외한 **25표의 모든 원 행 SHA**를 보존했고 cold restart 자체의 DB 행도 전후 같았다.

실제 단일 요청은 모두 기존30초 안이었다. 최장은 **28.752849초**, 원 replay는67,660bytes였다.
이는 소유 시험의 관측이며 공통 U1/동시 사용자 용량이나 G4 수용이 아니다.

## 첫 실패와 수정

첫 native 실행의 자동 완료/조회 뒤 SIGTERM 종료가-15여서 전체 시험을 미수용으로 보존했다.
설치된 Uvicorn0.54.0의 capture_signals는 원 handler를 복원한 뒤 신호를 다시 전달한다.
[같은 판본의 공식 source](https://github.com/Kludex/uvicorn/blob/0.54.0/uvicorn/server.py)와 설치 파일 지문을 대조했다.
호출자 handler에서 stop/서버 종료를 설정하고 모든 loop를 join한 다음 원 handler를 복원하도록 수정했다.
종료 코드를 허용 목록에 추가해 실패를 숨기지 않았으며, 최종 SIGTERM/cold restart·SIGINT를 실제 재검증했다.

.25초 표본의 최대 PID RSS는 **131,588,096bytes**, 보호+소유 합은 **504,340,480bytes**였다.
각 단계 PID512MiB/합1GiB·600초 이내였고 원2root/2,469감시 항목을 보존했다.
실패 단계까지 소유 PG/schema/role/temp/passfile·프로세스 잔여0, controller FD4→4를 확인했다.
Windows Chrome은 이 WSL 용량 증거에 포함하지 않았다.

전체 backend suite·이번 hosted CI·브라우저/사용자 배포는 미실행이다.
확인한 최근 웹 CI39870510699의 성공은 이전 source7d3d4d5의 기록이며 이번 변경의 CI 통과로 세지 않는다.

## 다음 사용자 확인점

다음은 새 판단 시각의 별도 retrospective 합성 farm/실제 완료 parent·보호 파일/키를 준비하고,
검증한 source를 불변 배포해 사용자 endpoint에서 같은 자동 완료/원 결과를 확인하는 단계다.
기존 과거 farm/job을 새 자료로 덮거나 소급 부착하지 않고 원 작업·DB/키·두 화면을 보존한다.
그 뒤 strict SDK→같은 job의 사실적 잎3D·UTC/표/그래프와 메뉴/reload·재연결/철회 제거를 연결한다.
남은 분해와 낮은 신뢰 추정은 [실행 계획](../tasks/plan.md#소유-leaf-runtime-조립-수용--2026-10-23)에 기록했다.

[현재5176 화면](http://localhost:5176/leaf-population-replay.html)은 여전히 저장 합성3→6잎 연구 재생이다.
실제 Axiany 계수/초기관측·독립 현장 작기0/승인 farm Run0, 전체 작기·생산/자원/경제/자율 선정,
최종 사실감 R2/첫 셰이더 경고·G0–G4와 전체 완료일 미정을 유지한다.
