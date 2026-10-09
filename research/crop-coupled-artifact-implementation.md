# Coupled 연구 계산의 저장 선행 artifact — 2026-10-05 KST

상태: **불변 파일 형식의 로컬 소프트웨어 수용**.
[계약](../contracts/crop-coupled-artifact-v1.md),
[실제 계산/시험·자원 증거](artifacts/crop-coupled-artifact-reference-20261005.json)를 확인한다.
농장 권리/DB 저장·API/3D는 다음 단계다.

## 현재 CLI와 구현

실제 CLI `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`,
`2026-10-04T18:26:29.821Z` turn context의 **gpt-6.1-sol / xhigh**에서
저장/계산 분리와 이 artifact를 판단·구현했다. 재귀 CLI는 없다.

`crop_coupled_artifact.py`는 정확한 canonical 합성 프로그램을 public
`integrate_plant_cohorts`로 계산한다. 호출자가 결과/계수/승인을 주는 import 경로는 없다.
원 입력 bytes/hash·세 고정 profile/고지·현재 코드·원 계산 결과를 하나의 닫힌
`crop-coupled-artifact-v1`에 보존한다. 입력 1 MiB·결과 16 MiB 상한과 적분의
24시간/128구간·128사건/512출력·10,000step 상한을 유지한다.

reader는 신뢰 참조의 bytes digest·artifact ID와 현재 profile/notice/code,
완전한 manifest·정규화 입력/result hash를 검사한다. 출력의 닫힌 단위/50 N/C와
LAI/과실 C 합계·누적 두 수지/ULP 예산, 원 관리 사건과 실제 N/C 제거·전후 상태를
대사한다. 완료 sample은 요구 시점 전체, hold는 확인된 앞부분만 유지한다.
sample UTC는 정수 초이며 실패 trial의 소수 초도 보존한다. 조회는 재적분하지 않는다.

artifact digest는 무결성 참조다. 이를 새 DB 판본에 묶을 때 **서버 소유 계산,
HMAC·현재 farm/program 권리·원자 저장**이 필요하다. 단독 hash를 소유권/G1 승인으로
채택하지 않는다. 이 모듈 자체에는 tenant/farm/Run/게시 서명이나 HTTP route가 없다.

## 실제 확인한 산출물과 검증

모듈 부재 RED는 **exit 2**, 첫 GREEN은 **41 passed / 6.54초**다.
소수 초 trial hold도 추가해 최종은 새 42개/기존 488개, **530 passed / 13.10초**다.

```sh
cd backend
env PYTHONPATH=. nice -n 10 .venv/bin/pytest -q \
  tests/test_crop_coupled_artifact.py tests/test_crop_plant_cohort_integration.py \
  tests/test_crop_plant_cohort_rates.py tests/test_crop_fruit_cohorts.py \
  tests/test_crop_fruit_allocation.py tests/test_crop_fruit_transport.py \
  tests/test_crop_growth_rates.py tests/test_crop_photosynthesis_domain.py \
  tests/test_crop_growth_integration.py
```

두 독립 참조 프로그램의 public 계산을 다시 artifact로 생성했다.
첫 낮→밤/관리 사례는 **131,036 bytes/6시점/3사건**, 야간 사례는
**68,300 bytes/5시점/0사건**이다. 실제 packet/result/manifest hash를 증거에 기록했고
원 artifact는 private `/tmp/ossf-crop-coupled-artifact-case-{0,1}-20261005.json`에 있다.
기관/50구획/누적량의 독립 수치와 분석은 [선행 적분 증거](crop-plant-cohort-integration-implementation.md)와 같다.

같은 입력의 exact 반복, caller와 reader 반환 사본 변경의 격리,
별도 실제 Python의 동일 ID 읽기·재적분 없는 조회를 확인했다.
실제 초과 제거 hold는 3개 과거 시점만 남겼고, 1.5초 k2 실패는 첫 경계만 남겼다.
비합성·동일 ID의 다른 block·잘못된 단위/형태/bytes/중복 키·비유한 입력은 계산 전에 거부한다.
재해시한 모델/코드/policy/profile·manifest/solver/origin·수지/예산·관리 제거/
시점/누락 시계열과 추가 실제 생산 필드도 거부했다.

## WSL2 실제 512출력 검사

한 개 `nice -n 10` Python 과정으로 같은 **합성 24시간/8,687step/512출력**을
public builder에서 재계산·검사했다. 앞선 실제 적분 결과와 **exact equality**를 확인했다.

| 측정 | 실제 값 |
| --- | ---: |
| 원 프로그램 bytes | 18,930 |
| artifact bytes | 3,683,992 |
| 계산 + artifact 검증 | 59.1135초 |
| artifact 읽기 + 검증 | 0.3055초 |
| 전체 과정 peak RSS | 85,224 KiB (약 83.2 MiB) |

이는 로컬 파일/CPU 측정이다. DB/권리·HTTPS 전체 본문이나 동시 사용자 성능은
측정하지 않았다. 16 MiB artifact 상한 안의 결과를 확인했지만 전체 166일/실제
작기 처리의 수용은 아니다. 새 서버/DB/Docker·의존성은 시작하지 않았다.

수동 검토에서는 193줄 제품 모듈의 경계·예산·출력 진단·신뢰 digest의 범위와
기존 public 계산 재사용을 확인했다. 기존 프로필/원식/적분·v1 저장은 수정하지 않았다.

## 다음 한 단계와 외부 의존성

`crop-coupled-result-storage`에서 새 artifact를 **같은 등록 farm/crop/batch/zone**,
원천 binding·현재 program 권리와 묶는다. 현재 v1 DB는 단일 profile/schema/ID에
고정돼 이 artifact를 넣을 수 없다는 구체적 근거로만 새 표/명시 role flag를 추가한다.
계산은 HTTP 밖에서 완료하고 조회는 저장 bytes를 읽는다. 실제 SCRAM·다른 프로세스/
동일 재시도·혼합/변조·현재 권리 철회·원자성/rollback·정리를 통과해야 부모 저장을 체크한다.
그 뒤 조회 페이지/30초 실제 전체 본문 → 같은 결과/시점 표·그래프·3D로 진행한다.

전체 작기 실행/초기 착과·실제 품종·forcing UTC/면적/수관/초기기관/관리/QC는
여전히 보류다. 국내 동의/독립 미사용 자료는 0건이다. artifact 소프트웨어 개발과
자료 확보는 병행하며 G0–G4 관문을 열지 않았다. 전체 생산 예측/추천·production
완료 날짜는 해당 실제 자료와 독립 검증 상태가 정해진 뒤에 추정한다.
