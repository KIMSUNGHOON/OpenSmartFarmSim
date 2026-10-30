# 한 작기·과실/수확의 기존 출처·품종·독립 자료 목록 — 2026-10-31 KST

상태: **기존 저장소 근거의 위치 목록**. 새 외부 조회·자료 수신·계수 선정·권리 채택·관문 판정은 없다. 과실/수확 식과 연구 소프트웨어는 이미 존재하며, 이 목록은 이를 없는 기능으로 취급하거나 다시 구현하자고 제안하지 않는다. 최종 모델 연결·채택 판단은 부모 native CLI 검토 대상이다.

## 대상과 품종 식별

- 해외 개발 참조는 **Axiany/Maxifort, Bleiswijk Reference303, 2019-12-16~2020-05-29**다. 최초 선정과 독립성 한계는 [crop-tomato-model-baseline-20261004.md:18](crop-tomato-model-baseline-20261004.md), 원 실험은 Hemming 등, DOI `10.3390/s20226430`의 [논문](https://pmc.ncbi.nlm.nih.gov/articles/PMC7698269/)에 연결된다. 같은 개발 작기 또는 AGC 다른 구역을 국내 독립 작기로 세지 않는다.
- 최신 국내 목록은 **국내 첫 품종 미확정**과 해외 참조를 구분한다: [independent-domestic-cherry-tomato-data-20261024.md:3](independent-domestic-cherry-tomato-data-20261024.md). 10월22일 국내 경로 노트의 “첫 대상 Axiany” 표현을 국내 확정 품종으로 확대하지 않는다.
- Axia의 기존 비언어 경로는 AXANTIA XR 제목으로 관측됐고, 나중 영문 경로는 AXIANY로 관측됐다. [최초 기록:29](crop-tomato-model-baseline-20261004.md) / [후속 기록:56](axiany-morphology-independent-data-20261022.md), [공식 영문 상품 경로](https://www.axiasemillas.com/en/segments-overview/axiany/). 이 기록은 상품 설명이며 종자 lot·국내 공급·기관 계수나 측정의 증거가 아니다. 사진/문구 재사용권도 미확인이다.
- 국내 논문의 HR24는 `Joeungyeo’`/Farm Hannong이라는 논문 표기까지다. 공식 한국어명·제품/등록 ID·대목 연결은 미확정이다: [crop-domestic-cultivar-hr24-identity-20261007.md:9](crop-domestic-cultivar-hr24-identity-20261007.md), [원 JATS](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml), [공식 종자 목록](https://www.farmhannong.com/kor/product/product_ct03/list.do). Axiany 또는 국내 첫 품종과 합치지 않는다.

## 이미 있는 과실·수확 원식과 매개변수 provenance

| 기존 1차 출처 / 고정 ID | 저장소의 정확한 위치와 확인 범위 | 품종·권리 한계 |
| --- | --- | --- |
| Vanthoor thesis, DOI `10.18174/170301`, [원 PDF](https://edepot.wur.nl/170301) | [crop-fruit-cohorts-baseline.md:36](crop-fruit-cohorts-baseline.md): Ch9 식9.2/9.3의 C/N 수지, 9.29~9.37의 착과/이동/배분, 9.38~9.42의 Gompertz 발달, 9.43~9.45의 호흡, 9.7의 연속 DM 수확. [원식 계수 출처:69](crop-fruit-cohorts-baseline.md), [고정 프로필:2](../fixtures/crop-fruit-cohort-reference-parameters-v1.json). | 일반 참조 매개변수이며 Axiany 보정값이 아니다. PDF/그림 전체 재배포권 미확인, 수학적 정의 연구/인용 범위. 프로필은 `reference_only_not_G0`, `available_at=null`. |
| GreenLight commit `7a7b36870135aa38bbe81e65590dcf5473786bdd`, [고정 작물 JSON](https://github.com/davkat1/GreenLight/blob/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json) | [crop-tomato-model-baseline-20261004.md:46](crop-tomato-model-baseline-20261004.md): 39개 const 항목의 값/단위/경로/근거. [crop-fruit-cohorts-baseline.md:21](crop-fruit-cohorts-baseline.md): 고정 단순화 코드는 전체 50구획 검증기가 아님. | [BSD-3-Clause-Clear 고지](https://github.com/davkat1/GreenLight/blob/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt) 유지 필요. 일반 SLA/분배/초기 밀도 등을 Axiany 실측 계수로 전환하지 않는다. |
| Greenhouses-Library commit `89ae0e8097eb0751abce2013d304fa5f9c09b885`, [저자 crop 코드](https://github.com/queraltab/Greenhouses-Library/blob/89ae0e8097eb0751abce2013d304fa5f9c09b885/Greenhouses/Components/CropYield/TomatoYieldModel.mo#L285) | [crop-fruit-allocation-policy.md:17](crop-fruit-allocation-policy.md): 인쇄 분모의 보존 문제, 코드/설명 차이를 대조. [명시 연구 배분 판본:43](crop-fruit-allocation-policy.md)은 입력 S/W1과 보존형 분모를 사용한다. | 저자 승인 정정이나 생리 검증이 아니다. BSD-3-Clause 조건 검토·연구 인용이며 외부 소스/runtime 이식은 없음. 자동 착과/초기 seed·진입 질량을 관측으로 제공하지 않는다. |
| Kuijpers 등2021, DOI [`10.1016/j.biosystemseng.2021.06.002`](https://doi.org/10.1016/j.biosystemseng.2021.06.002) | [crop-fruit-allocation-policy.md:34](crop-fruit-allocation-policy.md): 지연 모델의 평활 온도/정상 상태 가정과 초기 작기 공백을 기록. | 현재 결합의 초기 W1/분모 해결 근거로 채택하지 않음. 기존 노트는 CC BY4.0을 기록하며 PDF/그림 재배포는 없음. |
| GreenLight 고정 [예제](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/scripts/greenlight_example.py), Vanthoor 식9.7, AGC2/논문 | [crop-harvest-conversion-baseline-20261006.md:49](crop-harvest-conversion-baseline-20261006.md): CH2O→DM, DM/FW 표본, 연속 terminal·관리 제거·실제 수확의 차이. [단위 대조:65](crop-harvest-conversion-baseline-20261006.md). | 예제 DMC 0.06, 논문 평균9.0%, Brix는 Axiany 날짜별 실측 환산값으로 채택되지 않았다. C/N 제거는 생과kg·등급·판매를 자동 제공하지 않는다. |

연구 구현의 실제 위치도 존재한다: [crop_fruit_cohorts.py:16](../backend/app/crop_fruit_cohorts.py)의 고정 연구 모델/프로필과 [crop_harvest.py:60](../backend/app/crop_harvest.py)의 `research_removal_math_only` 행. 이것은 구현 위치 확인이며 실행·통합·현장 수용을 새로 검증한 결과가 아니다.

## 실제로 받아 감사한 해외 자료와 남은 QC

AGC2 DOI `10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7`, article12764777 **v2/file24757220**는 단순 catalog만 있는 후보와 구분된다. 과거 실제 archive와 선택 Reference CSV를 받아 감사한 기록이 있다: [crop-forcing-audit.md:16](crop-forcing-audit.md), [공식 기탁 metadata](https://api.figshare.com/v2/articles/12764777), [공식 파일](https://ndownloader.figshare.com/files/24757220). v2 게시 `2020-09-23T10:41:39Z`, 원 retrieval `2026-10-04T08:49:39.307459Z`, archive SHA-256 `b889e9ab1663fe3b8a90a3dab71d4340a6ecd49492532c43784cc82d799708ca`는 기존 근거다. 이번 재수신/재해시가 아니다.

| 실제 감사 대상 | 기존 관측 위치 | 채택에 남는 공백 |
| --- | --- | --- |
| Reference climate / growth / production / quality / resources | [crop-forcing-audit.md:42](crop-forcing-audit.md): 47,809 climate 행, 23 growth 행, 24 production 행, 8 quality 행과 raw/가공 구분. | UTC/DST·구간 의미, 필수 결측/이상값, 수관 온도·초기 상태, 면적/밀도·개별 관리 사건. 가공 PAR/공급열은 독립 PAR/구매 에너지 계량으로 전환하지 않는다. |
| 주별 생장 집계 | [axiany-morphology-independent-data-20261022.md:27](axiany-morphology-independent-data-20261022.md): 10표본 줄기의 신장/직경/화방 평균. | 초기 기관 ID/길이·개별 출현/절간·Axiany phyllochron/기준온도/신장 계수·독립 기관 추적은 미확보. |
| DMC / 생산 면적 | [crop-harvest-reference303-dmc-followup-20261008.md:11](crop-harvest-reference303-dmc-followup-20261008.md): 공식 v1/v2만 확인; v1 ReadMe는 v2 CSV의 제공자 정정이 아님. | header7/data8의 8열 후보 미채택; 건조/표본 FW-DM/QC와 Reference303의 62.5/76.8/96m² 연결 미해결. 후속 확인에서도 실제 환산 근거는 보류. |

기존 notes는 dataset **CC0-1.0 선언**을 기록한다. 이는 해외 실제 측정/가공 파일의 긍정적인 권리 근거다. 개별 파일 고지·설명서/그림과 QC·품종 적용·독립성을 별도로 남긴다: [axiany-morphology-independent-data-20261022.md:49](axiany-morphology-independent-data-20261022.md). 모든 의사결정용 `available_at`은 미복원이며, Reference303은 이미 개발 참조다. 현재 임시 원본의 존재를 이번에 확인하지 않았고 원 archive/CSV를 저장소에 복사하지 않았다.

## 국내 자료: catalog/schema/access 경로이며 원측정 수신은 0

최신 묶음은 [independent-domestic-cherry-tomato-data-20261024.md:11](independent-domestic-cherry-tomato-data-20261024.md)이다. 아래 publication·license·절차는 그 노트가 기록한 관측이며 **2026-10-31에 외부 재확인한 상태가 아니다**.

| 공식 제품 ID / 1차 URL | 기존 목록이 제시하는 범위 | 실제 수신·사용/표시/재배포 상태 |
| --- | --- | --- |
| [RDA ADP4129](https://adp.rda.go.kr/portal/pub/data/dataDetail.do?dataId=4129&dataTypeCd=PBLCATE), DOI `10.23138/RDA.20260521-00002.r1` | 2023 작기 방울토마토58농가, 환경·생육·생산(판매), 품종/정식일/면적; 출판2026-05-21. | ZIP/측정행 수신0. CC0 1.0 표기와 타인 공유 제한 안내, 본인인증/목적 절차의 적용관계 미확정. 파일별 허락/QC/농장·작기·품종/독립성 미검사. |
| [RDA ADP4163](https://adp.rda.go.kr/portal/pub/data/dataDetail.do?dataId=4163&dataTypeCd=PBLCATE), DOI `10.23138/RDA.20260707-00001.r1` | 2024/25 작기 방울토마토79농가; 목록 출판/등록2026-07-01. | 같은 수신/권리 공백. DOI 날짜를 목록 출판일로 고쳐 쓰지 않음. 58+79를 중복 없는 독립 작기로 합산하지 않음. |
| [SmartFarmKorea7581](https://www.smartfarmkorea.net/structuredDataset/selectDetailView.do?menuId=M11040101&crpsnSn=7581&fcltyId=PF_0021341_01&facilityId=PF_0021341_01&fcltyYear=2024&yearCheckNm=2024&itemCode=080600&itemCheckNm=080600) / `PF_0021341_01` | 공개 HTML의2024-08-29~2025-07-03 기간·시설/작기 ID. | ZIP/측정행0. 품종·채널별 전체 기간·QC·처리/표시/재배포권 미확인. |
| [DATA15121331](https://www.data.go.kr/data/15121331/openapi.do) | 혁신밸리 환경/생육·시설/작기·면적 API 설명, 2022–2025 작기; 등록2023-08-30/수정2025-07-09. | 실제 API 응답0. 무료/허락 제한 없음 표기, 개발 자동/운영 심의 승인. 품종/방울 여부·수확/단위/주기·원판본은 미검사. |
| [AI Hub534](https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&currMenu=11&dataSetSn=534&topMenu=) / [공식 정책](https://www.aihub.or.kr/intrcn/guid/usagepolicy.do?currMenu=151&topMenu=105) | 토마토6농가; 2021 구축, v1.0 개방2022-07-13/v1.1 수정2023-06-30. 생장/수확·환경·급배액 등 schema. | 원측정/샘플 수신0. 목적 신청·승인, NIA 표시·제3자 제공·국외 이용 제한을 기록. 결정적 모델 검증·제품 표시/배포·외부 처리 허락 미확보. `KW` 표기는 구매kWh가 아님. |
| [DATA15090553](https://www.data.go.kr/data/15090553/fileData.do) / [EPIS 제품20210928000000001574](https://data.mafra.go.kr/opendata/data/indexOpenDataDetail.do?data_id=20210928000000001574&service_ty=&filter_ty=F) | 방울토마토 환경/생육 CSV 메타, 등록2021-09-29/수정2026-09-21. | ZIP/측정행0. 포털 허락 제한 없음은 긍정적 근거이며 제공자 약관·ZIP별 권리 적용은 미해결. [행위별 권리 목록:75](crop-domestic-epis-rights-scope-20261009.md). 수정일은 새 관측 작기 증거가 아님. |

국내 Frontiers DOI `10.3389/fpls.2025.1730694`의 **부록 DOCX 판본1은 실제 수신**했지만, 검토한6표는 회귀계수/통계 요약이다. 원시 환경·생장·수확 측정을 수신한 것으로 세지 않는다: [crop-domestic-supplement-schema-20261020.md:7](crop-domestic-supplement-schema-20261020.md), [공식 부록 API](https://www.frontiersin.org/api/v4/articles/1730694/supplemental-data). 논문/저자 권리 부록의 조건부 CC BY 판단과 파일별 예외·외부 처리 미확정 범위는 [crop-domestic-supplement-rights-20261007.md:27](crop-domestic-supplement-rights-20261007.md)에 있다.

## 합성 fixture·확보 상태·검토 경계

- [crop-fruit-cohort-reference-parameters-v1.json:2](../fixtures/crop-fruit-cohort-reference-parameters-v1.json)은 일반 문헌 프로필이며, [같은 파일:40](../fixtures/crop-fruit-cohort-reference-parameters-v1.json)은 Axiany 보정·자동 생리 기본값·생과중이 아니라고 기록한다. [fixtures/README.md:3](../fixtures/README.md)의 Decimal/RK4 reference도 농장 측정·새 품종 계수·권리/관문 승인을 공급하지 않는다.
- [crop-independent-data-status.json:3](crop-independent-data-status.json)은 **2026-10-04 기록**으로 국내 동의농장/수신자료/예약 독립작기 각각0이다. 최신10월24일 [목록:3](independent-domestic-cherry-tomato-data-20261024.md)과 [결론:54](independent-domestic-cherry-tomato-data-20261024.md)도 새 수신·독립 reviewer·as-of 복원이 없음을 기록한다. 오래된 status 파일의 기록일을 갱신하지 않았다.
- 이미 정의된 이용 범위 구분은 [crop-independent-data-protocol.md:18](crop-independent-data-protocol.md)의 개발/보정/검증·CLI 처리·표시/공유·철회 항목이다. 새 접근 동의/요청이나 연락은 이번 목록으로 생기지 않는다.

이번 작업은 README/AGENTS 및 기존 문서·프로필/짧은 코드 위치를 읽고 이 한 파일만 새로 작성했다. 기존 조사 CLI의 실제 invocation/output 근거는 [모델 조사:10](crop-tomato-model-baseline-20261004.md), [과실 조사:11](crop-fruit-cohorts-baseline.md), [환산 조사:22](crop-harvest-conversion-baseline-20261006.md), [DMC 후속:107](crop-harvest-reference303-dmc-followup-20261008.md), [국내 후속:61](independent-domestic-cherry-tomato-data-20261024.md)에 있다. 이 위치 목록은 새 독립 source review나 runtime CLI 호출의 증거가 아니다.

신규 외부 GET·대형 raw 다운로드·제한 원문/개인 농장기록 열람·재귀 CLI·제품 계산·시험·CI·브라우저/서비스 조작·원 source/profile/plan 수정은0이다. 문서의 상대 링크 존재와 줄끝 공백을 확인하는 범위만 검증하며, 품종/권리/관문과 실제 한 작기 생산·경제의 남은 hold는 변경하지 않는다.
