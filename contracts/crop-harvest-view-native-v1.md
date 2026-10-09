# 같은 실제 DB의 수확·생장 3D 검증 — v1

2026-10-09 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
선행 [화면](web-crop-harvest-view-screen-v1.md) 뒤3 core파일은 이 계약,
`backend/tests/crop_harvest_view_native_smoke.py`, `web/e2e/harvest-replay-native-smoke.mjs`다.
기존 소유120걸음/3sample/4event·원6행의 실제 SCRAM fixture와 보호 loader/표준 ApiRuntime을 재사용한다.
metadata·시각·DB·응답을 바꾸어 결속을 맞추지 않는다.

현재 source의 실제 빌드와 검증된 native Nginx를 사용해 같은 origin에서 HTTPS API를 조회한다.
조회 중 RHS/행 재생성·증명 발행·게시를 금지한다. 원 부모/농장/manifest/수확 ID와
6행/단위/원 수량·정확 분수·목적/미배정·부분/전체 합계·관문 미평가를 실제 App에서 대사한다.
현재 저장3시점의 캔버스 UTC·50 C/N 값·LAI와 원 sample을 확인하며 미대응90초 사건은 연결하지 않는다.
데스크톱/390px 모바일·키보드와 원본 보존도 확인한다.

실제 표시 권리 철회/복원, 계정 변경과 양쪽 endpoint의 scope 거부를 확인한다.
지연 시험은 실제 서버 요청을 잠시 대기시킬 뿐 응답/계산을 대체하지 않는다.
수확 조회 취소·계정 변경 뒤 원 요청을 해제하고 이전 값/3D가 복원되지 않는지 확인한다.
통제한 요청 순서의 active peak와 취소된 client/서버 응답 관측을 구분한다.

전체 본문30초/2MiB, 원600초 마감, nice19·단일512MiB/소유 고유 PID RSS 합1GiB를 유지한다.
PG/controller와 재부모화된 소유 자식까지 감시하고 실제 원 도구 종료0·thread/FD·DB schema/role/
passfile·PG/API/Nginx/Node/Chromium/임시 경로 정리를 기록한다.
지정 heap/viewport/SwiftShader·필요한 명시 GC의 자원 수용을 일반 운영 용량으로 확대하지 않는다.
소유 Linux 시험의 browser 시작 전 Python GC/glibc trim과 조회 뒤 Chromium/Node GC를
전후 RSS/heap·진행 단계에 기록한다. 원 수식·행·요청/단언·제품 코드는 바꾸지 않는다.
시험 Chromium의 `--in-process-gpu`는 [공식 switch](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/content/public/common/content_switches.cc)의
GPU thread 구성을 쓴다. 실제 WebGL/원값 단언과512MiB/1GiB를 유지하며 표준 브라우저 process 격리/운영 용량의 수용은 아니다.
실패는 원 종료/관측을 보존하며 입력/단언/시간·자원 상한을 축소·완화해 통과시키지 않는다.

작은 native 자식 뒤 `crop-harvest-view` 부모를 같은 범위에서 평가한다.
전체166일 질량 부하와 replay 부모·기후/물·양분/구매 에너지·경제/사용자 실행은 별도다.
실제 품종 계수/독립 농장 자료·G0–G4·생산/미래 마진/추천은 승인하지 않는다.
