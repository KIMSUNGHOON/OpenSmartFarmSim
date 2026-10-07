# 공개 부록 판본1의 파일 내부 credit·권리 고지 검사 — 2026-10-07

대상: DOI `10.3389/fpls.2025.1730694`, article `1730694`, `fileServerId=1730694/data-sheet/1`, 판본1.
원 DOCX:863,123B, SHA256 `53d65c2d06d46a569e068f6290dc5ff5f6c2c3ac07c9fad573aca4eabad80df2`.
검토자: 실제 native Codex CLI `gpt-6.1-sol` / `xhigh` 배경 조사 에이전트와 부모 CLI.
부모가 같은 파서의 별도 재계산·구조화 권리 필드·원본 보존을 대사했다. 제한된 검사 범위의 검토 완료이며 권리/G0·자료 채택 승인은 아니다.

## 확인한 사실과 판단 경계

기존 사설 원본을 읽기 전용으로 검사했다. **검사한 XML 텍스트·속성·관계·문서 속성과 제한된 이미지 메타데이터에서 명시적 copyright/license/credit/복제 제한 고지 후보를 찾지 못했다.** 아래 파서·표현 목록에 한정한 관측이며 파일 전체에 고지가 없다는 확정은 아니다. 수신 경로와 이 파일 hash의 결속은 [선행 접근 보고서](crop-domestic-supplement-access-20261007.md), [정상 출판사 부록 API](https://www.frontiersin.org/api/v4/articles/1730694/supplemental-data), [실제 최종 파일 URL](https://public-pages-files-2025.frontiersin.org/articles/1730694/file/data_sheet_1.docx/1730694_data-sheet_1/1)에 근거한다. 이번에는 네트워크 요청을 하지 않았다.

**인용한 파일 내부 notice 구절은0개다.** 후보를 발견하지 못했으므로 일반 본문·표 행을 대신 복사하지 않았다. 이미지 픽셀 안의 고지, 비표준 표현과 외부 template 내용은 미검토다.

저자 권리 출판 내용의 CC BY 기본 조건을 배제할 새 텍스트 근거는 이 검사에서 발견되지 않았다. 이는 [앞선 권리 검토](crop-domestic-supplement-rights-20261007.md)의 조건부 해석을 유지한다는 CLI 판단이다. 파일 안의 별도 label 부재만으로 일반 CC BY를 취소하거나 파일 전체의 무조건 허가를 확정하지 않는다. 실제 논문은 CC BY4.0을 명시한다. [논문 JATS license](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml)

## 실제 파서와 처리 범위

| 범위 | 수행한 검사·결과 |
|---|---|
| ZIP 원본 | 표준 `zipfile`, 중앙 디렉터리38항목. XML/rels36개를 읽고 `ElementTree`로 파싱했다. 파일시스템에 패키지를 풀지 않았다. 항목수<200·비압축 합계<16MiB·개별 XML≤2MiB를 제한하고 DTD/entity 선언은 거부했다. |
| 본문·표 | `word/document.xml` paragraph358개: 표 안336개, 표 밖22개. `w:t`·`instrText`·`delText`를 paragraph 단위로 연결해 로컬 메모리에서 notice 표현만 검사했다. 모든 XML의 개별 text/attribute도 검사했다. 표6개의 행·수치·계수는 해석하거나 prompt/log/repo로 출력·보관하지 않았다. |
| header/footer·각주 | `header1/2` 각 paragraph1개, `footer1/2` 각3개, `footnotes/endnotes` 각2개를 포함했다. 동일 notice 검사에서 후보0개. paragraph 수를 실측 표본수로 쓰지 않는다. |
| 기타 XML | styles·settings·theme·numbering·fontTable·webSettings·customXml·문서 속성을 포함한 전체 XML/rels의 text/attribute를 검사했다. raw XML·본문 문장·표 셀 값은 receipt에 복사하지 않았다. |
| 관계 |29개 관계 중 external1개: `word/_rels/settings.xml.rels`의 `attachedTemplate`, scheme `file`. 대상은 따라가지 않았고 개인 로컬 경로 대신 target SHA만 보존했다. 관계 URL의 권리 표현 후보0개. |
| 문서 속성·소유 | `docProps/core/app/custom.xml`의 필드 존재·권리 표현만 검사했다. creator/lastModifiedBy가 있지만 값을 내보내거나 저작권 소유자라고 해석하지 않았다. `DocSecurity=0`, Word `documentProtection/writeProtection/readOnlyRecommended` 노드0개이며 기술 플래그는 저작권 허락이 아니다. |
| PNG 메타데이터 | `image1.png`의 `tEXt/zTXt/iTXt` chunk만 제한 검사: 텍스트 필드0개. 픽셀을 디코딩/표시하지 않았다. |
| JPEG 메타데이터 | `image2.jpeg`의 scan 이전 COM/XMP·첫 EXIF IFD의 Copyright tag를 검사했다. XMP packet1개, 명시적 rights namespace/`rights/license/copyright/UsageTerms/WebStatement/Marked` 필드0개. 창작 도구/사용자/GUID 값은 내보내지 않았다. 픽셀/OCR 미수행. |

첫 pass는 copyright/©·Creative Commons/CC BY·license/licence·permission/복제/재사용 제한·credit/courtesy·adapted/reprinted/reproduced from·Source:·한국어 권리 표현을 검사했다. 두 번째 pass는 provided/supplied/created/designed/drawn/photographed by/with, image/photo/figure/table/data credit/from/by, acknowledgement/attribution/rights holder 표현을 추가했다. **두 pass 모두 후보0개**였다. 정확한 정규식·코드와 각 pass의 별도 receipt를 보존했으며 첫 receipt를 덮어쓰지 않았다.

paragraph 연결 검사와 node/attribute 검사는 중복 후보가 생길 수 있는 설계다. 여기서는 둘 다0개다. 정규식0건은 포괄적인 법률검토·시각검토 결과가 아니다. 표 텍스트는 notice 필터를 통과시킨 로컬 처리 범위이며 수치행의 외부 CLI 입력·재배포나 데이터 내용 검토를 수행한 결과가 아니다.

## 불변 입력·소유와 시각

| 항목 | 확인/미확인 |
|---|---|
| 기존 원본 경로 | `/home/sunghoonk/.local/state/OpenSmartFarmSim/20261007-supplement-access-research/Data_Sheet_1.docx` |
| 파일시스템 소유·권한 | owner/group `sunghoonk`, UID/GID1000, `0600`. 이것은 저장 파일의 OS 소유이며 저작권 소유 선언이 아니다. |
| 검사 전후 보존 | SHA256·크기·mode·UID/GID·owner/group·inode·mtime/ctime nanoseconds 모두 동일. 원본 write/chmod/chown은 없었다. 읽기에 따른 atime은 불변 대사 필드로 삼지 않았다. |
| 원 회수완료 UTC | `2026-10-07T06:37:04.464547Z`; 기존 수신 receipt를 재사용했고 재다운로드하지 않았다. |
| 이번 notice 검사 UTC | 첫 XML pass `07:21:08.842585Z`, 확대 pass `07:22:06.488998Z`, 구조화 권리 필드 검사 `07:23:10.558710Z`, 원본 최종 대사 `07:24:59.737150Z` — 모두2026-10-07 |
| 공표·`available_at`·revision | 첨부 최초 공표/`available_at` unknown. provider 현재 판본1 이외 교체 이력 unknown. 원 회수시각·파일 편집/수정 메타데이터를 최초 공개시각으로 바꾸지 않았다. |
| 관측·단위/QC | 농장 관측시각·농업량 단위·수량/QC는 이번 검사 대상이 아니다. 파서의 파일/paragraph 수는 문서 구조 메타데이터다. |

## 사설 증거와 실제 native 문맥

새 사설 경로: `/home/sunghoonk/.local/state/OpenSmartFarmSim/20261007-supplement-credits-research/` (`0700`, 모든 파일 `0600`). 원 DOCX·표 행·그림 데이터의 새 사본은 만들지 않았다.

CC BY baseline에 참조한 기존 JATS 원천은 `/home/sunghoonk/.local/state/OpenSmartFarmSim/20261007-validation-access-research/frontiers-1730694-public-article.xml`, SHA256 `8ae905d37b49ee858c66b8542151a1a36faba68ef16a2eeb03088552f4aa5e2e`다. 선행 권리 검토의 `/home/sunghoonk/.local/state/OpenSmartFarmSim/20261007-supplement-rights-research/read-only-source-reuse-receipt.json` SHA256 `62cecac259f090bf5da671f34fe6abbb0becc14000e9ae9c00157186e924e34d`가 그 경로/hash를 결속한다. 이번 notice 파서의36개 XML 범위는 DOCX 패키지이며 JATS 본문은 포함하지 않는다.

- `manifest.json`: 자신을 제외한14개 파일 결속, SHA256 `2d2c5c5c088c48b87996688dbe3ac2121c40fb199e2c12715abf56aa114e1873`.
- 보존된 파서 `notice_scan.py` SHA256 `bfb807457011ac1bb6596d174a9d57ff38f6f63995ede4fecf145b8abea5e312`; 확대 파서 `notice_scan_v2.py` `eb918bbf0f5004a5350a0f5dc9c0b91a563cc9cd47bde3cab8d3271dbf3741c8`.
- `notice-candidate-index-v2.json` `fcb0a6af203a14fb0b6c1082b26880050804d05c788da44e437a13fbb83d8412`; `xml-structure-and-relationships-v2.json` `a9d39601222cc3e53e72cee1529389ab392728fa541f5b1488cccd59460d5d06`.
- `image-metadata-notice-review-v2.json` `b9a9fddb6556eb2d5d27ff12e42143d26de280882e92259f144cd86ae81f0fbb`; `structured-rights-fields-review.json` `1f0199d900cb9591f910467921a526336813f00229f6b73308d01d463725c604`.
- `input-preservation-and-source-binding.json` `ba9707702a79149c270cbf21af93a3483ada3294a108ce79fcc9b0269c906a97`; `notice-review-conclusion.json` `58169adab610278d038adc246872487a59fad41a85a621ec0ae4a6c34a4bc26a`.
- 실제 native 원행: `/home/sunghoonk/.codex/sessions/2026/10/07/rollout-2026-10-07T14-17-40-01a114cb-c275-7051-9c20-624e4bad4594.jsonl:961`, `2026-10-07T07:17:28.051Z`, 정확히 `model=gpt-6.1-sol`, `effort=xhigh`.
- 원 문맥 한 줄 SHA256 **끝 LF 포함** `99db8fad4bda947b9efb312daca3aa927c688bdc147d9768098341b57ad33ed0`; **LF 제외** `b688bff32908eb19d169c8375902d2d8b5b63986572483914e0283fec04c8d28`. whitelist만 기록하고 원 바이트와 재대사했다. `native-context-recheck.json` SHA256 `2219af1ce571e4d9bf7ce12a87420945d651c2af6f1e125492e08570fa002edd`.

실제 실행은 기존 native 턴의 `exec_command` → `python3` 표준 ZIP/XML/hash·컨테이너 메타데이터 검사다. 새 다운로드/PMC 요청/외부 연락·외부 관계 추적·이미지 표시/OCR·재귀 CLI는0회였다.

파서는 출력 `ROOT` 경로를 고정한다. 부모의 독립 재계산은 코드 사본의 출력 `ROOT`만 새 사설0700 경로로 지정해 수행해야 기존 receipt를 덮어쓰지 않는다. 원 파서/receipt는 위 해시에 묶인 채 보존한다.

## 검토되지 않은 부분과 다음 허용 가능한 범위

이미지 픽셀 속 notice는 **미확인**이다. JPEG EXIF 검사도 첫 IFD와 명시한 metadata 범위이며 모든 가능한 바이너리 고지를 보장하지 않는다. 외부 template 내용, 비표준·미인식 문구, 시각적으로 조합된 credit도 이번 결과로 배제하지 않는다.

다음은 필요하면 그림 데이터가 외부 prompt/log에 노출되지 않는 내부 notice-only 절차로 이미지의 credit/제한 표시를 확인하는 단계다. 확인한 권리 범위 안에서 표 제목/열 이름 같은 schema 검토로 이어갈 수 있다. 원행·수치·그림의 외부 전송/표시/재배포는 이 문서로 승인하지 않는다.

독립 raw time-series의 존재·단위/수량·독립성, G0 승인·자료/품종/계수 채택을 주장하지 않는다. 기존 보고서·receipt·제품/계획/CI 파일·고정55개 소스·실행 중166일 실험/프로세스는 수정하지 않았다. 새 보고서1개만 작성했고 해시/권한·링크를 대조했다. 시험·서버·계산·commit/push는 실행하지 않았다.

## 부모 CLI의 제한적 수용

위 실행 내역은 배경 에이전트의 기록이다. 부모는14개 manifest 항목의 hash/권한/UID와 실제 native 문맥을 확인했고,
출력 `ROOT`만 바꾼 동일 파서를 별도 사설 경로에서 재계산했다. 시각만 제외한 결과가 같다.
별도 구조화 XML/XMP 대사와 원 DOCX의10개 보존 필드도 일치했다. 서로 다른 알고리즘의 독립 정확도 검증이라고 부르지 않는다.
[부모 receipt](artifacts/crop-domestic-supplement-credits-parent-20261007.json)에 원 agent 보고서 SHA와 재검토 판본을 구분한다.
이 결과를 연구 baseline/계획에 반영했으며 이미지 픽셀·원측정/독립성·품종 식별·외부 서비스 범위와 자료0건/관문 보류는 유지한다.
