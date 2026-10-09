# Reference303 DMC·면적·정정 판본 후속 확인 — 2026-10-08 KST

상태: **범위를 한정한 원천 재확인 완료, 실제 환산 근거 보류**.
[기존 환산 조사](crop-harvest-conversion-baseline-20261006.md)의 차원식이나 계수를 다시 선정하지 않았다.
현재 공식 판본 목록과 작은 원문은 확보했지만 Reference303의 헤더 정정,
과실 건조·표본 방법, 생산량 면적 분모를 해결할 제공자 근거는 확보하지 못했다.
새 채택 자료·계수·작물 Run은 각각 0건이고 G0–G4는 `not_assessed`다.

## 확인한 범위와 결론

| 질문 | 이번에 직접 확인한 근거 | 판단과 보류 |
| --- | --- | --- |
| 공식 정정 판본이 있는가? | [Figshare 판본 API](https://api.figshare.com/v2/articles/12764777/versions)는 1·2만 반환한다. [현재 metadata](https://api.figshare.com/v2/articles/12764777)는 v2/file24757220이며 기존 등록부와 원 bytes hash가 같다 | 조회한 공식 기록에서 새 정정 판본은 찾지 못했다. 모든 위치에 정정이 없다고 단정하지 않는다 |
| 7개 헤더/8개 값의 대응을 승인할 수 있는가? | [v1 ReadMe](https://ndownloader.figshare.com/files/24363344) p14는 Weight(g)와 DMC_fruit(%)를 별도 항목으로 설명한다 | 의미상 분리 후보를 지지한다. v2 CSV의 실제 정정 지시·정정 파일은 아니다. 기존 [8열 후보](crop-forcing-register.json)는 계속 미채택 |
| DMC의 건조·표본 방법을 확인했는가? | 같은 v1 ReadMe p14는 격주·%·WUR Smaaklab을 기재한다. Hemming 등 [원 저자 논문 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7698269/fullTextXML) §2.4는 품질 분석을 설명하지만 DMC 건조 절차를 주지 않는다 | 확인한 문서에서 온도·시간·건조 종점, DMC용 표본 수/숙도, 동일 표본 FW/DM 쌍·저울 QC를 찾지 못했다. 다른 실험실의 일반 방법으로 채우지 않는다 |
| 62.5/76.8/96m² 중 어떤 분모인가? | v1 ReadMe p1/9는 5개 팀 구역의 전체96m²·growing/production62.5m²를 설명한다. 위 원 논문 Figure1은 전체96m²·crop-growing76.8m²다 | Reference303의 수확 모집단·분모를 연결하는 도면/원 합계가 없다. 기존 [면적 hold](crop-forcing-audit.md#면적관리생과-환산경제)를 유지한다 |

**v1 문서와 v2 데이터는 구분한다.** v1 metadata에는 별도 ReadMe file24363344가 있고,
v2에는 archive file24757220만 있다. 이번 v1 PDF hash는 기존 v2 ReadMe의 등록 hash와
다르다. 두 문서를 동일 판본으로 간주하거나 v1 정의를 v2에 자동 적용하지 않았다.
[공식 v1 metadata](https://api.figshare.com/v2/articles/12764777/versions/1),
[공식 v2 metadata](https://api.figshare.com/v2/articles/12764777/versions/2),
[기존 v2 원천 감사](crop-forcing-audit.md).

기존 임시 원본 경로는 현재 없었다. 7z 도구도 사용 가능한 경로에서 찾지 못했고,
도구 설치·다운로드 없이 이번 archive 재다운로드·추출을 생략했다. 따라서 이번에는
v2 CSV의 행·교차 팀 헤더·archive 내부 공지를 새로 검사하지 않았다. 기존
header7/data8·DMC 후보6유한/2결측은 **선행 감사의 관측**이다.
[기존 forcing 등록부](crop-forcing-register.json).

논문 §4.1의 평균 DMC9.0%는 합친 자료의 설명이며 해당 원자료를 제시하지 않는다.
이를 Reference303의 일별 또는 전작기 계수로 채택하지 않았다. 논문 XML 본문의
`drying`, `oven`, `constant weight`, `freeze` 검색 결과는 각각 0개였고 §2.4와 §4.1을
직접 읽었다. 이 검색만으로 실험실 SOP가 존재하지 않는다고 주장하지 않는다.
[Hemming, de Zwart, Elings, Petropoulou, Righini, Sensors 20(22),6430,2020](https://doi.org/10.3390/s20226430).

## 다음 구현에 미치는 영향

원 C/N 제거 원장의 소프트웨어 개발은 실제 DMC 선정 없이 진행할 수 있다.
기존 검증 결과의 terminal 차이와 명시 과실 제거를 대사하는 첫 단계는
[현재 계약](../contracts/crop-harvest-v1.md#첫-구현-한-단계의-수용-기준)의 범위다.
진행 중인 전체 작기 실행의 고정 소스는 이번 조사에서 변경하지 않았다.

실제 생과 환산과 생산량 게시를 위해서는 다음 제공자 근거가 여전히 필요하다.

1. **CSV 정정:** 대상 DOI/판본/파일·원 hash, 올바른 delimiter/열 순서와 단위,
   수정 사유·제공자 확인·새 판본. 문서에서 유추한 열 재배열은 후보로 남긴다.
2. **DMC 표본:** Reference303의 날짜·sample/batch ID, 과실/화방·숙도·줄기/꽃받침 포함 범위,
   같은 표본 FW/DM, 건조 온도·시간·종점/반복·저울 QC와 측정 불확실성.
3. **면적·밀도:** Reference303의 구획/재배/수확 집계 면적 도면, 각 분모의 정의와 적용 기간,
   면적당 생산량과 원 수확 합계의 대사, stem/plant 밀도의 같은 모집단 대응.
4. **시간·독립성:** 실제 접근 가능 시각 `available_at`, 의사결정 시각·계수 판본,
   개발/보정에 쓰지 않은 독립 작기의 환산·수확 대조.

이 목록은 이미 식별한 hold를 해결할 다음 확인 대상으로 좁힌 것이다. 이번에 제공자에게
연락하지 않았고 0.06·9%·Brix 대체, 면적 자동 환산, 실제 수확/판매 배정도 채택하지 않았다.
[기존 보류 근거](crop-harvest-conversion-baseline-20261006.md#확보하지-못한-근거),
[환산 계약](../contracts/crop-harvest-v1.md).

## 원천 판본·시각·권리

아래 `retrieval`은 UTC 요청 시작 기록이다. 관측 기간은 선행 원천 등록부의
2019-12-16~2020-05-29 실험 범위를 유지하며 개별 DMC 표본의 UTC 시각을 새로 승인하지 않았다.
모든 의사결정용 `available_at`은 unknown/null이다. 공개일을 농장의 당시 이용 가능 시각으로
소급하지 않았다. [선행 등록부](crop-tomato-source-register-20261004.json).

| 원천·제품·판본 | publication / retrieval / units·QC | use / display / redistribution |
| --- | --- | --- |
| Figshare article12764777 versions/current | 목록은 v1·v2; v2게시2020-09-23T10:41:39Z. 보존 조회02:53:50.319047/02:53:51.465634Z. API200·65,536B 상한·첫 조회와 hash 일치. 수치 입력 아님 | metadata의 CC0 선언/판본 연구용. 자체 요약·링크만 공개. API 원문 재배포·제품 표시 미채택. [공식 API](https://api.figshare.com/v2/articles/12764777) |
| ReadMe file24363344, dataset v1 | v1게시2020-08-20T11:13:00Z; retrieval02:52:35.279038Z. g·%·m²·격주. PDF17p·기탁 MD5 일치·페이지/content stream 상한·p1/9/14 직접 확인 | v1 metadata CC0 선언을 기록. 연구 열람·자체 요약·출처 링크. 파일별 이미지 공지/제품 적용 미수용·PDF 재배포0. [공식 v1](https://api.figshare.com/v2/articles/12764777/versions/1) |
| Hemming 등 원 논문, DOI10.3390/s20226430, EuropePMC XML | XML epub2020-11-11; retrieval02:52:54.071716Z. ≤1MiB XML·§2.4/4.1·Figure1 직접 확인. %,g,m² 설명 자료 | XML의 저자©2020/CC-BY-4.0 확인. 저자·DOI·권리 표시한 연구 요약. 그림/논문 원문 제품 표시·재배포0. [공식 원문](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7698269/fullTextXML) |

[WUR 논문 등록](https://research.wur.nl/en/publications/cherry-tomato-production-in-intelligent-greenhouses-sensors-and-a/)은
게시일2020-11-02로 표시하지만 원 논문 XML은2020-11-11이다. 이 metadata 불일치를 기록하며 기존
게시일을 조용히 바꾸지 않았다. [DataCite](https://api.datacite.org/dois/10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7)의
`updated=2025-06-01T06:17:47Z`도 dataset version2를 가리키므로 새 CSV 정정 판본의 증거로 쓰지 않았다.

web 도구의 Figshare/4TU 오류·403, PMC CAPTCHA·WUR PDF403 뒤 작은 공식 API/PDF/XML을
직접 HTTP로 읽었다. 판본 목록/current metadata는 처음 memory에서 hash를 기록한 뒤 부모의
원 bytes 감사 요청으로 한 번 더 보존 조회했다. 일치 확인 뒤 반복 조회를 종료했다.

### 실제 읽은 raw bytes

| 원천 | bytes / SHA-256 |
| --- | --- |
| versions API | 166 / `97543c08bc7fc4872e4de52a3f1a0809ba8e8681376aaca72480e429f95d53a0` |
| current v2 metadata | 8,797 / `56d641d0da19c6750020a48ae92da642dc7a4aa82e3e857190643fb2f6741ce6` |
| v1 ReadMe PDF | 734,320 / `b93b9d18c12615b18a237c99770de39c00e3537bd0204fcb5de5fbe273dab5ec` |
| 원 논문 EuropePMC XML | 188,223 / `916249bd1c0647133edc3ee7a32ddb27d98b20bcae681b1ba25153a9dd4aeed1` |
| v1 metadata, 최초 memory 조회 | 9,138 / `4453dee1f21bcc4e0885bc93bac91b8f28e5a1e3e51da24388592164d1622c0d` |
| 명시 v2 metadata, 최초 memory 조회 | 8,799 / `47d0bc15e1fa886ba9939e8612754494e885a5dfa7c0e4e277c6576ed69e71e6` |
| DataCite, 최초 memory 조회 | 14,796 / `580f57622ff3522bf97178780bbfaaed45dbdf4ed524868800620c82da0fbf12` |

마지막 세 payload는 memory에서 읽고 hash를 기록했으며 원 bytes를 보존하지 않았다.
current/명시v2 endpoint의 hash 차이를 데이터 파일 개정으로 해석하지 않았다.
첫 네 원문과 URL→파일/시각/hash manifest는 새 소유 private0700 디렉터리의400파일로
보존했다. 원문은 저장소에 추가하지 않았다. manifest SHA-256은
`d3a53cd9430179e9c21d18a9f5e64386b0f8110b056d94d80dd943cd1301b7c8`다.

부모는 보존한 PDF/XML·metadata/목록·manifest의 실제 hash와400권한을 별도로 확인했다.
기존 pypdf로 PDF17페이지와 p1/9/14, XML의 해당 절과
`sensors-20-06430-f001` caption을 다시 읽어 위 좁은 관측을 대사했다.
이는 같은 공개 원천의 개발 검토이며 독립 농장 자료나 관문 승인으로 기록하지 않는다.

## 실제 조사 CLI와 확인 범위

작성·원천 재검토자는 부모 CLI가 `engineering-suite:research`의 조사 위임으로 생성한
`/root/harvest_reference303_dmc_followup_20261008`의 Codex다. 자신의 실제 JSONL에서
다음을 직접 확인했다. 해시는 개행 포함 원 행 bytes의 SHA-256이다.

| 항목 | 실제 관측 |
| --- | --- |
| 자식/부모 session | `01a1196b-313b-7cd3-a5a1-0cb668c72f92` / `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` |
| CLI / own session_meta | `0.161.0` / `2026-10-08T02:50:17.799Z` |
| own session_meta 행 hash | `5d54acd6204733afd92a19f677e52da7d9c750381a55aeed89f76b0c316e0702` |
| own turn_context | `2026-10-08T02:50:18.860Z`, `model=gpt-6.1-sol`, `effort=xhigh` |
| own turn_context 행 hash | `16565bba84d5b57f9614c4e9d6e8dff6e39fbc704a8eca96061d934b3e43f218` |

재귀 CLI·추가 에이전트·시험/PG/브라우저/작물 계산·CI/push는 실행하지 않았다.
이 Markdown만 새 저장소 파일로 작성했으며 생성 전 없음·현재398개 고정 소스에 포함되지 않음을
확인했다. 원 bytes/hash·작은 문서/metadata·문서 링크 확인은 개발 조사 증거이며 제품 CLI 호출,
독립 검토, 서버 gate 승인이나 생과 환산 검증의 증거가 아니다. 부모 검토는 별도다.
