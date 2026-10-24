# 추적 shoot 잎 장부와 생산 모델 결합의 1차 근거 — 2026-10-24

상태: **출처 대조와 작은 연구 경계 제안**. 계수·농장 자료 채택, 생산/순위 또는 G0–G4 승인이 아니다.
README·RESEARCH_BASELINE, [직전 제거 조사](crop-declared-leaf-removal-primary-sources-20261024.md),
[생애 계약](../contracts/crop-leaf-lifecycle-v1.md)·[기관/50구획 결합](../contracts/crop-plant-cohort-rates-v1.md)·[적분](../contracts/crop-plant-cohort-integration-v1.md)을 읽었다.

## 실제 조사 방법과 대조 결과

부모의 실제 `spawn_agent` 인자는 `task_name=leaf_production_coupling_sources`, `fork_turns=none`, `model=gpt-6.1-sol`, `reasoning_effort=xhigh`였다.
자식 native timestamp/원행은 도구에서 미제공이다. 부모가 전달한 검토 context `2026-10-24T03:58:33.577Z`/LF SHA `ec42ad72f3232995f1fd96ddcf1c69176104a8c5a7c247d35e8d17479d28029a`는 **부모 증거**다.
이 자식이 공개 HTTPS 원문을 직접 수신·SHA-256 계산하고 PDF 본문/식·저자 JSON을 읽었다. 재귀 CLI/추가 자식·로그인·외부 연락은0이다.
웹 edepot403·OUP/DOI500 뒤 공개 edepot HTTPS는 성공했다. PDF 읽기용 pypdf는 `/tmp`에만 설치했으며 제품 의존성을 바꾸지 않았다.

| 원문 | 확인한 사실과 결합 한계 |
| --- | --- |
| Vanthoor(2011), Ch9 §9.2/9.4, 인쇄 pp242–245 | 분모는 greenhouse floor이며 `C_leaf`는 CH₂O 저장량이다. `LAI=SLA×C_leaf`; 잎 변화는 분배−유지호흡−적엽이다. [S1] |
| 같은 원문 p245 Eq9.5, p267 Table9.1 | SLA는 `m²_leaf/mg_CH2O`이고 일정하다는 가정이다. p265의 CH₂O→DM은 별도 변환 가정이다. 건물 기준 SLA와 기호만 같다고 호환되지 않는다. [S1] |
| 고정 GreenLight JSON `cLeaf/lai/sla/mcLeafHar` | `cLeaf`는 CH₂O인데 `sla` 단위는 `mg{leaf}`로만 적힌다. 위 원문 기준을 명시해야 하며 이를 DM 측정으로 읽지 않는다. 집계 적엽 유량은 개별 ID 제거가 아니다. [S2] |
| Vanthoor pp244–245/253–257/267 | 50발달 구획은 면적당 C/N의 유입·이동·호흡·말단 유출이다. 식9.43–45는 성장/유지호흡을 구분한다. 잎 ID와 실제 개별 과실의 대응을 제공하지 않는다. [S1] |
| 고정 GreenLight JSON/설명서 | 단순화된 집계 `cFruit` 모델이며 50개 C/N 배열이 없다. 현재 50구획의 독립 검증기로 쓸 수 없다. [S2][S2R] |
| Smoleňová 등(2025) §2.1.1/2.1.4/2.3, pp5–7 | 단일 stem 구조이며 면적–biomass 관계가 기관 순번/시간에 따라 달라 잎 면적 확장을 biomass와 별도로 계산했다. 면적 곡선에서 질량을 곧바로 역산할 근거가 아니다. §4.1의 LAI→기후 feedback도 이 연구에서는 사용하지 않았다. [S3] |
| Hemming 등(2020) §2.4/3.3 | Axiany 실험은 plant와 stem 밀도를 구별하고 측지를 키워 stem 밀도를 변경했다. 한 tracked shoot를 한 plant 또는 고정 밀도의 전체 수관으로 복제할 수 없다. [S4] |

## 다음 계약에 필요한 명시 상태·단위 — 출처를 바탕으로 한 설계 제안

| 경계 | 최소로 기록·검사할 내용 |
| --- | --- |
| 모집단/면적 | leaf→shoot→plant ID와 포함/제외 기관, whole compound leaf/leaflet 구분, 측정 면적의 면 정의·방법, 해당 시각의 추적 범위를 기록한다. 3D 양면 mesh 면적을 측정 leaf area로 바꾸지 않는다. S3 §2.1.1/2.2.1. [S3] |
| 바닥 분모 | 양수의 명시 `model_footprint_m2_floor`와 원 근거를 받는다. `tracked_LAI=ΣA_active/model_footprint`는 **추적 면적의 정규화**다. 실제 full-canopy LAI에는 별도로 증명된 전체 shoot/표본확장 범위가 필요하다. S1 §9.2/9.4, S4 §2.4. [S1][S4] |
| 밀도 | 첫 경계에서는 plant↔shoot 복제/밀도 계수를 넣지 않는다. 후속 적용에는 각 시점의 면적·plant 수·stem/shoot 수와 관리 이력을 같은 분모로 대사해야 한다. `complete=true` 선언만으로 측정 완전성을 증명하지 않는다. S4 §2.4/3.3. [S4] |
| 질량 기준 | `A_i(m²_leaf)`, `C_leaf(mg_CH2O/m²_floor)`, `DM_leaf(mg_DM)`를 구분한다. `η=DM/CH₂O`라면 차원상 `SLA_CH2O=η×SLA_DM`이지만 같은 조직/시각·변환 근거가 필요하며 이번에는 η/SLA를 채택하지 않는다. S1 Eq9.5/9.7/Table9.1, S3 §2.3. [S1][S3] |
| 초기/출현 | 초기 면적과 초기 CH₂O를 독립 근거에 결속한다. 출현 때 양의 면적을 생성했다고 탄소를 무료로 추가하지 않는다. 질량 출현을 넣으려면 buffer/기관 분배·성장호흡의 대응 장부와 판본이 필요하다. S1 Eq9.1/9.4/9.43–44, S3 §2.4. [S1][S3] |
| 관리 제거 | 사건 직전 잎 면적과 별도의 제거 CH₂O 질량을 보존한다. 순간 제거 `mg_CH2O/m²_floor`와 연속 유량 `/s`를 구분하고 같은 제거를 두 경로에서 차감하지 않는다. 면적만 감소한 사건으로 질량을 채우지 않는다. S1 Eq9.4/9.47. [S1] |
| 수지/권위 | 기존 `LAI=SLA×C_leaf`와 독립 logistic 면적을 동시에 강제하면 불일치가 가능하다. 첫 단계는 차이를 기록하며 어느 쪽도 보정하지 않는다. 후속 생산 결합은 잎 분배/호흡/제거와 전체 buffer+기관+ΣC_j 보존을 함께 재검증한다. S1 Eq9.1–6/9.43–45, S3 §2.3. [S1][S3] |
| 과실/시간 | 잎 면적은 초기50개 C/N·S/W1/RGR를 식별하지 못한다. 기존 구획 상태를 유지하고 총 과실을 중복 보유/호흡 차감하지 않는다. 정확 분수 초의 잎 사건과 정수 초의 기존 적분은 무단 반올림 없이 새 시간 계약으로 결속해야 한다. S1 §9.4/9.5.3–4와 위 기존 두 계약의 차이다. [S1] |

**가장 작은 다음 구현:** 원 저장 lifecycle의 동일 정확 시점에서 active 면적만 읽고, 호출자가 명시한 합성 model footprint로 나눈 `tracked_LAI`를 돌려주는 순수 단방향 연구 변환이다.
원 결과/입력·분모·단위·코드 판본/hash를 결속하고, 제거 마지막값·pending 면적을 현재 합계에 섞지 않는다. 이는 [S1]의 바닥 분모를 적용한 프로젝트 산술이며 full-canopy 또는 생산 입력 승인이 아니다.
독립 Fraction/Decimal 참조로 면적/분모, 마지막 잎 제거·빈 active, 같은 정확 시각, 단위·0/음수/비유한 분모 거부와 입력 불변을 확인한다. 기존 RHS·SLA·50구획·실제 밀도는 변경하지 않는다.
현재 전체 수관 증거가 없는 원 저장 목록에 임의 `complete`를 추가하거나, `tracked_LAI/SLA`를 생산 질량으로 쓰는 단계는 보류한다. [S1][S3][S4]

## 독립 증거와 명시 보류

실제 결합에는 같은 식별 shoot/plant의 초기·반복 전체 잎 면적, 출현/whole-leaf 제거 시각·마지막 면적, 제거 및 잔존 잎의 건물/질량 기준, 전체 면적·plant/stem 이력과 측정/QC·권리가 필요하다. 이것은 S3 §2.2.1/2.3의 기관 계측과 S4 §2.4의 관리 범위를 결합한 **검증 설계 제안**이다. [S3][S4]
면적→질량/분배 관계는 보정에 쓰지 않은 표본·작기에서 따로 대조하고, 이후 생산 결합은 수관 온도/PAR/CO₂·기관 질량과 개화/착과/수확 관측까지 동기화해야 한다. S1 §9.3–5, S3 §2.3–4에 근거한 제안이다. [S1][S3]
S3의 plant 검증은 기관 parameterization과 **같은 실험**이며 첫 측정으로 상태를 교체했다. 첫 실험은 적엽하지 않았다. 따라서 이를 우리 Axiany 적엽·전체 작기·미래 생산의 독립 검증으로 세지 않는다. S3 §2.2/2.4. [S3]
최종 면적 하나는 출현/제거 이력·biomass·누적 동화/호흡·과실50구획·수확을 식별하지 못한다. 원식은 시간별 환경·저장량·흐름을 요구한다. S1 §9.4–5, S3 §2.3. [S1][S3]
실제 품종 계수·독립 국내 작기/전체 수관 coverage·잎 질량/제거 탄소·시간 결속·생산/자원/경제와 G0–G4는 계속 보류한다. 연구 제안을 승인 입력이나 관문 증거로 쓰지 않는다.

## 원천 판본·시각·권리/QC

아래 retrieval은 2026-10-24 UTC의 직접 요청 시작→완료다. 관측시각/역사적 `available_at`은 모두 미확보이며 게시일로 소급하지 않는다. 대조 reviewer는 이 연구 자식이고 독립 자료 승인 reviewer는 없다.

| ID/판본·게시 | retrieval UTC·원 SHA-256/bytes | 이용·표시·재배포 |
| --- | --- | --- |
| S1 DOI `10.18174/170301`, 2011-06-17 학위논문 | `03:57:02.128016→03:58:27.616793`; `965ecc5573290d0cc59b514e9766b301f9584d212545dec177efa66dd756ac38` /3,423,075 | 공개 원문 대조·자체 요약/링크. PDF/그림 재배포권 미확인; 원문 저장소 미포함. |
| S2 JSON, commit `7a7b36870135aa38bbe81e65590dcf5473786bdd`, 파일 고지May2025 | `03:57:02.129437→03:57:02.398950`; `272a589edf0bb40d1a91b34e883f8e94b9adf747a576be4620c50296c03d7033` /26,741 | [고정 라이선스][S2L] Clear BSD: 재사용/배포 시 저작권·조건·면책 보존 등. 정확 최초 공개/수정시각 미검증. 코드/계수 도입0. |
| S2L LICENSE / S2R readme, 같은 commit | `03:57:02.130033→02.483497`, `96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a` /1,716; `03:57:02.130603→02.483350`, `9e5ca837f6be1524886550f2c00d0ddab0cf980fd4be778e7e8d3532f4239ad9` /2,581 | 코드 권리를 논문/농장 자료에 전이하지 않는다. |
| S3 DOI `10.1093/insilicoplants/diaf022`, advance2025-11-26, WUR PDF | `03:57:02.128847→03:57:48.777079`; `a950a3458d902bf0d7c142ce202f5db48d9bc81fa1c2ca3e62daca626887e49b` /2,319,684 | 첫 면 ©저자2025/OUP/Annals of Botany Company, CC BY4.0. 저자·제목·DOI·권리 표시 요약. 코드/보충물 권리 신규 승인0. 관측NPEC2021, revision시각 미검증. |
| S4 DOI `10.3390/s20226430`, 게시2020-11-11, PMC HTML | `03:59:47.140385→03:59:48.011912`; `343f901abfe9e93a36c57072dce45defde472fd165c5b8b1920583b9162fe9f6` /282,743 | ©저자2020/MDPI, CC BY4.0. 출처 표시 요약. 실험2019-12~2020-05; 개별 관측시각·HTML revision 미검증. |

PDF header·해당 절/식/단위와 코드 단위를 대조했고 S1/S2/S3 hash는 직전 조사와 일치했다. 이는 원 객체/QC 확인이며 농장 측정 품질 승인이 아니다.
이번 저장소 변경은 이 메모1개다. 상대 링크/공백 검사는 수행했고 제품 구현·수치/브라우저 시험과 실제 입력 채택은 수행하지 않았다.

[S1]: https://edepot.wur.nl/170301
[S2]: https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json
[S2L]: https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt
[S2R]: https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/readme.txt
[S3]: https://edepot.wur.nl/706749
[S4]: https://pmc.ncbi.nlm.nih.gov/articles/PMC7698269/
