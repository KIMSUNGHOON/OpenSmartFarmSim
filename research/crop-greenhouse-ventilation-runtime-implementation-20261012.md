# 환기 결과의 명시 서버 조립 — 2026-10-12

상태: **로컬 수용**. [계약](../contracts/crop-greenhouse-ventilation-runtime-v1.md) · [검증 영수증](artifacts/crop-greenhouse-ventilation-runtime-reference-20261012.json).

## 구현 범위

별도 `operator-greenhouse-ventilation-api-config-v1` 설정으로 수용한 조회 API를 실제 서버에 조립한다.
공통 runtime에 기본 None인 새 store/query factory와 결과 객체만 추가했다.
같은 jobs·farm·현재 principal·정확한 query/store와 서로 다른 입력/서버/DB 키를 요구한다.
잘못된 flag/factory 조합은 I/O 전에 거부하고, 설정·DSN·TLS·키 파일은 factory와 조립 전후 재검사한다.
기존5설정 판본의 새 기능 생략/False 동작과 기본 비활성은 유지한다.
자동 권한 부여·키 발급·DB 이전·계산·결과 생성·worker 시작은 추가하지 않았다.

합성32초 결과의 읽기 서버 조립이다. 사용자에게 새 모델을 배포하거나 전체 작기·생산 예측을 완성한 단계는 아니다.

## 통과한 검증

| 범위 | 원 도구 handle | 검사 | 종료 | guard 시간 |
| --- | ---: | ---: | ---: | ---: |
| 설정·파일 변경·I/O 전 거부·기존 설정/API/OpenAPI |15832|233|0|115.876초|
| 실제 SCRAM/검증 TLS 새·기존 정상/보류 |83368|4|0|309.138초|
| 실제 DB/ASGI의 잘못된 조립·늦은 철회 |74834|2|0|130.838초|

고유239개다. 모든 원 도구 종료를 수집했고 마지막 같은5개 핵심 파일 SHA로 검증했다.
TLS4건과 DB/ASGI2건을 구분한다. 새로운 정상/보류의 요약·생장·사건 원 bytes와 마이크로초 UTC가 동일하다.
기존 정상/보류도 같은 저장 query의 bytes를 반환하고 새 경로는 인증된503으로 비활성이다.
foreign store/query·키3쌍 재사용·code pin 변경·실제 SELECT 권한 철회를 거부하고 복원 뒤 재조립했다.
응답 생성 중 입력 권리와 계정이 철회되면422/401로 차단한다.
조회9수치 entrypoint·새 결과 등록·기존 cycle 실행0, DB 행·원 입력/설정 파일과 FD를 유지했다.

첫 native 시험29319는 실패했다. 시험용 공존 fixture가 구 joint flag와 권한을 활성화했는데
새 모델 전용 runtime에는 joint factory가 없어 올바르게 거부됐다.
새 모델 전용 시험 fixture에서 구 flag/권한을 명시적으로 비활성화하고 실제 권한 감사를 다시 확인했다.
제품의 조립 거부 조건을 완화하지 않았다. 수정 전162검사는 최종233개에 중복 합산하지 않았다.

## 보존과 화면

기존 계산 baseline256 중255파일은 동일하며 공통 runtime 한 파일의 변경을 전후 SHA로 기록했다.
baseline 밖의 기존 runtime 시험에는 새 기능의 비활성503 확인만 추가했다.
기존 OpenAPI57경로/313스키마는 이번 단계에서 변경하지 않았다.
원본2,148항목·frozen source1,911/자산171·prior UI171/현재172자산·source194·현재 권리/안내·4보호 root를 유지했다.
각 guard의 FD4→4, 소유 non-zombie/PG/passfile/임시 PG 잔여0이다.
검증3묶음의 최대 단일 RSS187,506,688bytes/보호 포함 합931,209,216bytes로512MiB/1GiB 이내다.
두 사용자 주소200·원 index/NGINX 설정·권리/검토 기록을 유지했고 사용자 백엔드/worker 재시작0이다.

[진행 화면](http://localhost:5174/#crop-execution)에239검사 통과와 남은 자동 계산→같은 UTC3D→사용자 적용을 게시했다.
HTTP200/no-store·main/published/handoff SHA가 일치한다. 단계 설명은 검증한 진행 시점에 갱신하며 화면은15초마다 조회한다.
5173은 기존 완료166일 재생이며 개발 패널은5174에 있다. 기존 사용자 작업64/64는 완료 상태다.
원26590의 실제 브라우저/guard0·4.069초에서 인증 없이239검사와 API 완료/실행 다음 단계를 확인했다.
390px overflow0·API쓰기0·pageerror0이다. 브라우저 포함 단일260,968,448/합991,260,672bytes도 한도 이내다.
새 모델3D 자체의 브라우저 검증은 후속이다.

## 다음 한 단계와 남은 의존성

다음은 **`crop-greenhouse-ventilation-execution`**이다. 기존 작업표/임대·서명 저장을 사용해 새 입력/모델 판본을 구분한다.
수용 기준은 실제 접수→자동 worker 확정 checkpoint→정상/보류 결과의 원자 게시,
취소/재시작·현재 권리·원 수치/UTC·조회 재계산0·구 모델/두 화면/WSL 보존이다.
그 뒤 typed web·같은 UTC의 확정 부분/완료3D·실제 브라우저 정상/보류/취소/재접속·사용자 적용을 진행한다.

작업자/웹2–4와 사용자 검증/적용1–2의 합3–6집중시간은 잠정 남은 작업량이다.
이번 서버 연결 검증의 guard 합은555.852초이며 준비·진단·수정·기록 시간은 별도다.
전체 제품 완료 날짜는 독립 농장 자료와 미완료 자원/경제/최종 UI의 수용 상태에 따라 별도로 산정한다.
실제 농장 Run·독립 국내 자료0, G0–G4 not_assessed, 실제 품종 생산·자원 구매·미래 마진/작물 순위는 보류한다.
native Codex CLI `gpt-6.1-sol / xhigh`의 실제 turn context/원 행 SHA를 영수증에 기록했다. 재귀 CLI0이다.
전체 CI/remote·새 자동 worker/웹/사용자3D·전체 작기 성능·실제 자료 검증은 미실행이다.
