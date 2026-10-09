# 등록 수확의 실제 HTTPS 연결 — v1

2026-10-08. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
선행 [보호된 reader factory](crop-harvest-protected-factory-v1.md) 뒤 세 core파일은
이 계약·`backend/tests/crop_harvest_tls_fixture.py`·`backend/tests/test_crop_harvest_runtime_tls.py`다.

기존 계산 operator loader가 실제 시험 dependency module을 import해 표준 ApiRuntime과
실제 TLS 서버를 구성한다. module import를 가짜 객체로 바꾸지 않는다.
reader는 실제 같은 SCRAM DB·원 계산 query/jobs/farm/principal에 결속되며,
기존 명시 private reader config/key/DSN과 기본 비활성 계약을 사용한다.
소유 private bundle·키·입력/결과 증명·권리/시계 제어는 시험용이며 제품 운영 계정/CLI 증거가 아니다.

작은 소유120걸음 계산/부모 게시와 합성 계수/배정의 원6행 등록 뒤 읽기에서 계산·행 재생성·
증명 발행·게시를 금지한다. HTTPS 요약/전체6행·두 분할/빈 끝은 같은 DB와 artifact의
원 result/parent·UTC·단위·정확 수량·판본·미배정/hold·승인false를 보존해야 한다.
각 전체 응답을30초·2MiB 이하로 끝내고 인증서 검증·no-store·공개 query/code header를 확인한다.
권한 없는/다른 tenant·없는 ID·표시 권리 철회·HEAD 및 실제 요청한 page 변경·투영 후 철회/소유 시계 만료는
원 결과를 내보내지 않는다. source/권리/시계 제어의 변경은 복구하고 저장 원본을 보존한다.
요약은 서명된 root/summary 범위이며, 반환하지 않는 page 전체의 검사로 표시하지 않는다.

같은 보호된 설정의 서버 재구성 뒤에도 같은 결과를 읽는다. 서버/thread/FD·입력/설정 bytes와
inode·DB counts·역할/passfile/PG/임시 경로를 대사하고 WSL primary512MiB·pipeline1GiB와
원 native600초 상한을 지킨다. 실제 도구 원 종료 기록과 별도 source/정리 감사를 보존한다.
표준 서버의 첫 로깅 초기화가 닫는 pytest `/dev/null` descriptor를 따로 기록하고,
그 구성 직후의 FD 대상/device/inode를 두 HTTPS 실행의 동일 기준으로 사용한다. custody FD0 검사는 유지한다.
시간/자원 실패는 좁은 통과로 대체하지 않고 원 실패를 남겨 원인을 수정한다.

수용 시 `crop-harvest-runtime-tls`와 선행 세 자식이 입증한 `crop-harvest-api-runtime` 부모를
평가한다. SDK·같은 UTC 표/3D·전체166일 질량 부하·기후/자원/경제 연결은 후속이다.
실제 품종 계수/독립 농장 자료·G0–G4·생산/미래 마진/추천은 이번 시험으로 승인하지 않는다.

## 로컬 수용 기록

2026-10-09 00:09:41 KST. [실제 검증 보고서](../research/crop-harvest-runtime-tls-implementation-20261009.md)와
[원 종료·source·정리 영수증](../research/artifacts/crop-harvest-runtime-tls-implementation-reference-20261009.json)에 따라 집중74개/원 종료0·HTTPS17개를 수용했다.
시험 전 계약 snapshot은 영수증의 tested source에 보존한다. SDK/표·3D·실제 생산/관문은 후속이다.
