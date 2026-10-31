# 저장 material 열·수분8항목과 구매량의 경계 — 2026-10-31

상태: **1차 출처·현재 코드 대조이며 새 자료/계수/요금 채택이나 G0–G4 해제가 아니다.**
[현재 같은3D·수량 화면](supply-material-quantity-screen-20261031.md)과
[경제 계약 §1·2·5](../docs/ECONOMICS.md)을 대조했다.8항목은 면적당 부호 있는 연속 전달량이다.
현재8항목에서 구매 전기·연료·관개량이나 청구액을 직접 만들 근거는 없다.
이 판단은 아래 코드식의 의미와 미구현 경계를 확인한 결과이며 독립 농장 검증 결과가 아니다.

## 실행·조사 범위

`engineering-suite:research`가 요구한 native 연구 자식에서 실제 수행했다.
CLI0.166.0의 `2026-10-31T02:12:40.747Z` 원 `turn_context`는
**gpt-6.1-sol / xhigh**이며 한 줄 LF 포함 SHA-256은
`c9400d2a49597185c1531340387c5336b75f48709e122e6e0c5d634f45a3b882`다.
새 CLI/다른 에이전트 실행은0이다. 실제 출력은 이 문서이며 실행·출처·최종 문서의
별도 영수증은 private state에 보존한다. 독립 승인 reviewer는 없다.

관측·모델·요금 자료를 새로 채택하지 않았다. DOE의 COP 정의와 NIST의 단위 정의만 확인했고,
미국 주택용 설비의 예시 효율·가격·운전시간은 이 온실에 적용하지 않았다.
기존 모델식의 원 출처·권리는 [기존 canopy 조사](crop-canopy-exchange-baseline-20261009.md)를
유지한다. 이번에는 외부 모델 코드나 계수를 새로 받지 않았다.

## 정확한8counter 의미

원 매핑은 [growing `_flux`:135](../backend/app/crop_growing_geometry_climate.py#L135),
단위는 [동 파일:127](../backend/app/crop_growing_geometry_climate.py#L127)이다.
순간 열 항은 `W/m2_floor`, 수증기 항은 `kg_water/m2_floor/s`이며 시간 적분 뒤 아래 단위가 된다.
현재 조회는 [quantity reader:39·51·85](../backend/app/crop_supply_material_quantities.py#L39)의
원 lifetime counter 양끝 차와 인접 구간의 정확 합을 제공한다. 실제 계량기 증분이 아니다.

| Counter / 적분 단위 | 원 순간 필드·식과 양수의 의미 | 구매량으로 사용할 수 없는 이유 |
|---|---|---|
| `sensible` / `J/m2_floor` | `exchange.exchange.sensible_heat = H`; 수관→공기 현열. `H`는 수관/기온 차의 부호를 보존한다. | 내부 열 이동이며 난방기 공급열·전기 계량량이 아니다. 음수는 공기→수관 전달이다. |
| `latent` / `J/m2_floor` | `exchange.exchange.latent_heat = λE`; 수관 현열에서 수증기 에너지로 가는 항. `E`와 같은 부호다. | 아래 내부 에너지 대사에서 상쇄된다. 이를 별도 구매 에너지로 합산하면 내부 전달을 지출로 만든다. |
| `incoming_heat` / `J/m2_floor` | `capacity_transport.energy_flows.incoming = gin × (Tin − Tref)`; 표현된 수관 열용량 유입의 기준온도 상대 에너지. | 설비 공급열이 아니다. `gin ≥ 0`이어도 온도 차 때문에 음수가 될 수 있다. |
| `outgoing_heat` / `J/m2_floor` | `capacity_transport.energy_flows.outgoing = gout × (Tout − Tref)`; 표현된 수관 열용량 유출의 기준온도 상대 에너지. 수관 수지에는 이 필드를 뺀다. | `gout ≥ 0`도 에너지의 양수를 보장하지 않는다. 유출 에너지의 부호·절대값은 구매 수요가 아니다. |
| `canopy_external` / `J/m2_floor` | `forcing.canopy_external_heat`; 양수는 수관의 비물질 외부 열원으로 더한다. | 현재 원 forcing은 전달 원천/설비/계량기를 분해하지 않는다. 난방기 출력으로 식별되지 않았다. |
| `air_external` / `J/m2_floor` | `forcing.air_external_sensible_heat`; 양수는 공기 현열 저장량으로 더한다. | 현재 원 forcing은 환기·외피·기기 등 원천과 구매 경계를 식별하지 않는다. |
| `vapor` / `kg_water/m2_floor` | `exchange.exchange.water_vapor = E`; 양수는 수관측에서 공기 수증기로 전달, 수관측 경계는 `−E`다. | 배지 급수·관개·구매 수도량이 아니다. 음수는 식이 표현하는 반대 방향 전달이며 음의 관개/환급을 뜻하지 않는다. |
| `external_vapor` / `kg_water/m2_floor` | `forcing.air_external_vapor`; 양수는 공기 수증기에 외부 질량을 더한다. | 원 forcing은 가습·환기·제습 등 경로/장비를 식별하지 않는다. 유입·배출을 물 구매량으로 간주할 수 없다. |

`H/E/λE`의 실제 구현은 [crop_canopy_exchange.py:98–128](../backend/app/crop_canopy_exchange.py#L98)다.
해당 이름의 실제 파일은 `crop_canopy_exchange.py`이며 `crop_canopy_air_exchange.py`는 없다.
현재 explicit-LAI 경로는 [RHS:117](../backend/app/crop_explicit_lai_climate_rhs.py#L117)에서 이를 호출하고,
capacity 항은 [crop_area_canopy_energy.py:48–80](../backend/app/crop_area_canopy_energy.py#L48)의
명시 `gin/gout/Tin/Tout/Tref` 식을 쓴다. 이 모듈의 수치 도우미는
[crop_canopy_energy_transport.py:9](../backend/app/crop_canopy_energy_transport.py#L9) 이하이며,
그 파일의 별도 [continuous transport:140–166](../backend/app/crop_canopy_energy_transport.py#L140)도
기준온도 상대 유입/유출을 사용한다. 두 경로를 같은 입력 계약으로 혼동하지 않았다.

## 부호·내부 전달·단위의 대사

[공동 RHS:121–144](../backend/app/crop_explicit_lai_climate_rhs.py#L121)의 식을 그대로 대사하면
수관 현열 변화는 `Fcan − H − λE + Qin − Qout`, 공기 현열 변화는 `Fair + H`,
공기 수증기 변화는 `E + Fv`다. 따라서 수관 현열·공기 현열·공기 수증기 잠열을 합한
reduced-energy 변화에는 **내부 `H`와 `λE`가 상쇄**되고
`Fcan + Fair + λFv + Qin − Qout`이 남는다.
[적분 수지:181–192](../backend/app/crop_growing_geometry_climate.py#L181)도 같은 경계다.
제습기·가습기·펌프가 실제로 전기를 쓸 수 있다는 사실은 별도의 설비/계량 경계를 요구한다.
내부 `latent`에 전기요금을 곱하는 근거가 되지 않는다.

`incoming_heat/outgoing_heat`는 기준온도를 바꾸면 값이 변하는 상대 에너지다.
현재 [area 식:61–67](../backend/app/crop_area_canopy_energy.py#L61)는 온도 변화율에는
`Tin − Tc`, `Tout − Tc`를 사용한다. 이는 상대 에너지 부호를 설비 수요로 읽으면 안 되는
추가 코드 근거다. 시간 중 전달 방향이 바뀌면 signed 누적량이 서로 상쇄될 수 있다.
누적량의 절대값·양수 절단은 원 의미를 바꾸며 구매 경계를 새로 식별하지도 못한다.

NIST의 [SI Appendix B.8](https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8)은
`W·s = J`, `kWh = 3.6 × 10⁶ J`의 정확 단위 관계를 제공한다.
이 관계는 열/전기의 **단위 변환**만 설명한다. 면적당 열 전달을 `kWh_e` 구매 전기로
승격하거나 원 floor basis를 검증 없이 실제 농장 면적으로 곱하는 규칙이 아니다.

## 구매량·요금 연결에 남은 경계

DOE [FEMP COP 정의](https://www.energy.gov/cmei/femp/purchasing-energy-efficient-geothermal-heat-pumps)는
히트펌프의 열출력 대 전기입력 비율이다. 해당 페이지는 미국 주택용 지열 히트펌프 취득 안내로,
한국 온실의 효율/COP·실제 요금 자료가 아니다. 프로젝트의 구매량 연결은
[ECONOMICS §5](../docs/ECONOMICS.md#5-열요금현금흐름)의 범위로 유지한다.

| 연결 대상 | 먼저 식별·확인할 입력 | 현재 hold |
|---|---|---|
| 구매 전기 `kWh_e` | 설비 ID/운전 방식·서비스 경계, 시간별 실제 전달열/냉각량, 해당 운전점의 COP/효율·부분부하·보조전력·축열/배분 경계, 같은 기간 전기 계량 대사 |8counter에 장비/계량 결속이 없다. 냉각·제습 운전의 전기량을 음의 난방열로 대체하지 않는다. |
| 연료 `L/kg/m³/kWh_fuel` | 설비별 열출력·효율, 연료 종류/발열량·HHV/LHV 기준·구매량/재고/계량 | 원 forcing과 연료 공급·소비의 연결이 없다. 임의 평균 효율·발열량을 채우지 않는다. |
| 관개/구매 물 | 급액·배액·재순환/회수·저장량과 공기 수증기의 경계를 구분한 물수지, 유량/수도 계량·관개 사건/기간 | 현재 상태는 공기 수증기이며 배지/급액 물수지와 구매 수도 경계가 없다. bulk saturation은 [명시 hold:107](../backend/app/crop_explicit_lai_climate_rhs.py#L107)이고 완결된 응결/회수 모델도 아니다. |
| 청구/지급 KRW | 같은 농장·계약종별·기간/시간대·단위의 구매량·요금·기본/수요/조정 항목·세금 포함 범위, 청구서와 지급일 대사 | 물리 전달량만으로 비용을 만들지 않는다. 미확인을0원으로 두지 않는다. |

기존 경제 원장의 `Decimal` 입력을 사용하는 **명시 사용자 가정의 구매량·단가**는 별도의
불변 소유 입력으로 조건부 산술에 연결할 수 있다. 원8counter에서 수량·단가를 자동 생성하지 않는다.
원 exact 유리수 시각·phase는 경제 입력의 발생/지급일·KST 청구기간과 따로 보존해야 한다.
실제 구매량/청구액 게시와 모델 비용 승격에는 해당 설비·계량·청구의 독립 증거가 남는다.
생과중·수확/판매량·요금·효율 수치를 이 조사에서 가정하거나 채택하지 않았다.

현재 [EconomicNumber:17·27](../backend/app/economic_contracts.py#L17)는
`origin=user`·`evidence_level=assumed`만 받는다. 자원 비용의 지원 단위 쌍은
`kWh_e`/`KRW/kWh_e`, `L`/`KRW/L`이며 `kWh_th`·`kWh_fuel`·`m3`와
`measured/quoted` 입력은 현재 계약에 없다. 이는 향후 물리 모델/경제 범위와 구별할 구현 제한이다.
불변 소유 입력·범위·결정 당시 가용성 검사는 [원 ledger:231](../backend/app/economics.py#L231)을 유지한다.

첫 조건부 연결은 **명시적으로 기간에 귀속된 자원 비용 가정**을 기존 `Cost`로 전달하는 범위다.
[기존 `_costs`:651](../backend/app/economics.py#L651)는 같은 평가기간에 수확 사건이 선언된
배치의 생산비라면 그 수확 전 발생비도 허용한다. 그러나 **평가기간 전체에 수확 사건이 없는
배치**의 생산비는 현재 거부된다. 이를 우회하려고0수확을 만들거나 작물 생산비를
`purpose=period` 간접비로 바꾸지 않는다. 미수확 배치/배분의 지원 공백은 hold로 남기며,
[원 Cost:249](../backend/app/economic_contracts.py#L249)의 생산/판매/기간 의미를 유지한다.

## 출처 메타데이터·권리·QC

아래 URL이 product ID다. 모두 실측 시계열이 아닌 정의/정책 문서여서 `observed_at`과
계측 QC는 해당 없음이다. 각 판본의 과거 최초 `available_at`은 미확인이다.
이번 조사에서 확인 가능한 보수적 이용 시각은 각 `retrieved_at`으로만 기록하며,
과거 의사결정에 소급하지 않는다. 서버 `Last-Modified`는 수신 영수증에 따로 보관했고
내용의 발행일·개정일로 바꿔 쓰지 않았다. 검토자는 위 native 자식이며 독립 채택 승인자는 없다.

| 출처/URL | `published_at`·판본/개정·`retrieved_at` (UTC) | 단위·QC와 raw SHA-256 |
|---|---|---|
| S1 [DOE FEMP 지열 히트펌프](https://www.energy.gov/cmei/femp/purchasing-energy-efficient-geothermal-heat-pumps) | HTML 최초 게시 `2013-10-07T10:32:00-0400`, modified `2026-09-15T11:42:19-0400`; 본문 취득 안내 판본은 December2024. 수신 `2026-10-31T02:13:50.031578Z` | COP 무차원. HTTP200/HTML·정의 본문 확인. 미국 예시 수치 미채택.148,485bytes; `b518d5b50c7240022bbb97dd8abe20e3e65f1d35739724e6469eb319b195a921` |
| S2 [NIST SP811 Appendix B.8](https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8) | HTML 게시 `2016-02-01T14:55-05:00`, modified `2025-08-18T14:13-04:00`; 수신 `2026-10-31T02:13:50.150604Z` | J/W·s/kWh. HTTP200/HTML·해당 변환행의 정확값 굵은 표시를 원 HTML에서 확인.169,493bytes; `04144e12942c0073627ec6853b0326e31cfeca7edff258252484aef3c71d1ef5` |
| S3 [DOE Web Policies](https://www.energy.gov/web-policies) | HTML 게시 `2011-07-30T17:05:08-0400`, modified `2018-01-26T18:12:38-0500`; 수신 `2026-10-31T02:13:50.041135Z` | 단위 해당 없음. HTTP200/권리·링크 정책 본문 확인.133,113bytes; `63b4fa08a68e15f909eb0798ebf545446fe0010a437cdd4ade879d044cb8d137` |
| S4 [NIST 권리 정책](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications) | HTML 게시 `2015-05-27T09:45-04:00`, modified `2025-06-24T09:23-04:00`; 수신 `2026-10-31T02:13:50.117334Z` | 단위 해당 없음. HTTP200/일반 NIST 저작물과 technical publications 범위 확인.94,091bytes; `086a91df97309b7fa4a8ee7386c513baa6e7aff860f5f16610af1b142c10b580` |

S3는 DOE 정부 정보의 복사·배포와 출처표시 요청을 설명하며 제3자 자료의 권리를 구분한다.
이 문서는 DOE의 짧은 정의를 자체 문장과 링크로 표시한다. 외부 이미지·표·미국 예시 자료는
복제/재배포하지 않았다. S4는 NIST 자체 저작물의 미국 내 저작권 범위와 해외 사용 허락·출처표시,
제3자/SRD 예외를 구분한다. 이 문서는 NIST의 단위 관계만 출처와 함께 표시한다.
공개 접근 가능성을 다른 제공자·계약/농장 자료의 사용·표시·재배포 허가로 전이하지 않는다.

원 HTML/HTTP 영수증·내용시각/QC·코드 hash/최종 출력 영수증은
`/home/sunghoonk/.local/state/OpenSmartFarmSim/20261031-material-energy-boundary/primary-sources/`에만 보관한다.
제3자 원문은 저장소에 넣지 않았다. 최초 축약 NIST URL의 웹404는 정식 B.8 경로로 해결했다.
최초 로컬 `python` 명령은 실행기 부재로 실패했고 `python3`의4요청 모두200을 확인했다.
링크/원8필드·단위·부호와 원 수지를 검토했으며 새 수치 계산/농장 검증/관문 평가는 실행하지 않았다.
