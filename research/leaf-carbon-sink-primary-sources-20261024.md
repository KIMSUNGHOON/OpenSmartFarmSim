# 잎 탄소 배분·출현의 근거와 다음 의존성 — 2026-10-24 UTC

검토 가능한 연구 판단이다. 날짜는 조사 착수 UTC이며 수용 보고 시각은 **2026-10-25 KST**다.
기존 [연속 결합 계약](../contracts/crop-geometry-carbon-coupling-research-v1.md)의6단계를
[기계적 코드 지도](growing-geometry-lifecycle-code-map-20261024.md)와 부모의 직접 코드/원문 대조로 분해했다.
새 생리 계수·품종/농장 자료나 전체 작기 모델을 채택하지 않았다.

판단한 현재 native Codex CLI의 실제 `turn_context`는 `2026-10-24T14:23:11.773Z`,
model=`gpt-6.1-sol`, effort=`xhigh`, 원 LF 행 SHA-256은
`6d6bca9a4b3f49cb95881cb196fe93e6751ac0e7a8c9f00deec15ed50206ca07`다.
기존 세션 안에서 재귀 CLI를 실행하지 않았다. 별도 자식의 작업은 코드 사실 지도에 한정했으며
자식 native 실행 증명은 없다. 부모 증거를 자식 증명으로 사용하지 않는다.
정리/독립 검사 시점의 후속 native context도 `2026-10-24T15:10:23.072Z`, 같은 모델/effort이며
원 LF SHA는 `e4ad869a1679242e80b4f389457bb5084fec203db0070353cb6e7265476ff2da`다.

## 확인된 구현 간극

현재 동적 vector에는 합계 buffer/leaf/stem_root C와50개 fruit C·**fruit number N**,
기후와 잎별 나이 a/면적 A가 있다. 여기서 N은 질소가 아니다.
연속적인 개별 잎 C 재고는 없으며 제거 사건의 명시 현재 C 분포는 외부 합성 입력이다.
기존 정확 시계의 새 잎은 양의 초기 면적을 가진 형태 사건이며 탄소/초기 조직·현열 자금 조달은 구현하지 않는다.
기존 piecewise 실내 기온의 정확 시계와 새 동적 Ta 적분도 별도 계약이다.
현재 독립 A의 미분은 C 공급을 읽지 않으므로 면적 계산의 수용을 공급 제한/기아 대응으로 해석하지 않는다.
각 함수/단위/원 SHA는 코드 지도에 고정했다. 부모는 새 배분에 필요한
[원 C RHS](../backend/app/crop_explicit_lai_carbon_cohorts.py),
[공동 RHS](../backend/app/crop_explicit_lai_climate_rhs.py),
[재개 문맥](../backend/app/crop_growing_geometry_continuation.py),
[과실 startup](../backend/app/crop_fruit_startup.py)을 직접 읽고 호출/수지를 대조했다.

## 원문과 권리

실제9건의 URL·판본/조회 UTC·원 byte SHA·권리/QC·reviewer는
[원천 기록](artifacts/leaf-carbon-sink-sources-20261024.json)에 보관한다.
HTTP200/404는 관측 사실이며 G0 승인 근거가 아니다. 관측 원행 시각과 역사적 `available_at`는 미확보로 남긴다.

| 원문 | 확인 범위·사용 한계 |
|---|---|
| [Vanthoor2011, Ch9](https://edepot.wur.nl/170301) | 기존 집계 CH2O/분배/호흡과 SLA 권위의 선행 검토를 동일 PDF SHA로 재확인했다. 이번에 원문 전체를 다시 읽었다는 주장은 하지 않는다. PDF/그림 재배포권 미확인, 저장소에 원문을 넣지 않는다. |
| [고정 GreenLight JSON](https://github.com/davkat1/GreenLight/blob/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json)·[Clear BSD](https://github.com/davkat1/GreenLight/blob/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt) | 이미 고정한 CH2O/floor/s 예산과 cLeafG만 재사용한다. 새 계수/프로필 변경0, 기존 고지 보존. 원 JSON의 mcBufLeaf 단위 표기와 검토된 rate 단위를 혼동하지 않는다. |
| [Smoleňová 등2025, diaf022](https://doi.org/10.1093/insilicoplants/diaf022)·[OA PDF](https://edepot.wur.nl/706749), pp5–6 | 공통 동화 pool·beta 잠재 성장에 따른 상대 sink·기관별 유지/생장호흡·과잉 reserve 처리가 있다. 논문은 CC BY4.0(저자/OUP/Annals of Botany Company),2025-11-26 발표다. 자체 요약이며 원 코드/자료 권리에 이 허가를 확장하지 않는다. |
| [저자 VTC 코드 저장소](https://github.com/ksmolen2/vtc/tree/ae01e73911103b934663f3b4406451a84cdc06d4), commit2025-12-10T07:59:11Z | README는 GroIMP2.2.1을 권한다. API license=null/해당 license endpoint404와25개 tree 항목에서 이름이 LICENSE/COPYING/NOTICE인 파일 없음까지 확인했다. 개별 소스 header는 미검토다. 재사용 권리 미확인으로 코드 복사/실행·GroIMP 설치/의존성 추가를 보류한다. |

VTC tree에는 `input/exp2_climate_kaspro_avg.csv`(36,950bytes),
`input/exp2_harvest1_merlice_avg.csv`(828bytes)가 있으나 **파일 내용은 수신하지 않았다**.
후자는 논문의 초기화용 첫 수확 자료와 이름이 대응하는 후보일 뿐 독립 국내 검증 자료가 아니다.
`output/tomato_export.csv`를 측정으로 세지 않는다. 코드/CSV의 권리·원 관측/단위/QC·사용 분할은 미확인이다.
논문의 기본 parameterization Merlice와 업데이트 사례 Merlice/Brioso/Moneymaker를
우리 첫 방울토마토 품종 선정으로 전용하지 않는다. 어린 식물 사례는 성숙/전체 작기 검증을 제공하지 않는다.
계정/연락/지출·제한 자료 수신0, 독립 국내 원 측정/미사용 작기 확보0을 유지한다.

## 선택한 첫 계산 — 프로젝트의 명시 조건부 정책

다음은 **출처에서 그대로 채택한 성장 법칙이 아니라 자체 합성 예산 산술**이라는 설계 판단이다.
상대 sink 개념만 참고하며 논문의 beta 함수·잠재 수요 상한·reserve 법칙을 구현했다고 하지 않는다.
기존 합계 leaf 요청 G와 이미 고정된 비용 c=cLeafG를 받아 명시 상대 priority w_i≥0에 배분한다.
G/g_i의 단위는 `mg_CH2O/m2_floor/s`, w_i는 `1`이다. 기관 단위 절대 mg나 건물 g와 자동 변환하지 않는다.

- W=Σw_i>0: g_i=G·w_i/W, 실현 F=G, 미사용 D=0.
- W=0: g_i=F=0, D=G.
- 요청/실현/회피 생장호흡: cG/cF/cD.
- 상위가 이미 G+cG를 차감한 기준의 조정: buffer′에 D+cD, leaf′에 −D, 총 생장호흡에 −cD를 **원자적으로 한 번** 반영한다.

weight는 상대 우선순위이므로 g_i≤w_i 같은 차원 없는 질량 수요 상한은 없다.
기본 균등 분배·면적/SLA 역산·임의 물성/품종 계수도 없다.
[첫 계약](../contracts/crop-leaf-carbon-partition-v1.md)과 [수용 보고](leaf-carbon-partition-20261024.md)는
조정량을 반환하는 순수 함수에 한정한다. 현재 상위 RHS/시간 적분은 변경하지 않았다.

## 이후 구현·수용 조건

| 순서 | 다음 산출물·통과 조건 | 계속 남는 조건 |
|---|---|---|
| 1 | 같은 stage의 G/cLeafG/잎 ID와 배분을 결속한 별도 공동 RHS. buffer/leaf/호흡3조정을 한 번 적용하고 원 P/기후/과실·나머지 미분을 보존한다. 독립 전체 C 수지·전부0/일부0 sink·중복 호출/불변성·fresh 검증. | 시간 전진·개별 재고/출현은 아직 없음. |
| 2 | 권위 있는 개별 C_i 상태를 원 ID/정확 시각/분모에 결속. 합계 C_leaf=ΣC_i, 유지호흡/제거 분배·고갈/음수 거부를 명시한다. 같은 stage 적분·분할 재개·512경계·독립 장부를 대사한다. | 합계를 따로 전진한 후 C_i를 재맞추거나 원 면적으로 역산하지 않는다. |
| 3 | 양의 새 잎 초기 C의 실제 출처/순간 buffer 차감·생장호흡, 용량/유입 현열·원 UTC/시계/attachment와 사건 순서를 결속한다. 빈 수관·동시 출현/제거·중복 사건·실패 prefix를 검증한다. | 공급 제한/면적 feedback 법칙과 품종 계수의 근거는 별도 조사/검증이 필요하다. |
| 4 | 수용한 계산만 불변 저장→strict SDK→같은 시간/phase의3D로 연결한다. | 현재 새 제거 화면의 무모사 실제 표시 창 확인/R2는 별도 보류다. |
| 5 | 실제 품종·한 작기→생산량·자원 계량→Decimal 경제·거시/수급→자율 후보 비교를 검증한다. | 국내 독립 측정/G2·미사용 미래/G3a·대응 비교/G3b·제품 CLI/배포G4는 합성 시험으로 대체하지 않는다. |

개발은 명시 합성 입력/버전·수지 계약으로 착수할 수 있다. 독립 농장 자료 확보를 개발의 대기 조건으로 두지 않는다.
예측/추천 게시는 실제 자료의 권리/QC·해당 G0–G4 증거가 필요하다.
첫 공동 RHS만 원문 추가 계수 없이 진행 가능하며, 이후 고갈/유지호흡/출현·면적 feedback은 판단과 독립 검증을 먼저 요구한다.
공동 RHS의 코드/단위·독립/회귀·fresh/기록 작업은 현재 작은 계산의 실적을 기준으로 **90–180집중분, 낮은 신뢰**로 추정한다.
외부 자료 수신일과 전체 제품 완료일은 아직 추정할 근거가 없다.
