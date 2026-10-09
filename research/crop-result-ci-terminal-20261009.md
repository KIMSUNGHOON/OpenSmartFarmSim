# 작물 저장·재생 회귀의 hosted 종료 확인 — 2026-10-09

상태: **8dd386d Backend 실패, 전체 hosted 수용 미완료**.
[실제 run](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37877099838)과
[원 로그/metadata hash·종료 영수증](artifacts/crop-result-ci-terminal-reference-20261009.json)을 확인했다.
동일 native Codex CLI `gpt-6.1-sol / xhigh`에서 조사했으며 재귀 CLI0이다.

Backend는14:04:56 KST 종료했다. 분할2/3은 성공,0/1/4/5와 집계는 실패다.
같은 head의 C0/앱 runtime/작성 PG/Web 네 workflow는 성공이다.
최신 로컬 후보4703411의 hosted 시험 결과는 아니다.
여섯 분할의 컨테이너/비밀번호 파일 정리 **단계**는 성공했으나,
시험 내부 schema/role/passfile 감사에는 실패가 남았다. 분할0의 후속 Linux UID 접근 검사는 건너뛰었다.
전체 inventory·UID·Backend 수용으로 표시하지 않는다.

## 확인한 실패와 다음 작은 수정

| 위치 | 실제 실패 | 다음 확인/수정 범위 |
| --- | --- | --- |
| 분할0/4/5의 수확 TLS import·current query·runtime factory 시험 | 새 Python에서 `crop_harvest_tls_fixture`, `test_crop_harvest_current_query`, `test_crop_harvest_runtime_factory`를 찾지 못함 | `PYTHONPATH` 없는 CI 조건을 먼저 재현하고 해당 세 시험의 별도 자식 import 경로를 명시. 실제 fresh process/권리 거부·조회 계산0 단언은 유지 |
| 분할5의 게시 선언 단위 시험8개 setup | `publisher.sources()`가 과거 수용 source hash와 달라 `accepted supervision sources changed` | 합성 선언 fixture를 역사적 checkout에 의존하지 않게 격리. 실제 `sources()`의 원 hash 변경 거부는 별도 검사하며 과거 영수증/제품 source guard는 변경하지 않음 |
| 분할5 `test_runtime_roles.owned_scope` 정리 | `DROP OWNED` 중 AccessExclusiveLock 교착 | 동시 연결/transaction 수명과 lock 순서를 조사·재현. assertion 생략·무조건 재시도로 대체하지 않음 |
| 분할1/5의 로그인 자원 감사 | schema/role/passfile 개수0 단언 실패 | 분할1은 별도 DB이므로 분할5 교착의 결과로 설명하지 않음. 실제 잔여 자원의 생성/정리 주체를 확인 |

원 `--log-failed`에는 분할4/5·집계만 있어, 분할0/1은 원 job log를 별도로 받았다.
세 로그와 run metadata의 원 hash·실제 다운로드 종료0을 보존했다. 비밀과 원 로그는 저장소 밖에 두었다.
이 조사에서 fixture·runtime·workflow 수정이나 hosted 재실행은 하지 않았다.
앞선 [host SCRAM 초기화 후보](ci-explicit-host-scram-candidate-20261009.md)를 전체 hosted 수용으로 바꾸지 않는다.

## 실행 우선순위

진행 중인 전체 복구의 frozen producer와 현재 미리보기는 유지한다.
브라우저는 동시 자원 보류 상태이므로, 낮은 자원의 선언/import 재현과 작은 fixture 수정은 병행할 수 있다.
각 수정은 집중 원 실패→수정 후 통과·fresh DB/자식·정리와 native CLI/source 증거를 확보한 뒤 수용한다.
전체 복구의 대사/게시/보존·source 정리 뒤 UI 브라우저 계약을 수행하고 실제 목록 화면에 연결한다.
운영 기반은 기존 범위를 유지하며, 위 작물 저장·조회 회귀의 관측 실패에 필요한 수정만 추가한다.
