# 잎 제거 탄소·열용량의 순간 결속 — 2026-10-24

상태: **부모 결합 작업의 순간 계산 자식을 수용**했다. 전체 연속 생장/작기 결합은 미완료다.
[계약](../contracts/crop-leaf-carbon-removal-v1.md), [구현](../backend/app/crop_leaf_carbon_removal.py),
[검사](../backend/tests/test_crop_leaf_carbon_removal.py), [기계 검증 근거](artifacts/leaf-carbon-removal-20261024.json).
기존 사용자3D/서버/DB·키와 고정 수치 프로필을 바꾸지 않았다.

## 달라진 계산

[선행 경계](crop-leaf-canopy-basis-20261024.md)의 면적/floor와 [1차 조사](leaf-lifecycle-production-primary-sources-20261024.md)를
실제 `crop_leaf_lifecycle`·`crop_climate_joint_management` 함수/상태와 대조했다. 새 계수는 채택하지 않았다.
기존 관리 함수는 시계 없는 원자 전이이므로 이번에는 원점/정확 초가 같은 **명시 순간 상태**를 받는다.
분수 초도 원 유리수로 보존하며 시간을 전진시키거나 기존 정수 UTC 실행을 새로 지원했다고 주장하지 않는다.

생애 checkpoint의 현재 제거 batch를 원 순서로 고른다. 제거 마지막 상태를 현재 active에 더해 순간 직전 목록을 구성하고,
과거 제거·pending은 제외한다. 별도로 명시한 각 잎의 mg_CH2O와 floor만으로 탄소를 환산한다.
원 case/shoot 표지·두 state SHA/개수·순서·질량 합을 대사하고, 같은 시각의 batch 누락·중복이나
비0 연속 leaf 제거를 거부한다. 표지는 합성 입력의 일치이며 실제 원 농장/shoot의 권한·계보 승인이 아니다.

직전 질량 합은 집계 leaf stock과 같아야 한다. 사건 전후의 추적 면적/floor는 기존 `SLA_CH2O×C_leaf`와
binary64 64ulp 한도에서 맞아야 한다. 한도는 회계 roundoff이며 생물학적 정확도 오차가 아니다.
맞지 않으면 면적/질량/온도를 보정하지 않고 hold한다. 양수 mass/floor의 0·subnormal 소실도 거부한다.
합산한 제거량을 기존 원자 관리 함수에 한 번 전달해 C/N·수관 열용량·signed sensible energy/Tc 수지를 재사용한다.
stem 제거와50과실 분율은0이므로 원 buffer/stem/과실 C/N·공기·온도 필터는 보존한다.
전체 입력/출력·source/mass basis/코드/프로필 SHA를 기록하고 부분 성공·영속 쓰기를 만들지 않는다.

## 통과한 증거와 실패 이력

- **RED:** 새 모듈 부재 import 오류를 실제 확인했다.
- 첫 구현 검사35통과/1실패: 합성 분모를 바꾸면서 Uref를 함께 환산하지 않은 fixture가 기존 온도 domain을 벗어났다.
  수용 기준/온도 범위를 유지하고, fixture의 leaf stock과 Uref를 같은 면적 비로 환산했다.
- **고유234검사:** 새45, 기존 공동 관리69/잎 생애79/추적 LAI41=189이다. 중간226과 최종45는37개가 겹치며 합산271이 아니다.
  단일/동시 제거·정확0/1⁄3초·과거 제거 제외·빈 수관/초과·질량/ID/단위/시간/SHA·중복/누락과 원 입력 불변을 확인했다.
  같은 입력의 동일 결과, 사건 후 상태에 원 mass basis 재사용 거부, 같은 총 C이지만 잘못된 제거 잎 분포의 hold를 검사했다.
  기존8 RHS domain의 낮/어둠·과실 빈 상태·음/0 Uref와 온도 보존을 확인했다.
- **fresh 합성16사례:** 질량을 먼저 선언한 paired fixture다. 두 제거 batch×0/1⁄3초×낮/어둠/음/0 Uref이며,
  leaf C/LAI·용량/제거 용량·Uref/제거 열의96개를 app 식을 호출하지 않는100자리 Decimal/Fraction과 대조했다.
  각 상대 차이≤5e-14,0 참조는 정확0이었다. 이 fixture의 면적은 고정 SLA와 일치하도록 만든 소프트웨어 입력이며
  실제 leaf mass–area 관계를 발견/보정하거나 현장 정확도를 검증한 자료가 아니다.
  관리16회·공동 RHS32회, 생애 advance/적분·DB/CLI/network/파일 쓰기0과 FD 보존을 확인했다.
- **실제 저장 원본의 거부:** 기존 명시 제거 root의 원 manifest/권리·초기 state SHA를 reader와 private file policy로 검증한 뒤
  원 초기 checkpoint를 읽었다. 다른 집계 C fixture를 붙이면 `CANOPY_HOLD`이며 관리 함수 호출0이다.
  원31blob bytes/메타데이터·FD와 DB/CLI/network/쓰기0을 확인했다. 독립 농장 자료라는 뜻이 아니다.
- **WSL:** .25초 샘플/512MiB PID·1GiB 합/600초·로그4MiB를 유지했다.
  관련226 배치의 PID peak91,918,336/합603,435,008bytes, 마지막45는 합532,783,104bytes,
  fresh16은 합489,078,784bytes였다. 4보호 root 생존·원2,966항목/코드·감독FD4→4/소유 잔류0을 대사했다.
- **미실행:** 전체 backend/호스티드 CI·브라우저 시험, 연속 crop/leaf 결합·실제 농장/예측/추천·배포 검증.
  원 web CI는 이전 UI commit의 증거로 유지하며 이번 Python 코드의 전체 CI로 재분류하지 않는다.

## 판단 방법과 다음 의존성

부모 native CLI `gpt-6.1-sol/xhigh`, context `2026-10-24T04:15:59.633Z`, raw LF SHA
`6e061accc2310ba6ba3bed2dc515a900945381cef4d781e6b43a5e9232a940cc`를 기록했다. 재귀 CLI0이다.
기존 source note의 원문/권리/단위와 고정 프로필을 재사용했으며 새로운 농업 계수·자료/관문 승인0이다.

다음은 **연속 생장 결합의 면적·탄소 권위와 상태 전진 경계**다. 독립 logistic 면적과 기존 SLA×C를
시간 내내 함께 강제할 수 없으므로 무단 rescale 대신 후보 모델/분배·새 출현 질량·제거/forcing의 근거를 먼저 대조한다.
같은 crop/case의 한 짧은 구간→정확 사건→다음 구간, 기관/buffer/50과실 C/N·열·물과 재개/분할 대사는 후속 수용이다.
이번 순간 자식은 임의 새 질량 분배·전체 작기·source/farm 게시·물/구매 에너지·경제 feedback을 대신하지 않는다.
현재 농장 실행/관리 SourceRecord와 [국내 독립 원 자료 획득](independent-domestic-cherry-tomato-data-20261024.md)은 병행한다.
원 측정/미사용 독립 국내 작기0·첫 국내 품종 미확정이며 실제 G0–G4/생산·경제/추천과 전체 완료일은 미정이다.

앞의75–140집중분은 이 순간 자식의 실적으로 갱신하되 부모 완료로 처리하지 않는다.
다음 근거/기존 상태 대조25–45 + 결합 후보/권위 계약25–50 + 첫 작은 독립 fixture20–40 + 기록10–20 =
**80–155집중분**, 낮은 신뢰의 개발 작업량이다. 연속 결합 구현 전체·실제 자료 확보/검증·제품 완료 시간은 포함하지 않는다.
