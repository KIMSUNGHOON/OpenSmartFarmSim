# 기존 미리보기 인증/TLS 갱신 — 2026-10-17

[기계 증거](artifacts/frozen-preview-authentication-renewal-20261017.json).
이전 goal turn은 잠금 충돌 수정·집중6검사와 실제 시간 상한 실패를 남긴 **progress**다.
이번에는 실제24시간 미리보기 인증 만료를 확인하고 기존 사용자 경로를 갱신했다.
새 Solar 배포·생산 예측·G0–G4 수용은 아니다.

## 유지한 범위

legacy는 원 frozen source/동일 불변 manifest에서 새 namespace로 복원했다.
공통 joint API와 환기도 각각 기존 f6be606/2aa45fa source로 재기동했다.
동일 토큰·모델 integrity key·입력/결과·권리·역할/수식을 보존했다.
공통 runtime의 변경은 인증 시각, 환기는 인증/그 원본 hash와 새 TLS 경로뿐임을 대사했다.
새 네트워크 TLS 인증서/키는 새 실행 디렉터리에 보존했다.
공통/환기 인증 유효 종료는 **2026-10-18T11:50:17.207038Z**다.
legacy는 원86340초 수명 정책을 사용한다.

만료된 joint와 거의 수명이 끝난 legacy만 검증한 기존 PID/start/boot·pidfd로 정상 종료했다.
기존 환기는 만료 시 정상 종료했다. 수용 시험의 메모리 통과를 위해 서비스를 정지하지 않았다.
재기동 감독은 현재 ownership helper를 사용하고512MiB/PID·합1GiB·0.25초를 유지했다.
새5root의 동적 자식/별도 PG를 포함하며, 재기동 후에는5root 필수 조건을 복원했다.

## 실제 검증

| 검사 | 실제 결과 | guard 초 | 합 RSS 최고 bytes |
| --- | --- | ---: | ---: |
| legacy 원 생장/수확·권한·HTML |94524:0,8읽기:200×6/403/404·FD8→8·계산/게시0|50.247|932,077,568|
| joint 원 입력/저장 HTTPS |58985:0,입력3/저장9시점·원 현재 결과·조회21후크0|27.922|991,084,544|
| 환기 정상/보류 원문 |32251:0,proxy6+검증 HTTPS2·조회23후크0·FD identity8→8|48.208|928,137,216|

legacy의47,809저장 생장시점/47,813수확행·DB counts를 유지했다.
이 수치는 이미 저장된 합성 시험 자료의 크기이며 실제 농장 생산량이 아니다.
환기8응답은 재기동 전 저장 원문 bytes와 같고 TLS CA/호스트/시각 검증을 사용했다.
두 HTML 원문과 상태 feed200/no-store를 확인했다.
각 guard는 원2,148항목·frozen source/자산·원본과 감독FD4→4·시험 소유 비좀비/PG/임시/passfile0을 통과했다.
환기 frozen source2,173파일도 유지했다. 서비스 PG/작업자는 의도적으로 실행 중이다.
현재 browser DOM/WebGL·전체 회귀·새 Solar 계산은 실행하지 않았다.

## 보존한 초기 실패와 복구

- 새 joint nginx 기본 생성기에 기존 개발 상태/proxy 확장이 없어서 환기 serve-v9가 시작 전 실패했다.
  보존한 기존 설정에서 실행 경로만 갱신하고 nginx 검사를 통과했다. 모델 source를 바꾸지 않았다.
- legacy를 갱신하자 이를 보호하던 환기가 정상적으로 중단되어 첫 legacy 실행의 retained root 검사가 실패했다.
  이 시도를 남기고 **기반 두 서비스→마지막 환기** 순으로 복원했다.
- 환기 첫 읽기는 응답 직후 FD 동일 검사에서 실패했다(54821:1).
  첫 비교 원문이 남지 않아 그 차이의 원인은 확정하지 않았다. 별도 안정 상태 검사에서는
  응답 직후/연결 정리 후 모두8개·동일 identity였다. 응답 연결 정리 대기는 최대2초이며
  동일 FD 판정은 유지했다. 앞선 실패는 수용 건수에서 제외했다.

앞으로 인증 갱신은 환기를 먼저 중단하고 기반 두 서비스를 갱신한 뒤,
최종4root를 보호하도록 환기를 마지막에 시작한다. 다음 공통 만료 전11:40UTC까지 준비한다.
이는 로컬 미리보기 운영 순서이며 자동 기동/G4 수용은 아니다.

## 사용자 경로와 후속

기존 화면은 `http://localhost:5173/`, 환기는 `http://localhost:5174/#ventilation-execution`이다.
현재 사설 안내는 `~/.local/state/OpenSmartFarmSim/20261009-full-harvest-user-preview/run-v27/service/OPEN-UI.private.txt`,
`~/.local/state/OpenSmartFarmSim/20261013-ventilation-user-activation/user-service-v3/OPEN-UI-ISOLATED-20261017.private.txt`다.
토큰은 공개하지 않는다.

다음은 [Solar의 확정 단계·구간별 시간 계측](../contracts/crop-solar-worker-progress-diagnostics-v1.md)이다.
원360초 정상 시험의 미완료와 로컬 용량·S3/S4·실제 자료/권리·전체 완료일 보류를 유지한다.
native CLI gpt-6.1-sol/xhigh의 실제 context/hash를 증거에 남겼고 재귀 CLI를 실행하지 않았다.
