# 국내 공개 부록의 표 스키마 확인 — 2026-10-08 KST

상태: **검사한 여섯 표의 스키마 검토 완료, 동기화 독립 원측정 확보는 보류**.
대상은 Kim, Jeong, Kim의 DOI `10.3389/fpls.2025.1730694`에 연결된
`1730694/data-sheet/1`, 제공자 판본1의 기존 DOCX다.
이번에는 [권리 검토](crop-domestic-supplement-rights-20261007.md)와
[파일 내부 credit 검토](crop-domestic-supplement-credits-20261007.md)가 허용한 좁은
제목·열 의미·단위/시간키·구조 확인만 수행했다. 파일 전체 표시·재배포나 수치행의
외부 CLI 전송 허가를 새로 판단하지 않았다.

## 실제 확인한 스키마

원 문서를 로컬 메모리에서 파싱하고, 제목과 각 표 첫 행의 문자에 **고정 의미 분류표**를
적용했다. 임의 원문 문자열을 출력하지 않았다. 첫 행이라는 이유만으로 헤더로 간주하지
않았으며, 여섯 통계 항목의 조합과 제목을 근거로 통계형 헤더 후보를 식별했다.
[실제 공개 부록](https://public-pages-files-2025.frontiersin.org/articles/1730694/file/Data_Sheet_1.docx/1730694_data-sheet_1/1),
[정상 수신과 원 hash 결속](crop-domestic-supplement-access-20261007.md).

| 범위 | 확인한 구조·의미 | 해석의 한계 |
| --- | --- | --- |
| 부록 표1–6 | 각각8행·행당7셀·grid7열. 첫 행의 셀 병합 span은 모두1. 여섯 표의 분류된 첫 행 구조가 같다 | 문서 행/셀 수이며 관측 시점·개체·반복 표본 수가 아니다 |
| 여섯 caption | 선형 회귀·계수와 온도·상대습도·광, 최소/최대 관련 의미가 모두 인식됐다 | 제목 전문·숫자·연도·원 수치행은 출력하지 않았다. 표별 정확한 종속변수·표본/처리군 대응은 이번 분류로 확정하지 않았다 |
| 첫 열 | 비어 있지 않지만 고정 분류표에서 의미 미인식 | 열 이름이나 개체/시간 ID라고 추정하지 않았다 |
| 둘째–다섯째 열 | 계수, 표준오차, t 통계, p값의 의미를 순서대로 인식 | 계수·오차·유의성 값은 읽어 해석하거나 채택하지 않았다 |
| 여섯째–일곱째 열 | 하한·상한과 % 표기 | 통계 신뢰구간 표기의 일부로 해석했다. RH 또는 DMC 측정의 물리 단위%로 전이하지 않았다 |
| 시간·물리 단위 | 인식한 통계 열들에 날짜/시간키와 작물 질량·면적의 물리 단위는 확인되지 않았다 | 미인식 첫 열·전체 문서의 시간/단위 부재를 입증하지 않는다. 통계표의 % 기호만으로 환경/생과 측정이 확보되지 않는다 |

Word의 반복 헤더 플래그는 여섯 표의 모든 행에서 없었다. **회귀 요약 스키마라는 분류는
caption과 계수/표준오차/t/p/신뢰구간 열의 조합에 근거한 판단**이다. 데이터 행의 숫자를
읽어 회귀식·성능·개별 측정을 검증한 결과가 아니다. 표1–6의 제목/첫 행 밖 텍스트,
이미지 픽셀과 다른 파일은 내용 조사 범위에 포함하지 않았다.
[검사 대상 판본1](https://public-pages-files-2025.frontiersin.org/articles/1730694/file/Data_Sheet_1.docx/1730694_data-sheet_1/1).

## 독립 검증에 필요한 채널과의 대조

| 필요한 자료 | 검사한 표 스키마에서 확인한 것 | 아직 필요한 근거 |
| --- | --- | --- |
| 같은 시각의 환경 | 환경 변수에 관한 회귀 요약의 의미 | 시각/시간대·센서/위치·단위·원 주기·QC를 가진 실제 온도/RH/PAR/CO₂ 시계열 |
| 작물 생장 | 여섯 표에서 작물 상태의 동기화 원행을 확보하지 못함 | 같은 품종/대목·개체/반복·시각의 LAI·기관/과실 상태·질량과 측정 불확실성 |
| 수확·DM/FW | 통계형 열 구조이며 수확 배치·대응 DM/FW를 확인하지 못함 | 수확 사건/배치·원 FW/DM 쌍·건조 방법·등급/폐기·면적/밀도 분모 |
| 관리 사건 | 명시 관리 원장 스키마는 이번 확인에서 확보되지 않음 | 정식·줄기 변경·적엽/적과·적심·수확 시각과 제거 모집단/양 |
| 독립성 | 제목/열 구조만으로 판정할 수 없음 | 개발·선정·보정에 미사용한 자료/작기의 사전 분리, 이용 권한과 검증 계획 |

이는 **검사한 텍스트 표의 제한적 적합성 대조**다. DOCX 전체·이미지·다른 제공 파일에
원측정이 없다는 주장이 아니다. 기존 [논문 접근 조사](crop-domestic-validation-access-followup-20261007.md)의
자체 모델 보정/검증·품종/수확일/QC 보류도 그대로 유지한다. 이번 회귀표를 프로젝트의
독립 관측이나 작물 계수로 전이하지 않았다.

다음 필요한 외부 산출물은 시각·개체/배치·환경·생장·수확·관리의 대응과 권리/QC·미사용
독립성을 확인할 원측정 제품이다. 같은 부록의 권리/카탈로그 조회를 반복하는 것으로
그 자료를 확보했다고 처리하지 않는다. 그림의 추가 내용 검토도 별도 범위이며 이번에는
렌더/OCR하지 않았다. [독립 자료 현황](crop-independent-data-status.json)의 국내 동의 농장·
수신/예약 작기0건과 G2/G3 보류를 변경하지 않았다.

## 원천·시각·권리와 불변 보존

| 항목 | 실제 확인/미확인 |
| --- | --- |
| source URL/product | [공식 부록 API](https://www.frontiersin.org/api/v4/articles/1730694/supplemental-data)의 기존157B 응답이 표시명과 정확한 다운로드 URL을 결속한다. `fileServerId=1730694/data-sheet/1`, version1. 수신 receipt의 최종 URL은 파일명이 소문자로 정규화된 경로다 |
| 원 retrieval | `2026-10-07T06:37:04.464547Z`. 기존 receipt/hash를 대사했으며 이번 네트워크 요청은0회다 |
| 이번 local inspection | 최종 v2 `2026-10-08T03:06:04.702308Z`. 로컬 재검토를 새 다운로드로 기록하지 않았다 |
| publication/observation | 기존 JATS의 논문 날짜2025-12-19. 부록 최초 공개·개별 원측정 관측시각은 unknown. 논문의2022/2023 실험 설명을 모든 첨부 행의 시각으로 부여하지 않았다 |
| `available_at`/revision | unknown/null. 제공자 현재 판본1 외 교체 이력 미확인. HTTP/문서 편집시각은 최초 이용 가능 시각으로 쓰지 않았다 |
| use | 기존 저자 권리 출판 내용의 CC BY4.0 조건부 해석과 파일 notice 검토 안에서 로컬 스키마 연구만 수행 |
| display/redistribution | 자체 분류·구조 수와 출처 링크만 공개. 원문 caption/header의 직접 인용0개. DOCX·수치행·그림을 저장소/외부 CLI에 전송·표시·재배포하지 않았다 |
| 남은 권리 범위 | 이미지 픽셀/비표준 credit·외부 template·제3자/개인정보·전체 파일/외부 서비스 조건은 기존 hold를 유지 |
| reviewer | 아래 native 자식 CLI와 부모의 같은 알고리즘 재대사. deterministic 최종 출처/권리/QC 승인자는 미지정이며 gate 승인과 별개 |

권리·시각의 근거는 [선행 수신](crop-domestic-supplement-access-20261007.md),
[권리 해석](crop-domestic-supplement-rights-20261007.md),
[내부 notice 범위](crop-domestic-supplement-credits-20261007.md),
[논문 JATS](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml)다.

원 DOCX는863,123B, SHA-256
`53d65c2d06d46a569e068f6290dc5ff5f6c2c3ac07c9fad573aca4eabad80df2`다.
검사 전후 hash와9개 파일 identity 필드(device/inode/size/mode/UID/GID/mtime/ctime/nlink)가
같다. 원 mode0600을 변경하지 않았고 새 원문 사본을 만들지 않았다.

## 파서·재대사와 실제 native CLI

새 사설 증거 디렉터리는
`/home/sunghoonk/.local/state/OpenSmartFarmSim/20261008-supplement-schema-research/`(0700)다.
helper/receipt는400·새 파일로 보존했다. 첫 v1의 부분 분류는 그대로 남기고,
숫자로 시작하는 셀의 보류와 통계형 헤더 조합을 명시한 v2를 최종 조사에 사용했다.

표준 `zipfile`/`ElementTree`만 사용했다. ZIP38항목·비압축 합계1,255,640B에 대해
항목≤200/합계≤16MiB/본문XML≤2MiB를 제한하고 중복 항목·DTD/entity를 거부했다.
본문 XML 전체를 로컬 메모리에 파싱했지만 행2–8의 셀 텍스트를 의미 추출 대상으로
순회하지 않았다. 해당 행은 구조만 셌다. 이미지·외부 관계·문서 개인 속성을 읽거나
전달하지 않았다. 파서의 출력은 고정된 의미 code, count/boolean, 출처 hash/파일 identity뿐이다.

| 증거 | SHA-256 |
| --- | --- |
| `schema_inventory_v2.py` | `48b44fb4218080388662e59550300965dedc38c46f553fb1a3237692d7a06d1c` |
| `schema-inventory-v2.json` | `caf4cbff40c8f29f32df0d1f7cec1acf55685b5d88b858c9ebb5ead0d5f2442c` |
| `source-binding.json` | `61d7c11db71d12dc1a7c178fd605ed88faa63301d3de13d8da1f23246e27d151` |
| `native-context.json` | `db8f99023b27e9faae8d2fd40179ced7845b8578d68e40f62a0e8f298b5e24ff` |
| 부모 `root-schema-inventory-v2.json` | `d50f77a5fbac90b058959a95e3a125eae08cb8548ab026b4ff222aa4d1f22840` |
| 부모 `root-schema-recheck.json` | `efa9d88afd8541a04bef325acd551cf318a86e66a18e332d3704c990806dfd39` |

부모는 v1과v2 변경·출력 허용 목록을 검토한 뒤 같은 v2를 `nice -n 19 python3`로
새 출력에 실행했다(종료0). `inspected_at`만 제외한 전체 결과가 같고 원본 identity도 보존됐다.
같은 알고리즘의 재대사이며 독립 농업 정확도 검증으로 부르지 않는다.

현재 작성자는 부모 native CLI의 `engineering-suite:research` 배경 조사 위임을 받은
`/root/harvest_reference303_dmc_followup_20261008`다. 자신의 JSONL에서 다음을 직접 확인했다.

| 항목 | 관측 |
| --- | --- |
| own session/CLI | `01a1196b-313b-7cd3-a5a1-0cb668c72f92` / `0.161.0` |
| own 최신 turn_context | `2026-10-08T03:02:43.592Z`, 정확히 `model=gpt-6.1-sol`, `effort=xhigh` |
| 해당 원 행 SHA-256(LF 포함) | `d148f13e709aa9534d03db4f20c1f1a87f9680cd6507807065d41556d8e4f2c5` |

상속된 부모 문맥을 자신의 현재 호출로 기록하지 않았다. 재귀 CLI·추가 에이전트·네트워크·
설치/다운로드·시험/PG/브라우저/작물 계산·CI/push는0회다. 새 저장소 파일은 이 Markdown뿐이고
생성 전 없음·현재398개 고정 소스에 미포함을 확인했다. 새 자료/계수/품종 채택·독립 작기·
작물 Run은0건이며 G0–G4는 `not_assessed`를 유지한다.
