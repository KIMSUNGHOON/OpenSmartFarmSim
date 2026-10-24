# 동적 실내 기온·기존 잎 면적과 용량 흐름의 1차 검토 — 2026-10-24

상태: **새 프로젝트 합성 연구 정책의 검토 근거**. 연속 궤적/품종·실제 물질/엔탈피·기후 feedback이나 G0–G4를 승인하지 않는다. 새 계수/관측 채택0이다.
README와 [잎 순간율](../contracts/crop-leaf-expansion-rate-v1.md)·[canonical 상태](../contracts/crop-leaf-area-state-v1.md)·[기존 기온 시계](../contracts/crop-morphology-thermal-clock-v1.md)·[결합 경계](../contracts/crop-geometry-carbon-coupling-research-v1.md), [식 대조](tomato-leaf-expansion-equation-20261022.md)·[면적 현열 조사](explicit-area-canopy-energy-primary-sources-20261024.md)·[수용된 면적 현열](../contracts/crop-area-canopy-energy-v1.md)·[공동 RHS](../contracts/crop-explicit-lai-climate-rhs-v1.md)를 읽었다. 아래 수학적 판단은 해당 원문이 새 hybrid를 검증했다는 주장이 아니다.

## 원문이 뒷받침하는 범위

- Smoleňová 등(2025), DOI `10.1093/insilicoplants/diaf022`, §2.1.2–3/PDF p5는 작물 위 실내 기온을 쓰고 시간별 기후 출력을 일별로 모은 뒤 일별 기온에서 품종 기준온도를 차감한다고 설명한다. §2.3/p7은 기관 출현 이후 열적 나이에 곡선을 맞추며 §2.4/p8의 실행 간격은1일이다. 정확한 일평균 가중/일 경계·연속 ODE·하한 절단/미만 처리식은 이 대조에서 확인하지 못했다. [S1]
- §2.1.4/p6·§2.3/p7은 logistic 잎 면적을 biomass와 별도 계산한다. 보충 Table S1/PDF p8은 Merlice의 기준온도/면적 곡선 매개변수와 단위를 제시하지만 우리 품종/물성의 근거가 아니다. 완전한 canonical 초기면적은 이 표에서 정해지지 않는다. §4.1/p15는 LAI→기후 feedback을 사용하지 않았다고 밝힌다. 따라서 본 연구의 연속 기온–면적–기후 결합 검증으로 세지 않는다. [S1], [S1S]
- 고정 GreenLight Ch8 `/Capacities/capCan`의 Eq8.20은 `capCan=capLeaf*lai`이며 `/Parameters/Table 8.1/capLeaf`는 잎 면적당 상수 용량이다. `/State equations/Temperature states/tCan`의 Eq8.1은 순열/용량의 온도 미분이다. 이 식에는 아래 새 gross 유입/유출이나 용량 곱 미분 항이 없다. 이 한 식의 확인을 전체 모델 모든 식에 대한 부재 주장으로 확대하지 않는다. `/Time/unit`은 초이며 `tAir`와 `tCan`은 별도 상태다. [S2]

## 새 동적 기온 시계·면적 ODE의 지위

기관 i의 명시 합성 기준온도 `Tb_i`, 출현 후 나이 `a_i`, 양수 면적 한계 `M_i`, 양수 기울기 `b_i`, 변곡 나이 `m_i`를 구분한다. 기울기 `b_i`의 `1/degC_day`는 지수를 무차원으로 만드는 프로젝트 차원 판단이며 보충표의 `–`를 원문 역온도일 표기로 바꾸는 인용이 아니다. canonical 식과 미분 관계는 [고정 저자 구현을 구별한 선행 대조](tomato-leaf-expansion-equation-20261022.md)의 수학 관계를 따른다. 원 코드/표의 수치·계수는 복사하지 않는다.

```text
F_i(a) = M_i / (1 + exp[-b_i*(a-m_i)])
R_i(a) = dF_i/da = b_i*M_i*exp[-b_i*(a-m_i)]/(1+exp[-b_i*(a-m_i)])^2
v_i = a_i' = (Ta-Tb_i)/86400
A_i' = R_i(a_i)*v_i
```

`a_i`는 `degC_day`, `R_i`는 `m2/degC_day`, `v_i`는 `degC_day/s`, `A_i'`는 `m2/s`다. Ta는 같은 RHS stage의 **실내 공기 온도**이며 수관 Tc로 대체하지 않는다. 86,400초/day와 동적 Ta의 ODE는 새 프로젝트 시간 정책이다. 상수 Ta에서는 기존 선형 누적과 수학적으로 환원되지만, 원문 일평균/시간대나 정확한 유리수 시계의 재현을 증명하지 않는다. 연속 Ta에 대한 이 chain rule 자체는 수학이며 원 논문의 생물학적 검증 결과가 아니다.

이 ODE 자체에는 clipping이나 기준 미만 정지식이 없다. Ta<Tb이면 수학적으로 v_i<0이다. 기존 계약의 지원 영역을 유지하는 첫 후보는 기준 미만을 **실행 hold**하고, v_i를0으로 바꾸지 않는다. 이것은 생리학적 발달 정지가 아니다. 미만 값을 허용하려면 감소 나이/면적·음수 나이 진입 및 재개 의미를 별도 정책으로 정해야 하며, 원문의 미기재가 어느 선택의 승인도 아니다. 내부 solver stage의 지원 영역 이탈도 끝점 정상만으로 숨길 수 없다. 같은 순간 Ta=Tb이면 v_i=0이다.

새 상태는 기존 잎 목록이 고정된 연속 구간만 대상으로 하며 기존 exact/canonical leaf 상태를 자동 변환하지 않는다. 부모의 검토 후보는 **a_i와 표현 면적 A_i를 함께 적분**한다. 최초 requested initial_area는 F_i(a_i)와 기존 relative1e-12/absolute0 산술 기준으로 대사한 뒤 canonical binary64 F로 **초기화 때 한 번** 정규화하고 요청값/canonical값/나이·곡선 anchor를 남긴다. 이 기준은 현장 오차가 아니다. 이후 A_i를 F_i(a_i)로 다시 맞추지 않는다.

정확 ODE에서는 `D_i=A_i-F_i(a_i)`에 대해 `D_i'=0`이다. 따라서 독립 참조는 초기 수치 잔차 D_i(0)를 보존하고 **D_i(t)−D_i(0)**와 최초 잔차를 각각 대사해야 한다. 모든 D_i를 무조건0으로 간주하거나 후속 resnap으로 오차를 지우면 안 된다. A와 a를 같은 적분법으로 계산해도 비선형 F의 이산 불변식이 자동으로 정확해지는 것은 아니다. 독립 참조/step refinement·지원 영역/초기오차·허용차는 새 수용의 대상이며 이번 메모에서 통과시키지 않는다.

고정 양수 모델 floor 면적 B와 같은 추적 목록에서 `L=ΣA_i/B`, `Ldot=ΣA_i'/B`를 같은 stage에 만든다. 고정 `k_c>0`에 대해 `C=k_c*L`은 적분한 A의 **선형 재고**다. A와 U를 같은 stage/step/가중치로 적분하면 C의 이산 변화도 같은 Ldot quadrature를 따른다. 이 선형 관계는 endpoint의 F(a)로 면적을 다시 계산할 때 생기는 숨은 용량 변경을 피한다. 반올림/solver 오차·분할 재개는 별도 검증이 필요하다. 새 출현/적엽의 불연속 변화와 그 탄소/용량 사건은 이 구간의 연속 A'에 섞지 않는다.

## 독립 gross outflow를 선택하는 새 용량 정책

현재 [면적 현열 계약](../contracts/crop-area-canopy-energy-v1.md)은 gin/gout를 모두 독립 입력으로 받아 `gin−gout=k_c*Ldot`를 검사한다. 부모 후보는 이 기존 API 의미를 바꾸는 것이 아니라, **새 opt-in 프로젝트 회계 정책**에서 독립 자유 입력 gout로 gross 쌍을 매개화하는 것이다. `gross_out_plus_geometry_net_capacity_research_v1` 같은 별도 정책 식별자(가칭)를 명시하고 입력/정책/코드 hash에 결속해야 한다. 미선언/default 선택은 허용하지 않는다.

```text
Cdot = k_c*Ldot
gout = caller가 독립 선언한 비음수 gross 용량 유출률
gin = gout + Cdot
U = C*(Tc-Tref)
Qmaterial = gin*(Tin-Tref) - gout*(Tout-Tref)
Udot = Qnonmaterial + Qmaterial
Tc' = [Qnonmaterial + gin*(Tin-Tc) - gout*(Tout-Tc)]/C
```

이는 Cdot가 주어졌을 때 남는 gross 흐름의 자유도1개를 **호출자가 고르는** 수학적 closure다. `gout>=0` 외에 `gin>=0`도 필수이며 감소 Ldot에서는 `gout>=−Cdot`가 필요하다. 부족한 gout를 자동 증대하거나 gin을0으로 자르면 선언한 순량을 바꾼다. gout=0도 반드시 명시한 선택이어야 한다. Tin/Tout/Tref/Qnonmaterial은 유량0에서도 명시한다. 단위는 C가 `J/m2_floor/K`, gin/gout/Cdot가 `J/m2_floor/K/s`, U가 `J/m2_floor`, 열률이 `W/m2_floor`다.

binary64에서는 `gin=fsum(gout,Cdot)`라도 작은 순량이 큰 gross에 묻힐 수 있다. 유한성·부호와 함께 기존 **순량8ulp** 대사를 유지하고, 표현 불가/상쇄 불일치는 hold해야 한다. gross 크기로 오차 분모를 키우거나 Cdot를 재작성하지 않는다. 이 연산·검사는 구현 후보이며 이번에 실행하지 않았다.

같은 Cdot에 서로 다른 gout가 대응하므로 면적 순변화는 실제 gross 물질 흐름을 식별하지 못한다. Ldot=0에서도 gin=gout>0이 가능하고 Tin≠Tout이면 운반열은0이 아니다. 이 정책은 실제 수분/조직·질량당 비열·C 공급/호흡·에너지의 기원을 제공하지 않는다. 원문 S1은 이 운반 정책을 제시하지 않으며 S2는 용량의 면적 비례만 뒷받침한다. 일반화한 이 회계식의 내부 일관성과 실제 잎의 물리 closure를 구분한다.

고정 기준을 `Tref_new=Tref+δ`로 옮기면 `U_new=U−δ*C`, `Qmaterial_new=Qmaterial−δ*Cdot`, `Udot_new=Udot−δ*Cdot`이며 Tc와 위 Tc'는 불변이다. 같은 quadrature와 초기 U 변환은 이 선형 관계의 이산 대사에 필요하다. 적응 step/오차 norm은 기준 이동에 따라 달라질 수 있으므로 순간 식의 불변을 전체 궤적의 bit 동일 주장으로 확대하지 않는다. signed U/운반열을 음수라는 이유로 clip하지 않는다.

Udot에 운반열을 넣었다면 `(Tc−Tref)*Cdot`는 chain rule 대사항이지 다시 더하거나 빼는 외부 열이 아니다. 같은 stage의 H/LE/E는 기존 공동 RHS에서 각1회만 사용한다. 유출 열을 자동으로 공기 열에 가산하거나 C/N의 동화·호흡을 조직 현열/물질 생성으로 다시 세지 않는다. 초기 canonical 정규화 뒤 endpoint resnap·별도 용량 보정도 숨은 열원/유출을 만들 수 있다. 이 항목들은 새 결합을 검토할 때의 중복계산 반례이며 원문 검증 결과가 아니다.

## 실제 실행·원천 시각/권리/QC

이 조사자의 native session `01a16c84-beaa-7760-8fba-a66da2ec16cd`, agent `/root/dynamic_air_geometry_capacity_sources`의 `turn_context`는 **2026-10-24T06:06:42.316Z / gpt-6.1-sol / xhigh**다. 메타데이터 행10의 원 LF 포함 SHA-256은 `5e1c817eb574dc574798a24f7d1db1600cd328d24fdc792f999d4be812a9db8d`다. 프롬프트를 출력하지 않고 해당 type의 모델/effort/시각·hash만 확인했다. 부모의 별도06:05:37.443Z/hash는 자식 증명으로 재사용하지 않았다. 재귀 CLI/추가 자식/외부 연락0이다. reviewer는 이 조사자이며 독립 부모 검토/자료 채택 reviewer는 아직 미확정이다.

아래 UTC는 직접 GET 시작→완료이며, S1S는 명시한 이전 원 bytes를 재대조했다. 모든 원행 `observed_at`과 역사적 `available_at`은 **null/미확보**다. S1의 실험 연도2021·게시일은 개별 관측/가용시각이 아니다. 파일별 새 revision/정확 최초 게시시각도 아래 확인 범위를 넘겨 추정하지 않는다.

| 원천·제품/판본·위치 | retrieval UTC·bytes·raw SHA-256 | 권리·QC/미확인 |
| --- | --- | --- |
| S1 위 DOI, *Development of a tomato functional–structural plant model for digital twin applications*, in silico Plants7(2), advance2025-11-26(PDF p1 확인); WUR mirror PDF20쪽. §2.1.2–4/2.3/2.4/4.1 | `2026-10-24T06:08:27.975254Z→06:09:05.474344Z`; HTTP200; 2,319,684; `a950a3458d902bf0d7c142ce202f5db48d9bc81fa1c2ca3e62daca626887e49b` | PDF/절/시계·피드백 대조, 기존 pin 일치. ©저자2025/OUP/Annals of Botany Company, CC BY4.0(PDF p1). 자체 요약/출처 표시; 원문 재배포0. 선행 기록의2025-12-08 typeset 수정은 이번 미재검증. 출판사 web open은500 redirect 실패. |
| S1S 출판사 `diaf022_supplementary_data.pdf`,13쪽, Table S1/p8; 별도 게시/수정 미상 | 직접 무서명 URL GET `2026-10-24T06:08:27.976127Z→06:08:28.060107Z`는403. 이전 공개 원본 retrieval `2026-10-21T13:53:01.764497Z`의 캐시를 `2026-10-24T06:09:47.973274Z`에 재검토; 1,057,600; `ce01dd7c054adb7039304f00a37380c4bfe6776161ca47e0da49fcba430c7e51` | 캐시 raw hash/쪽수·Merlice/단위 직접 대조. 이번 성공 GET으로 표시하지 않는다. 별도 use/display/redistribution 고지 미확보; 논문 권리를 자동 전이하지 않으며 표/원 bytes 재배포0. |
| S2 GreenLight Ch8 JSON, commit `7a7b36870135aa38bbe81e65590dcf5473786bdd`; `/Info/Date`는May2025 생성 고지, commit 게시시각 미검증 | `2026-10-24T06:08:27.976642Z→06:08:28.241567Z`; HTTP200; 130,649; `c0fb7a025533f15b80cb6cd60aafdc19be9fe42df6b8183cf97b83fc086138b3` | JSON parse/상기 pointer·초/용량 단위 대조, 기존 pin 일치. Clear BSD의 고지/조건/면책 보존 등을 따르는 이용/재배포 범위[S2L]; 실제 농장 물성 채택0. |
| S2L 같은 commit LICENSE, ©2025 David Katzin/Wageningen Research Foundation | `2026-10-24T06:08:27.977154Z→06:08:28.283866Z`; HTTP200; 1,716; `96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a` | 라이선스 명칭/조건·기존 hash 대조. 외부 논문/측정 자료 권리로 확대하지 않는다. |

QC는 문서/식/단위·hash 대조이며 현장 자료 QC/승인이 아니다. 원 bytes는 메모리/기존 임시 캐시에서만 읽었고 저장소에 넣지 않았다. 새 측정·계수/품종 적용·실제 조직/질량·물/총 온실 에너지·열 구매·생산/경제/추천과 G0–G4는 모두 hold다. 연속 적분/수렴·정확 사건/재개·출현/관리 공급은 이번에 시험하거나 수용하지 않았다.

변경은 이 문서1개다. Markdown 상대 링크와 공백을 검사했다. 모델/pytest·Docker/npm·브라우저·농장 시험은 실행하지 않았다.

[S1]: https://edepot.wur.nl/706749
[S1S]: https://oup.silverchair-cdn.com/oup/backfile/Content_public/Journal/insilicoplants/7/2/10.1093_insilicoplants_diaf022/1/diaf022_supplementary_data.pdf
[S2]: https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json
[S2L]: https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt
