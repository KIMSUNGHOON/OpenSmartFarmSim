# 명시 LAI와 기관·50과실 탄소 수지 — 2026-10-24

상태: **부모 연속 결합의 같은 stage C/N RHS 자식 수용**. 재고를 시간 전진시키거나 예측을 게시하지 않는다.
[계약](../contracts/crop-explicit-lai-carbon-cohorts-v1.md), [구현](../backend/app/crop_explicit_lai_carbon_cohorts.py),
[검사](../backend/tests/test_crop_explicit_lai_carbon_cohorts.py), [검증 근거](artifacts/explicit-lai-carbon-20261024.json),
[후속 순서](../contracts/crop-geometry-carbon-coupling-research-v1.md).
기존 모델/프로필·저장 결과/3D·서버·DB/키를 바꾸지 않았다.

## 실제 의존성과 변경

기존 `crop_plant_startup_rates`는 전체 `crop_growth_rates`에서 SLA 기반 광합성을 계산한 뒤,
빈 과실 sink의 요청 F를 effective/deferred로 나누고 buffer 보정·실제 과실 성장 호흡을 함께 반영한다.
이 전체 함수를 호출하고 P만 덮어쓰면 새 LAI가 유효해도 이전 SLA 보상점 검사에서 먼저 중단될 수 있다.

새 `calculate_plant_rates`는 원 닫힌 state/50 C/N/RGR·forcing·제거·S/W1와 명시 geometry를 받는다.
원 profile 타입/바이트·공통 계수·같은 T24/Tsum·post-onset/유한 수량/단위를 먼저 확인하고,
명시 광 동화1회와 비광학 분배/잎·줄기 fixed RGR 호흡을 따로 계산한다.
기존 파일의 non-optical 식을 새 조립에 명시적으로 옮겼다. 원 파일/저장 지문을 바꾸지 않는 선택이며
동일 LAI의22개 기존 참조·전체 source SHA로 이 식의 차이를 검출한다. 새 농업 계수는 없다.

그다음 기존 public startup/50과실을 각1회 사용해 유효 유입만 과실로 보낸다. 유보 F와 회피한 성장 호흡을
buffer에 같이 반영하며, 과실 유지 호흡/말단 C/N은 구획에서만 가져온다. 별도 과실 총량/호흡을 이중 보유하지 않는다.
최종 buffer/leaf/stem의0 저장량이 밖으로 흐르면 hold하며 C/N 미분·호흡·제거/말단/P 전체를 대사한다.
양의 기하/0 leaf C 관계는 이 연구 부품에서 미지원으로 보류한다. 면적에서 C를 역산하지 않는다.
source/profile/정책·raw/정규 입력·component SHA, 명시 면적/재고/미분·유보와 수지를 보존한다.
새 복합 모델은 연구 가정이며 전체 수관 대표성·기관 질량 분배/실제 품종 검증을 의미하지 않는다.

## 통과한 증거

- **RED:** 새 모듈 부재 import 오류를 실제 확인했다.
- 첫 검사39통과/1실패는0 buffer에서 기존 명시 과실 진입이 요청 F를 초과해, 기대했던 고갈 검사보다
  entry budget hold가 먼저 난 fixture였다. 같은 물리 guard를 유지하고 S/W1을0으로 명시해 최종 고갈 검사를 시험했다.
- **고유324검사:** 새67/기존 startup78·plant cohort43·광 동화136=257. 같은 구현의 전체324 뒤
  새67을 마지막으로 재검사했으며 중복 합산391이 아니다.
- 기존22사례는 같은 LAI에서 원 전체 참조/배분·과실/유보/P·미분과 대사했다.
  [독립120자리 oracle](crop-explicit-lai-carbon-reference.py)은 app 없이 기존 독립 과실 참조와
  별도 비광학/명시 광학 식으로 [다른 LAI24사례](../fixtures/crop-explicit-lai-carbon-reference-v1.json)를 생성했다.
  23계산/1보상점 hold이며, 기존 SLA 영역 밖이지만 명시 기하가 유효한 경우도 포함했다.
  기존 geometry로 대체하거나 forcing·leaf C를 조정해 통과시키지 않았다.
- unit은 빈 sink/첫 진입·작고 큰 tail·동시 buffer/호흡 보정·C/N/temperature·input hash/alias,
  잘못된 단위/수량·공유 상태/개수·entry/면적·고갈과 반쪽 startup 보정의 거부를 확인했다.
  반환 잔차를 출력된 모든 원 항의 fsum으로도 다시 계산했다.
- **fresh46사례:** 같은 LAI22+다른 LAI24의45계산/1hold를 별도 프로세스에서 실행했다.
  각 성공의218개 원량, 합9,810개 독립 값을 대사했고4,744개0 참조는 정확0이었다.
  최대 상대 차이4.0124773169261425e-15는 사전5e-12/24ulp 기준 안이다. 참조는 동일 bytes로 재생성됐다.
  광 동화/그 helper46회, startup/50과실45회다. 성공마다 각1회이고 보류1회는 P 영역에서 멈췄다.
  기존 전체 plant carbon/plant-cohort RHS·적분/기관 advance·DB/CLI/network/쓰기0, FD 보존을 확인했다.
- **WSL:** .25초 샘플/512MiB PID·합1GiB/600초/로그4MiB를 유지했다.
  전체324는 PID peak91,000,832/합520,540,160bytes, 최종67은 합514,740,224bytes,
  fresh는 합486,105,088bytes다. 원2,966항목/전후 repo source·4root 생존·감독FD4→4/소유 잔류0을 확인했다.
- **미실행:** 전체 backend/호스티드 CI·브라우저, 새 열·물/연속 궤적·새 출현/관리·실제 농장/품종·미래/비교/배포 검증.
  기존 UI CI는 이전 UI commit의 증거이며 이번 Python 코드의 전체 CI로 쓰지 않는다.

## 실제 판단과 다음 의존성

부모 native Codex CLI gpt-6.1-sol/xhigh, context2026-10-24T04:57:05.334Z와 원 LF SHA
`86153aa9ae1b91690e519b5cc00519cca813de0a2de352dee80f7bdd0733c30f`를 기록했다. 재귀 CLI0이다.
기존 [1차 source/권리·모델 판단](continuous-leaf-carbon-primary-sources-20261024.md)과 고정 source/프로필을 재사용했다.
새 원문/매개변수·측정 자료/관문 채택0이다. 현재 함수가 최초 G1 제품 CLI/농장 실행의 승인을 대신하지 않는다.

다음은 **독립 면적의 열용량·현열 경계**다. 기존 수관 용량과 material heat는 SLA×C·분배/호흡·제거를 따라간다.
새 LAI/dLAI를 쓰면서 이를 그대로 재사용하지 않는다. 면적당 열용량 가정과 변화율·물질 운반의 필요한 독립 입력,
현재 Tc/기준 온도·signed U/dU의 chain-rule 수지를 원문/기존 코드로 대조하고 가장 작은 명시 계산을 정한다.
면적 변화만으로 유입/유출 열·온도를 채우거나0으로 기본 설정하지 않는다. 그 뒤 짧은 구간→정확 사건→다음 구간/재개다.
새 출현 질량·공급 제한/관리 C·농장/현재 source·전체 수관/작기·열/물·생과/등급/경제와 게시 관문은 후속이다.
관리 SourceRecord/현재 농장 실행과 국내 독립 원 자료 확보는 병행한다. 원 측정/미사용 국내 독립 작기0·첫 국내 품종 미확정이다.

앞의80–145집중분은 이 순간 C/N 자식의 실적으로 갱신하며 부모 완료로 처리하지 않는다.
다음 열 경계는 원 가정/필수 입력15–30 + 최소 순수 계산20–40 + 독립 chain-rule/장부·회귀25–45 + 기록10–20 =
**70–135집중분**, 낮은 신뢰의 개발 작업량이다. 실제 열/물·전체 연속 구현/자료 확보·예측/경제 검증과 제품 완료 시간은 포함하지 않는다.
전체 완료일과 실제 생산·자원/경제·추천/R2/G0–G4는 미정/미완료다.
