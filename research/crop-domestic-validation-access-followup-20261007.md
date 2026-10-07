# 국내 방울토마토 검증 자료 접근 후속 — 2026-10-07

상태: **새 국내 연구 온실 논문·첨부 식별자와 공개 권리 근거를 확인했다. 동기화된 농장 원자료·첨부 본문·독립 검증 자료 확보는 미확인이다.**
[기존 B 서버 응답 조사](crop-domestic-download-server-metadata-20261006.md)를 반복하지 않고,
공식 출판물 한 경로 `10.3389/fpls.2025.1730694`를 조사했다.
[접근 프로토콜](crop-independent-data-protocol.md)과 [확보 상태](crop-independent-data-status.json)는
수정하지 않았다. 이 메모는 CLI 연구자의 검토 제안이며 자료·권리·관문 승인이 아니다.

## 확인한 접근 경로

출판사 [Frontiers 공식 논문](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/full)과
[공식 JATS XML](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml)을
익명 GET으로 받았다. 제품 식별자는 DOI `10.3389/fpls.2025.1730694`, 논문 ID `1730694`다.
제목은 *Morphological analysis-based yield modeling in greenhouse grown cherry tomato
(Solanum lycopersicum) under prolonged heat stress*, 저자는 Kim S, Jeong J, Kim S,
학술지는 *Frontiers in Plant Science* 16이다.
[출판사 서지·본문](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/full).

공식 HTML에 포함된 현재 파일 메타데이터는 다음 네 파일을 식별한다.
파일명에 `Data Sheet`가 있다는 사실만으로 원측정 표라고 판단하지 않는다.
[출판사 공개 파일 메타데이터](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/full).

| 표시 파일명 | 제공자 `fileServerId` | `fileServerVersionNumber` | 이번 수신 |
| --- | --- | --- | --- |
| `Publishers-Proof.pdf` | `1730694/publishers-proof` | `1` | 미수신 |
| `EPUB.epub` | `1730694/epub` | `1` | 미수신 |
| `fpls-16-1730694.xml` | `1730694/xml` | `1` | 공식 XML HTTP 200 |
| `Data Sheet 1.docx` | `1730694/data-sheet/1` | `1` | 실제 DOCX 미수신 |

저자 출판물을 보존한 [공식 PMC 항목 `PMC12757247`](https://pmc.ncbi.nlm.nih.gov/articles/PMC12757247/)도
익명 직접 GET에서 본문을 반환했고, 공개 HTML이
[첨부 `DataSheet1.docx`](https://pmc.ncbi.nlm.nih.gov/articles/instance/12757247/bin/DataSheet1.docx)를
연결했다. 그 정확한 링크에 한 번 GET한 실제 결과는 HTTP 200이지만
`Content-Type: text/html; charset=utf-8`, 1,817 bytes였다. ZIP/DOCX 서명이 아니어서
DOCX 검사·압축 해제·내용 추출을 진행하지 않았다. 응답 본문은 보관하지 않았고
상태·형식·길이·반환 HTML 해시만 사설 receipt에 남겼다. 재시도·우회는 없었다.
출판사 XML의 첨부명 `DataSheet1.docx`와 현재 HTML 표시명 `Data Sheet 1.docx`의 대응은
문서 위치·첨부 종류 수준이며, 동일 본문 byte를 대사한 결과는 아니다.
[출판사 XML의 `SM1`](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml),
[PMC 첨부 목록](https://pmc.ncbi.nlm.nih.gov/articles/PMC12757247/).

## 국내 관측 후보로 확인한 범위와 QC 보류

논문의 방법 2.1은 국내 Wanju의 국립원예특작과학원 온실 두 동에서
2022·2023년에 HR17과 HR24를 조사했다고 기술한다. HR24의 상용 품종명은
본문 표기 `Joeungyeo’`이며 대목은 미확인이다. May 18부터 대조/고온 처리를
구분한 토경 실험이다. 온도·습도, 초장/줄기, LAI와 생체·과실 질량·과실수의
측정 방법 및 수확 사건을 설명한다. 이는 공개된 연구 실험의 설명이며 상업 농장
전체 작기의 원측정 파일이 확보되었다는 뜻은 아니다.
[방법 2.1·2.3](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/full).

| 필요한 확인 | 공개 출판물의 범위 | 원자료 확보 전 보류 |
| --- | --- | --- |
| 품종·작기 | HR17/HR24, 2022·2023, 처리 시작과 수확 상대 일자 | Axiany/Maxifort와 별도 품종; 대목·정식일·가명 개체/반복 ID 미확인 |
| 환경 | 실내 최고/최저 온도 °C·습도 %, 외기 요약 | UTC/KST·센서 교정·결측/QC·원시 주기·PAR/CO₂ 연속 측정 파일 미확인 |
| 생장·수확 | 방법의 g·cm·mm, 표의 kg/plant·m, 건과 수량 비교의 Mg/ha | 생과/건물·개체/면적 분모·관측 시점/제거 사건의 원행 연결 미확인 |
| 첨부 | `SM1`, DOCX, 파일 버전 `1`; 본문은 추가 그림/회귀표를 참조 | 첨부 실제 구성·CSV/XLSX 포함 여부·동기화 원측정 존재 미확인 |

표의 범위는 [논문 방법·표 1/3/4/6·첨부 참조](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/full)를
대조한 **출판물 설명**이다. 원행의 단위나 보유율을 승인하지 않는다.
QC상 수확 상대 일자는 방법의 `34th`와 다른 절의 `35th`를 대사해야 한다.
날짜·단위·분모를 추정해 통합하지 않았다. 논문은 이 실험을 자체 모델 보정/검증에도
사용했다고 기술하므로, 이 프로젝트의 미사용 독립 자료라는 증거는 별도로 필요하다.
[방법 2.1·2.3](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/full).
수량 값·계수·성능 수치를 프로젝트 입력이나 승인 결과로 옮기지 않았다.

추가 식별/QC 보류도 있다. 방법의 시험 재료는 HR17/HR24인데 매개변수 설명에는
`HR23`이 나타나며, 재료 공급기관 설명의 `Wonju`와 시험지 `Wanju`를 서로 바꾸어
해석하지 않았다. 관측 수량을 사용한 모델 조정·보정이 명시되어 있어 논문의 적합
오차를 이 프로젝트의 독립 정확도로 전이할 수 없다. 공개된 생과·건물 요약도 같은
수확 사건별 대응 DMC 시계열을 제공한다는 증거가 아니다.
[방법 2.1·2.3](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/full).

## 시각·판본과 사설 수집 근거

| 필드 | 관찰·미확인 범위 |
| --- | --- |
| 관측 기간 | 출판물 설명의 2022·2023년 온실 처리; 전체 정식~종료 원자료 범위 미확인 |
| 전자 공표일 | JATS `pub-date`와 HTML 모두 `2025-12-19`; 정확한 시각/시간대 미확인 |
| 논문 이력 | 접수 `2025-10-23`, 수정 접수 `2025-11-21`, 승인 `2025-11-26`; 관측자료 revision 날짜가 아님 |
| `available_at` | 논문 공표 **날짜** 근거는 `2025-12-19`; 정확한 timestamp는 미확인으로 둔다. 첨부·원측정 파일의 최초 공개/`available_at`은 미확인 |
| vintage/revision | 연구 관측 vintage 2022·2023; 현재 제공자 파일 버전 `1`. 그 파일 교체일·과거 원본 이력 미확인 |
| 권리 표시 시점 | JATS CC BY 4.0 `license_ref start_date="2025-12-19"`; 원측정 데이터 별도 계약 효력일 미확인 |
| 검토자 | 본 CLI 연구자; 최종 출처/권리/QC deterministic 검토자 미지정 |

위 공표·권리 날짜는 [실제 공식 JATS](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml)에
근거한다. 날짜만 있는 값을 임의의 UTC 자정으로 바꾸지 않았다.
다음 UTC는 이 연구의 직접 GET 완료 시각이며 제공자의 최초 공개 시각이 아니다.

| 공식 출처 / 사설 파일 | 직접 GET 완료 UTC / bytes / SHA-256 |
| --- | --- |
| [출판사 HTML](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/full) / `frontiers-1730694-public-article.html` | `2026-10-07T05:19:12.995576Z` / `829144` / `5d96756a1a8393a8b264d82ba339ab4fdcd24f3b18fe540710fb56c9ef8ba81c` |
| [출판사 XML](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml) / `frontiers-1730694-public-article.xml` | `2026-10-07T05:20:19.685503Z` / `115218` / `8ae905d37b49ee858c66b8542151a1a36faba68ef16a2eeb03088552f4aa5e2e` |
| [CC BY 4.0 요약](https://creativecommons.org/licenses/by/4.0/) / `cc-by-4-deed.html` | `2026-10-07T05:20:19.828230Z` / `31950` / `8dda1ccec4be91fc80821d4e4fd5c568072b9a3a74b2fdc07c249a27e920ef01` |
| [PMC 공개 HTML](https://pmc.ncbi.nlm.nih.gov/articles/PMC12757247/) / `pmc-12757247-public-article.html` | `2026-10-07T05:21:04.923430Z` / `216585` / `534fcca794defe991527f3107d91060bdaecf22f57a624823c3209858a6d79f1` |
| [PMC 첨부 요청](https://pmc.ncbi.nlm.nih.gov/articles/instance/12757247/bin/DataSheet1.docx) / body 미보관 | `2026-10-07T05:21:44.225237Z` / `1817` / 반환 **HTML** `f1cd53eb25e36a6df740942ae2779137243cc392755dbee244b87205cff13623` |
| [CC BY 4.0 법문](https://creativecommons.org/licenses/by/4.0/legalcode.en) / `cc-by-4-legalcode.html` | `2026-10-07T05:24:27.460278Z` / `48742` / `58230517b7895aa219ff46a6ed63e67057a1582fb9ea054b16728a8c13525650` |
| [출판사 저자 지침](https://www.frontiersin.org/guidelines/author-guidelines) / `frontiers-author-guidelines.html` | `2026-10-07T05:24:28.689663Z` / `285569` / `cd44b198e3ffdf38ec4c376dcda7314fe06dd945813f5d9e48ae3efba4057266` |

모두 HTTP 200이다. 농장 원자료 raw hash는 **없으며**, 첨부 요청의 HTML 해시는
DOCX 해시가 아니다. 사설 보관 경로는
`/home/sunghoonk/.local/state/OpenSmartFarmSim/20261007-validation-access-research/`이며
디렉터리 `0700`, 파일 `0600`이다. 허용된 공개 출판물·정책/인터페이스 메타데이터와
조회 영수증만 보관했고 농장 원행·제한 자료는 없다.

## use/display/redistribution와 CLI 범위

출판사 HTML과 실제 JATS는 논문에 CC BY 4.0을 명시한다.
[논문 권리 표시](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/full),
[JATS license](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml).
CC 법문 2·3절은 해당 라이선스가 적용된 자료의 복제·공유·변경과 모든 매체/형식을
허용하고 출처/라이선스·변경 표시 조건을 둔다. 다른 권리와 미공개 자료에까지
허락을 확대하지 않는다.
[CC BY 4.0 법문](https://creativecommons.org/licenses/by/4.0/legalcode.en).

| 대상·용도 | 확인된 근거와 경계 |
| --- | --- |
| 공개 논문의 내부 읽기·계산 참고 | CC BY 4.0의 복제·변경 허락 근거 있음. 작물 계수/정답 자료 채택과 별개 |
| 공개 논문의 표·그림·분석 표시/재배포 | 저자·Frontiers 원출판·DOI·라이선스와 변경을 표시하는 조건. 이 메모는 원 수량표·그림을 복제하지 않음 |
| 공개 서지 메타데이터 | 공식 약관 7절은 열거된 서지/권리/파일 수 메타데이터를 CC0로 설명. 모든 HTML·레이아웃·JavaScript까지 CC0라고 해석하지 않음 |
| CLI의 공개 논문·메타데이터 검토 | CC BY의 매체 제한 없는 허락과 공식 약관의 공개 자료 TDM 설명을 검토 근거로 기록. 논문 검토를 외부 모델에 미공개 농장 기록을 보낼 권한으로 확대하지 않음 |
| `Data Sheet 1.docx` 자체 | 공개 첨부 식별자와 일반 출판 조건만 확인. 본문/제3자 고지/실제 구성 미확인으로 파일별 최종 범위 보류 |
| 원측정·농장 자료의 검증/표시/재배포/외부 CLI·국외 처리 | 별도 데이터 제품·허락·실제 파일 미확인. 공개 논문의 라이선스로 미공개 기록 사용을 승인하지 않음 |

권리 표의 일반 조건은 [Frontiers 약관 7·9·14절](https://www.frontiersin.org/legal/terms-and-conditions),
[저작권 정책](https://www.frontiersin.org/legal/copyright-statement),
[저자 지침의 공개 접근·첨부 안내](https://www.frontiersin.org/guidelines/author-guidelines)에 근거한다.
약관 14절의 TDM 설명은 외부 과학문헌 컬렉션을 풍부하게 하는 정당한 목적의
공개 콘텐츠 mining을 허용하되 서비스 성능과 라이선스/개인정보 조건을 유지한다.
이는 특정 외부 CLI 서비스나 국외 처리에 대한 별도 동의 문구가 아니다.

**정책 조회의 한계:** 약관/저작권 정책 본문은 web 도구가 반환한 공식 페이지 표현에서
읽었다. 캐시 표현이 포함될 수 있고 공표·효력·개정 시각은 미확인이다.
별도 직접 GET은 두 URL 모두 같은 7,696-byte 애플리케이션 shell을 반환했으며
정책 본문을 포함하지 않았다. 그 SHA-256
`46131dbefe25e574d057f5a34ccbe573174509184a814c03f40cabccbdb7f5a1`을
현행 약관 본문의 해시로 사용하지 않는다. 직접 GET 완료는 각각
`2026-10-07T05:24:27.587431Z`, `05:24:27.599562Z`다.
따라서 논문별 실제 CC BY 표시와 일반 약관의 현재 적용판 대사를 구분한다.

## 실제 CLI 실행·검증과 다음 행동

현재 연구자의 native Codex CLI 로그
`/home/sunghoonk/.codex/sessions/2026/10/07/rollout-2026-10-07T14-17-40-01a114cb-c275-7051-9c20-624e4bad4594.jsonl`에서
자신의 `turn_context` 허용 필드만 독립 확인했다. 실제 문맥 시각은
`2026-10-07T05:17:41.598Z`, 모델은 정확히 `gpt-6.1-sol`, effort는 `xhigh`다.
원 JSONL 줄 SHA-256은 **끝 LF 포함**
`9f83457f266501377b138dcbba1f36c54d6cd1ac9ae2de35e0b26556c654db5c`,
LF 제외 `9461d85b1d4c4d85c9ba3456651038306d5ad3ce20aa360a7502294b25ec42b0`이다.
부모가 전해 준 설정만 인용한 기록이 아니다. `codex`/`codex exec` 재귀 호출은 없다.

실제 조회는 이 native 턴의 `web.run`과 `exec_command` 안에서 실행한
`python3 - <<'PY'`의 bounded `urllib.request.urlopen()` GET이다.
HTML은 5 MB 이하, 첨부 응답은 2 MB 이하, timeout은 20–30초였고
쿠키·인증·신청·목적 제출·외부 연락은 없었다. XML은 표준
`xml.etree.ElementTree`로 읽었다. 새 의존성·lock 변경은 없다.
첨부 구조 추출은 DOCX 형식 불일치로 수행하지 않았다. 공개 HTML의 파일 메타데이터
추출 첫 일반 재귀 decoder는 실패했고, 알려진 두 필드 수준만 읽는 후속 추출로
위 네 파일/버전/ID를 확인했다. 이 실패를 첨부 검증 성공으로 보고하지 않는다.

사설 receipt `native-context-verification.json` SHA-256은
`8b298daa646fb3d4906eee9a48e5e6ed5c931057a24b14097be6927ba89a60fb`,
`provider-file-descriptors.json`은
`7459c478ed19401a10e6fded24f83ecbfc6092731bbf66bc2725226a70e9642c`,
실패한 첨부 요청 receipt `published-supplement-inventory.json`은
`36c8abb8a436fc24a809a8b3d7a421d30ff63052e951300eda4ce72318630426`이다.
공개 인터페이스 추적용 JavaScript 두 개와 각 GET receipt를 포함한
19개 사설 파일의 이름/길이/권한/해시는 `retrieval-collection-manifest.json`에 기록했다.
그 manifest SHA-256은
`4db078f4b0882956cf3b92b96c75ca5158165d2402df525bfe0883de17a951be`다.
원 CLI 로그 본문·인증 정보·개인 농장 기록은 문서/receipt에 복제하지 않았다.

**구체적 다음 행동:** 새 자료 접근 검토는 위 공식 출판사 항목의
`1730694/data-sheet/1`, version `1`인 첨부 하나부터 시작한다.
정상 공개 다운로드에서 실제 DOCX와 별도 권리 고지를 확인할 수 있을 때에만
그림/회귀표·원측정 표를 구분하고, 품종·연도·처리/반복 ID·관측 시각·생과/건물
단위의 동기화 원행 존재를 목록으로 확인한다. 현재 요청의 HTML을 DOCX로 저장하거나
추정 URL/인증 우회로 진행하지 않는다. 첨부에 원측정이 없으면 동기화된
기후/개체·수확 기록과 그 이용/처리 허락을 가진 별도 제공자 공개 제품 또는
후속 명시적 자료 제공이 **외부 의존성**이다. 이번 작업에서 연락하지 않았다.

남은 hold는 실제 첨부/원측정 수신, 파일별 권리·CLI 처리 범위, 품종/대목·시간대·
단위/분모·센서 QC, 사전 미사용/독립성 증거다. 공개된 과거 연구 요약은 미래 독립 작기
확보가 아니다. 이 메모 하나만 저장소에 새로 작성했고 기존 수신 수치·G0~G4·계수·
프로필·시험·task 및 실행 중인 전체166일 실험 파일/프로세스를 변경하지 않았다.
링크·내용/해시의 집중 대사를 수행했으며 PG·브라우저·빌드·시험은 실행하지 않았다.
