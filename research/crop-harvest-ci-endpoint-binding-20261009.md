# 수확 보호 복원 시험의 endpoint 형식 수정 — 2026-10-09

19:13 KST, core6fcf6a0. [작은 수정 계약](../contracts/crop-harvest-ci-endpoint-binding-v1.md)과
[원 실행·해시·자원 기록](artifacts/crop-harvest-ci-endpoint-binding-reference-20261009.json).
native Codex CLI `gpt-6.1-sol`/`xhigh`, 재귀 CLI0이다.

## 원인과 변경

Backend37892105708 분할5의 원 protected/fresh 복원 시험은 TCP DSN fixture의 문자열 포트와
실제 인증 연결의 정수 포트를 서로 다른 JSON으로 해시했다. 원 로그의 두 전체 SHA가 같은
host/port/database에서 이 자료형 차이만으로 정확히 재현됐다.
예상 endpoint의 포트에 `int(...)`를 적용하는 **시험 한 줄**을 바꿨다.
제품 코드·공통 fixture·CI workflow와 실제 host/port/database·SCRAM/password·서명/권리 검사는 유지한다.

## 실제 검증

- 원14421 종료1: CI와 같은 Python3.12.13·소유 TCP/SCRAM에서 원 단언 실패를 재현했다.
  실제 fixture 포트는 str, 실제 연결 포트는 int이며 정수 정규화한 예상 SHA가 원 연결과 같다.
- 원49894 종료0: 같은 TCP 경로의 원 시험1개/16.694초를 통과했다.
- 원17664 종료0: 기존 socket fixture/Python3.12.3 경로에서도 원 시험1개/16.957초를 통과했다.
  양쪽의 실제 reader는 TCP/SCRAM이다. 각 경로에서 별도 Python2개와 private 설정 거부/복원을 확인했다.
  원 jobs/events88/88·crop/harvest0, 보호16파일과 FD13→13/TCP·12→12/local을 보존했다.
- 원87796 종료0: 관련 집중60개/9.784초를 통과했다. native 대상의 두 환경 실행을 합치면
  통과한 고유 기존 사례는61개다. 새 수확/생장 결과 및 실제 HTTP/TLS 검증0이다.
- 각 실행의 schema/role/passfile·protected file0, 소유 PG 정지·임시 디렉터리 제거,
  source1,615개·원 입력/key/권리 자료와 진행 중 전체 writer의 고정 source·기존 미리보기를 확인했다.
  별도 root 감사 원064692 종료0·frontend200이다. 첫 보조 감사의 두 환경 공통 FD13 가정은
  실패로 남기고 원12→12/13→13의 각 전후 일치로 수정했다. 제품/원 검증 증거는 바꾸지 않았다.
- 0.25초224표본/새 PG168표본의 단일/관측 합 RSS136,675,328/763,723,776bytes로512MiB/1GiB 안이다.
  소유 시험과 지정 기존 미리보기·전체 writer/PG tree의 관측이며 WSL 전체/운영 용량 증거가 아니다.

## 남은 범위

**로컬 시험 결함 수정만 수용**한다. 실제 hosted PostgreSQL18.6 분할5/전체 CI는 아직 미확인이다.
분할3의 pidfd 호환 실패는 별도 작업이며 새 전체 CI는 그 수정과 필요한 국소 검증 뒤 평가한다.
진행 중 정상 전체 수확 writer/보존/fresh → 보호 API/대표3D의 순서를 유지한다.
U3 실시간 연결·실제 품종/농장 Run·독립 자료/G0–G4·생산/미래 마진/추천은 이번 수정으로 완료되지 않는다.
