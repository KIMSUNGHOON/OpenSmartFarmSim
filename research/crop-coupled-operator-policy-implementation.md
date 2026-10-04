# Coupled 저장 기본 정책의 운영 설정 회귀 수정

상태: **99개 집중/실제 SCRAM·운영 TLS 로컬 통과; 수정 판본 hosted 재검증은 별도**.
[실제 증거](artifacts/crop-coupled-operator-policy-reference-20261005.json)는 실패 판본/
Actions run·로그 hash·RED/GREEN·코드와 임시 자원 정리를 기록한다.
현재 실제 CLI `gpt-6.1-sol / xhigh`로 판단했고 재귀 CLI를 실행하지 않았다.

## 필요한 이유와 최소 변경

`crop-coupled-result-storage`가 추가한 기본 false policy 필드는 `asdict`에
직렬화된다. 그러나 기존 `operator_config.py`의 닫힌 허용 목록에는 빠졌다.
`bdcade9`의 [Application run 37233284248](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37233284248)은
이미지/허용 문맥 검사 뒤 실제 Compose API가 exit 2로 시작되지 않았다.
비밀값을 출력하지 않는 진단은 `operator_config.py:98`의 `ValueError`를 확인했다.
그 실패에서도 Compose/볼륨/비밀 정리 단계는 성공했다.

이 문제는 기존 API로 같은 저장 연구 결과를 읽는 경로의 선행 회귀다.
운영 기반 동결을 유지하며 기존 로더/그 시험 두 파일만 고쳤다.
새 policy 필드는 생략과 정확한 `false`만 읽고 기존 기본값을 유지한다.
새 조회 store/factory는 아직 구현하지 않았으므로 `true` 및 비 bool을
dependency factory import 전에 거부한다. 기존 crop v1 option은 동일하다.
계수·프로필·생장/저장 코드·DB grants·Compose·이미지·서버/작업자 역할은 바뀌지 않았다.

## 실제 검증

수정 전에 기존 완전 직렬화 정책과 명시 false가 실패하고 생략만 통과했다
(`2 failed, 1 passed`, exit 1). 이 반례를 포함한 새 7개는 생략/false 수용과
`true/0/1/"false"/null`의 factory 이전 거부를 검증한다.

수정 뒤 다음 전체 두 파일을 한 저우선순위 Python·하나의 사설 loopback
PostgreSQL 16.15/SCRAM으로 실행했다.

```bash
cd backend
.venv/bin/python -m pytest -q tests/test_operator_config.py tests/test_api_runtime.py
```

실제 실행 cwd는 `backend`, 연결/비밀번호는 사설 실행기가 임시 파일로 넣었다.
**99 passed /30.01초, skip 0**, exit 0이다. 단순 monkeypatch 로더 시험 외에도
실제 SCRAM identity/grant/provider/TLS 거부·별도 운영 프로세스의 TLS/Bearer와
기동 뒤 grant drift 거부·기존 runtime 조립/HTTPS가 포함됐다.
20:48:41–20:49:13 UTC에 실행/정리했다. DB shared buffers 32 MB·24 connections,
`nice=10`을 유지했고 DB와 비밀번호 파일이 제거됐다.
로컬 Docker Engine은 없으므로 실제 Compose의 수정 판본 수용은 새 hosted run이 필요하다.
기존 564개 저장 수용을 반복하거나 이 99개로 대체하지 않았다.

## 다음 핵심과 남은 관문

[coupled 페이지 API](../contracts/api-crop-coupled-replay-v1.md)의 실제 구현 때
new flag/store factory의 정확한 조립을 추가하고, 이 로더의 `true` 거부도
그 조립/권리·실제 HTTPS 검증과 함께 갱신한다. 지금은 새 API/50구획 3D를
구현한 것으로 보고하지 않는다. 실제 국내 독립 자료 0개·forcing/Run 0개와
기존 전체 작기/품종/권리 hold·G0–G4 조건은 그대로다.
