# 작물 개발 우선순위와 운영 기반 고정 — 2026-10-04

사용자 요청에 따라 **작물 생장 계산 → 저장 결과/성장 3D → 생산량·자원·경제 연결**을
현재 구현 순서로 고정했다. [현재 계획](../tasks/plan.md#작물-생산과-성장-3d-우선순위-2026-10-04),
[작업 목록](../tasks/todo.md#작물-생산성장-3d-구현-2026-10-04-현재-우선순위),
[첫 계산 계약](../contracts/crop-growth-research-v1.md)을 함께 읽는다.

## 확인한 Git와 진행 중 수정

고정 코드 판본은 `d19f7c064907fe39c307cba5b61211aef3b121ff`다.
확인 당시 로컬/원격 `chore/bootstrap-c0`가 같고, 별도 CI 가지의 `b8df8f9`에서
수용한 운영 코드를 포함한다. 현재 재정렬은 문서·조사 산출물이며 기반 코드의
기능/권한·잠금·이미지를 변경하지 않았다.

진행하던 결합 원천 Compose 시제품은 **미수용**이다. 실제 집중 시험은 새 helper
누락으로 **1 failed / 1.75초**였고, 이후 helper 후보는 실행 수용 전이었다.
새 파일 3개와 기존 파일 변경 patch를
`/tmp/ossf-source-compose-wip-20261004/`에 보존한 뒤 작업 트리에서 그 변경만 제거했다.
임시 보존물은 Git의 영구 산출물이 아니다. 이 시제품의 진행/합격을 상위 체크에
반영하지 않으며 작물 핵심 경로가 필요로 할 때 별도 계약으로 재검토한다.

## 고정한 운영 소프트웨어 완료 범위

| 수용한 것 | 확인한 범위 | 남은 범위 |
| --- | --- | --- |
| API/웹/경제 자동 소비 Compose | 실제 TLS/SCRAM 접수·자동 완료·현재 조회·동일 재시작·권한 변경·정리 | 독립 자격증명 소유권·실제 제품 CLI·전체 G1/G4 |
| 수집 소비 Compose의 개별 단계 | 합성 소유 부모의 자동 저장·같은 판본 재시작·부모/권한 철회·UID/자원·정리 | 조사부터 수집/검토/평가까지 결합 원천 경로 |
| authority/supervisor/dispatcher Compose의 개별 단계 | 지역 접수→시험용 CLI 캡처/서명·현재 검증 보류, 사설 파일/peer 거부·소켓 재시작/권한 철회·정리 | 실제 모델 실행·작업별 격리·독립 custody/해제 |
| 기존 불변 입력/작업/열·경제/조회·3D | 아래 같은 판본 회귀로 기존 계약 확인 | 동적 작물 엔진·성장 3D·생과 생산·물/구매 에너지·예측/추천 |

API/AUTH/SIM은 기존 writer UID/GID·권한을 공유하고 시험 controller가 비밀/키를
준비한다. 별도 서비스 UID·사설 마운트 거부 시험은 독립 기관의 custody 증거가
아니다. fake CLI/합성 서명을 쓰는 소프트웨어 수용을 G0 승인·G1 종단 간·G2·G3·
G4로 승격하지 않는다. `application-source-consumers`와 `application-compose-runtime`
상위 작업 및 `end-to-end-g1`의 체크는 미완료로 유지한다.

## 같은 판본의 CI 종결 상태

2026-10-04에 실제 terminal metadata와 작업별 로그/정리를 확인했다.
**5개 workflow 모두 completed/success**다. 실행 ID·모든 job/step 종결·로그 SHA-256과
바이트 수는 [CI 증거 등록부](runtime-freeze-ci-20261004.json)에 보존한다.
공개 raw 로그를 저장소에 복제하지 않는다.

| 실행 | 실제 통과/검사 |
| --- | --- |
| [Backend 37177945604](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37177945604) | 기본 2,491개/무건너뜀, 별도 UID 4개. 여섯 파트 302/287/495/371/551/485와 동일 전체 목록/최종 집계·정리 |
| [Web 37177945597](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37177945597) | Vitest 160개·Chromium 51개, typecheck/build·정리 |
| [C0 37177945611](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37177945611) | PostgreSQL 새 컨테이너 건강 확인·재생성 뒤 sentinel 보존·정리 |
| [Application 37177945615](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37177945615) | baseline/collection/authority 개별 mode의 실제 이미지·TLS/SCRAM·UID/자원/사설 마운트·재시작/철회·각 정리 |
| [Authored 37177945618](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37177945618) | 7개 묶음 141 실행(4/13/104/3/1/1/15), 실제 HTTPS/SCRAM·브라우저와 정리 |

Backend 목록 SHA-256은
`e2b387bc7d8d5deb65e843444c129ee7c2cea2f7b61fd6536bbac8adaea4fb2f`다.
partition 0의 기존 G0 fixture Pydantic 직렬화 경고 2건을 보존한다.
pytest 건너뜀은 없고 별도 UID가 아닌 파트의 해당 준비 step 건너뜀은 구조상 구분한다.
합격한 테스트 수는 생산 모델이나 현장 예측의 존재/정확도 증거가 아니다.

## 기반 작업 재개 기준과 다음 한 단계

새 기반 작업은 필요한 **작물 기능 ID 또는 필수 공개 관문**, 현재 경로의 실패/누락
증거, 최소 변경 파일과 수용 절차를 계획에 붙인 경우만 추가한다. 예를 들어 새
작물 결과의 원자 저장/현재 권리 제공자가 부족하면 해당 저장/API 단계 안에서
그 공백을 수정한다. 결합 원천 조립·대규모 처리량 확대·배포 전용 보완은 현재
순수 생장 계산을 막지 않는다.

모델 후보·계수·권리·검증 가능성을 기존 **Codex CLI gpt-6.1-sol / xhigh**에서
[조사](crop-tomato-model-baseline-20261004.md)했고 재귀 CLI는 실행하지 않았다.
첫 코드는 `crop-growth-rates`이며 고정 원식/단위·독립 수치 참조·야간/잎 0·탄소
수지·부적합 입력 거부를 확인한다. 국내 농장 자료 획득/독립 분할은 병행한다.
첫 성장 3D 연구 재생의 작업량 추정과 완료일 조건은 [계획](../tasks/plan.md)에 있다.
국내 자료/동의 0건이므로 최종 예측·추천·production 날짜는 미확정이다.


## 이번 재정렬의 문서/조사 수용

실행: `python3 /tmp/ossf-check-crop-plan-20261004.py`.
원문 등록부 10개의 실제 SHA-256/바이트 수, 39개 const의 근거 참조/보류·`cRgr` 정정,
CC0 archive MD5, 5개 CI terminal과 17개 job 로그 해시, 백엔드 6파트 합계 2,491개를
재대조했다. 신규/수정 상대 링크와 heading, 네 요청 문서의 단계 ID/관문,
기존 작업 체크 63개의 보존, 국내 확보 0건/검증 미통과, 실행 코드 변경 0개를 확인했다.
`git diff --check`도 통과했다.

`crop-model-baseline`과 `crop-independent-data-protocol`만 이 증거로 닫는다.
자료 접근·실제 forcing QC·작물 계산/성장 3D 구현·예측/추천 체크는 열린 상태다.
이번 문서 변경으로 새 pytest/브라우저·Docker 전체 시험은 실행하지 않았다.
사용자 WSL의 Docker 부재와 자원 제약을 유지하고 기존 수용 판본 CI를 고정 증거로 쓴다.
