# 국내 방울토마토 논문 부록의 정상 공개 접근 — 2026-10-07

상태: **정상 출판사 경로에서 실제 DOCX를 받았다. 파일별 권리·동기화 원측정·독립성은 보류다.**
검토자: native Codex CLI `gpt-6.1-sol` / `xhigh` 배경 조사 에이전트; 부모 검토 대기, 최종 deterministic 출처/권리/QC 검토자 미지정. 이 문서는 검토 가능한 CLI 증거이며 품종·계수·자료 채택 또는 관문 승인이 아니다.

## 정상 경로를 확인한 근거

[선행 접근 조사](crop-domestic-validation-access-followup-20261007.md)의 사설 공개 HTML/JATS/파일 메타데이터를 우선 읽고 해시를 대사했다. 출판사 논문 ID는 `1730694`, DOI는 `10.3389/fpls.2025.1730694`, 표시명은 `Data Sheet 1.docx`, `fileServerId=1730694/data-sheet/1`, `fileServerVersionNumber=1`이다. JATS `SM1`의 상대명은 `DataSheet1.docx`다. [공식 논문](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/full), [공식 JATS](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml)

현재 공식 화면의 정상 코드에서 아래 경로를 좁혀 확인했다. 원 JATS의 상대명으로 다운로드 URL을 추측하지 않았다.

1. 공식 full route [C6T_etef.js](https://www.frontiersin.org/ap-2024/_nuxt/C6T_etef.js)가 [BaA8sTLO.js](https://www.frontiersin.org/ap-2024/_nuxt/BaA8sTLO.js)를 렌더링한다. 이 proxy는 현재 HTML의 article template `v4`에 [DN9Rc2jw.js](https://www.frontiersin.org/ap-2024/_nuxt/DN9Rc2jw.js)를 선택한다.
2. v4가 연결한 [WvuNs0DR.js](https://www.frontiersin.org/ap-2024/_nuxt/WvuNs0DR.js)의 `ArticleInfoDrawer`는 `getSupplementalDataFiles(article.id)` 결과의 `name`과 `downloadUrl`을 표시/링크한다.
3. 그 API class를 제공하는 [B0Pwtj_j.js](https://www.frontiersin.org/ap-2024/_nuxt/B0Pwtj_j.js)는 같은 origin의 GET `/api/v4/articles/${id}/supplemental-data`를 명시한다.
4. 실제 [공식 부록 메타데이터 API](https://www.frontiersin.org/api/v4/articles/1730694/supplemental-data)는 HTTP200 JSON157B, 단일 항목과 아래 **정확한 `downloadUrl`**을 반환했다. 항목의 키는 `name`, `downloadUrl`뿐이다.

[정상 익명 공개 DOCX 다운로드](https://public-pages-files-2025.frontiersin.org/articles/1730694/file/Data_Sheet_1.docx/1730694_data-sheet_1/1)

API 응답이 위 URL과 표시명을 직접 연결한다. 현재 파일 locator/판본1과 경로 끝의 `1`을 기록했으며, 이전 PMC 첨부와 바이트 동일성을 대사한 결과는 아니다. 기존 PMC 단일 요청의 HTTP200/HTML1817B는 재요청·우회하지 않았다. [선행 PMC 조회 기록](crop-domestic-validation-access-followup-20261007.md)

## 실제 응답과 문서 열람 범위

| 항목 | 직접 관측 |
|---|---|
| GET 상태/최종 URL | HTTP200; 요청 URL은 위 API 제공 `https://public-pages-files-2025.frontiersin.org/articles/1730694/file/Data_Sheet_1.docx/1730694_data-sheet_1/1`; receipt의 최종 URL은 파일명이 소문자로 정규화된 `https://public-pages-files-2025.frontiersin.org/articles/1730694/file/data_sheet_1.docx/1730694_data-sheet_1/1` |
| MIME | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| 크기/회수완료 UTC | 실제 본문863,123B; `2026-10-07T06:37:04.464547Z` |
| 원 파일 SHA256 | `53d65c2d06d46a569e068f6290dc5ff5f6c2c3ac07c9fad573aca4eabad80df2` |
| 형식 확인 | 선두4B `504b0304`; ZIP 중앙 디렉터리와 `[Content_Types].xml`, `word/document.xml` 존재 확인; 본문 XML 파싱 가능 |
| 컨테이너 구성 | ZIP38항목, 비압축 합계1,255,640B; 본문 XML의 paragraph358개·표6개 |
| 표 구조 | 각 표8행, 행마다 `w:tc`7개. 이 수는 문서 셀 구조이며 실측 표본수로 해석하지 않는다. |
| 식별자/부속 구성 | `Supplementary Figure 1`, `Supplementary Table 1`–`6` 문자열 확인; `word/media/`2항목 |
| 별도 데이터 파일 | ZIP 내 `word/embeddings/`0개, CSV/XLSX/XLS 확장자0개. 외부 링크 대상은 가져오지 않았다. |

위 구성은 [실제로 받은 공개 DOCX](https://public-pages-files-2025.frontiersin.org/articles/1730694/file/Data_Sheet_1.docx/1730694_data-sheet_1/1)를 표준 `zipfile`/`ElementTree`로 제한 검사한 결과다. 전체 OOXML schema 검사·모든 ZIP 항목의 개별 무결성 검사를 수행한 결과는 아니다. 문서 수치행·회귀계수·농장/개체 원행을 CLI prompt/log/repo로 출력하거나 복제하지 않았다. 이미지 표시/OCR·별도 사진 다운로드도 없었다.

**자료 존재 판단의 한계:** 실제 문서와 표/그림 식별자는 확인했다. 표의 수치행을 읽어 원측정·회귀요약 여부를 판정하지 않았으므로, 동기화 환경/개체·수확 원행이나 수확별 대응 DMC의 존재는 **미확인**이다. CSV/XLSX가 없다는 사실만으로 DOCX 안의 원행 부재를 증명하지 않는다. 품종/대목·관측시각/시간대·단위/분모·QC·미사용 독립 작기는 이 검사로 확보되지 않았다.

## 공표·수정·`available_at`과 권리

| 항목 | 근거와 보류 |
|---|---|
| 논문 공표 | 기존 실제 JATS의 날짜 `2025-12-19`; 정확한 시각/시간대 unknown. 첨부의 최초 공개시각은 별도다. [JATS](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml) |
| 파일 HTTP 표시 | `Last-Modified: Wed, 26 Nov 2025 09:29:47 GMT`; opaque ETag `"0x8DE2CCE57312CC3"`. 서버 수정 표시는 최초 공개/`available_at` 또는 검증된 내용 checksum이 아니다. [파일](https://public-pages-files-2025.frontiersin.org/articles/1730694/file/Data_Sheet_1.docx/1730694_data-sheet_1/1) |
| 내부 편집 표시 | `docProps/core.xml` created `2025-11-19T03:29:00Z`, modified `2025-11-20T07:14:00Z`; 문서 편집 메타데이터이며 공개 가용시각 근거가 아니다. [파일](https://public-pages-files-2025.frontiersin.org/articles/1730694/file/Data_Sheet_1.docx/1730694_data-sheet_1/1) |
| 파일 관측/공표/`available_at` | 실제 연구 원행의 관측시각, 첨부 공표시각, 첨부 `available_at` 모두 unknown |
| vintage/revision | 현재 provider locator 판본1; 교체·수정 이력 unknown. 논문의2022/2023 실험연도를 모든 첨부 행의 vintage로 자동 부여하지 않는다. |
| 파일 내부 권리 표시 | 본문 paragraph 텍스트에서 `creative commons`, `cc by`, `cc-by`, `copyright`, `license`, `licence` 문자열 모두0건. 키워드 검사 범위의 결과이며 이미지/모든 고지에 권리가 없다는 증거는 아니다. |
| 제공자 일반 조건 | 논문 JATS는 CC BY4.0을 명시한다. 기존 회수 저자 지침은 논문 및 표/그림의 CC BY 조건과 제3자 권리 책임을 설명한다. 현재 부록 메타데이터 API에는 별도 license 필드가 없다. [JATS](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml), [저자 지침](https://www.frontiersin.org/guidelines/author-guidelines), [부록 API](https://www.frontiersin.org/api/v4/articles/1730694/supplemental-data) |
| 이용/표시/재배포/외부 CLI | 파일별 최종 범위와 원측정·제3자 내용의 처리 허락 **미확인**. 논문 CC BY 또는 익명 다운로드 성공을 부록 원농장자료의 허가로 자동 전이하지 않는다. 이 메모는 파일 본문/그림/수치행을 재배포하지 않는다. |

기존 약관·copyright 직접 GET은 실제 정책 본문이 없는 shell이었다. 현행 TDM 약관을 이번 요청으로 확인했다고 주장하지 않는다. 일반 저자 지침의 공표/효력/개정시각도 unknown이며 기존 hash-matched 공개 회수본을 재사용했다. [정책 조회 한계](crop-domestic-validation-access-followup-20261007.md)

## 사설 증거와 실제 native CLI

보관: `/home/sunghoonk/.local/state/OpenSmartFarmSim/20261007-supplement-access-research/` (`0700`, 모든 파일 `0600`). 공개 DOCX 원 파일, 공식 인터페이스 코드·메타데이터·조회 영수증과 구조/권리 검사 결과를 보존했다. 문서 원 파일에 원측정 행이 포함되는지는 미확인이며, 원행 텍스트를 prompt/log/repo에 내보내지 않았다.

- `manifest.json`: 자신을 제외한23개 파일의 경로/바이트수/SHA256/권한을 결속. SHA256 `ee8e615078ae9d4c301592338d5c79d0e6916ef3f8bd9a8b6f9490b394199504`.
- 부록 API 회수완료 `2026-10-07T06:36:41.678765Z`,157B, SHA256 `78c5ee8b5441e18653c59c5b142c68b272446a8a340fe020de2d055a5755ba4c`.
- `frontiers-attachment-retrieval.json` SHA256 `7e2d1c8461bd54c8b10077197522790b438796cb3b2d585158b27a4b86920b1c`; `docx-structure-and-rights-review.json` SHA256 `d10b2240d1ad69e9967a625b3e9dea9f5a9231432900d16462a9ddfecb87bede`.
- 실제 현재 native `turn_context`: `2026-10-07T06:32:16.604Z`, 정확히 `model=gpt-6.1-sol`, `effort=xhigh`. 자기 세션 원 JSONL의 event type·timestamp·model·effort·경로/줄번호·두 SHA만 whitelist로 직접 확인하고 재대사했다.
- 원 `turn_context` 한 줄 SHA256 **끝 LF 포함** `a5e7e62c64c284d0ccd6af6d68926a78c65fbc7a8c8845d1ab07bca2aa83e6a3`; **LF 제외** `aa87054256822db955e8f9693147bf491253901b9ef781aa6ac1a755ccdd1b03`.
- `native-context-recheck.json` SHA256 `87f5e15e43caedd3f94008d0c3679c47d03a67cb32951d4bbacf64e1e3d7f120`; `bounded-review-receipt.json` SHA256 `f7d550f1b0d2489a6bd0efaa13f685dc821854f6499bc299203cbef8dbb498f4`.

실제 호출은 이 native 턴의 `exec_command` → `python3` 표준 `urllib.request.urlopen()` 순차 GET이다. 새 GET은 공식 연결 인터페이스 JS7개, 정상 부록 API1회, 그 API가 반환한 attachment1회로 총9회다. 사전 연결된 `DANK1qUt.js`/`BVTC1wnn.js`도 읽었으나 파일 locator를 제공하지 않았으며 이 사실을 receipt에 남겼다. JS≤2MB/API≤200KB/첨부≤8MiB, timeout20–25초, 재시도0회였다. 계정·연락·figshare POST·PMC 재조회·추정 attachment URL·재귀 CLI·추가 agent는 없었다.

## 다음 단계와 남은 외부 의존성

**다음 행동은 파일별 권리 검토다.** 명시 허락 범위가 확인되면 이 판본/SHA에 묶인 표의 제목·열 이름·단위/시간키를 먼저 검토해 회귀요약과 실제 원측정 행을 구분할 수 있다. 그 전에는 수치행을 외부 CLI 입력이나 데이터·계수 채택 근거로 사용하지 않는다. 동기화 원측정이 이 부록에 없다면 해당 기록과 이용/표시/재배포/CLI 처리 허락을 함께 가진 별도 공개 제공 제품이 외부 의존성이다.

이번 범위에서 농장 검증자료·품종·계수 채택은0건이다. [현재21개 공식 제품의 카탈로그 대조](crop-domestic-cultivar-hr24-catalog-followup-20261007.md)와 별개인 출판 부록 접근/구성 조사이며, HR24의 공식 한국어명·제품/등록 ID 연결을 추가로 확정하지 않았다.

독립 검증과 품종 동일성·대목·시간/단위·센서 QC·사전 미사용 증거의 hold를 유지한다. 이 문서 하나만 새로 작성했으며 기존 보고서/receipt·프로필·수신/채택 수치·작업 checkbox·고정 소스·실행 중166일 실험/프로세스를 수정하지 않았다. 사설 해시/권한·문서 링크를 대조했고 시험·서버·계산·CI·commit/push는 실행하지 않았다.
