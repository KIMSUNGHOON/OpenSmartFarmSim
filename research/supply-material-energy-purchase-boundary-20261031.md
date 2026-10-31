# 저장 열·수분에서 구매량·비용으로 넘어가는 경계 — 2026-10-31

현재8counter의 의미·부호·단위와 기존 Decimal 원장을 대조해
[조건부 비용 결속 계약](../contracts/supply-material-resource-economics-binding-v1.md)을 작성했다.
**조사·입력/수용 계약을 수용한 단계이며 새 비용 계산이나 UI 연결은 아직 구현하지 않았다.**
[기존 화면](http://localhost:5184/supply-material-quantities-replay.html)은17:03 KST 첫 만료까지 그대로 유지한다.
[1차 출처/8항목 표](supply-material-energy-primary-sources-20261031.md),
[기계 증거](artifacts/supply-material-energy-boundary-20261031.json).

## 판단과 다음 구현의 범위

내부 현열/잠열은 수관·공기·수증기의 reduced-energy 수지에서 상쇄된다.
열용량 유입/유출 에너지는 `Tref` 상대값이며 외부 forcing도 설비·구매 경계를 식별하지 않는다.
단순 합·절대값·양수 절단으로 구매 수요를 만들지 않는다.
DOE의 [COP 정의](https://www.energy.gov/cmei/femp/purchasing-energy-efficient-geothermal-heat-pumps)는
열출력/전기입력의 관계다. 이 미국 주택 설비 안내의 예시 효율·가격을 온실에 적용하지 않았다.
NIST의 [정확 단위 관계](https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8)는
단위 변환 근거이며 구매 전기·설비 성능이나 농장 면적의 근거가 아니다.

기존 [EconomicNumber/Cost](../backend/app/economic_contracts.py)와
[Decimal 원장](../backend/app/economics.py)을 재사용한다. 원장/권한/산술을 우회하는 두 번째 계산기를 만들지 않는다.
현재 지원하는 전기 `kWh_e/KRW/kWh_e`, 품목이 명시된 연료/물 `L/KRW/L`의
**독립 사용자 가정 구매량·단가**는 원 소유 입력·기간·등급을 보존해 조건부 비용에 사용할 수 있다.
이는 model8counter에서 도출한 값이 아니다. `kWh_th/kWh_fuel/m3`나 `measured/quoted`를
기존 단위/assumed로 바꾸어 통과시키지 않는다.

결속에는 원 root/projection/result SHA와 exact window, 별도의 불변 economic scenario/Cost/input 참조,
관계 `independent_user_assumption`, 구매/청구 기간·포함/누락 범위가 필요하다.
원 분수 초를 반올림해 비용 발생/지급 사건을 생성하지 않는다.
수초 연구 창과 한 달 가정 비용을 같은 기간의 모델 비용으로 표시하지 않는다.
현재 연구 root에는 소유 FarmScenario/제품 작업 결속이 없으므로 그 연결은 별도 수용이 필요하다.

## 발견한 생산 배치 경계

현재 `_costs`는 production 비용의 batch가 평가기간 harvest 목록에 있어야 한다.
동일 기간 후반의 명시 수확보다 먼저 발생한 비용은 지원할 수 있다.
그러나 **기간 전체에 수확 사건이 없는 재배 중 batch의 직접 생산비**는 현재 받지 않는다.
기간 비용을 누락하거나 수확0 사건·가짜 판매를 만들거나 직접비를 period로 바꾸지 않는다.

따라서 작물이 재배 중인 평가기간의 비용을 연결하려면 명시 생산 batch·직접비·미수확/미판매
비용·달력/현금 대사를 먼저 지원해야 한다. 실제 공통 기간 비용의 기존 조건부 계산은
이 배치 작업과 병행할 수 있으며 농장/구매 자료 확보를 기다려 소프트웨어 개발을 중단할 필요는 없다.

## 실제 검증

- 기존 코드의 관련 **28검사**를 현재 source에서 통과했다. area 기준온도4/legacy1,
  음수 교환1/latent·capacity의 공기 중복 가산 차단1, Decimal exact/초과2,
  숫자 문자열8/단위·등급 등 metadata7, 소유 입력1/모델 재검증1/Cost 목적1/무수확 batch1이다.
  실행0.56초·guard2.121초/PID112,140,288bytes/합계282,370,048bytes였다.
- 별도 프로세스에서 기존 자체 reference4사례를 128자리 Decimal 컨텍스트에서 기존 독립 reference 값과 대조했다.
  같은 열용량·gross flow·온도 변화율에도 기준온도를 바꾸면 유입/유출 에너지가 양수에서 음수로
  바뀜을 확인했다. 기존 fixture를 변경하거나 농업/설비 매개변수로 채택하지 않았다.
- 같은 프로세스에서 원101CAS를 읽어 실제4state quantity 응답을2.128117초에 재조회했다.
 40,481bytes/SHA `ccc1d63a51279017b4b8400d8dfc5cbb59da8b23a7be899858ecb273f2010dbd`가
  수용된 원 결과와 같고8단위·음수 외부 수증기·정확 source 창을 보존했다.
  이 조회의 성장/RHS·DB/network/CAS쓰기·process/CLI 진입0, FD4→4와101CAS metadata를 확인했다.
  앞선4개의 순수 reference 산술은 조회 이후 계측0에 섞지 않았다.
- 이전 화면687source/4output/private745/외부 phase46·추가3pin과 이전 CAS/GUI 계보,
  새 화면238파일의 실제 HTTP bytes/hash/no-store/CSP·PID/boot/ticks·첫 만료를 대사했다.
  보존 guard6.386초/62,767,104/233,009,152bytes·소유 자손0·FD4→4였다.
  원4500감시 항목과 기존 화면/자료는 보존했다. Windows Chrome/전체 host RSS는 새로 측정하지 않았다.

1차 연구는 스킬이 요구한 native 자식의 실제6.1-sol/xhigh/CLI0.166.0과 원 turn/output 지문으로 기록했다.
부모의 현재 실제6.1-sol/xhigh/CLI0.157.1 turn `2026-10-31T02:11:50.433Z`에서 독립 코드/정의·계약과
대사 출력을 검토했다. 재귀 CLI0이다. DOE/NIST 정의·권리의4개 원 HTTP200·raw hash/발행·수집 시각·
권리/미확인 available_at·QC는 위 1차 조사와 private 영수증에 있다. 제3자 원문은 repo에 넣지 않았다.
독립 농장 검증·새 G0 자료/매개변수·요금 채택은0이다.

## 다음 수용 기준과 추정

다음 계산 자식은 **명시 미수확 생산 batch의 기간 비용**이다. 기간 안 수확0건인 명시 batch에도
원 가정 직접비를 한 번만 비용 처리하며, 수확·판매 사건을 만들지 않아야 한다.
원 batch/Cost/input 판본·tenant/decision/기간·목적을 대사하고 Decimal 독립 산술,
같은 기간 후속 수확·미수확/미판매·기초 재고/과거 비용 재부과·월별 지급/미지급,
입력 불일치·누락/중복·현재/늦은 변경과 기존 원장 회귀가 수용 기준이다.
기존 schema3/원 실행/결과/화면을 보존하는 새 판본으로 개발하며 실제 농장 게시를 자동 해제하지 않는다.
첫 커널/새 입력 계약·집중 검증 **3–5집중시간 초안**이고 API/worker/SDK/UI는 포함하지 않는다.
세부 코드 경계와 실제 검사 후 후속 연결 공수를 갱신한다.

그다음 원 저장 창·소유 경제 입력 결속→strict SDK/같은 선택 UI로 진행한다.
독립 자료 확보와 긴 작기/반복 성장·품종 모델 개발은 병행한다.
실제 구매량은 설비·계량·급배액/재순환·가격 계약/청구와 권리의 외부 의존성이 남는다.
생과중·수확/판매, 독립 국내 농장 raw0·경제/거시·수급·자율 비교·최종 제품/R2도 미완료다.
G0–G4 미평가·R2 미승인·전체 goal active/incomplete·전체 완료일 미정을 유지한다.
새 경제 adapter·API/UI·전체 suite/새 browser/hosted CI는 이번 단계에서 실행·수용하지 않았다.
