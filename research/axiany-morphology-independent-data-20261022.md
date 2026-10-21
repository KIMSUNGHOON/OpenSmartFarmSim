# Axiany 기관 형태·독립 측정 자료 확보 조사 — 2026-10-22 KST

상태: **공개 자료 경로 확인, Axiany 개별 기관 자료·계수 미확보**.
이번 조사에서 계수/실측을 채택하거나 G0–G4를 해제하지 않았다.
대상은 Axiany/Maxifort, WUR Bleiswijk Reference303 한 개발 작기다.
[기존 원 파일 감사](crop-forcing-audit.md), [등록부](crop-forcing-register.json),
[형태 모델 조사](tomato-morphology-primary-sources-20261021.md)를 전제로 한다.
아래 시각은 UTC이며 보고서 날짜와9시간 차이가 있다.

## 실제 실행과 검색 범위

native Codex 연구 자식 session `01a15e5b-df68-7b91-90d8-27f4258bcd14`,
`/root/tomato_morphology_sources_20261021`에서 재귀 CLI 없이 수행했다.
실제 `turn_context`는 `2026-10-21T15:19:12.196Z`, **gpt-6.1-sol / xhigh**다.
원 JSONL491행 SHA-256(마지막 LF 포함)은
`fcb7ff59a0becbfb409972ea85ef411363ef789c62c6ff41200674d1c7cfd4c7`다.
작성/출처 대조자는 이 세션이며 독립 자료 승인 reviewer는 없다.

검색은 Axiany와 `internode`, `phyllochron`, `plant architecture`, `morphology`의 조합,
WUR/4TU/원 출판사와 DataCite 공개 메타데이터로 한정했다. DataCite의
[Axiany 검색 API](https://api.datacite.org/dois?query=Axiany&page%5Bsize%5D=10)는2건을 반환했으며,
모두 **동일 AGC2 실험의 판본1·2**였다. 검색 범위에서 별도 Axiany 기관 측정 자료를 찾지 못한
것이며, 전 세계 모든 비공개/미색인 자료가 없다고 입증한 것은 아니다.

## 확보 가능성과 실제로 남는 공백

| 필요한 자료 | 확인한 공개/요청 경로와 단위 | 이번 판정 |
| --- | --- | --- |
| 실내 AIR 시계열 | **공개 경로 있음**: AGC2 `Reference/GreenhouseClimate.csv`, `Tair:°C`,5분 표방 자료. 기존 감사47,809행·Tair71결측. | 관측 후보는 있지만 UTC/DST·구간 의미와 QC/센서 적용성은 보류. 기온값은 품종 **기준온도 계수**가 아니다. |
| 주별 집계 성장 | **공개 경로 있음**: `Reference/CropParameters.csv`,23행.10표본 줄기의 신장 `cm/week`, 굵기 `mm`, 누적 화방 `count/stem` 평균과 밀도. 주요3성장 열은 각각5결측. | 기존 감사의 공개 집계다. 초기 절대 키·각 절간 길이·모든 마디/잎 수·개별 기관 출현을 채우지 못한다. |
| 초기 개별 기관 상태 | 같은 줄기의 기관 ID·순서·초기 절간 길이 `m`, 기관별 출현 시각·기존 기관 나이. | **미확보**. 기존 Reference 파일의 초기 LAI/기관량도 미확보다. 전체 줄기 신장을 임의로 마디에 나누지 않는다. |
| Axiany phyllochron/첫 출현 phase | `degC_day`, 명시한 기준온도·기관 출현 정의·반복 기관 ID와 기온. | **미확보**. 주별 화방 평균은 전체 phytomer 출현 이력이 아니며, 잎/화방 구조를 가정해 역산하지 않는다. |
| 절간 길이 계수 | 동일 품종/대목·관리의 `maxlen:m`, `klen:1/degC_day`, `tmlen:degC_day`와 보정 표본/오차. | **미확보**. Smoleňová2025의 공개 표는 다른 품종의 근거다. Axiany 값으로 옮기지 않는다. |
| Axiany AIR 기준온도 | 기준온도 `°C`와 독립적인 기관 발달 관측·온도 처리 근거. | **미확보**. 다른 품종의4°C나 임의 기온 하한을 기본값으로 쓰지 않는다. |
| 다른 품종의 상세 계측 | **요청 경로만 있음**: Smoleňová2025 NPEC 실험은 기관 길이/개수·영상 계측을 설명하고 매개변수화 자료는 요청 시 제공한다고 밝힌다. | 수령/계약0. Merlice/Brioso/Moneymaker 등의 자료이며 **Axiany 자료가 아니다**. 자료 재사용권도 미확인이다. 연락하지 않았다. |
| 독립 Axiany 검증 작기 | 모델 개발/보정에 쓰지 않은 품종/대목·관리 대응 기관 추적·기온 자료. 국내 주장은 국내 독립 측정이 필요하다. | 이번 검색/수령 **0건**. AGC2의 다른 구역은 같은 시설·작기를 공유한다. 판본1·2나 구역 수를 독립 작기 수로 세지 않는다. |

**주별 집계는 개별 기관의 공백을 메우지 못한다.** 이는 기존 실제 파일의 열/표본 정의와 이번
모델 입력 요구를 대조한 판단이다. `Stem_elong`은 주별 길이 변화이며 초기 절대 길이와 기관별
배분을 주지 않는다. `Cum_trusses`도10표본 평균으로 개별 줄기의 정수 사건 시각이 아니다.
동일 집계와 일치하는 서로 다른 초기 기관/출현 이력이 가능하므로 하나를 임의 선택하지 않는다.

Reference303은 이미 개발 대상으로 골랐으므로 같은 관측으로 fitting한 뒤 그 관측을 독립 정답으로
사용하지 않는다. 다른 AGC2 구역은 사전 분할한 외부 비교의 후보가 될 수 있으나 같은 환경/작기를
공유한다는 제약을 남겨야 한다. 국내 G2·새 미래 작기 G3a의 대체가 아니라는 것은 프로젝트의
검증 설계 판단이다. [확보 상태 파일](crop-independent-data-status.json)은2026-10-04 기록 기준
국내 동의 농장/수령 자료/미사용 작기 예약0이다. 이번 조사도 새 수령·동의·예약을 만들지 않았다.

## 확인한 1차 출처·권리·시각

| 출처/제품 ID·URL | 관측·게시/판본·retrieval | 사용/표시/재배포와 QC 범위 |
| --- | --- | --- |
| **AGC2** DOI `10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7`; [WUR](https://research.wur.nl/en/datasets/autonomous-greenhouse-challenge-second-edition-2019/), [기탁 API](https://api.figshare.com/v2/articles/12764777), [DataCite](https://api.datacite.org/dois/10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7) | 작기2019-12-16~2020-05-29, 파일 시각의 UTC 미승인. **v2 게시2020-09-23T10:41:39Z**, 수정1초 뒤. WUR의2020-08-20 공개일을 v2의 as-of 시점으로 소급하지 않는다. 새 API retrieval은 아래. | 데이터셋 **CC0-1.0** 선언 재확인. 사용/표시/재배포 선언이 채널 QC·품종 적용 승인과 같지 않다. 개별 파일 고지·그림/설명서 재배포는 별도 미채택. 원 파일은 이번에 받지 않았다. |
| **원 실험 논문**, Hemming 등2020, DOI `10.3390/s20226430`; [원 출판사](https://www.mdpi.com/1424-8220/20/22/6430), [보존 논문](https://pmc.ncbi.nlm.nih.gov/articles/PMC7698269/) | Axiany/Maxifort·파종2019-10-19·정식2019-12-16/해당 작기 맥락. 게시2020-11-11. 새 출판사 요청429; 원 검색/기존 감사 근거만 사용. | 논문 **CC BY4.0**, 저자·제목·DOI·라이선스 출처 표시. 그림/원문 재배포 없음. 초기 기관 계수/개별 추적 자료 확보의 근거로 쓰지 않는다. |
| **Smoleňová 등2025**, DOI `10.1093/insilicoplants/diaf022`; [원 논문](https://academic.oup.com/insilicoplants/article/7/2/diaf022/8342854), [저자기관 등록](https://research.wur.nl/en/publications/development-of-a-tomato-functionalstructural-plant-model-for-digi/) | NPEC2021 봄/가을 다른 품종 실험; 개별 관측 시각 미확보. 게시2025-11-26/typeset 수정2025-12-08. 이번엔 보존 원문 §2.2/2.3·Data availability를 읽고 기관 등록을 웹 조회했다. | 논문 **CC BY4.0**. 요청 대상 매개변수화 자료·영상/최적화 코드의 권리는 별도 미확인. 원 코드/자료 재사용0. |
| **Axia 종자사 AXIANY 영문 페이지**, 제품 경로 `/en/segments-overview/axiany/`; [공식 페이지](https://www.axiasemillas.com/en/segments-overview/axiany/) | 이번 웹 제목은 **AXIANY**다. 관측 시험/표본·게시/수정일·고정 판본 미확인. 직접 HTTP raw 요청403. | 품종 상품 설명이며 기관별 원 측정/모델 계수는 제시하지 않는다. 재사용 라이선스 미확인, ©2026. 페이지/사진/표시 수치를 모델이나 자산으로 채택하지 않았다. [판매 약관](https://www.axiasemillas.com/terms-and-conditions/)은 데이터 재배포 허가의 근거로 쓰지 않는다. |

전 출처의 농장 의사결정용 **`available_at`은 미복원**이다. 공개일/메타데이터 갱신일을
해당 파일·개별 관측의 당대 이용 가능 시각으로 바꾸지 않았다. 웹 도구만으로 읽은 페이지의
정확한 응답 시각/새 raw hash는 미확보이며 조회 날짜는2026-10-22 KST다.

## 이번 메타데이터와 기존 원 hash의 구분

이번에는 작은 공개 메타데이터만 임시 공간에 보존했다. 새 retrieval·원 응답 SHA-256은 다음과 같다.

| 응답 | retrieval UTC | bytes·SHA-256 |
| --- | --- | --- |
| Figshare article12764777 v2 |2026-10-21T15:20:21.673941Z|8,797; `56d641d0da19c6750020a48ae92da642dc7a4aa82e3e857190643fb2f6741ce6`|
| DataCite v2 DOI |2026-10-21T15:20:21.674667Z|14,796; `580f57622ff3522bf97178780bbfaaed45dbdf4ed524868800620c82da0fbf12`|
| DataCite query=Axiany,2건 |2026-10-21T15:20:53.494947Z|12,030; `3d281e591f6896f05be768ce8b32c73c12f613f35aea6f2160447dbeb50382f9`|

앞의 두 hash는 기존 메타데이터와 같다. 검색2건의 다른 DOI는 같은 제품의
`10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7.v1`이다. v1의 원 파일 내부를 새로
감사하지 않았으므로 추가 기관 파일이 있다고 추측하거나 v2와 완전히 동일하다고 단정하지 않는다.
검색 응답/기관 웹페이지의 메타데이터 자체 재배포권을 별도로 승인하지 않았고 원 응답은 Git에 넣지 않았다.

아래는 **기존 원 파일 감사**의 hash이며 이번 재다운로드 증거가 아니다.

- archive file ID `24757220`,8,418,715bytes: `b889e9ab1663fe3b8a90a3dab71d4340a6ecd49492532c43784cc82d799708ca`.
- `24757220#Reference/CropParameters.csv`,704bytes: `a7083f3355e2a61bc84510cd25e708ca2d833a69f45009e31be1e64010ecf392`.
- `24757220#Reference/GreenhouseClimate.csv`,13,977,512bytes: `eb99daf5360315232d4fd7a58f64a7226188d10a650d873e13640606ce076ebc`.

그 원 archive retrieval은 `2026-10-04T08:49:39.307459Z`다. CropParameters의 후보 Excel
날짜는2019-12-24~2020-05-27, 기후 파일은2019-12-16~2020-05-30 경계까지이며 시간대는 미확인이다.
행/열·단위/결측과 hash는 등록부의 기존 QC를 재사용했고 새로운 원본 QC를 실행하지 않았다.

Smoleňová 원 HTML은 이전 retrieval `2026-10-21T12:08:58.938525Z`,449,439bytes,
SHA-256 `e3d4b09e1d0e2041d43736d1fd5181442e2fbd851f2434a84a553bdf13422749`다.
Hemming 원 논문의 기존 retrieval/hash는 [모델 출처 등록부](crop-tomato-source-register-20261004.json)에
남아 있으며 새429 응답을 원 논문 bytes/hash로 기록하지 않는다.

## 남는 외부 의존성과 이번 확인 범위

실제 Axiany 연결에는 같은 줄기의 초기 기관 ID/순서·길이와 반복 출현/길이, 교정된 AIR/시각,
품종/대목·관리 사건, 보정용/독립 검증용 작기의 분리와 자료 이용·표시·재배포 권리가 필요하다.
확보 전에는 일반 수식·명시 합성 입력의 소프트웨어 개발 범위만 유지한다.

이번 작업은 이 보고서만 작성했다. 외부 연락·농장/개인자료 수집·자격증명 조회·대형 raw 다운로드·
새 모델 계산/제품 파일 변경은 없다. 상대 링크 존재·공백을 확인했고 제품/전체 시험은 수행하지 않았다.
