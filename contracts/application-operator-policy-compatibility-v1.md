# 기존 앱 설정 생성의 계산 정책 호환 — 개발 계약

2026-10-07 KST. native Codex CLI `gpt-6.1-sol / xhigh`; 재귀 CLI0회.
`353bffb`의 실제 Application CI37622257162는 기존 API loader의 정책 필드 검사에서 종료했다.
설정 생성기의 전체 dataclass 직렬화가 구형 config 판본에 없는 새 기본 false 필드를 포함한다.
원 loader는 server custody의 서명 dependency이므로 그 파일과 원 signed 이력을 보존한다.

## 범위

core4파일: `scripts/check-application-runtime.py`,
`backend/tests/test_application_operator_policy.py`, `backend/tests/test_operator_config.py`, 이 계약.
기존 설정 생성 시 새 계산 저장 flag가 정확한 false인 경우만 구형 API policy에서 생략한다.
true는 파일 생성/권한 변경 전에 고정 오류로 거부한다. 구형 판본으로 활성 기능을 낮추지 않는다.
simulation fixture에는 원 policy를 보존한다. 기존 필드·config 판본·서비스·프로필·한도는 유지한다.
기존 loader 시험의 두 policy 생성 지점도 구형 판본을 명시하도록 false만 생략한다.
원 시험 본문과 거부 조건은 바꾸지 않는다. 새 계산 활성 설정은 후속 별도 loader의 책임이다.

## 수용 기준

1. 현재 기본 정책의 실제 설정 생성→보호된 파일 로더를 통과하는 반례를 먼저 실행한다.
   기본/기존 저장 옵션을 유지하고 원 policy 객체·simulation policy와 파일 mode/FD를 확인한다.
   이 시험은 UID/Compose·실제 API 조립을 대신하지 않는다.
2. 활성 새 flag는 파일 생성/chown 전에 거부한다. 구형 loader에 새 필드를 직접 넣는
   false/true/비 bool은 기존 닫힌 형식으로 factory import 전에 거부한다.
3. 기존 정상 loader 반례와 집중 회귀·실제 SCRAM/TLS 조립을 검증하고 원 loader SHA,
   보존 source/원 이력·소유 PG/schema/역할/비밀번호/PID/임시 tree 정리를 기록한다.
4. Docker가 있는 hosted의 기존 Application workflow에서 실제 세 Compose 경로와 정리를 확인한 뒤
   부모 체크박스를 완료한다. 로컬 Docker 부재·CI 대기는 별도 보류이며 focused 통과로 대체하지 않는다.

현재 WSL에는 Docker가 없다. 자동 설치하지 않는다. remote Backend37622257043가 살아 있는 동안
추가 push하지 않으며 기존 workflow를 취소/재시도하거나 설정·한도를 바꾸지 않는다.
실제 작물 입력/국내 독립 자료0건과 G0–G4 `not_assessed`는 유지한다.

## 로컬 검증 — 2026-10-07

[실제 보고서](../research/application-operator-policy-compatibility-20261007.md): 새10개/기존115개·고유125개 분할,
실제 SCRAM/TLS·원 loader/70 source·기존 시험 본문 보존·PG PID/data/비밀번호/임시 tree 정리를 확인했다.
첫 제품 반례와 새 시험 연결 오류 두 번을 구분해 보존했다. hosted Compose 수용은 아직 보류다.
