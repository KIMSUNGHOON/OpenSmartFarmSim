# 국내 공개 토마토 자료 카탈로그 검토 — 2026-10-05

상태: **공식 공개 목록 3개 후보의 범위·권리 점검만 완료. 원자료 확보·G0 채택·독립 검증 승인 전**.
[체크리스트](crop-independent-data-checklist.md),
[접근·분할 프로토콜](crop-independent-data-protocol.md),
[현재 확보 상태](crop-independent-data-status.json),
[첫 Axiany/Maxifort 개발 참조](crop-tomato-model-baseline-20261004.md)를 따른다.
공개 목록 열람은 농장 동의나 자료 수신이 아니며 이 검토로 확보 수치를 올리지 않는다.

## 조사 실행과 수신 범위

기존 native Codex CLI 오케스트레이션의 위임 연구 턴에서 모델 `gpt-6.1-sol`,
reasoning effort `xhigh` 설정으로 수행했다. 부모가 확인해 전달한 실제 부모
`turn_context` 시각은 `2026-10-05T12:31:45.220Z`, SHA-256은
`35f44d2c1d7e32eb54a9ff5014d7221380df339ff168c3a061f043526af9d66d`다.
이 설정·해시 확인은 부모 제공 실행 근거이며, 본 메모가 별도 CLI 명령을 실행하거나
그 원 로그를 다시 확인했다는 의미는 아니다. 재귀 `codex`/`codex exec` 호출은 없었다.
산출물은 이 메모와 부모에게 보낸 공식 URL/발견 요약이다. 최종 출처 대사와
권리·품질·관문 판정은 후속 deterministic 검토에 남긴다.

`2026-10-05T12:59:00Z`부터 `2026-10-05T13:10:01.476512Z`까지 공식 공개 HTML·정책·
공개 목록 JavaScript만 열람했다. 일부 목록은 web 도구의 캐시 표현을 포함하므로
이 구간은 **이 연구의 조회 시각**이며 제공자 서버의 게시 시각을 뜻하지 않는다.
SmartFarmKorea 목록의 공개 HTML 식별자와 목록 JavaScript는 별도로 직접 읽었다.
ZIP·CSV·이미지·샘플·활용가이드 등 **원자료 파일은 다운로드하지 않았다**.
로그인·신청·담당자 접촉·외부 메시지 발송·농장/DB 시험 자원 접근은 없었다.

부모는 출처를 별도로 재조회해 B의 무제한 표기/제품 연결과 C의 식별자·작기 표기·
표 구조 단위를 대사했다. 부모가 전달한 **공개 HTML 응답**의 SHA-256은 아래와 같다.
이 해시는 동적인 카탈로그 응답의 조회 근거이며 원 ZIP 해시나 데이터 vintage가 아니다.

| 부모 독립 재조회 UTC | 공식 페이지 | 공개 HTML SHA-256 |
| --- | --- | --- |
| `2026-10-05T13:10:57Z` | [B 공공데이터포털](https://www.data.go.kr/data/15090553/fileData.do) | `f778d0edfb298061763e1e3a2d524cfb06094d800162602779dbaf47f67d38bf` |
| `2026-10-05T13:10:57Z` | [C 상세](https://www.smartfarmkorea.net/structuredDataset/selectDetailView.do?menuId=M11040101&crpsnSn=7581&fcltyId=PF_0021341_01&facilityId=PF_0021341_01&fcltyYear=2024&yearCheckNm=2024&itemCode=080600&itemCheckNm=080600) | `1c90480f960a4af4f75a9662f0c4de174572ac353f8eca01007c0e64d0852dfd` |
| `2026-10-05T13:11:00Z` | [C 목록](https://www.smartfarmkorea.net/datamart/fclty/list.do?menuId=M11040101) | `a2b789dd5a611c753ca27470fd0deeeef54b9884bf442de96c7889b73420931e` |

| 후보 | 공식 제품/목록 식별자와 URL | 조회 시각 UTC |
| --- | --- | --- |
| A: AI Hub 토마토 | `dataSetSn=534`, [지능형 스마트팜 통합 데이터(토마토)](https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&currMenu=11&dataSetSn=534&topMenu=) | 위 조회 구간 |
| B: EPIS 지역별 방울토마토 | `15090553`, [공공데이터포털](https://www.data.go.kr/data/15090553/fileData.do); 이 목록이 연결한 제공자 `data_id=20210928000000001574`, [농식품 공공데이터포털](https://data.mafra.go.kr/opendata/data/indexOpenDataDetail.do?data_id=20210928000000001574&service_ty=&filter_ty=F) | 메타데이터 재조회 `2026-10-05T13:01:00Z`; 권리 HTML 직접 GET `2026-10-05T13:10:01.038093Z`~`13:10:01.476512Z` |
| C: SmartFarmKorea 2024 방울토마토 | 목록 `menuId=M11040101`, 작기 식별자 `7581`, 시설 식별자 `PF_0021341_01`, 품목 `080600`; [시설원예 목록](https://www.smartfarmkorea.net/datamart/fclty/list.do?menuId=M11040101), [해당 항목](https://www.smartfarmkorea.net/structuredDataset/selectDetailView.do?menuId=M11040101&crpsnSn=7581&fcltyId=PF_0021341_01&facilityId=PF_0021341_01&fcltyYear=2024&yearCheckNm=2024&itemCode=080600&itemCheckNm=080600) | 상세 HTML HTTP 200 `2026-10-05T13:08:06.997677Z`~`13:08:07.696495Z`; 작기 표 재조회 `2026-10-05T13:09:26.266838Z`~`13:09:26.687391Z` |

## A — AI Hub 534: 온실·생육·수확 채널의 후보

공식 목록은 토마토 농가 6개의 자료, 구축년도 2021, 최초 개방 `2022-07-13`(v1.0),
원천 수정 `2023-06-30`(v1.1)을 기록한다. 수집 날짜 필드가 있으나 실제 농가별
정식~종료일·품종/대목·시간대·면적은 이 목록에서 확인하지 못했다.
[공식 534 개요/변경이력/메타데이터](https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&currMenu=11&dataSetSn=534&topMenu=).

| 체크리스트 항목 | 목록이 명시한 채널·단위 | 확보 전 남은 확인 |
| --- | --- | --- |
| 온도·CO₂·광 | 온도 °C, CO₂ ppm, 일사 W/m²; 열화상 주요 10지점 °C | 센서 위치/보정·수관 대표성·PAR µmol photons/m²/s 채널 미확인 |
| 생육 | 초장·생장길이·엽장/엽폭·줄기·화방 높이 cm, 엽수·착과/꽃 개수 | 반복 표본법·LAI·실측 잎 면적·기관 건물 미확인 |
| 수확 | 구조표는 수확 개수와 중량 kg; 다른 특성표는 생과중량 g | kg/g·개/점 필드의 대응/측정 분모 미확인; 총수확과 개별 과중 등 서로 다른 측정일 수 있음 |
| 물·에너지 | 급액/배액 센서 kg; 에너지 `KW`; 생산 품질/출하 `TEXT` | 원 단위/QC 필요; 구매 전력 kWh·연료·비용/정산은 확인되지 않음 |

위 채널·단위는 [공식 534 데이터 명세/특성표](https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&currMenu=11&dataSetSn=534&topMenu=)의 서로 다른 표를 대조한 것이다.
표기 차이를 오류로 확정하지 않고 실제 필드/측정 기준의 단위 대사를 요구한다.
일사와 열화상이라는 명칭만으로 수관 위 PAR·수관온도 입력을 확정하지 않는다.
파일 실측/QC와 작기 연결을 확인하면 국내 역사적 생육/수확 측정 검토에 도움이 될
가능성이 있다는 **프로젝트 판단**이다. 원자료가 없으므로 채널 보유율이나 정확도는 평가하지 않았다.

## B — EPIS 15090553: 역사적 지역별 방울토마토 후보

공공데이터포털은 자동수집·실측, CSV, 환경 온도/습도/일사/바람/토양정보와
화방높이·줄기직경·엽장·엽수·개화/착과군·열매수를 설명한다.
등록일 `2021-09-29`, 수정일 `2026-09-21`, 갱신은 1회성 수시로 표기하며
시간·공간 범위는 비어 있다. **2026 수정일은 실제 관측 작기나 새 원자료 판본의
증거가 아니다.** [공식 15090553 메타데이터](https://www.data.go.kr/data/15090553/fileData.do).

제공자 페이지는 SmartFarmKorea 자료임을 명시하고 지역 ZIP 4개를 나열한다.
제공자 등록/수정일은 `2021-09-28`이며 별도 버전·실제 관측 기간은 없다.
[공식 제공자 제품 20210928000000001574](https://data.mafra.go.kr/opendata/data/indexOpenDataDetail.do?data_id=20210928000000001574&service_ty=&filter_ty=F).

품종/대목·농장별 작기·면적·밀도·초기 기관/관리, 온도/CO₂의 실내·수관 위치,
PAR·측정 주기/단위·수확 생과 kg·건물/LAI·센서 불확도는 **목록만으로 미확인**이다.
환경/생육 필드 연결의 확보 후보라는 **프로젝트 판단**이며, 열매수나 착과군을
수확 중량·생산량으로 해석하지 않는다. 이 제품과 A/C가 같은 농장/작기를 포함하는지도
미확인이므로 세 제품을 독립 표본 3개로 세지 않는다.

## C — SmartFarmKorea 2024: 한 작기 식별자를 가진 방울토마토 후보

공식 목록 첫 방울토마토 항목의 공개 HTML은 `7581`/`PF_0021341_01`/`2024`/`080600`,
원 파일명 `7581_PF_0021341_01_080600.zip`을 연결한다. 표시 범위는 전라남도,
연동·소규모·비닐·전기·고설베드다. 목록은 환경 8장비/48,207건, 제어 0장비/0건,
생육 10표본/32주차, 경영 **출하량 1건**을 표시한다.
[공식 시설원예 목록](https://www.smartfarmkorea.net/datamart/fclty/list.do?menuId=M11040101).
개별 위치·농가 이름·원자료 값은 수집하거나 메모에 넣지 않았다.

공개 JavaScript는 목록 식별자를 `crpsnSn`, `fcltyId`, `fcltyYear`, `itemCode`로
상세 조회에 넘긴다. 위 ZIP 다운로드 버튼에는 이용목적 팝업이 연결되어 있다.
[공식 목록 동작 코드](https://www.smartfarmkorea.net/static/js/page/datamart/fclty/list.js).
이를 다운로드 동의/승인으로 간주하지 않았고 팝업 제출도 하지 않았다.
web 도구의 상세 GET은 실패했으나 직접 공개 HTML GET은 HTTP 200으로 복구했다.
작기 표는 작기년도 `2024`, **정식일 열에** `2024-08-29 ~ 2025-07-03`을 표시한다.
정식/종료 사건의 정확한 의미와 실제 데이터 보유 기간은 별도로 대사해야 한다.
[해당 항목의 공식 상세 페이지](https://www.smartfarmkorea.net/structuredDataset/selectDetailView.do?menuId=M11040101&crpsnSn=7581&fcltyId=PF_0021341_01&facilityId=PF_0021341_01&fcltyYear=2024&yearCheckNm=2024&itemCode=080600&itemCheckNm=080600).

상세 표 설명은 내부 CO₂ ppm, 내부온도 `도`, 일사 `W/m-2·s`, 생장/잎 cm·줄기 mm·
엽수/열매 개·개화/착과 점, 출하 kg·단가 원/kg를 명시한다. 이는 **표 구조 설명**이고
이 항목의 환경/생육 원행·실제 채널 보유를 확인한 것은 아니다. 일사의 표기/적산 의미는
미확인이며 PAR로 변환하지 않는다. [공식 상세 표 설명](https://www.smartfarmkorea.net/structuredDataset/selectDetailView.do?menuId=M11040101&crpsnSn=7581&fcltyId=PF_0021341_01&facilityId=PF_0021341_01&fcltyYear=2024&yearCheckNm=2024&itemCode=080600&itemCheckNm=080600).

품종/대목·관측 시각/시간대·`available_at`·개방/수정일·원자료 판본,
센서 위치/오차·수관 온도/PAR·LAI/기관 건물·생과 수확과 출하의 연결/QC는 미확인이다.
32주차는 완전한 전체 작기 증거가 아니며 출하 1건은 수확 실측 1건을 뜻하지 않는다.
작기/시설 ID별 누락 확인을 먼저 할 수 있다는 **프로젝트 판단**이다.
목록의 2024 표기를 미래 미사용 작기로 취급하지 않는다.

## 접근·용도별 권리 근거와 보류

AI Hub 534는 내국인 신청 및 다운로드 승인 뒤 API 사용을 안내한다.
[공식 534 접근 안내](https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&currMenu=11&dataSetSn=534&topMenu=).
현재 [AI Hub 데이터 이용정책](https://www.aihub.or.kr/intrcn/guid/usagepolicy.do?currMenu=151&topMenu=105)은
NIA 사업결과 표시, AI 학습모델의 학습 목적, 국외 이용자/국외 반출에 대한 별도 합의를
명시한다. 이 정책의 현 프로젝트·처리 환경 적용과 제품별 추가 조건을 확정하지 않았으며,
외부 CLI로 원자료를 보내지 않았다. 법적 권리 승인 판단은 이 메모의 범위 밖이다.

EPIS B는 공공데이터포털에서 무료 및 이용허락범위 제한 없음으로 표시된다.
직접 HTTP 200 조회에서도 정책 링크 `/ugs/selectPortalPolicyView.do`의 본문이
`이용허락범위 제한 없음`임을 확인했다(위 표의 `13:10:01Z` 구간).
[공식 15090553 권리 표기](https://www.data.go.kr/data/15090553/fileData.do).
반면 [제공자 제품](https://data.mafra.go.kr/opendata/data/indexOpenDataDetail.do?data_id=20210928000000001574&service_ty=&filter_ty=F)의
이용허락범위 필드는 비어 있다. 포털의 긍정적인 권리 표기는 보존하되 해당 ZIP 판본·
항목/제3자 권리에 적용되는지 아직 대사하지 않았다. C에 B의 권리 표기를 전이하지 않는다.

| 구분 | A: AI Hub 534 | B: EPIS 역사적 방울토마토 | C: SmartFarmKorea 2024 항목 |
| --- | --- | --- | --- |
| 실제 접근 | 승인 안내 확인; 신청/수신 0 | 무료·제공자 링크 확인; 신청/수신 0 | 공개 목록/상세 HTML 확인; 다운로드 조건 미확인·수신 0 |
| 내부 계산·보정/검증 | AI 학습 목적과 deterministic 작물 이용의 적용 미확인 | 무제한 목록 표기; 원 ZIP/용도 적용 대사 전 | 제품별 허락 미확인 |
| 결과/집계/도표 표시 | 원자료와 2차 결과의 허용 범위 미확인; NIA 표시 조건 확인 | 목록 근거 있음; 원 파일/표시 범위 대사 전 | 미확인 |
| 원문 공개/재배포 | 별도 허락 범위 미확인 | 목록 근거 있음; 파일별 적용 대사 전 | 미확인 |
| 외부 CLI/모델 처리 | 처리 위치·반출 해당 여부/합의 미확인 | CLI/국외 처리 특약 및 항목 범위 미확인 | 미확인 |
| 상업 서비스 | 학습 목적 조건 외 별도 허락/제품 조건 미확인 | 무제한 목록 표기의 실제 파일 적용 미확인 | 미확인 |

이 표는 위 공식 접근·정책 근거를 목적별로 나눈 **확보 전 판단**이다.
`public_listing=true`와 `received=false`를 구분하며,
`source_rights_accepted=false`, raw hash/QC/reviewer 승인·G0/G2/G3a는 계속 미수용이다.
공개된 설명/정책을 읽은 범위만 허용 사실로 기록하고 원자료 권한을 발급하지 않는다.

## 다음 확보 점검

1. B/C의 제품·작기 식별자에 대응하는 설명서/실제 파일 목록과 현재 권리를 먼저 대사한다.
   내부 계산/보정·독립 검증, 결과 표시, 원문 재배포, 외부 CLI/국외 처리, 상업 이용을
   각각 기록한다. A는 AI 학습 목적 조건이 현 deterministic 이용에 적용 가능한지 먼저 확인한다.
2. 품종/대목·작기·시설/면적·밀도·초기 LAI/기관·관리/수확 사건을 확인한다.
   다른 품종을 Axiany/Maxifort로 합치지 않는다. A/B/C의 농장/작기 중복도 대사한다.
3. 허용된 원자료 수신 뒤 센서 위치/보정/오차, PAR/CO₂/온도·생육/수확 단위,
   순간/적산·주기·UTC/현지 시각·결측/QC를 검사한다. A의 kg/g·개/점 필드/분모부터 대사한다.
4. 원 URL/제품·관측/공표/`available_at`/수집 시각·vintage/revision·원 단위/QC·
   raw SHA-256·권리/검토자를 불변 등록한다. 목록 수정일로 원자료 vintage를 채우지 않는다.
5. 역사적 자료는 사전 목적/분할·미사용/독립성 증거가 있는 범위에서만 평가 후보로 둔다.
   국내 G2 측정 후보 검토와 별도로 G3a의 새로운 미래 작기는 모델/입력 cutoff를 먼저
   고정해야 한다. 공개 역사적 목록만으로 미래 수확·자원 구매·마진/순위를 승인하지 않는다.

이번 작업에서 코드/시험/계수/프로필·authoritative 확보 상태를 바꾸지 않았다.
원자료 QC·제품별 현재 권리 승인·독립 작기 확보가 남아 있으며, 이를 코드 개발 중단의
이유로 확대하지 않는다.
