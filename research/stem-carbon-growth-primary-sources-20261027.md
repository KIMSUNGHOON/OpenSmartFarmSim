# 줄기·뿌리 탄소 배분과 신장 결합의 1차 근거 — 2026-10-27 KST

현재 근거로 먼저 구현할 수 있는 것은 **기존 줄기+뿌리의 새 구조 CH₂O 유량을 명시 절간과 명시 뿌리 구획에 보존적으로 나누는 순간 산술**이다. 이것만으로 개별 기관의 현재 재고나 공급 제한 신장을 계산했다고 하지 않는다. Smoleňová 등(2025)은 절간 길이와 biomass를 독립적으로 계산한다. GreenLab의 토마토 사례는 기관 건물 배분과 실측 allometry의 선례이며, 현재 품종에 적용할 질량→길이 계수를 제공하지 않는다.

[README](../README.md), [명세](../docs/PROJECT_SPEC.md), [연구 기준선](../docs/RESEARCH_BASELINE.md)과 기존 [잎 sink 조사](leaf-carbon-sink-primary-sources-20261024.md), [토마토 형태 조사](tomato-morphology-primary-sources-20261021.md), [새 잎 조달 판단](crop-leaf-funded-births-design-20261026.md)을 읽고 다음 범위를 대조했다. 계수·품종·관측 자료의 신규 채택은 0이다.

## 실행과 검토자의 범위

research 스킬에 따라 부모가 background 연구자를 위임했고 추가 자식은 만들지 않았다. 부모가 전달한 collaboration API의 명시 모델 요청은 `gpt-6.1-sol` / `xhigh`다. **이 연구자의 실제 native turn context는 직접 관측하지 못했으므로 요청값을 검증된 자식 실행 증거로 쓰지 않는다.** 새 Codex CLI를 실행한 횟수는 0이다.

부모가 기존 CLI 로그에서 읽어 전달한 현재 부모 증거는 다음과 같다. 관측 `2026-10-26T16:39:40.677799Z`, turn context `2026-10-26T16:34:47.652Z`, model `gpt-6.1-sol`, effort `xhigh`, 원 LF SHA-256 `ec7abfa12c7b7c55cb7a1c7ccdf3e228512e4797229d733ea7e31b39055608fe`. 이는 **부모 검토의 증거**이며 이 연구자가 그 원 로그를 직접 확인했다거나 자식 호출을 증명했다는 뜻이 아니다. 검토자는 위임된 Codex 연구자와 부모이며 독립 농업 검증자·G0 승인자는 없다.

## 직접 확인한 관계와 재사용 경계

| 1차 근거 | 확인한 관계 | 이번에 지지하는 범위와 남은 조건 |
|---|---|---|
| S1 [Vanthoor(2011), Ch9](https://edepot.wur.nl/170301), DOI `10.18174/170301`, §9.2–9.3, 인쇄 pp242–243 | 면적 기준은 온실 floor다. `CStem`은 줄기와 뿌리의 결합 CH₂O 재고다. | `CStem`을 절간만의 질량으로 취급하거나 절간 수·길이로 기존 재고를 배분할 근거가 없다. |
| S2 [고정 GreenLight JSON](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json), `cStem`, `mcBufStem`, `mcBufAir`, `mcStemAir` | `mcBufStem = hBufOrg × hTCan24 × gTCan24 × rgStem`; `dCStem/dt = mcBufStem − mcStemAir`. 생장호흡의 기여는 `cStemG × mcBufStem`이며 buffer에서 따로 나간다. | 재사용 대상은 기존 집계 유입과 기존 호흡 비용이다. `mcBufStem`은 유지호흡 차감 뒤의 순 상태 미분이 아니다. 각 배분처에서 같은 생장호흡을 다시 부과하면 이중 비용이다. |
| S3 [Smoleňová 등(2025)](https://doi.org/10.1093/insilicoplants/diaf022), §2.1.4/2.3 | 공통 동화 pool과 기관별 잠재 beta 생장에 따른 상대 sink 분배가 있다. 한편 절간 신장·폭은 biomass와 별개의 logistic 함수로 계산한다. | 기관 분배의 개념적 근거다. 탄소 부족 때 기존 logistic 신장률을 줄이는 법칙이나 계수의 근거가 아니다. |
| S4 [Dong 등(2008)](https://pmc.ncbi.nlm.nih.gov/articles/PMC2710282/), DOI `10.1093/aob/mcm317`, Methods Eq(3), Table1, geometry 문단 | `Δq_o(i,j) = [P_o f_o(j) / D(i)] Q(i−1)`. 기관별 증가 **건물**을 생장 cycle마다 배분한다. 뿌리계는 하나의 기관이며 별도 sink를 가진다. 절간 건물중과 길이·직경의 관계는 실험 조건마다 측정했다. | 명시 뿌리 구획과 상대 배분의 선례다. 연속 CH₂O 식·현재 품종 allometry·초기 재고나 보편 sink 계수로 직접 옮길 수 없다. 밀도 사이 일부 매개변수의 안정성에도 한계가 있었다. |

S2의 flow `unit` 문자열에는 `m**2`가 있지만 대응 state 단위·상태식·S1의 floor 규약은 `mg_CH2O/m2_floor/s`를 요구한다. 원 파일의 문자열과 프로젝트가 확인한 rate 차원을 같은 것으로 보고하지 않는다. 이번에 그 상위 파일을 수정하지 않았다.

S3는 단일 줄기 어린 토마토가 대상이다. §2.2.1/2.3은 절간별 생체중과 형태를 측정하고 기관 유형·개체·수확 시점별 건물률로 개별 건물중을 추정했다. 길이와 biomass의 관계가 절위·시점에 따라 일정하지 않아 독립식을 택했다. §2.4/4.1은 초기 보정 자료가 부족해 첫 수확 시점의 실측 기관 무게·크기로 상태를 보정했다고 설명한다. 기존 열적 나이·길이만으로 초기 탄소 재고가 정해진다는 근거가 아니다.

## 단위와 표현 대상

다음은 원 자료를 혼동하지 않기 위한 프로젝트 해석이며 새 환산계수 채택이 아니다.

- 현재 `mg_CH2O/m2_floor`는 모델의 탄수화물 상당 질량을 floor 면적으로 나눈 양이다. 변수 이름 `C`를 원소 탄소 자체의 mg로 바꾸어 읽지 않는다. 절간에 배분해도 같은 floor 분모를 가진 기여량이다.
- S1 Table9.1, 인쇄 p265의 CH₂O→건물 계수는 `ηC_DM = 1 mg_DM/mg_CH2O`이고, 근거란은 lignification을 가정하지 않는 모델 규약이다. 실제 절간의 조성·건물률·밀도나 현재 품종 물성의 측정이 아니다. 이번에 이 계수를 새 기관 환산으로 채택하지 않는다.
- S3/S4의 개체·기관 건물 g/mg와 현재 CH₂O/floor는 분모와 물질 정의가 다르다. 실제 한 기관 질량으로 바꾸려면 그 기관 집합이 대표하는 명시 floor 면적과 물질 환산 근거가 필요하다. 화면 개체 수나 절간 수를 밀도로 대체하지 않는다. 한 포기의 여러 줄기에 같은 뿌리계를 중복 계상하지 않는다.
- 생체중에는 물이 포함된다. 건물→생체중에는 같은 기관·시기·관리 조건의 건물률이 필요하고, 기하 volume을 쓰려면 대응 밀도·단면·형태 가정도 필요하다. 길이 하나로 이 값들이 정해지지 않는다.
- 열적 나이에 따른 잠재 길이 속도와 `mg_CH2O/m2_floor/s`의 구조 형성 속도는 차원이 다르다. 비율을 곱해 결합할 때에도 잠재 수요의 정의·시간 기준·allometry를 별도로 근거화해야 한다.

## 첫 제한 구현에 둘 수 있는 명시 정책

여기는 **원 논문을 재현하는 생리 법칙이 아닌 프로젝트 합성 연구 정책**이다. 부모는 기존 코드의 `allocation['stem_root']`, `cStemG`와 유지호흡을 직접 확인했다고 보고했다. 이 연구자는 그 코드 감사나 구현 시험을 맡지 않았다.

기존 새 구조 형성 요청을 `G`, 생장호흡 비용 계수를 기존 `cStemG = c`로 둔다. 각 절간과 필수 명시 뿌리계에 상대 priority `w_i ≥ 0`를 입력한다. 모든 `G`와 배분 `g_i`는 `mg_CH2O/m2_floor/s`, priority는 무차원이다.

```text
W = Σ w_i
W > 0: g_i = G × w_i/W, realized F = G, deferred D = 0
W = 0: g_i = 0, F = 0, D = G
requested/realized/avoided growth respiration = cG / cF / cD
```

`w_i`는 **상대 우선순위이며 질량 수요 상한이 아니다**. `g_i ≤ w_i`라는 제한은 차원상 성립하지 않는다. 양의 sink가 하나라도 있으면 이 정책은 전체 요청을 배분한다. 잠재 생장 상한·allometry·초과 reserve·최종 기관 크기를 구현한 것이 아니다. 초기값에서 뿌리 배분율이나 균등 분배를 암묵적으로 만들지 않는다.

모든 priority가 0일 때 배분을 미루고, 기존 상위가 `G+cG`를 이미 buffer에서 뺀 경우에만 `D+cD`를 돌려주며 집계 구조 형성을 `D`, 생장호흡을 `cD` 줄이는 환급은 **이 프로젝트의 명시 정책**이다. 원 논문의 0수요 분기로 확인한 것이 아니다. 하위에서 같은 조정을 다시 하지 않도록 부모의 계약·독립 산술 검증이 필요하다.

이 첫 단계는 새 **순간 유량만** 반환한다. 기존 `CStem` 분배, 기관별 현재 재고, 유지호흡 배분·고갈, 출현점 초기 조직, 질량/건물/생체중·길이 추정은 포함하지 않는다. 기존 logistic 길이 표시를 이 배분에 대응하는 탄소 제한 생장으로 부르지 않는다.

## 재고·길이 결합 전에 부족한 것

1. **초기 재고와 대표 범위.** 같은 UTC/phase·절간 ID/절위·뿌리계 ID·floor 분모의 명시 초기 탄소가 필요하다. 합계를 기존 `CStem`과 일치시킨다면 이를 검사한다. 미배분 초기 재고를 남기면 명시 residual로 보관하고 전체 기관을 덮는 현재 재고라고 보고하지 않는다. 크기나 기관 수에서 기존 재고를 역산하지 않는다.
2. **연속 재고 수지.** 같은 ODE stage의 유입·유지호흡·제거/이동·출현 초기 비용·고갈과 음수 처리를 정해야 한다. 집계와 기관 합계를 따로 진행한 뒤 비례 보정하는 절차는 이 순간 배분의 검증으로 도출할 수 없다. 합성 소프트웨어 정책과 실제 식물에 대한 근거를 구별한다.
3. **수요와 형태의 측정.** 같은 기관의 출현 정의·나이·길이·두 방향 폭/단면·생체중·건물중 또는 검증된 건물률, 품종/대목·절위·시각·밀도·관리 이력을 대응시켜야 한다. 기존 logistic을 잠재 길이 후보로 유지할 수 있지만, 그 탄소 수요 allometry와 공급 부족/초과·굵기/신장 분리는 미해결이다.
4. **권리와 독립 검증.** 실측 raw의 사용/표시/재배포 권리, 원 시각/available_at·revision·QC, 보정과 독립 검증의 분리가 필요하다. 2025년 Merlice/Brioso/Moneymaker 등의 계수나 2008년 밀도별 sink를 현재 품종에 채택하지 않는다. 국내 독립 자료·미사용 미래 작기의 검증은 미확보다.

## 출처의 판본·시각·권리·QC

각 행의 observation time은 원 관측을 수신하지 않았으므로 미확보다. 서지/코드 기록에 농장 관측 단위를 붙이지 않는다. 역사적 `available_at`은 전부 미복원이며 공표일·commit 시각·이번 접근 가능성으로 채우지 않는다. 아래 raw hash는 실제 존재하는 response bytes의 값이며 본문만의 hash나 논문 정확성을 뜻하지 않는다. 제3자 raw를 이 저장소에 추가하지 않았다.

| ID / URL·product·판본 | 공표·retrieval·원 bytes | 사용·표시·재배포와 확인 한계 |
|---|---|---|
| S1 [WUR thesis](https://edepot.wur.nl/170301), `10.18174/170301`, 2011 thesis | 공표 `2011-06-17`은 [기존 조사](tomato-morphology-primary-sources-20261021.md)의 기록이다. 앞선 성공 retrieval `2026-10-24T14:39:49.781371Z`는 [기존 receipt](artifacts/leaf-carbon-sink-sources-20261024.json)에 있다. 이번에는 cache bytes를 `2026-10-26T16:39:54.242925Z`에 재해시했다. 3,423,075bytes / SHA `965ecc5573290d0cc59b514e9766b301f9584d212545dec177efa66dd756ac38`. | 공개 원문을 읽고 자체 요약/링크한다. PDF·그림 재배포권 미확인이다. cache의 Ch9 추출문을 위 항목에서 확인했다. 새 HTTP 성공이나 논문 전체 재심사를 주장하지 않는다. |
| S2 [GreenLight JSON](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json), product `davkat1/GreenLight`, revision `7a7b36870135aa38bbe81e65590dcf5473786bdd` | [기존 register](crop-tomato-source-register-20261004.json)의 commit 시각 `2026-09-09T16:00:54Z`는 최초 공개 시각이 아니다. 이번 HTTP200 retrieval `2026-10-26T16:37:43.470196Z`. 26,741bytes / SHA `272a589edf0bb40d1a91b34e883f8e94b9adf747a576be4620c50296c03d7033`. | [Clear BSD](https://github.com/davkat1/GreenLight/blob/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt)의 사용/재배포 조건·저작권/조건/면책·저자/기관의 보증 오인 금지 고지를 기존처럼 유지한다. 이번 라이선스 bytes는 재수집하지 않았다. state/flow/호흡식을 직접 확인하고 위 단위 표기 차이를 기록했다. 계수의 농장 타당성/QC·G0는 미승인이다. |
| S3 [Development of a tomato functional–structural plant model for digital twin applications](https://doi.org/10.1093/insilicoplants/diaf022), `diaf022`, corrected/typeset HTML | 공표 `2025-11-26`, typeset `2025-12-08`. 직접 OUP는403, [출판사 minimal HTML](https://oup.silverchair-cdn.com/article-minimal/8342854)은200, retrieval `2026-10-26T16:38:20.151599Z`. 449,439bytes / SHA `e3d4b09e1d0e2041d43736d1fd5181442e2fbd851f2434a84a553bdf13422749`, 이전 수집과 같다. | 논문은 ©저자2025/OUP/Annals of Botany Company, CC BY4.0. 저자·제목·DOI·license를 표시하여 자체 요약한다. §2.1.4/2.2.1/2.3/2.4/4.1을 직접 확인했다. 단일 줄기 어린 식물 시험이며 현재 품종/성숙·한 작기 검증이 아니다. 논문의 허가를 별도 VTC code/CSV에 전가하지 않는다. |
| S3s [출판사 supplement](https://oup.silverchair-cdn.com/oup/backfile/Content_public/Journal/insilicoplants/7/2/10.1093_insilicoplants_diaf022/1/diaf022_supplementary_data.pdf), TableS1 | 판본은 S3 부속이며 별도 공표 시각 미확인이다. 기존 receipt retrieval `2026-10-21T13:53:01.764497Z`, 이번 cache 재해시 `2026-10-26T16:39:54.246677Z`. 1,057,600bytes / SHA `ce01dd7c054adb7039304f00a37380c4bfe6776161ca47e0da49fcba430c7e51`. | TableS1의 잠재 절간 건물 매개변수와 별도 길이/폭 매개변수 존재를 확인했다. 수치는 채택하지 않는다. 논문 CC BY와 개별 부속물 권리 범위가 같다고 확정하지 않으며 부속 PDF/그림/자료를 전재하지 않는다. |
| S4 [Dong 등 PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC2710282/), `10.1093/aob/mcm317`, Ann Bot101(8),1195–1206 | 출판사 표시 `2008-01-16`, 호는2008년5월이다. 브라우저는 CAPTCHA, urllib의 PMC HTML은200, retrieval `2026-10-26T16:38:19.782830Z`. 215,009bytes / SHA `21cb021e02eccc375467ab1db61d4b08016f0c4e3a94ac60113bcf061b86fc02`. | ©저자2008/OUP/Annals of Botany Company, all rights reserved. 접근을 전재권으로 보지 않고 자체 요약/DOI 링크만 한다. Methods/Eq(3)/Table1/geometry와 밀도 사이 한계를 확인했다. 원 그림·본문·자료 재배포0이다. |

S4 Eq(3)은 HTML의 식 이미지를 실제로 표시해 확인했다. [원 이미지](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/2b89/2710282/98aaeb9a441b/mcm31711.jpg)는 `2026-10-26T16:38:58.632393Z` retrieval, 12,418bytes, SHA `080a48b3590ebfcfaaacf2fff34516063ea1e9bfd0b2840a4e11f07f23853eee`다. 이미지는 임시 영역에만 두고 저장소나 공개 화면에 전재하지 않았다.

GreenLab 일반 치수 설명 페이지도 검색했지만 [CIRAD의 해당 URL](https://greenlab.cirad.fr/GLUVED/html/P2_GLab/Prod/GLprod_orga_005.html)은 이번 직접 수집이404였다. 검색 단편만의 식·계수는 채택하지 않는다. 이번 목적에 필요한 직접 토마토 논문까지 조사했으며 TOMGRO 전체 감사나 모든 FSP 모델 비교를 수행하지 않았다. VTC 코드/CSV 신규 수신·실행, 외부 연락·유료 이용은0이다.

## 이번 확인과 남은 hold

출처 실제 bytes/hash·제한 원문과 식 이미지를 확인하고 이 Markdown만 새로 만들었다. 코드·계수·원 evidence·농장 입력/Run·체크박스나 G0–G4 상태를 변경하지 않았다. 부모가 수행할 순간 유량 구현·focused/독립 수치 시험을 이 연구자의 시험 결과로 보고하지 않는다. 실측 allometry·초기 기관 재고·공급 제한 길이·실제 품종/독립 국내 자료와 G0–G4는 보류다.
