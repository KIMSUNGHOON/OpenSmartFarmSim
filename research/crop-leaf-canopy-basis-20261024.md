# 잎 생애와 생산·자원·경제 연결 경계 — 2026-10-24

상태: **단위·상태 감사와 저장된 추적 면적의 명시 바닥 면적 환산을 수용**했다.
[계약](../contracts/crop-leaf-canopy-basis-v1.md), [구현](../backend/app/crop_leaf_canopy_basis.py),
[검사](../backend/tests/test_crop_leaf_canopy_basis.py), [실제48건·수용 근거](artifacts/leaf-canopy-basis-20261024.json).
완전한 수관/질량·생산/자원/경제 결합이나 실제 예측·추천 승인이 아니다. 사용자 서버/3D·원 DB/키는 유지했다.

## 실제 모델과 누락된 결합

[1차 문헌·저자 코드 조사](leaf-lifecycle-production-primary-sources-20261024.md)는 SLA의 CH2O/DM 기준,
shoot/plant·바닥 분모, 기관 면적과 질량의 분리 및 제거 원장을 대조했다. 아래는 실제 코드와 대조한 설계 판단이다.

| 현재 구현/권위 | 보존하는 상태·단위 | 연결 전에 필요한 것 |
| --- | --- | --- |
| `crop_leaf_lifecycle.py` / 기존 저장 reader | 선언 초기 잎/미래 출현·제거, ID/부착, 정확 초·열적 나이, 현재 m2와 제거 마지막 m2 | 원 목록은 추적 shoot의 범위다. 전체 실제 수관·leaflet/복엽·면적 정의/측정법·표본 확장 근거가 없다. |
| 이번 `crop_leaf_canopy_basis.py` | 현재 면적/명시 model footprint → `tracked_leaf_area_index`, m2_leaf/m2_floor | 자체 합성 가정으로만 산술 검증한다. 밀도/식물 수로 복제하지 않으며 전체 수관 대표성을 만들지 않는다. |
| `crop_growth_rates.py` / 고정 reference profile | buffer/leaf/stem_root의 mg_CH2O/m2_floor, Tc/PAR/CO2, `SLA_CH2O×leaf`인 LAI | DM 기준 SLA와 호환하지 않는다. 개별 잎 면적을 carbon inventory로 역산하지 않는다. 새 잎 면적이 출현해도 buffer에서 질량을 공짜로 생성하지 않는다. |
| `crop_plant_cohort_rates.py` / integration | 50개 fruit C/N/RGR와 S/W1, 총 fruit C는 구획에서 한 번 파생 | leaf 면적은 착과·개수·초기 C/N·S/W1/RGR를 식별하지 못한다. 기존 과실 총량/구획의 중복 저장·호흡을 피한다. |
| `crop_greenhouse_solar_joint.py` / `crop_climate_joint_rhs.py` | 같은 stage의 SLA 기반 LAI·PAR/NIR·수관 열용량/온도·공기 수분·CO2 | 독립 logistic 잎 면적과 동시에 강제하면 수지 불일치 가능성이 있다. 같은 농장/작기·floor·시계/forcing 결속과 명시 결합 모델이 필요하다. |
| `crop_climate_joint_management.py` / canopy energy transport | 명시 제거 CH2O/m2_floor, capacity/동반 sensible energy와 C/N 수지 | 현재 개별 잎 제거는 면적/마지막 상태만 가진다. 별도 잎별 제거 질량·basis·같은 사건 ID/정확 시각과 연속 유량의 중복 차감 방지가 필요하다. |
| `crop_canopy_exchange.py` / 열·공기 적분 | kg_water/m2_floor/s, W/m2_floor 및 누적 모델 경계량 | 증산은 공급/배수/재순환/양분 투입량이 아니고, 열 경계는 구매 kWh/연료량이 아니다. 실제 설비·효율/제어·계량·요금/정산과 수지가 더 필요하다. |
| `crop_harvest.py` / verified result/current query | 과실 C/N 말단 유출·관리 제거, 별도 명시 DM/CH2O·DM/FW·배정 | 모든 말단 유출을 판매 수확으로 바꾸지 않는다. 수확/적과/폐기·미배정, fresh/등급 H/P/S와 같은 batch를 유지한다. |
| `economics.py` / farm economic execution | Decimal KRW·kg, 같은 기간의 재고/판매/원가/수금과 불변 참조 | 위 모델 수확/자원과 공통 농장·배치의 실행 결속, 농가 계약/등급·시점·시장 판본과 구매 비용이 필요하다. 모델 수확을 사용자 가정으로 재분류하지 않는다. |

따라서 이번에는 생산 RHS를 교체하지 않고, 저장 면적의 바닥 분모를 처음 명시한 단방향 연구 계산을 구현했다.
이것이 질량/시간 결속의 선행 산술이며 전체 production coupling의 완료는 아니다.

## 구현과 검증

명시 합성/assumed 입력만 받으며 기본 바닥 면적·밀도 계수는 없다. 원 lifecycle reader가 원 SHA·입력/준비·권리·부착/UTC/면적을 확인한다.
활성 면적만 나누고 removed 마지막값·pending은 제외한다. 빈 현재 목록은 0이고 큰/작은 양수의 비정상 환산은 hold다.
원 입력 복사본/SHA와 root/result/input/appearance/management/preparation SHA, 원 UTC/정확 초·ID/개수를 보존한다.
입력은 읽기 전에 포착해 조회 중 호출자의 변경으로 원 입력 해시와 표시 분모가 달라지지 않는다.
출력의 `tracked_inventory_comparison_only`와 `gates=not_assessed`는 고정이다. 새 API/DB·worker·저장 판본을 만들지 않았다.

- **RED:** 모듈이 없는 상태의 import 실패를 실제로 확인했다. 개발 실패이며 baseline 통과로 기록하지 않았다.
- **고유202검사:** 새41와 기존 artifact68/export30/preparation63=161이다. 같은 구현의 중간198과 최종41은37개가 겹치므로 합산239가 아니다.
- 새 검사는 원 두 시나리오/24시점×명시 footprint 2개=48환산, 실제 저장한 빈 active 12시점,
  독립 Fraction·비2진 거듭제곱/넓은 규모 분모, 원 값/정확 시각/해시·입력 불변과 조회 중 변경 포착을 포함한다.
  단위/누락/임의 density/coverage 승인·나쁜 값/underflow/overflow·원 저장 변조/접근 보류를 검사했다.
- **fresh 단위 검사:** 자체 합성 세 artifact의 36시점/72환산에서 생장 모듈 import·DB/CLI/network/쓰기 0과 FD 보존을 확인했다.
- **실제 원 저장 결과:** 사용자 재생의 무제거/명시 제거 두 root를 별도 프로세스에서 읽었다. 24원 시점×분모0.5/2.0=48건이
  원 blob의 면적/ID·UTC/정확 초·result SHA와 독립 Fraction 나눗셈에 정확히 일치했다.
  두 분모는 **자체 합성 소프트웨어 가정**이며 실제 면적·밀도·품종 계수가 아니다.
  생장 import·DB/CLI/network/파일 쓰기0, FD 보존과 원 lifecycle62/appearance52/stem29/public40 파일의 bytes·메타데이터를 확인했다.
- **WSL:** .25초 샘플, PID512MiB/합1GiB/phase600초/로그4MiB를 그대로 적용했다.
  마지막 집중/실제 fresh의 PID peak91,918,336bytes, 합557,490,176/533,237,760bytes, 4보호 root 생존·감독FD4→4/소유 잔류0이다.
  관련198 배치도 합572,633,088bytes와 원2,966항목/검사 전후 source 보존을 통과했다.
- **미실행:** 전체 backend/호스티드 CI·이번 변경의 브라우저 시험. UI·실행 서버·기존 물리 모델을 바꾸지 않았고,
  직전 전체 web2248/318은 이전 commit의 증거로 유지한다. 이번 Python 구현의 전체 CI라고 재사용하지 않는다.

## 실제 CLI·출처와 다음 단계

부모 native `gpt-6.1-sol/xhigh`, context `2026-10-24T03:58:33.577Z`, 원 LF SHA
`ec42ad72f3232995f1fd96ddcf1c69176104a8c5a7c247d35e8d17479d28029a`를 기록했다. 재귀 CLI0이다.
research 스킬이 요구한 자식의 실제 spawn 인자도 같은 모델/effort와 fork none이었다. 자식 제안을 부모가 코드/원 단위와 대조했다.
원문 권리/게시·retrieval/available_at 미확보와 PDF·코드 raw hash는 위 조사에 남겼으며 계수/관문을 신규 승인하지 않았다.

다음 작은 구현은 **명시 잎 제거 탄수화물량→기존 공동 탄소·열용량 관리 전이**다.
같은 합성 case의 shoot/leaf·사건 ID와 원점/정확 시각, 별도로 명시한 mg_CH2O와 floor를 결속한다.
분수 초를 기존 정수 초 적분으로 반올림하지 않고 미지원은 보류한다. leaf 면적으로 C를 역산하지 않는다.
원 연속 제거율과 같은 사건의 중복 차감, 제거량 초과/소진·SLA 수관 면적과의 불일치를 먼저 명시한다.
이후 buffer/기관/50과실의 C/N·열용량/에너지 수지와 관리 전후 재개를 확인하며, 면적 성장과 carbon 성장의 feedback은 별도 모델 판단이다.
관리 SourceRecord/현재 농장 실행과 독립 국내 원 자료 획득은 병행한다. 독립 자료 수신을 합성 계약 개발의 선행으로 두지 않는다.

앞 단계70–130집중분 계획은 이번 실적으로 대체한다. 다음은 사건·시간/질량 계약20–35 + 원 관리 전이 adapter20–40 +
독립 수지/반례·회귀25–45 + 기록10–20 = **75–140집중분**, 낮은 신뢰의 작업량 추정이다.
전체 작기·실제 예측/추천 완료일은 국내 원 측정/미사용 독립 작기0·첫 국내 품종 미확정 때문에 미정이며 G0–G4 보류를 유지한다.
