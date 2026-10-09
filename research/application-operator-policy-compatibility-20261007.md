# 기존 앱 설정 생성 호환 — 로컬 검증과 hosted 수용

2026-10-07 KST. 실제 앱 CI37622257162의 API 시작 실패를 설정 생성 경계에서 수정했다.
[고정 영수증](artifacts/application-operator-policy-compatibility-reference-20261007.json)은 native
Codex CLI `gpt-6.1-sol / xhigh`·재귀 CLI0회·실제 실행/로그/source SHA와 정리를 기록한다.
운영 기반 동결을 유지하는 기존 기동 회귀 수정이며 새 작물 API/관문 수용이 아니다.

## 원인과 수정

현재 policy의 전체 `asdict`에는 기본 false인 새 계산 저장 flag가 있지만,
기존 `operator-api-config-v1`의 닫힌 loader는 그 필드를 받지 않는다.
[실패한 hosted 실행](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37622257162)은
`operator_config.py:99`의 필드 검사 실패와 Compose 자원 정리를 기록했다.
원 loader는 server 서명의 file helper dependency이므로 수정하지 않았다.

[설정 생성기](../scripts/check-application-runtime.py)는 정확한 false만 기존 API policy에서 생략하고,
true는 파일 작성/chown 전에 고정 오류로 거부한다. simulation fixture의 원 policy는 보존한다.
[기존 loader 시험](../backend/tests/test_operator_config.py)의 두 fixture도 구형 판본으로 명시했다.
AST 대사에서 기존 시험 본문/거부 조건은 모두 같고 두 fixture 함수만 달라졌다.
[새 시험](../backend/tests/test_application_operator_policy.py)은 실제 생성한 보호 파일을 원 loader로 읽는다.
assembly/chown만 격리했으며 UID·실제 API/Compose 검증으로 세지 않는다.

## 실제 실행과 실패 보존

| 실행 | 실제 결과 |
| --- | --- |
| 수정 전 생성 정상3개·활성 거부·기존 정상 loader | 5실패/1.00초·종료1 |
| 제품/기존 fixture 수정 뒤 같은 사례 | 2통과/3실패·0.97초·종료1 |
| 새10개+기존 loader/runtime115개 | 122통과/3실패·33.02초·종료1 |
| 새 생성 정상3개의 시험 연결 수정 뒤 | 3통과/0.90초·종료0 |

첫 수정 뒤 남은 실패는 격리된 시험 factory 이름이 실제 config의 `dependencies_factory`와
달랐기 때문이다. 실제 예외 위치121/`AttributeError`를 별도 관측하고 보존했다.
다음 전체 실행의 세 실패도 새 시험에서 importlib를 바꾼 뒤 dotted monkeypatch 대상을 찾는
순서 오류다. patch 순서만 수정했다. 제품 source SHA는 수정 후 세 실행에서 같다.
**새 고유10개·기존115개, 고유125개 분할 검증**이며 단일125개 성공으로 표시하지 않는다.
실패한 원 로그·명령·판본도 보존했다. 추가 전체 재시험은 하지 않았다.

기존 실제 SCRAM/TLS 조립·별도 운영 프로세스/HTTPS·권한 변화 시험은 전체 실행에서 통과했다.
소유 PG cluster2개의 PID/data 부재, 비밀번호 파일0개·임시 tree 제거를 확인했다.
주 시험은 nice19·표본 최대 RSS116,256,768bytes이며 PG까지 합친 peak가 아니다.
원 loader를 포함한 **70 source SHA를 전후 보존**했고 정확성·가독성·경계·보안·비용을 검토했다.
계약은 시험 뒤 로컬 검증 기록을 추가했으므로 영수증의 계약 SHA는 시험 당시 판본이다.

## 10월7일 당시 남은 수용과 다음 작물 작업

현재 WSL에는 Docker가 없고 로컬 Compose 실행은0회다. 자동 설치하지 않았다.
remote `353bffb`는 다른3workflow 성공·앱 실패이고 Backend의 두 분할이 실제 진행 중이다.
기존 CI를 취소/재시도하거나 한도를 바꾸지 않고 전부 종료한 뒤 수정 판본을 push한다.
기존 세 Compose 경로/정리의 hosted 성공 전에는 호환 작업 부모를 체크하지 않는다.

다음 [새 runtime factory 계약](../contracts/crop-cycle-calculation-runtime-factory-v1.md)은
기본 None/flag 결속·same jobs/farm의 exact 새 store/query와 실제 SCRAM 조립을3 core파일로 검증한다.
이어 원 loader를 보존하는 별도 operator config → 인증 route/실제 TLS → 같은 UTC3D다.
전체 등록166일 prefix/복원과 생과/자원·Decimal 경제 연결은 남아 있다.
실제 품종 입력·국내 독립 자료·작물 Run0건과 G0–G4 `not_assessed`는 유지한다.

## Hosted 수용 — 2026-10-08

정상 push한 `f2dc10f`의 [Application 실행37647874843](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37647874843)이 성공했다.
[별도 고정 영수증](artifacts/application-operator-policy-hosted-reference-20261008.json)은 실제 종료 로그의
세 Compose 단계/42개 사건과 기존 세 수정 source의 hosted/현재 SHA 일치를 기록한다.
경제 자동 완료, 소유 수집, scoped 조사 권한의 재시작·현재 권한 변화 거부·각 process/volume/credential 정리를 확인했다.
이 증거와 위 로컬125개 분할 검증을 합쳐 설정 호환 부모만 완료한다.
새 native/전체 Backend·작물 생산 정확도·실제 제품 CLI/G1/G4 수용은 아니다.
추가 제품/CI 변경·취소/rerun·push는0회다. 진행 중인 Backend의 terminal과 새 작물 통합은 별도 확인한다.
