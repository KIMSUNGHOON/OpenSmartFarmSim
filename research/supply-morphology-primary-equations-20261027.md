# 공급 제한 면적·절간 길이: 원문 식과 합성 정책의 경계 — 2026-10-27 KST

검토 가능한 연구 메모다. **확인한 1차 자료는 현재 품종의 유일한 탄소 제한 절간 신장 법칙을 제공하지 않는다.** 잎에는 새 건물 증가량에 따른 면적 증가의 직접적인 선례가 있다. 줄기에는 실측 질량–길이 관계와 탄소 배분 뒤 기관 크기를 계산하는 선례가 있지만, 이를 현재의 `mg_CH2O/m2_floor` 배분·열적 잠재 길이·유지호흡에 결합하는 법칙은 별도 합성 연구 정책이다. 새 계수·농장 자료 채택, 코드 구현이나 G0–G4 승인은 0이다.

[README](../README.md)의 현재 범위와 [제품 명세](../docs/PROJECT_SPEC.md), [연구 기준선](../docs/RESEARCH_BASELINE.md), [줄기 탄소 조사](stem-carbon-growth-primary-sources-20261027.md), [잎 sink 조사](leaf-carbon-sink-primary-sources-20261024.md), [기존 SLA 대조](continuous-leaf-carbon-primary-sources-20261024.md)를 읽었다. 현재 출현/재개의 소프트웨어 증거를 실측 작기 검증으로 확대하지 않는다.

## 실행·검토 범위

research 스킬의 background 연구자로 위임받았다. 추가 자식·재귀 Codex CLI·외부 메시지/계정·유료 도구·무거운 작업은 실행하지 않았다. **이 자식의 실제 native model/effort와 turn context는 직접 관측하지 못했으므로 실행은 미검증이다.** 부모가 전달한 native 검토 증거는 timestamp `2026-10-27T05:18:30.358Z`, model `gpt-6.1-sol`, effort `xhigh`, 원 LF SHA-256 `421dac202f3bee5652fe54fd782cf42b79e8faf21a851d971eead0f769ee125a`, 관측 `2026-10-27T05:19:37.076397Z`다. 이는 부모 증거이며 자식 실행 증명으로 쓰지 않는다. 검토자는 위임 연구자와 부모이고 독립 농업 reviewer/G0 승인자는 없다.

이번 외향 query/open/find/direct-fetch 요청 항목은 17개다. 검색 단편은 탐색에만 사용했고 아래 채택 근거는 실제 PDF/HTML 또는 이전에 수신한 동일 hash의 원문 bytes에서 확인했다. 직접 수신한 논문 원문은 `/tmp`에만 두었으며 저장소에 제한된 제3자 raw·그림·관측 자료를 추가하지 않았다.

## 직접 지지되는 식

### S1: 현재 재고를 면적으로 읽는 원 모델

[Vanthoor(2011) 학위논문](https://edepot.wur.nl/170301), Ch9 인쇄 p245, Eq9.4–9.6:

```text
dC_leaf/dt = MC_BufLeaf − MC_LeafAir − MC_LeafHar
LAI = SLA × C_leaf
dC_stem/dt = MC_BufStem − MC_StemAir
```

`C`는 CH₂O/floor, 각 flow는 CH₂O/floor/time, `SLA`는 `m2_leaf/mg_CH2O`다. Table9.1 인쇄 p267은 SLA 일정 가정을 명시한다. 따라서 이 원 모델에서는 유지호흡으로 잎 C가 감소하면 LAI도 변한다. `C_stem`은 뿌리까지 포함하며 절간 길이 식이 아니다. p245 Eq9.7 및 p265 Table9.1의 CH₂O→건물 환산은 생장호흡을 이미 고려하고 lignification을 가정하지 않는 모델 규약이다. 실측 기관별 건물 조성/밀도나 현재 품종 계수가 아니다. [S1](https://edepot.wur.nl/170301)

**해석:** 현재 C에서 매번 면적을 재구성하는 방식과, 새 구조 유입만으로 면적을 늘리고 유지호흡 때 면적을 유지하는 방식은 서로 다른 상태 계약이다. 후자를 Eq9.5의 그대로의 재현이라고 할 수 없다.

### S2: 새 건물 증가량을 면적 증가에 연결하는 선례

Katsoulas·Peponakis·Ferentinos·Kittas(2015), *Calibration of a growth model for tomato seedlings (TOMSEED) based on heuristic optimisation*, DOI [`10.1016/j.biosystemseng.2015.09.004`](https://doi.org/10.1016/j.biosystemseng.2015.09.004), [직접 확인한 PDF](https://kpf3.github.io/papers/TomSeed-Katsoulas_et_al.pdf), Appendix A.2.4, 인쇄 p46 Eq22:

```text
ΔLAI = ΔDM_leaf × pSLA
```

`ΔDM_leaf`: `g_DM/m2_ground`; `pSLA`: `m2_leaf/g_DM`. A.2.1 pp45–46 Eq10–13은 온도에 따른 잠재 면적 증가와 pool에 따른 `pSLA`를 사용한다. 저자는 `pSLA`가 현재 crop SLA가 아니라 **추가된 건물당 면적 증가 계수**이며 보정 대상이라고 명시한다. A.1.2 p44 Eq9와 A.2 p45에서는 유지호흡을 광합성 산물에서 차감해 pool에 넣는다. A.2.4 Eq20–21은 배분 pool을 구조 건물로 바꾸는 assimilate requirement를 별도로 쓴다. 이를 기존에 이미 생장호흡을 지불한 구조 CH₂O 유입에 다시 곱하면 같은 비용을 중복 부과할 수 있다. [S2 PDF](https://kpf3.github.io/papers/TomSeed-Katsoulas_et_al.pdf)

같은 A.2.3 pp45–46 Eq19/직후 문장은 실측 기반 전체 seedling shoot의 `DWLS(g_DM/cm)`를 누적 흡수 일사의 함수로 두고 `DM_shoot = SL × DWLS`로 계산한다. 이는 전체 shoot의 경험적 관계다. 개별 절간의 길이/굵기 분할, 고갈 시 역변환, 현재 품종의 한계 건설비는 제공하지 않는다. 이 논문 계수는 채택하지 않는다. [S2 PDF](https://kpf3.github.io/papers/TomSeed-Katsoulas_et_al.pdf)

### S3–S4: 탄소 배분과 형상의 관계가 하나로 정해지지 않는 근거

| 원문 위치 | 직접 확인한 관계와 적용 한계 |
|---|---|
| Smoleňová 등(2025), [*Development of a tomato functional–structural plant model for digital twin applications*](https://doi.org/10.1093/insilicoplants/diaf022), §2.1.4·2.3 | 공통 pool/상대 잠재 sink로 biomass를 배분하지만 잎 면적과 절간 신장은 biomass와 별도 logistic이다. 실측 면적–biomass/길이–biomass 관계가 절위·시간에 따라 달라 이 선택을 했다고 명시한다. 기존 logistic을 탄소 배분 비율로 제한하는 법칙의 근거가 아니다. |
| 같은 §2.4 | 초기 보정 자료가 부족해 첫 수확의 관측 기관 무게·크기로 상태를 동기화했다. 초기 면적/길이만으로 초기 C가 정해지거나 출현점에 무상 조직이 생성된다는 근거가 아니다. |
| Dong 등(2008), [*Does the Structure–Function Model GREENLAB Deal with Crop Phenotypic Plasticity Induced by Plant Spacing? A Case Study on Tomato*](https://pmc.ncbi.nlm.nih.gov/articles/PMC2710282/), Methods Eq3 및 “Three-dimensional representations of plants” | `Δq_o(i,j) = P_o f_o(j) Q(i−1) / D(i)`로 생장 cycle별 새 **건물**을 배분한다. 조건마다 측정한 allometry로 절간/엽병 건물중을 길이·직경에 연결하고 배분 biomass에 맞춰 기관을 그린다. 이 본문은 현재 품종의 보편적 선형 질량/길이 계수나 공급 제한/유지호흡의 연속 ODE를 제시하지 않는다. |
| 같은 Results, SLA/leaf-area 문단 | 식재밀도별 SLA 변화는 실측 개별 잎 면적을 optimization target에 추가해 반영했다. 시각적 fitting만으로 생물학적 기작을 입증하지 않는다고 저자도 경고한다. 고정 SLA 또는 길이당 질량의 품종·환경 불변성을 지지하지 않는다. |

## 제안 가능한 작은 계약 — 출처 재현이 아닌 합성 정책

다음은 부모가 검토 중인 공급 제한 연장 정책을 차원상 명시한 것이다. **위 논문에서 그대로 가져온 식/계수도, 실제 식물의 확인된 생리 법칙도 아니다.** 실제 품종의 allometry가 없다는 사실과 별개로 자체 선언한 합성 입력/정책 버전으로 소프트웨어 보존 계약을 시험할 수 있다.

`X_i`는 개별 잎의 `m2_leaf` 또는 개별 절간의 명시 길이 단위, `F`는 그 기관 집합이 대표하는 `m2_floor`, `g_i≥0`는 이미 배분·생장호흡 비용 처리된 새 구조 유입 `mg_CH2O/m2_floor/s`로 둔다. `p_i≥0`는 명시 열적 잠재 치수 속도 `X/s`, `κ_i>0`는 선언한 한계 건설비 `mg_CH2O/X`다. `κ_i`는 기존 생장호흡 비용 계수와 다른 물리량이다.

```text
q_extension,i = min(g_i, κ_i × p_i / F)
dX_i/dt = F × q_extension,i / κ_i
q_other,i = g_i − q_extension,i
```

- 이는 `0≤dX_i/dt≤p_i`와 새 치수 증가에 쓰는 C의 상한만 정하는 합성 산술이다. `q_extension`은 기존 배분을 분류하며 buffer에서 새로 한 번 더 차감하는 비용이 아니다.
- `q_other`를 기관 C에 남기는 경우, 실제 굵기/밀도/잎 두께를 계산하지 않았으므로 “추가 구조 재고, 형상 대응 미정”으로 기록한다. 자동으로 실제 thickening이라 부르지 않는다. 반대로 전체 배분을 줄이고 buffer로 환급하는 정책은 별도 수지 변경이다.
- `p_i`는 기존 열적 곡선의 잠재 속도 후보일 뿐이다. `dX/da`의 단위 `X/(°C·day)`에 `da/dt`를 곱해 `X/s`로 바꾸는 시간 규약을 결속해야 한다. 잠재 나이·clock을 실현 길이에서 다시 추정하지 않는다. 음의 잠재 속도나 감소 구간은 이 비음수 연장식의 domain 밖이며 clipping/hold 정책을 명시해야 한다.
- `F`는 density/화면 개체 수로 암묵 대체하지 않는다. 기관 C가 이미 floor 기준 기여량이라는 사실과 실제 한 기관 치수의 변환 근거를 보존한다. `g_i`, `κ_i`, `p_i`의 단위/물질 정의·기관 ID·같은 ODE stage가 맞지 않으면 실행을 보류한다.

### 유지호흡·고갈·초기 조직에서 별도로 필요한 결정

새 구조 유입을 쓰는 위 식에서 `dC_i/dt = g_i − m_i − removal_i + …`의 **순 미분**을 `g_i` 대신 넣지 않는다. 순 미분에는 유지호흡/제거가 섞여 있어 음수가 될 수 있고, 이는 새 구조 건설 속도와 다른 수량이다. S1의 현재 재고–면적 불변식이나 S2의 pool 유지호흡 정책과 혼합하려면 그 변경을 명시해야 한다.

유지호흡 뒤에도 형상을 유지한다는 정책은 **현재 고정 allometry**가 아니다. `C_i`가 감소하고 `X_i`가 유지되면 `C_i≥κ_iX_i/F` 또는 `X_i=FC_i/κ_i`를 계속 보장할 수 없다. 한계 건설비 정책을 택한다면 birth C/누적 construction C/유지호흡/제거/미대응 구조 C의 장부를 구별한다. 영구적인 mass–geometry 관계도 요구한다면 비이동성 구조와 reserve의 구분, remobilization/수축 또는 부족 시 hold 등 별도 상태 모델의 근거가 필요하다. 검토한 원문으로 유일한 선택을 식별할 수 없으며 음수 C를 자르는 것으로 해결하지 않는다.

출현점의 양의 `X_birth`, `C_birth`는 명시 입력과 같은 UTC/phase·기관/부모 ID·floor 분모에 결속한다. `C_birth=κX_birth/F`를 **정책으로** 요구할 수 있으나 S2/S3에서 도출한 실측 법칙이라고 하지 않는다. 유지호흡을 겪은 기존 기관의 현재 C를 이 관계로 역산/재초기화하지 않는다. 출현 C와 생장호흡을 이미 조달한 점 사건 뒤에 연속 연장이 같은 초기 조직을 다시 청구하지 않도록 한다. seedling 초기화는 반복되는 새 기관별 무상 seed 면적/질량을 허용하는 근거가 아니다.

수지·초기 사건/반복 재개·0공급/0잠재·초과 배분·고갈 경계·분할 재현의 합성 검사는 위 계약의 소프트웨어 증거만 만든다. 현재 품종 계수·같은 기관의 초기 면적/길이/건물·구조/저장 탄수화물·유지호흡/기아 자료와 독립 국내 검증은 계속 필요하다.

## 판본·시각·권리/QC와 실패 기록

각 출처의 원 관측 시각·농장 raw·역사적 `available_at`은 미확보다. 서지 발행일/이번 retrieval로 대체하지 않는다. 단위는 위 식의 모델 단위이며 현재 농장 측정 QC는 수행하지 않았다. 새 raw의 SHA는 성공 응답 전체 bytes의 값이며 본문만의 hash나 자료의 농업 타당성을 뜻하지 않는다.

| ID / URL·product·판본 | 공표·retrieval·원 bytes | 이용/표시/재배포·QC |
|---|---|---|
| S1 [WUR thesis](https://edepot.wur.nl/170301), DOI `10.18174/170301`, 2011 | 방어일2011-06-17은 기존 메모 기록. 이번 HTTP 재수신 없이 cache를 `2026-10-27T05:21:33.744309Z`에 재확인. 3,423,075bytes; SHA `965ecc5573290d0cc59b514e9766b301f9584d212545dec177efa66dd756ac38`. 이전 retrieval은 [기존 메모](continuous-leaf-carbon-primary-sources-20261024.md) 참조. | 공개 원문을 읽고 자체 요약/링크한다. PDF·그림 재배포권 미확인. Ch9 p245/265/267을 직접 대조했다. |
| S2 [TOMSEED PDF](https://kpf3.github.io/papers/TomSeed-Katsoulas_et_al.pdf), DOI `10.1016/j.biosystemseng.2015.09.004`, *Biosystems Engineering*140(2015),34–47 | PDF에는 accepted2015-09-16/online 날짜 placeholder가 있어 정확 online 시각은 미확인. 직접 HTTP200 `2026-10-27T05:20:24.419787Z→05:20:24.768652Z`; 1,248,978bytes; SHA `e0ef7249a6398ba2f645dd4f225e4e4900501bb1c745c03ccfd94f6a6cc6c8a4`. receipt는 임시 `/tmp/supply-morphology-primary-20261027-rogzf18n/fetch.json`. | ©2015 IAgrE/Elsevier, all rights reserved. 공개 접근을 재배포권으로 간주하지 않는다. Appendix A.1.2/A.2.1/A.2.3/A.2.4·nomenclature를 PDF와 웹 추출문으로 대조했다. 자체 요약/필요한 관계식과 링크만 기록하며 PDF·그림·raw 실험자료 전재/계수 채택0. |
| S3 [Smoleňová2025 DOI](https://doi.org/10.1093/insilicoplants/diaf022), typeset minimal HTML `https://oup.silverchair-cdn.com/article-minimal/8342854` | 공표2025-11-26. cache 재확인 `2026-10-27T05:21:33.747497Z`; 449,439bytes; SHA `e3d4b09e1d0e2041d43736d1fd5181442e2fbd851f2434a84a553bdf13422749`. 이전 성공 retrieval은 [줄기 조사](stem-carbon-growth-primary-sources-20261027.md). | ©저자2025/OUP/Annals of Botany Company, CC BY4.0을 cache에서 직접 재확인. 저자·제목·DOI·license 표시 자체 요약. 별도 저자 VTC 코드/CSV 권리 승인이나 실행은 하지 않는다. |
| S4 [Dong2008 PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC2710282/), DOI `10.1093/aob/mcm317` | 출판사 표시2008-01-16/호2008년5월은 기존 기록. 이번 browser CAPTCHA, 기존 HTML cache 재확인 `2026-10-27T05:21:33.748006Z`; 215,009bytes; SHA `21cb021e02eccc375467ab1db61d4b08016f0c4e3a94ac60113bcf061b86fc02`. | ©저자2008/OUP/Annals of Botany Company, all rights reserved. geometry·SLA 문단을 직접 재확인. Eq3 이미지의 선행 직접 대조/해시는 [줄기 조사](stem-carbon-growth-primary-sources-20261027.md)에 있고 이번 이미지를 다시 수신하지 않았다. 자체 요약/링크; 본문·그림·자료 전재0. |

추가 GreenLab 공식 [organ-dimensions 페이지](https://greenlab.cirad.fr/GLUVED/html/P2_GLab/Prod/GLprod_orga_005.html)는 browser404, [GreenScilab tutorial PDF](https://greenlab.cirad.fr/GLUVED/html/P3_Tools/download/greenscilabtutorial.pdf)는 직접 GET404/browser timeout, [Guo2006 공식 PDF 경로](https://greenlab.cirad.fr/GLUVED/html/bibliography/G_Guo_06.pdf)는 browser timeout이었다. 검색에 나타난 거듭제곱 allometry의 정확 지수/단위는 실제 문서로 검증하지 못했으므로 이번 근거식으로 채택하지 않는다. [Li2017](https://doi.org/10.1155/2017/2302731)은 publisher HTML을 열었지만 이번 필요한 절간/유지호흡 식을 직접 검증한 근거로 쓰지 않았다.

이번 산출물은 이 Markdown 1개이며 코드/계수·README/plan 체크박스·기존 원 evidence·실제 farm/Run·관문 상태를 변경하지 않았다. 상대 링크와 whitespace만 확인한다. 구현·수치 적분·브라우저·농장 시험은 수행하지 않았고, 개별 절간의 유일한 공급 제한 법칙·실측 allometry·초기 조직/고갈·독립 국내 측정·G0–G4는 보류다.
