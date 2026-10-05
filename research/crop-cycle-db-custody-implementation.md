# Cycle 계산 결과의 불변 DB 참조 — 로컬 수용

상태: **소프트웨어 범위 로컬 수용**, 2026-10-06 KST.
작업 `crop-cycle-db-custody`. [닫힌 게시 계약](../contracts/crop-cycle-db-custody-v1.md),
[서버 계산/서명 저장](crop-cycle-server-custody-implementation.md),
[원 표/권한](../contracts/crop-cycle-storage-v1.md)을 연결한다.
이번 DB child와 저장 parent는 아래76개 고유 분할 근거로 수용했다. API/client/3D parent는 열어 둔다.

## 구현 범위

`backend/app/crop_cycle_result_store.py`의 `CycleCropResultStore`는 이미 terminal인
서버 서명 결과만 기존 `crop_cycle_research_results`에 게시한다. 큰 입력/결과는
원 불변 파일에 두며 DB에는 canonical128KiB 이하의 닫힌 binding/progress/code 참조와
별도 domain/key의 HMAC을 둔다. 동일 retry는 최초 bytes/ID/시각을 보존한다.
현재 authority·flag/grants·농장/원천/입력 권리를 commit 전후 대사한다.
commit 뒤 철회된 private audit row가 남아도 현재 반환·표시 권한을 허용하지 않는다.

get/page/summary는 실제 서버 journal을 한 번 열어 현재 권리와 선택된 서명 HEAD를
대사하며 RHS/advance를 호출하지 않는다. summary는 원 manifest·수치 hold 사유와
확인된 과거를 그대로 읽는다. 파일 경로·사용자 제출 progress나 외부 artifact를 받지 않는다.
새 worker/queue·HTTP·schema/role migration·작물 Run은 이 변경의 범위 밖이다.
원 계산/저장/API/농장 결합/서버 실행49파일 hash를 보존했다.

## 실행·연구 근거

설계와 구현 판단은 현재 Codex CLI **gpt-6.1-sol / xhigh**에서 수행했다.
실제 `2026-10-05T12:31:45.220Z` turn_context 원 line SHA는
`35f44d2c1d7e32eb54a9ff5014d7221380df339ff168c3a061f043526af9d66d`다.
재귀 CLI0회이며 제품 런타임의 실제 CLI 수용을 이 개발 기록으로 대체하지 않는다.
순수 JSON fixture는 닫힌 형식만 시험하며 실제 농장/권리의 증거가 아니다.

초기 실행은60통과/1실패였다. artifact.sample_count의 `3.0`이 progress의 정수`3`과
Python 동등성에서 같아지는 실제 반례다. 대응 artifact를 canonical bytes로 비교하도록
수정해61개를 통과했다. summary 추가 뒤 동일61개도0.93초로 통과했다.
긴 참조의 `(result,state)` 반환을 unpack하는 수정은 실행 전에 발견한 시험 코드 수정이며
기능적 RED로 세지 않는다.

| 집중 실행 | 실제 결과 | 판본·범위 |
| --- | --- | --- |
| 순수 폐쇄 metadata | 61통과/0.93초 | 최종c182ba1d… module에서도 재통과; 실제 농장/DB 미포함 |
| 실제 SCRAM 짧은 게시/미생성·yielded 거부 | 2통과/344.15초 | summary 추가 전 code SHA76faa19f…; 현재 판본 전체 수용과 구분 |
| summary 최초 추가 후 짧은 게시/재시작·fork/거부 | 2통과/340.99초 | manifest 수정 전5c503da2…; 동일 원 bytes/ID/시각·읽기/게시 RHS0·정리 |
| 실제 commit 전후 철회·lock·hold·HMAC | 9통과/1,488.61초 | manifest 수정 전5c503da2…; 시험 source는ad9d3b0; roles/schema/password/서버 정리 확인 |
| 등록 농장25시간의 원 페이지 대사 | 1통과/2,732.14초 | manifest 수정 전5c503da2…/92advance/11,400걸음·독립 제어 흐름·7원 페이지·DB 참조·정리; 전체 실제 작기와 구분 |
| 실제 DB/파일 변조·현재 flag/grants | 1통과/152.11초 | 실제 행3종/파일4종·FD 보존·연구 row1/실제 Run0·권한 복구/원 조회·정리 |
| 최종 정상/hold manifest·기존 요약 중 철회 | 3통과/451.64초 | c182ba1d…; 새 고유2개+기존1개 재확인·RHS0·원 header/metadata·분리된 반환 복사·정리 |

고유76개 목록을 분할 실행과 대사했다. 순수61개와 실제 DB15개다.
최종3개 실행 중 기존 hold1개, 초기 판본2개와 순수 재실행은 중복으로 더하지 않는다.
경계9개는 quiet 로그의9통과와 실제 runner의 선택식/보존된ad9d3b0 시험 source로 대사했다.
다른 native 실행은 verbose의 실제 node ID를 대사했다. 단일76 GREEN/전체 backend GREEN으로 보고하지 않는다.

14:26:49.152Z의 같은 exact CLI 세션에서 API 계약과 실제 writer 형식을 대조해 추가 누락을 찾았다.
`writer._summary`는 원 commit metadata라 manifest가 없는데 현재 DB summary 함수는 그것만 복사한다.
정상/hold 모두 검증된 원 header/context.manifest를 함께 제공해야 계약을 충족한다.
25시간 판본을 고정해 통과·정리를 확인한 뒤 실제 정상/hold2개에서 manifest 누락을 재현했다.
2실패/280.45초와 실제 roles/schema/password·PG/cluster 정리를 확인했다.
검증된 원 context.manifest를 commit metadata와 함께 deepcopy하는 한 줄만 수정했다.
최종c182ba1d…/8c7e3d5에서 순수61개와 실제 정상/hold2개·기존 요약 중 철회1개를 확인했다.
정상18.013347초/hold17.194473초로 원 header manifest·원 metadata·반환 복사의 분리를 대사했다.
runner452.142495초/child 최대RSS123.375MiB, 실제 roles/schema/password0·PG종료·private cluster 삭제·owned server0이다.
새[최종 수용 영수증](artifacts/crop-cycle-db-custody-reference-20261005.json)은 이전 보류/진행 영수증과
초기1800초 중단·summary 수정 전 긴 참조를 보존한다. 수정 전 참조를 최종 판본의 단일 전체 실행으로 바꾸지 않는다.
로컬 Python3.12.3/PostgreSQL16.15의 증거이며 고정 hosted Python3.12.13/DB CI는 후속 판본에서 확인한다.

## 통과한 등록25시간의 실제 DB 대사

manifest 수정 전5c503da2… module에서300 forcing 구간·11,400계산 걸음·92advance의 terminal 결과를 게시했다.
독립 제어 흐름은 같은 고정 rates를 공유하며 원27시점/5사건을 canonical bytes로 대사했다.
sample4/event3의7개 원 페이지는18,145–61,591bytes, 각19.321246–19.459992초였다.
이는 저장소 직접 조회의 측정이며 다음 API의 실제 Bearer/TLS30초 통과로 보고하지 않는다.
불변 metadata6,528bytes·최초 ID/bytes/recorded_at retry·새 service를 확인했다.
게시와 조회 RHS0회, private 연구 row1/실제 crop Run0개다.

독립 계산105.101202초/서버 계산2,342.131896초/게시54.969514초/7페이지135.607444초였다.
전체 runner2,732.635748초, child 최대RSS125.23828125MiB이며 PostgreSQL/WSL 전체 메모리 합계가 아니다.
실제 roles/schema/runtime password0·PG종료 status3·private cluster/admin password 삭제·owned server0을 확인했다.
초기1800초 보류를 성공 기록으로 바꾸지 않는다. 이 새 실행의 실제 process/worker/HTTP 상한도 구분한다.
요약 manifest 수정 후 이 긴 실행이 수정 전5c503da2… 판본임을 최종 영수증에서 보존한다.

등록25시간 시험의 첫 private runner는30분의 process deadline을 사용했다.
`2026-10-05T13:43:58Z`의 실제 관측은53commit/6,608확인 걸음이며 terminal 참조는 없었다.
원11,400걸음/128전이씩의 서버·현재 farm/원천/입력 권리·서명/파일 통합 검사는
초기1800초 private process deadline으로 **실제 TimeoutExpired/runner exit1**이 됐다.
pytest가 완료하지 못했고 다음 물리 변조 사례도 실행되지 않았다. 이는 기능적 RED가 아니다.
`13:50:28Z` 확인에서 private cluster/자격 파일은 삭제되고 해당 PG PID는 없었다.
중단 전 roles/schema 수치는 수집되지 않았으므로 별도0 측정으로 보고하지 않는다.
현재 권리 검사 비용이 원인일 가능성은 이전 순수 실행과
코드 경로를 비교한 **추정**이며 세부 프로파일링으로 기여도를 측정하지 않았다.
이 중간 관측은 성공/실제 작기/DB 게시 근거가 아니다. 실제 종료·정리를 기록한 뒤
25시간과 물리 변조를 분리하고90분 이하의 별도 private native 검증 예산을 적용한다.
원 worker128전이·HTTP30초·파일/DB 크기·G0–G4 기준은 유지한다.
[분할 통과/첫 실행 보류 영수증](artifacts/crop-cycle-db-custody-hold-20261005.json)은
이 시점의 후보 상태이며 후속 최종 수용 영수증으로 덮어쓰지 않는다.

## 이미 통과한 짧은 실제 PostgreSQL 실행

PostgreSQL16.15·실제 loopback SCRAM authority로 같은 등록 농장의3시점/120걸음
서버 결과를 게시했다. 불변 metadata는6,515bytes였고 retry·새 service·별도 **fork**
프로세스의 ID/bytes/recorded_at·원 페이지가 같았다. fork는 새 Python exec나 다른 UID 증거가 아니다.
게시/읽기 RHS0회, private research row1/실제 crop Run0개다.

관측 put50.605674초/get17.054600초, sample page18.672203초/24,324bytes,
event page18.375463초/59bytes다. 이 수치는 summary 추가 전76faa19f… module에 대응한다.
HTTP/TLS30초의 증거가 아니며 한 응답에서 get와page를 별도로 호출하는 설계의 예산은
후속 API에서 실제 측정해야 한다. API 단계에서 원 결과를 다시 적분해 응답을 만들지 않는다.

manifest 수정 전5c503da2… 판본에서도 실제 SCRAM·동일 retry·새 service/fork·RHS0을 다시 확인했다.
동일6,515bytes, put52.963673초/get17.954383초, sample17.832712초/24,324bytes·
event17.901815초/59bytes다. current runner341.488069초/child RSS125.9375MiB와
roles/schema/password0·PG종료·private cluster/admin password 삭제·owned server0을 확인했다.
현재 관측을 초기 판본의 관측으로 덮어쓰지 않고 별도 근거로 보존했다.
[당시5c503da2… 판본/73개 분할 진행 영수증](artifacts/crop-cycle-db-custody-progress-20261005.json)은
등록25시간이 아직 미수용인 시점의 불변 기록이다.

nice10·private cluster1개·연결32/shared16MiB/work1MiB/maintenance16MiB로 순차 실행했다.
첫 runner344.699099초·sequential child 최대RSS125.21875MiB였다.
실제 roles/schema/runtime password0·PG종료·private cluster/admin password 삭제·owned server0을
확인했다. 단일 process의 RSS 최대이며 PostgreSQL 포함 WSL 전체 합계라고 보고하지 않는다.

## 다음 사용자 산출물과 외부 보류

DB 수용 뒤 같은 ID의 bounded sample/event와 원 manifest/hold를 typed API로 읽고,
그 실제 TLS 응답을 web decoder·선택 UTC·표/그래프/성장 연구3D에 연결한다.
다음 API 수용은 실제 Bearer/TLS/SCRAM·current rights·원량/UTC·30초/2MiB·유한 페이지·
부분/빈 hold·GET RHS0회·재연결/정리다. renderer에서 임의 성장 시점을 생성하지 않는다.
그 뒤 실제 긴 작기 부하/복원 → 근거 있는 생과 환산 → 자원/Decimal 경제를 진행한다.

[국내 공개 목록 검토](crop-domestic-public-catalog-review-20261005.md)를 병행했다.
공식 목록3개를 실제 독립 농장3건으로 세지 않는다. 원자료 수신·국내 독립 측정·미사용 작기0건,
실제 cultivar/forcing/초기/관리 채택0개와 G0–G4·생산 예측/경제 추천 게시 보류를 유지한다.
실제166일/품종 전체 작기·생과 수확·구매 전력/연료·미래 마진/순위는 이 합성 시험의 결론이 아니다.
