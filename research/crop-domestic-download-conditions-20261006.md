# 국내 방울토마토 후보 B 다운로드 조건 보완 조사 — 2026-10-06

상태: **공개 접근 경로·문서 연결·권리 충돌 후보의 조사 제안. 원자료 수신·권리 승인·관문 판정 전**.
[전일 목록 검토](crop-domestic-public-catalog-review-20261005.md)의 B만 보완했다.
[프로토콜](crop-independent-data-protocol.md), [체크리스트](crop-independent-data-checklist.md),
[확보 상태](crop-independent-data-status.json)의 국내 수신·독립 작기 0건은 그대로다.

## 실행 및 조회 근거

부모 native Codex CLI 연구 위임에서 `gpt-6.1-sol` / `xhigh`로 수행했다.
부모가 전달한 실제 부모 `turn_context` 시각은 `2026-10-06T06:56:05.970Z`,
원 줄 SHA-256은 `029e8836ef9b75943ae6577b91802f4b955a2a08002af41dd3f6246311db9836`이다.
이는 **부모 제공 실행 근거**이며 본 조사자의 원 로그 독립 확인이 아니다.
재귀 CLI 실행은 없었고 실제 산출물은 이 메모와 부모에게 전달한 발견 요약이다.
최종 출처·권리·품질·G0~G4 검토자는 미지정이다.

공식 공개 HTML을 직접 GET했다. 아래 UTC는 실제 수집 완료 시각이며 게시 시각이 아니다.
응답은 사설 임시 경로 `/tmp/crop-B-public-metadata-tuxg14d3/`에 보관했다.
로그인·신청·이용목적 제출·외부 연락·ZIP/CSV/농장 원자료·문서 파일 다운로드는 없었다.
공개 PDF 링크의 web 열람 시도는 접근 오류였고 내용을 확보하지 못했다.
이 문장은 위임 조사 단계의 상태다. 이후 부모의 실제 PDF 수신/읽기는 아래 별도로 기록한다.

| 공식 출처 / 사설 HTML 파일 | 직접 GET 완료 UTC / HTTP / SHA-256 |
| --- | --- |
| [data.go.kr 15090553](https://www.data.go.kr/data/15090553/fileData.do) / `data-go-15090553.html` | `2026-10-06T07:01:00.489022Z` / 200 / `f778d0edfb298061763e1e3a2d524cfb06094d800162602779dbaf47f67d38bf` |
| [MAFRA 제품 B](https://data.mafra.go.kr/opendata/data/indexOpenDataDetail.do?data_id=20210928000000001574&service_ty=&filter_ty=F) / `mafra-B.html` | `2026-10-06T07:01:00.602679Z` / 200 / `783099be0ea5ac356f14dbff076244b3d2e1f550ac917d32caf1da1bc0c9398e` |
| [MAFRA 이용약관](https://data.mafra.go.kr/intro/indexTerms.do) / `mafra-terms.html` | `2026-10-06T07:01:49.975675Z` / 200 / `01cbe8aeede5a00344de1e0026d7df05ae6ef848baf06900f4af49fb12ea18e3` |
| [2021 수집 데이터 표준](https://www.smartfarmkorea.net/board/view.do?menuId=M1105030801&searchBbsId=BBSMSTR_000000000031&searchNttId=3258) / `smartfarm-collection-standard-2021.html` | `2026-10-06T07:03:26.257189Z` / 200 / `ff7cfd393feb9f106b3aca83b0a37ea6e94c9f9156953656742d6d2ccbd88621` |

이 해시는 동적 공개 HTML 응답의 근거다. ZIP 원본 해시·관측 판본·QC 해시가 아니다.

부모는 B HTML을 `2026-10-06T07:02:41.173776Z`에 별도 HTTP 200으로 확인했고
직접 제출 함수/파일 Y·API N·빈 API 식별자를 대사했다. 부모 제공 기록은
`/tmp/ossf-domestic-provider-parent-review-20261006.json`, HTML SHA-256
`1d6588ef2b9f91d2b02546c098f7e7eab56247c5f11e8f6e0a931b6edcd9fe13`이다.
약관 제15조도 `2026-10-06T07:04:00.074154Z`에 HTTP 200으로 재확인했다.
부모 제공 기록은 `/tmp/ossf-domestic-provider-parent-terms-review-20261006.json`,
HTML SHA-256 `1ad50461c4f4c9f72e866e56cca734571700836e4cf89d564618f87683d1aa58`이다.
이는 부모의 독립 출처 재조회 보고이며 데이터/권리/관문 수용이 아니다.

## 새로 확인한 다운로드 경로와 한계

**공식 페이지 사실:** B는 `file_provd_ennc=Y`, `api_provd_ennc=N`, 빈 `api_id`를 내려준다.
`filedownload()`는 `data_id`, `file_ty_code`, `file_sn`을 넣어
`POST /opendata/data/downloadOpenDataWebFile.do`로 제출한다.
이 함수에는 로그인·이용목적·승인 확인이 없다. 지역별 연결은 아래와 같다.
[근거: B 공개 HTML의 함수·hidden 필드·첨부 목록](https://data.mafra.go.kr/opendata/data/indexOpenDataDetail.do?data_id=20210928000000001574&service_ty=&filter_ty=F).

| `data_id` | `file_ty_code` | `file_sn` | 표시 파일명 |
| --- | --- | --- | --- |
| `20210928000000001574` | `file` | `1` | `전라남도.zip` |
| 같은 제품 | `file` | `2` | `전라북도.zip` |
| 같은 제품 | `file` | `3` | `충청남도.zip` |
| 같은 제품 | `file` | `4` | `경기도.zip` |

**소스 코드에 근거한 해석:** 5,000건 제한과 로그인 이동은 별도 `getDataTotal()`의
OpenAPI 조회 결과 내보내기에 있다. B는 API 탭을 숨긴다. 따라서 이 템플릿 경고를
B ZIP의 크기 제한이나 신청 필수 조건으로 적용할 근거가 없다.
같은 숨겨진 탭의 ‘명세서 다운로드’는 빈 API 식별자로 구성되어 있어 ZIP 설명서의
증거가 아니다. ZIP 목록에는 별도 설명서/미리보기 링크가 없다.
[근거: B의 탭 초기화·다운로드 함수](https://data.mafra.go.kr/opendata/data/indexOpenDataDetail.do?data_id=20210928000000001574&service_ty=&filter_ty=F).

**미확인:** 서버의 POST·ZIP 응답을 시험하지 않았다. 익명 다운로드 성공,
서버 측 인증/승인 여부·파일 존재/크기/내용은 확정하지 않는다.

## 공개 문서와 실제 B 판본의 연결

별도로 찾은 [공식 2021 게시물](https://www.smartfarmkorea.net/board/view.do?menuId=M1105030801&searchBbsId=BBSMSTR_000000000031&searchNttId=3258)은
등록일 `2021-08-05`, 제목 ‘스마트팜 수집 데이터 표준’, 첨부
‘시설원예 분야 스마트팜 수집 데이터 규격.pdf’를 명시하며
[공개 첨부 경로 `fileId=3350`, `type=BBS`](https://www.smartfarmkorea.net/file/download.do?fileId=3350&type=BBS)를 제공한다.
문서 내용은 미확보이고 B 제품/ZIP에 적용된 규격 버전이라는 연결도 없다.

### 부모의 실제 첨부 수신과 판본 불일치 확인

부모는 같은 공식 `fileId=3350&type=BBS`를 직접 GET해
`2026-10-06T07:06:46.330619Z`에 HTTP200·`application/octet-stream`·PDF 서명을 확인했다.
실제 문서는1,090,524bytes·26쪽, SHA-256
`fff624e33e014467cda020472b019cebdd69aa791246a051671e8c24516e389e`다.
사설 파일은 `/tmp/ossf-smartfarm-2021-collection-standard-3350-20261006.pdf`,
조회 근거는 `/tmp/ossf-smartfarm-2021-collection-standard-3350-retrieval-20261006.json`에 남겼다.
시스템의 기존 `pypdf6.13.1`로 원문을 읽었고 프로젝트 의존성·잠금은 바꾸지 않았다.
`pdftotext` 부재로 첫 시도는 종료1이었으며, pypdf 읽기는 실제 종료0이었다.

**실제 PDF의 사실:** 표지1쪽은 `SPS-X KOAT-0009-7470:2022`, 제정일`2022-04-11`을
명시한다. 게시물의2021 날짜와 받은 첨부의 규격 판본이 다르다.7–8쪽은 CO₂의
µmol/mol, 광양자의 µmol/m²/s, 일사 에너지의 W/m²를 구분한다.14–15쪽의 재식밀도는
주/m²이고 정식·적엽·수확 시작/종료는 `xs:date` 필드다.
[근거: 실제 공식 첨부1·7–8·14–15쪽](https://www.smartfarmkorea.net/file/download.do?fileId=3350&type=BBS).

이는 현재 받는 문서의 설명이며 B 원행의 단위/시각 의미를 입증하지 않는다.
읽은 텍스트에서 UTC/KST 지정은 확인하지 못했고, 실제 archive 시간대는 계속 미확인이다.
첨부 교체일·최초 공개 시각·`available_at`·2021 ZIP에 적용된 규격은 알 수 없다.
2021 게시일을 현재 PDF의 최초 공개/이용 가능 시각으로 기록하지 않는다.
농장 ZIP/CSV 수신은0건이며 PDF 원 파일/전체 본문은 저장소나 외부 모델 프롬프트에 복제하지 않는다.

[2025 수집항목 변경 게시물](https://www.smartfarmkorea.net/board/view.do?menuId=M1105030801&searchBbsId=BBSMSTR_000000000031&searchNttId=4209)은
등록일 `2025-05-27`과 변경 PDF `fileId=3631`을,
[2026 생육조사 매뉴얼 게시물](https://www.smartfarmkorea.net/board/view.do?menuId=M1105030801&searchBbsId=BBSMSTR_000000000031&searchNttId=4361)은
등록일 `2026-03-20`과 토마토(방울토마토) 간편 PDF `fileId=4101`을 명시한다.
각 HTML은 `2026-10-06T07:03:05.989370Z`, `07:03:05.813606Z`에 HTTP 200으로 수집했다.
둘 다 B의 2021 지역 ZIP 판본을 설명한다고 확인되지 않았다.

**B에 대하여 원자료 없이 확인된 범위:** 제품→지역 ZIP 순번과 일반 채널 설명뿐이다.
정확한 단위·관측 주기/시각 의미·UTC/KST, 품종/대목, 작기·면적/밀도,
관리/수확 사건·표본법·센서 위치/오차는 계속 미확인이다.
새 매뉴얼이나 다른 SmartFarmKorea 제품의 표 단위를 B에 전이하지 않는다.

[15090553](https://www.data.go.kr/data/15090553/fileData.do)의 파일데이터명 접미사 `20210928`,
등록일 `2021-09-29`, 수정일 `2026-09-21`과
[제공자 B](https://data.mafra.go.kr/opendata/data/indexOpenDataDetail.do?data_id=20210928000000001574&service_ty=&filter_ty=F)의
등록/수정일 `2021-09-28`은 목록 날짜다. 실제 관측 기간·최초 공표 시각·
`available_at`·ZIP별 vintage/revision·수집 표준 적용일은 미확인이다.

## 새 권리 확인 사항과 구체적 다음 단계

[data.go.kr 제품](https://www.data.go.kr/data/15090553/fileData.do)은 ‘이용허락범위 제한 없음’을,
[제공자 제품](https://data.mafra.go.kr/opendata/data/indexOpenDataDetail.do?data_id=20210928000000001574&service_ty=&filter_ty=F)은
빈 이용허락범위를 표시한다. 추가로 [제공자 약관 제15조 ‘회원의 의무’](https://data.mafra.go.kr/intro/indexTerms.do)의
2·3항은 **회원**의 영리행위와 취득 정보의 복사/변경/출판·방송/타인 제공에 사전 승낙을 요구한다.
약관 효력일은 본문에서 확인하지 못했다. 제품별 허락과 회원 약관의 적용 대상·우선순위,
익명 이용·내부 계산/검증·집계 표시·원문 재배포·외부 CLI/국외 처리·상업 이용에 대한
적용은 **미해결 검토 사항**이다. 어느 표시도 이 메모에서 법적 승인으로 판정하지 않는다.

공개 규격 PDF의 실제 판본 대사는 위와 같이 진행했다. 현재 특정할 수 있는 다음 접근은
2021 B archive에 실제 적용된 규격/설명서와 현재의2022 첨부 교체 이력을 확인하는 것이다. B 자체에 연결된
추가 문서가 없으므로, 실제 자료 확보 단계에서는 권리·사설 보관/처리 범위를 확인한 뒤
**원래 B 페이지의 지역 ZIP 링크**로 서버 조건과 파일 목록/동봉 설명서를 점검해야 한다.
신청이나 목적 제출이 필요하다는 사실은 아직 확인되지 않았다. 이 조사에서 그 단계는
실행하지 않았으며 원 ZIP 해시·파일별 QC·reviewer 승인과 G0/G2/G3a는 보류다.

이번 변경은 이 조사 메모 하나다. 코드·시험·프로필·fixture·확보 상태는 변경하지 않았고,
PG·브라우저·빌드·시험 과정도 실행하지 않았다.
