# 과실 CH₂O·건물·생과 환산의 근거와 보류 — 2026-10-06 KST

상태: **부모의 원천·차원 검토 완료, 실제 환산 채택 보류**. `crop-harvest-conversion`의 계수·정책·구현을
수용한 기록이 아니다. 새 코드·농장 자료·작물 Run은 각각 0건이며 G0–G4는
`not_assessed`다. Axiany/Maxifort는 해외 개발 참조이고 국내 방울토마토
한 품종/작기의 생산 적용성은 미검증이다.

[과실 구획 조사](crop-fruit-cohorts-baseline.md),
[원식 등록부](crop-fruit-source-register.json),
[실제 입력 감사](crop-forcing-audit.md),
[미완료 작업](../tasks/todo.md)을 전제로 읽는다.
현재 저장한 `mg_CH2O/m2_floor`의 마지막 구획 유출·명시 제거만으로
생과 수확 kg·등급·판매를 결정할 수 없다. 필요한 연결은 CH₂O→DM의
모델 가정, 같은 과실 모집단의 DM/FW 측정, 면적/밀도, 실제 수확 사건이다.

부모도 원 PDF·model·ReadMe·Production·TomQuality와 고정 예제를 직접 대조했다.
문서와 원천의 해시 및 실제 CLI 관측은 [검토 기록](artifacts/crop-harvest-conversion-review-20261006.json)에
남긴다. 이 개발 조사의 검토 완료는 계수·자료·구현이나 관문 승인과 별개다.

## 조사 실행과 원천 접근

이 노트의 실제 작성자는 부모 CLI 세션에서 분기한
`/root/harvest_mass_basis_review`다. 자식 소유 JSONL에서 다음을 직접 확인했다.

| 관측 항목 | 실제 기록 |
| --- | --- |
| 자식 세션 | `01a10eaa-a45c-7fa3-bfd1-6bbf25fe738a` |
| 부모 세션 | `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` |
| CLI 버전 | `0.160.1` |
| `session_meta` 시각 | `2026-10-06T00:43:46.741Z`; `source.subagent.thread_spawn.agent_path=/root/harvest_mass_basis_review` |
| `turn_context` 시각·모델·강도 | `2026-10-06T00:43:48.056Z`; `model=gpt-6.1-sol`, `effort=xhigh` |
| 원 `session_meta` 행 SHA-256 | `52ef2fb741b0db37e89cd7ff700070c4f8a465dfad3f4c3f068122bc50a949fc` |
| 원 `turn_context` 행 SHA-256 | `f8fc4c2a4be29a5e2fa6d84c5d6ce66e21523dc84983d8779c986df04d56d3b1` |

행 해시는 개행을 포함한 원 bytes 기준이다. 실행 증거는 개발 조사 세션의
관측이며 제품 런타임 호출·독립 검토·서버 승인 증거가 아니다. 실제 출력은 이
Markdown 파일과 부모에게 전달한 출처/보류 기록이다. 재귀 CLI 호출은 0회다.
`engineering-suite:research`의 한 파일 조사 위임을 수행했으며 추가 에이전트,
시험·서버·작물 계산을 실행하지 않았다.

2026-10-06 UTC 재접근에서 WUR thesis PDF는 HTTP 403, PMC 논문은
CAPTCHA, MDPI는 HTTP 429, Figshare API는 web 도구 오류였다.
기존 임시 원본의 SHA-256을 등록부와 대사하고 원 Ch9 추출·기탁 ReadMe·
Reference 파일·논문 HTML을 읽었다. thesis의 게시일은
[WUR 원 저자 등록](https://research.wur.nl/en/publications/a-model-based-greenhouse-design-method/)에서도
재확인했다. GreenLight 고정 원문은 현재 직접 조회했다.
논문/PDF/이미지/원 CSV나 원 코드 전체를 이 저장소에 추가하지 않았다.

## 네 원천이 확인하는 범위

| 원천·위치 | 확인한 근거 | 이번 적용/보류 |
| --- | --- | --- |
| S1 [Vanthoor thesis](https://edepot.wur.nl/170301), Ch9 p245 식9.7 / p265 Table9.1 | 마지막 구획 CH₂O 유출을 적분하는 연속 DM 수확은 단순화 가정. 성장 호흡이 이미 반영되어 `η=1 mg_DM/mg_CH2O`; 표는 lignification 생략 가정 | 생과 수분함량·Axiany 과중 측정이 아님 |
| S2 고정 [model JSON](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json) / [설명서](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/readme.txt) | 단순화된 총 `cFruit` 모델; `mcFruitHar`는 CH₂O 단위의 평활 임계 제거 | 현재 50구획의 실제 수확 시각 검증기로 대체 불가 |
| S2 같은 commit [예제](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/scripts/greenlight_example.py), 원파일184–188행 | **“Assumed fruit dry matter content”**, `dmc=0.06`; `time_step * sum(mcFruitHar) * 1e-6 / dmc` | 0.06은 데모 가정; 품종/작기 실측 계수 미채택. web 파서165–169행과 원파일 행번호가 달라 아래 원hash 기준 |
| S3 [기탁 v2](https://ndownloader.figshare.com/files/24757220) ReadMe p9/p14 / [기탁 metadata](https://api.figshare.com/v2/articles/12764777) | DMC_fruit는 격주 `%`, Weight는 평균g, TSS는 별도°Brix. ProdA/B는 production62.5m² 기준 거래 가능/불가능 화방. 10표본 줄기 개수·g 합계는 별도 | Brix로 DMC 대체 불가. Reference/TomQuality header7/data8열·원 스키마 유효0행; DMC6유한/2결측은 [기존 mapping 후보](crop-forcing-register.json), 미수정/미채택 |
| S4 [Hemming 등 원 실험 논문](https://pmc.ncbi.nlm.nih.gov/articles/PMC7698269/), §2.4/3.3/4.2/Figure1 | Axiany/Maxifort·Reference303·화방 수확. crop-growing76.8m². DMC 평균9.0%는 합친 자료의 설명 통계이며 자료 미제시. INTKAM은 보정 후 수확 대조에도 적심 뒤 작기 말 증가를 충분히 재현하지 못함 | ReadMe62.5m²와 분모 hold. 평균9.0%를 Reference 매 수확일/국내 품종 상수로 승인 불가. 현재 코드·독립 국내 검증의 증거 아님 |

## 차원 대조: 계산 가능한 형태와 아직 없는 입력

아래는 단위 항등식의 대조다. 새 계수를 선정하거나 생산 수치를 계산한 것이 아니다.
`C`, `K`, `N`의 뜻은 [현재 구획 계약](../contracts/crop-fruit-cohorts-v1.md),
누적량/사건은 [현재 적분 계약](../contracts/crop-plant-cohort-integration-v1.md)을 따른다.

| 양 | 현재 의미/단위 | 환산 전에 확인할 것 |
| --- | --- | --- |
| `C_j` / `N_j` | 서 있는 구획의 `mg_CH2O/m2_floor` / `fruits_equivalent/m2_floor` | 실제 과실 정수 개수·생과 무게가 아님 |
| `K_50(t)` / `S_50(t)` | 마지막 구획의 CH₂O/과실 상당수 유량; 각 `/m2_floor/s` | 실제 성숙 판정·수확 시간·등급/처분 아님 |
| `∫K_50 dt` / `∫S_50 dt` | 누적 terminal CH₂O/과실 상당수, 각 `/m2_floor` | 유량에 시간 적분이 한 번 필요; 누적량에 시간을 다시 곱하지 않음 |
| `E_C[e]` / `E_N[e]` | 명시 사건으로 제거한 CH₂O/과실 상당수, 각 `/m2_floor` | 수확·적과·폐기·표본 채취 등 제거 목적과 실제 시각 |
| `η[e]` | `mg_DM/mg_CH2O` | 원 모델 가정과 품종 적용 범위를 구분 |
| `d[e]` | `kg_DM/kg_FW` | 동일 과실 모집단/날짜/숙도·건조법의 검토된 측정 또는 명시 가정 |

같은 제거량 `C_removed`와 같은 과실의 계수라면 단위상

    DM_kg_per_m2_floor = C_removed * η * 1e-6
    FW_kg_per_m2_floor = DM_kg_per_m2_floor / d
    DMC_percent = 100 * d

이다. `1e-6`은 mg→kg의 단위 변환이고 `η`, `d`는 생물학적/모델 근거가
필요한 별도 양이다. S1의 `η=1`이 FW 환산이나 fruit water mass를 제공하지 않는다.
`d=0`·비유한·범위 밖·단위/표본 불일치·결측에는 유효한 나눗셈이 없다.
`DMC %`를 분율로 먼저 바꾸어야 하며 `Weight g`·°Brix로 조용히 채우지 않는다.

시간별 `η(t)`·`d(t)`를 쓰려면 각각의 해당 terminal 과실 적용성이 필요하다.
그때의 형식은 `∫ K_50(t) * η(t) / d(t) dt * 1e-6`이다.
전체 누적 CH₂O를 격주 DMC의 단순 평균으로 나누는 것은 일반적으로 이
적분과 같지 않다. 같은 대상/기간의 bulk `d=ΣDM/ΣFW`를 확인한 경우와
몇 개 표본의 산술 평균을 구분한다. 보간·외삽·결측 대체·전작기 상수 선택은
측정 자체에서 나오지 않는 추가 가정이며 이번에 채택하지 않았다.

작기 중 실측 DMC는 형식/QC·표본 대응을 해결한 뒤 해당 시점의 **사후 환산 대조**에
쓸 자료 후보다. 정식/발주 결정 `D` 뒤 측정된 DMC를 당시 미래 생산 입력에 넣으면
미래 정보가 누출된다. 입력용 판본은 `available_at≤decision_at`의 확인이 필요하며
이번 `available_at` unknown 상태에서는 미래 적용을 보류한다. AGC 전체 작기를
보고 계수/환산을 개발하거나 보정한 뒤 같은 작기를 다시 대조하는 것은 독립 미래
검증이 아니다. [결정 시점·판본 계약](../docs/MARKET_INTELLIGENCE.md#5-가격-단계와-출처시각-계약).

제거 과실 상당수로 평균 과중을 나타내려면 같은 제거의 `E_N>0`가 필요하다.
`E_C/E_N`은 `mg_CH2O/fruit_equivalent`이고 같은 `η/d`와 단위 변환을
거쳐야 FW/과실 상당수가 된다. 연속 상당수에서 실제 개별 과실의 정수,
크기 분포나 등급 분포를 만들 수 없다.

## 연속 terminal·관리 제거·수확·판매의 대조 조건

현재 적분은 terminal과 관리 제거를 이미 서로 다른 C/N 누적량으로 보존한다.
관리 사건은 같은 구획의 N/C에 같은 비율을 적용하는 연구 입력이다.
그 입력은 해당 구획의 평균 CH₂O/과실 상당수를 유지하며, 특정 크기·등급을
선별한 실제 수확의 관측을 제공하지 않는다.
[현 적분 사건과 수지](../contracts/crop-plant-cohort-integration-v1.md).

후속 검토에는 각 제거의 ID, 수확/적과/폐기/채취 목적, crop/result/input version,
정확한 원시각과 시간대·UTC 변환, 대상 구획/배치, 제거 전후 C/N, 실제 계수
측정 ID, 질량/개수·면적 분모·저울/실험실 QC, 숙도와 줄기/꽃받침 포함 범위가
필요하다. 이 목록은 누락 근거를 식별하는 조사 조건이며 새 사건 스키마가 아니다.

terminal로 이미 빠진 같은 과실을 나중의 harvest 사건에 다시 더하면 수량이
중복된다. 수확 날짜별 표시를 위한 terminal의 배정과, 서 있는 구획에서 새로
제거한 양은 어느 원량에 속하는지 대사해야 한다. 실제 수확 관측과 모델 terminal의
시간별 차이도 보존한다. boxcar 마지막 이동을 상업 수확 달력으로 재명명하거나
terminal 전체와 관리 제거 전체를 무조건 합산하는 근거는 확보하지 못했다.
실제 수확 관측 `H`가 있더라도 모델 제거와의 연결/오차를 검토하기 전에는
그 관측을 모델 예측으로 표시할 수 없다.

`H`는 수확 FW, `P[t,g]`는 선별 뒤 판매 가능량, `S[t,g,h]`는 계약 조건을
충족한 판매 인정량이다. 모델 CH₂O·DM·FW의 환산으로 grades/packout이나
`S`가 생성되지 않는다. AGC A/B는 해당 실험의 화방 품질 정의이며 국내
품종·포장·채널 등급과의 대응은 미확인이다. A의 거래 가능성이 실제 판매/검수/
정산을 증명하지 않으며 B의 경진대회 가치를 판매로 바꾸지 않는다.
후속 연결은 grade/불량·미판매·폐기·반품·재고 및 날짜를 대사하는
[경제 H/P/S 계약](../docs/ECONOMICS.md#3-판매량가격비용-공식)과
[시장 판본/채널 계약](../docs/MARKET_INTELLIGENCE.md#5-가격-단계와-출처시각-계약)을
그대로 전제로 한다. 이번에 경제 원장이나 금액을 생성하지 않았다.

## 면적과 식재밀도의 대조 조건

동일한 절대 수량을 다른 분모로 나타내는 경우에만
`q_floor=q_source*A_source/A_floor`가 성립한다. `kg/m2_production`을
`kg/m2_floor`로 이름만 바꾸거나 전체96m²·crop-growing76.8m²·production62.5m²를
혼합할 수 없다. 어느 면적이 Reference303과 표본/생산량의 모집단에 해당하는지
도면·ReadMe/제공자 설명과 원 수확 합계로 확인해야 한다.
[기존 면적 hold](crop-forcing-audit.md#면적관리생과-환산경제).

10표본 줄기의 수확 g·개수 합계는 해당 표본 합계다. 단위상 `/10`으로
표본 줄기당 평균을 얻을 수 있어도 같은 면적 분모의 당시 stem density와
대표성·추가 줄기/표본 교체를 검토해야 구역 전체와 비교할 수 있다.
plants/m²와 stems/m²는 서로 다른 양이다. `nPlants`나 코드의 초기3.12밀도를
Reference의1.4 plants/m²·4→8 stems/m²와 혼합하지 않는다.
기탁 밀도의 분모/관리 시각은 [원 입력 감사](crop-forcing-audit.md)에서 아직 보류다.

## 확보하지 못한 근거

| 보류 | 실제 필요한 확인 | 현재 상태 |
| --- | --- | --- |
| CH₂O→DM 적용성 | 원 모델의 호흡/조성 가정과 해당 과실의 DM 대조·계수 version | S1은 참조 가정; Axiany/국내 적용 미수용 |
| DM→FW 표본 | 품종/대목/작기·숙도/등급·sample ID·개수·FW/DM 쌍·건조 온도/시간/종점·저울 QC·표본/기간 대표성·불확실성 | S3의 원 ReadMe/CSV에서 방법/표본범위 확인 불충분; header/결측 hold |
| 계수의 시간 범위 | DMC 관측일과 수확 대상의 대응, 측정 불확실성, 독립 기간의 DM/FW 대조 | 격주 표본·전작기 적용/보간/외삽 미수용; S2의0.06/S4의9.0% 기본값 미채택 |
| 실제 수확 사건 | Reference 날짜 이상값의 원 정정, 시간대, 화방/과실·제거 목적·성숙/배치·N/FW 합계 | Production 첫 serial43510의 작기 밖 날짜·개별 사건 부재 hold |
| area/density | Reference에 적용되는 면적·stem/plant 분모와 기간별 관리, 표본 확장 근거 | 62.5/76.8/96m²와 밀도 정의 hold |
| grade/H/P/S | 등급 판정·packout/불량 원 기록, 판매/반품/재고·계약/정산 연결 | AGC 품질 정의만 확인; 국내 대응/판매자료0건 |
| 독립 적용 검증 | 개발/보정에 쓰지 않은 국내 한 품종/작기의 수확·DM/FW·grade 대조 | 국내 독립 자료0건; 미래 생산/마진/순위 보류 |

위 조건이 해결되기 전 생과 시계열·실제 수확·등급·판매를 생성할 근거는 없다.
합성 계약 검증에 별도의 명시 가정을 쓰는 것과 실제 품종의 생산 검증은
[제품 claim gates](../docs/PROJECT_SPEC.md#6-검증과-수용-관문)의 서로 다른 증거다.
체크박스·의존성·구현/계수·gate 판단을 변경하지 않았다.

## 원천 시각·판본·권리·해시

모든 `available_at`은 **unknown/null**이다. 공개/기탁일과 당시 농장 결정의
실제 접근 가능 시각을 같다고 재구성하지 않았다. 관측 시각은 새로 승인하지
않았고 S3 Excel serial의 epoch 후보/시간대 hold를 유지한다.
기존 retrieval은 [과실 등록부](crop-fruit-source-register.json),
[forcing 등록부](crop-forcing-register.json),
[원 모델 등록부](crop-tomato-source-register-20261004.json)에서 가져왔으며,
캐시 재검토를 신규 다운로드로 기록하지 않았다.

| ID / 제품·판본 | publication / observation / retrieval | units / QC / use·display·redistribution |
| --- | --- | --- |
| S1 `10.18174/170301`; 원 thesis | 게시2011-06-17(WUR 확인); 이 식의 신규 관측자료없음; 원 retrieval `2026-10-04T08:51:13.324303+00:00` | CH₂O·DM/m² 및 유량; 원 PDF hash 일치·Ch9/Table9.1 대조; 수학적 정의 연구/짧은 인용만, fulltext/그림 재배포권 unknown·미채택 |
| S2 commit `7a7b36870135aa38bbe81e65590dcf5473786bdd` | pin commit 시각`2026-09-09T16:00:54Z`; 모델 파일 고지May2025·예제 copyright2025, 최초 파일 배포시각unknown; 관측자료없음; model 원 retrieval `2026-10-04T08:47:16.425493+00:00`; example 신규 retrieval `2026-10-06T00:46:15.796102+00:00`, 재조회`00:46:31.512058+00:00`; readme 신규 retrieval `2026-10-06T00:46:16.044454+00:00` | model CH₂O 유량·예제 DM/FW분율; pin/model·readme hash 일치, 예제 두 직접 조회 동일hash; BSD-3-Clause-Clear, 재사용/표시에 copyright·conditions·disclaimer 유지 및 endorsement 제한; 원 코드 재배포하지 않음 |
| S3 DOI `10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7`; article12764777 v2/file24757220 | 판본 게시`2020-09-23T10:41:39Z`; 실험2019-12-16/2020-05-29, Reference quality 후보2020-02-19/2020-05-29(UTC미확정); archive/내부파일 원 retrieval `2026-10-04T08:49:39.307459+00:00` | production kg/m²·표본g/개수·DMC%; 원 ReadMe/CSV hash 일치·기존 QC hold 유지; v2 metadata CC0 선언, 원본 연구 열람·자체 요약만, 개별 공지/이미지/자료 표시 적용성 미채택·원 archive/CSV/PDF 재배포0 |
| S4 `10.3390/s20226430`; 원 published article HTML | 게시2020-11-11(원HTML meta); 실험2019-12-16/2020-05-29; 원 retrieval `2026-10-04T08:49:34.622494+00:00` | 과실FW·DMC·면적/실험 조건의 설명; 기존 HTML hash 일치·§2.4/3.3/4.2/그림caption 대조; 원 등록부CC-BY-4.0·저자/출처/권리 표시, fulltext/그림/HTML 재배포0 |

현재 원천 재검토자는 위 자식 CLI 세션의 Codex다. 부모의 이후 대조는 별도
검토이며 이 노트 작성 시점에 독립 승인자로 기록하지 않는다. 다음 hash는
실제로 읽은 원 bytes의 SHA-256이며 source adoption이나 gate 통과를 뜻하지 않는다.

| 원 bytes / product locator | SHA-256 / bytes |
| --- | --- |
| S1 원 PDF | `965ecc5573290d0cc59b514e9766b301f9584d212545dec177efa66dd756ac38` / 3,423,075 |
| S2 model JSON | `272a589edf0bb40d1a91b34e883f8e94b9adf747a576be4620c50296c03d7033` / 26,741 |
| S2 model readme | `9e5ca837f6be1524886550f2c00d0ddab0cf980fd4be778e7e8d3532f4239ad9` / 2,581 |
| S2 example script | `f36f9db841298eb6e9d0c8ec11eaebf22ac56c730cd0a8f086a8b2e4ca761bbd` / 8,397 |
| S3 archive（기존 등록부 값; 이번 archive 재해시는 안 함） | `b889e9ab1663fe3b8a90a3dab71d4340a6ecd49492532c43784cc82d799708ca` / 8,418,715 |
| S3 ReadMe.pdf | `e884cc347088bac498b730eaf442ccb9593c7aa84d4f85090b1fe2927646509c` / 733,072 |
| S3 Reference/TomQuality.csv | `7f15759110c8df57efb376fa6f0808d076fbe143e436059f21b6df2243ac0978` / 395 |
| S3 Reference/Production.csv | `5124bacfd527a155c7fde61762a793a3192546253e9f442b42b7583ba3a69b65` / 1,086 |
| S3 figshare metadata（원 캐시） | `56d641d0da19c6750020a48ae92da642dc7a4aa82e3e857190643fb2f6741ce6` / 8,797 |
| S4 article HTML | `a67e101b95b7337806fd51413eb2687467c358ae7b94d824742f293d6791a6ca` / 282,743 |

검증은 문서/원 bytes 읽기·hash 대조·차원 대조와 상대 링크/anchor17개 확인에
한정했다. 누락 링크/anchor와 줄끝 공백은0개였다. native/CI 시험,
실제 작기 적분·생과 계산·실측 validation·서버 gate 검사는 실행하지 않았다.
부모의 진행 중 native/CI 증거와 별개이며 기존 불변 결과를 수정하지 않았다.
