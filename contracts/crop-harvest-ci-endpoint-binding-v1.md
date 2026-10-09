# 수확 보호 복원 시험의 endpoint 포트 형식 — v1

2026-10-09. native Codex CLI `gpt-6.1-sol`/`xhigh`, 재귀 CLI0.
선행은 Backend37892105708 분할5의 원 보호 복원 시험 실패다. 제품 조립 계약은
[기존 runtime](crop-harvest-runtime-assembly-v1.md)을 유지한다.
작은 수정 범위는 이 계약과 `backend/tests/test_crop_harvest_runtime_factory.py`의 예상 endpoint다.

## 확인한 결함과 수정 범위

`login_database`의 소유 socket 분기는 포트를 정수로, CI와 같은 TCP DSN 분기는
`conninfo_to_dict`의 문자열로 제공한다. 실제 인증 연결의 `conn.info.port`는 정수다.
원 CI의 두 해시는 같은 host/port/database에서 포트 JSON 형식만 바꾸어 모두 재현됐다.
예상 endpoint를 만들 때 포트를 정수로 정규화한다. 실제 연결의 host/port/database
일치 검사와 SCRAM/password·reader/원 jobs/farm/query 결속은 그대로 유지한다.

원 endpoint/SHA 단언을 삭제하거나 실제 응답으로 예상값을 덮어쓰지 않는다.
제품 코드·fixture/role grants·보호 설정/서명·읽기 권리·응답 한도는 수정하지 않는다.

## 수용

1. 원 실패 시험을 실제 소유 TCP/SCRAM과 CI의 Python3.12.13에서 수정 전 실패로 재현한다.
   동일 endpoint의 정수/문자열 해시와 fixture의 실제 자료형을 별도로 대사한다.
2. 예상 포트 형식 수정 뒤 같은 원 시험의 두 fresh Python 복원·private 설정 거부/복원과
   기존 국소 회귀를 통과한다. 소유 socket 분기도 같은 실제 시험으로 확인한다.
3. 원 종료·DB schema/role/passfile/FD 정리, 고정 source/현재 미리보기/진행 중 전체 writer,
   지정512MiB/1GiB 자원을 확인한다. 테스트 자료와 자격증명은 비공개로 취급한다.

이 증거는 국소 CI 결함 수정이며 hosted 분할5/전체 CI 성공을 대신하지 않는다.
전체 수확 writer/API/3D·U3·실제 품종/독립 자료·G0–G4는 별도로 남긴다.
