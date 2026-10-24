# 연속 잎 면적·탄소 결합의 1차 근거 — 2026-10-24

상태: **검토 가능한 연구 제안**. 가장 작은 다음 경계는 명시 LAI의 순간 광 동화 산술이다. 연속 작물·열 feedback, 새 계수/자료 채택이나 G0–G4 승인이 아니다.
AGENTS·README·PROJECT_SPEC·ARCHITECTURE·RESEARCH_BASELINE과 [선행 조사](leaf-lifecycle-production-primary-sources-20261024.md)·[순간 제거 수용](crop-leaf-carbon-removal-20261024.md)을 읽고 HEAD `3d8558ec8c7fd9165141456eb3158e399b1229c3`를 대조했다.

## 호출·원문 대조

부모가 확인한 실제 `spawn_agent` 인자는 `task_name=continuous_leaf_carbon_sources`, `fork_turns=none`, `model=gpt-6.1-sol`, `reasoning_effort=xhigh`다.
자식 native context timestamp/원행은 미제공이다. 전달받은 context `2026-10-24T04:35:59.972Z`와 raw LF SHA `81628c328dbffaf7a324b5ee944f23b8c154f63cc34203c8a5d2887e8a07b5a7`은 **부모 증거**이며 자식 native 실행 증명으로 바꾸지 않는다.
공개 HTTPS 원문4개를 직접 재수신하고 SHA-256·PDF 절/식·고정 저자 JSON/라이선스를 대조했다. 웹 도구의 edepot403 뒤 일반 공개 HTTPS는200이었다. 기존 임시 pypdf만 재사용했으며 재귀 CLI·추가 자식·계정/연락·제품 의존성 변경0이다.

| 원문 위치 | 확인된 사실과 한계 |
| --- | --- |
| Vanthoor(2011), Ch9 인쇄 p245 Eq9.4–5, p267 Table9.1 | 잎 CH₂O는 분배−유지호흡−적엽으로 변하고, LAI는 `SLA×C_leaf`인 semi-state다. SLA 일정은 명시적 가정이다. [S1] |
| 같은 원문 pp248–250 Eq9.16/18/20/23 | LAI가 수관 전자전달 용량·PAR 흡수·보상점에 들어간다. 이 식들은 순간 LAI를 입력으로 평가할 수 있지만 원 모델의 LAI 생성 법칙을 독립 면적으로 바꾸지는 않는다. [S1] |
| 고정 GreenLight `lai/j25CanMax/gamma/mcBufLeaf` | `lai=sla*cLeaf`를 유지한다. `parCan`은 이 JSON에서는 외부 입력이며 greenhouse 정의에 위임한다. 원 논문 광 흡수식과 JSON의 입력 경계를 구별한다. [S2] |
| Smoleňová 등(2025), §2.1.4 p6·§2.3 p7 | 잎 면적은 잎 biomass와 별도 logistic으로 계산하며, 면적/biomass 관계가 기관 순번·시간에 따라 일정하지 않았다는 이유를 명시한다. 절간만의 설명으로 읽을 수 없다. [S3] |
| 같은 원문 §2.1.2/4 pp5–6 | 기하·면적·광학 특성으로 기관별 흡수를 구하고 FvCB 동화→공통 pool→상대 sink strength에 따른 기관 biomass 분배/호흡을 계산한다. 단순한 면적 곡선만 있는 모델은 아니다. [S3] |
| 같은 원문 §4.1 p15 | LAI→KASPRO 기후 feedback은 API상 가능하지만 이 연구에서는 사용하지 않았다. 어린 작물 위의 기후값을 이용한 사례이며 우리 열·물 feedback 검증이 아니다. [S3] |

**원문 내부의 표현 긴장:** p15는 향후 잎 biomass·면적·길이를 분리하는 접근을 제안한다. 반면 pp6–7은 면적/biomass의 별도 계산을 이미 명시하고, 길이는 면적의 함수라고 한다. 이 문장들을 모두 보존한다. 기존 조사에 잎/절간 혼동이 있었다고 정정할 근거는 없으며, 세 변수의 완전한 독립과 실제 실행 순서/공급 제한은 저자 코드 대조가 필요한 미확인 항목이다. [S3]

## 세 후보의 지위 — 출처를 바탕으로 한 설계 판단

| 후보 | 가능한 연구 경계와 남는 문제 |
| --- | --- |
| A: 탄소/SLA 권위 | S1의 LAI 법칙을 유지하고 기관 기하는 그 총면적의 명시적 예시 분배에만 쓸 수 있다. 원 logistic 면적을 실측·독립 예측으로 표시하거나 조용히 rescale하지 않는다. 분배 규칙 자체도 별도 판본이 필요하다. [S1] |
| B: 독립 기관 면적/LAI 권위 | S3는 이런 분리의 선행 사례다. 그러나 그 면적을 S1 집계 C/50과실에 붙이면 **새 hybrid 연구 모델**이다. `LAI=SLA×C_leaf` 불변식을 버린다는 모델 변경과 공급·질량·관리·열 계약을 명시해야 한다. [S1], [S3] |
| C: 수요/분배·가변 SLA | S3의 상대 sink strength와 별도 면적은 참고가 되지만, 우리 기관별 C 분배·공급 제한·가변 SLA 법칙을 제공하지 않는다. `LAI/C_leaf`를 진단 비율로 계산하는 것과 생장 기작을 식별한 것은 다르며 C=0에서는 비율도 정의되지 않는다. [S3] |

B/C를 전진시킬 때 필요한 보류 조건은 다음과 같다. 이는 새 생리 법칙이나 계수의 채택이 아니다.

- **공급 고갈/출현:** 별도 logistic만으로는 탄소 부족 시 면적 확장·광 수용을 제한하는 정책이 입증되지 않는다. S1의 buffer 제한과 S3의 기관 수요/분배를 대체하지 않으며, 양의 새 잎 면적에 대응하는 초기 C·buffer 차감·성장호흡/외부 유입 근거가 없으면 질량 출현을 만들지 않는다. S1 Eq9.1/4/25–26·S3 §2.1.4. [S1], [S3]
- **관리 C:** 독립 면적 감소량을 고정 SLA로 나누어 제거 C로 만들지 않는다. 잎 ID별 사건 직전 별도 C 장부와 제거 합계·시각·한 번만 차감하는 규칙이 필요하다. 현재 순간 제거 API는 사건 전후 SLA 일치를 요구하므로 B에 그대로 쓰지 못한다. S1 Eq9.4/46–47. [S1], [현재 구현](../backend/app/crop_leaf_carbon_removal.py)
- **열용량:** 현재 joint RHS는 면적당 열용량×SLA×잎 C와 그 미분을 결속한다. 독립 LAI에서 같은 면적당 열용량 가정을 택하면 미분은 LAI 변화율을 따라야 하며, 면적 변화만으로 물질의 유입·유출 현열을 결정할 수 없다. 열용량/온도·에너지 운반의 새 근거 없이 기존 수지를 재사용하지 않는다. [현재 RHS](../backend/app/crop_climate_joint_rhs.py), S3 §4.1. [S3]
- **검증 범위:** S3의 기본 plant 평가는 기관 parameterization과 같은 실험이며 최초 측정으로 상태를 교체했다. 별도 실험은 주로 높이 updating pipeline 검증이고 첫 실험에 적엽은 없었다. 이를 Axiany 적엽·기아·성숙 수관·전체 작기/열·미래 생산의 독립 검증으로 세지 않는다. S3 §2.2/2.4/4.1. [S3]

## 가장 작은 다음 API·수용 제안

새 판본의 순수 `explicit_lai_photosynthesis` 연구 함수가 명시 `LAI(m²_leaf/m²_floor)`, buffer(`mg_CH2O/m²_floor`), 수관 온도(°C)·상부 PAR(`μmol_photons/m²_floor/s`)·CO₂(ppm)와 기존 고정 프로필을 받아 순간 동화(`mg_CH2O/m²_floor/s`)·진단만 반환하도록 제안한다. S1 Eq9.10–23과 기존 고정 GreenLight의 평활 buffer 억제를 유지하며 새로운 농업 계수는 필요하지 않다. [S1], [S2]
LAI/forcing/buffer·프로필·새 모델/코드 판본·입력 hash와 합성 연구 범위를 묶는다. 기존 `calculate_rates`의 SLA 권위와 저장 Run은 그대로 두고 이 API를 연속 C RHS·기관 출현·관리·기후 호출에 자동 연결하지 않는다.
`tracked_LAI`를 연결할 때에는 기존 [바닥 분모 경계](crop-leaf-canopy-basis-20261024.md)의 동일 정확 시각·추적 범위/footprint 근거를 유지한다. 계산 가능한 추적 비율을 실제 전체 수관 측정으로 승격하지 않는다.
수학적 domain은 기존 [광합성 적용 영역](../contracts/crop-photosynthesis-domain-v1.md)의 `0≤Γ≤Ci`를 명시 LAI에 적용한다. 낮은 CO₂에서는 허용 LAI 상한도 생기며, PAR=0·LAI=0의 기존 특례/hold를 유지한다. 이것은 원식의 계산 영역이며 검증된 생물학적 LAI 상·하한은 아니다. S1 Eq9.23. [S1]

1. app/helper를 호출하지 않는 독립 고정밀 참조로 Eq9.10–23·단위·진단을 대조하고, `LAI=SLA×C_leaf`인 경우 기존 순간 동화와 일치함을 확인한다.
2. buffer/환경을 고정하고 LAI만 바꾼 사례를 독립식과 대조한다. 동화를 임의 단조 법칙으로 검사하거나 다른 기관 C와 LAI를 자동 보정하지 않는다.
3. 낮/어둠·0/작은 LAI·낮은 CO₂ 상한·domain 경계 양쪽·잘못된 단위/비유한/음수·입력 불변/동일 재실행·기존 API 회귀를 확인한다.
4. 통과해도 순간 합성 산술 자식만 수용한다. 한 구간→정확 사건→재개/분할, buffer+기관+50과실 C/N·열·물 수지와 실제 현장 검증은 후속이다.

## 원천 판본·시각·권리/QC

아래는 2026-10-24 UTC 직접 GET 시작→완료와 원 bytes SHA-256이다. 관측 원행 시각·역사적 `available_at`·정확 revision 시각은 미확보이며 게시일/이번 수신시각으로 소급하지 않는다. S3 실험 연도는2021이다. 대조 reviewer는 이 연구 자식이며 독립 자료 승인 reviewer는 없다.

| ID·판본/게시 | retrieval UTC·SHA-256·bytes | 이용·표시·재배포 |
| --- | --- | --- |
| S1 `10.18174/170301`, 학위논문2011; 방어일2011-06-17 | `04:39:19.739470→04:40:30.745687`; `965ecc5573290d0cc59b514e9766b301f9584d212545dec177efa66dd756ac38`; 3,423,075 | 공개 원문 대조·자체 요약/링크. PDF/그림 재배포권 미확인; 저장소에 원문 없음. |
| S2 commit `7a7b36870135aa38bbe81e65590dcf5473786bdd`; 파일 생성 고지May2025 | `04:39:19.740777→04:39:19.963393`; `272a589edf0bb40d1a91b34e883f8e94b9adf747a576be4620c50296c03d7033`; 26,741 | Clear BSD. 코드 재사용/배포에는 저작권·조건·면책 보존 등이 필요하다. 최초 공개/commit 시각 미검증. |
| S2L 같은 commit LICENSE | `04:39:19.741233→04:39:19.995911`; `96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a`; 1,716 | ©2025 David Katzin/Wageningen Research Foundation. 이름을 통한 무단 보증 금지·특허권 불부여도 명시한다. [S2L] |
| S3 `10.1093/insilicoplants/diaf022`, Smoleňová 등, *Development of a tomato functional–structural plant model for digital twin applications*, advance2025-11-26 | `04:39:19.740224→04:40:21.608041`; `a950a3458d902bf0d7c142ce202f5db48d9bc81fa1c2ca3e62daca626887e49b`; 2,319,684 | ©저자2025/OUP/Annals of Botany Company, CC BY4.0. 저자·제목·DOI·권리 표시 자체 요약. 별도 코드/보충물 권리는 이번에 승인하지 않았다. |

단위/QC: S1/S2 C는 CH₂O·floor 기준이고 SLA는 leaf-area/CH₂O 기준이다. S3의 건물(g, Table2)·열적시계(°Cd)를 이를 대체하는 질량/초 단위로 읽지 않는다. HTTP200·PDF header/쪽수·해당 식·라이선스를 읽었으며 네 hash가 선행 수신과 일치했다. 제공자 농장 QC는 미수신이며 이 검사는 농장 자료 승인/계수 채택이 아니다.
이번 변경은 이 메모1개다. 상대 링크·공백·줄 수를 검사했다. 구현/수치·브라우저·현장 시험은 수행하지 않았다. 실제 품종·출현/제거 C·전체 수관/공급 제한·열 feedback·독립 국내 작기·생산/자원/경제/추천 및 G0–G4는 계속 보류한다.

[S1]: https://edepot.wur.nl/170301
[S2]: https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json
[S2L]: https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt
[S3]: https://edepot.wur.nl/706749
