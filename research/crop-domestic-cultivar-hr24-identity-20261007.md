# HR24 상용 품종명 식별 조사 — 2026-10-07

상태: **`HR24` / `Joeungyeo’`의 공식 한국어명·제품/품종 등록 ID 연결은 `unconfirmed`**.
[선행 접근 조사](crop-domestic-validation-access-followup-20261007.md)를 이어
FarmHannong 공식 종자 목록 경로 하나를 확인했다. CLI 연구 제안이며 품종·자료·관문 승인이 아니다.

## 원 명칭과 공식 검색 결과

논문 방법 2.1은 HR24를 상용 품종 `Joeungyeo’`, 공급자를 `Farm Hannong`으로 기술하고,
HR17은 원형, HR24는 타원형 과실이라고 설명한다. 이는 논문의 식별 표기다.
한국어명·동의어·종자 lot·공식 제품번호·품종 등록번호는 그 문단에 없다.
[공식 논문/JATS](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml).

실제 [FarmHannong 종자 목록](https://www.farmhannong.com/kor/product/product_ct03/list.do)의
GET form은 `productCt1=PRODUCT_CT03`, `productName`을 제공한다.
영문 검색어 `Joeungyeo`로 [제품명 검색](https://www.farmhannong.com/kor/product/product_ct03/list.do?productCt1=PRODUCT_CT03&productName=Joeungyeo&pageIndex=1)을
조회한 결과는 HTTP 200·표시 **0건**이다. 입력 검색어는 응답 input에 보존되어 있다.
검색 인덱스의 범위·한국어 전용 명칭·과거 판매품 포함 여부를 알 수 없으므로,
0건을 품종 부존재나 단종의 증거로 해석하지 않는다.

같은 form의 `crops_crops46=CROPS46`은 ‘토마토(방울토마토)’ 필터다.
[해당 공식 목록](https://www.farmhannong.com/kor/product/product_ct03/list.do?productCt1=PRODUCT_CT03&crops_crops46=CROPS46&pageIndex=1)은
총 21건을 표시하며 이번 첫 페이지에는 제품 ID 20개가 있다.
첫 페이지에는 `HR24`·`Joeungyeo` 연결 표기가 없다. 전체 21건의 상세나 과거 목록을
전수 조사한 것은 아니다. 다른 제품의 과형이나 비슷한 발음만으로 대체 품종을 지정하지 않았다.

| 식별 항목 | 이번 결론·적용 한계 |
| --- | --- |
| 논문 ID/시험 재료 | DOI `10.3389/fpls.2025.1730694`, HR24; `HR24`는 공식 종자 제품 ID로 확인되지 않음 |
| 공식 한국어명/동의어 | `unconfirmed`; 검색 탐색용 음역을 공식 명칭으로 채택하지 않음 |
| 제품/품종 등록 ID | `unconfirmed`; 개별 공식 제품 연결 실패. 국립종자원 등록 조회는 이번 단일 경로 범위 밖 |
| 원형/타원 방울 분류 | 논문상 HR24 타원형. 공식 제품의 ‘대추형’ 분류로 자동 매핑하지 않음 |
| 대목/접목 | 미확인; 같은 목록의 대목 제품 존재를 HR24의 사용 대목 근거로 삼지 않음 |
| 재배 방식 | 논문은 토경 온실 시험을 설명함. 제품별 수경/토경 적용·국내 전체 작기 적합성은 미확인 |

위 논문 범위는 [방법 2.1·2.3](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml),
목록 범위는 [공식 종자 검색](https://www.farmhannong.com/kor/product/product_ct03/list.do)에 근거한다.
새 계수·모델·프로필을 선택하거나 기존 Axiany/Maxifort와 합치지 않았다.

## 시각·판본·권리와 조회 증거

논문 관측 vintage는 2022·2023, 공표일은 `2025-12-19`이다. 정확한 공표 시각/시간대와
`available_at` timestamp는 미확인이다. 선행 조사에서 직접 받은 JATS를 로컬 재검토했으며,
원 수집 시각 `2026-10-07T05:20:19.685503Z`, SHA-256
`8ae905d37b49ee858c66b8542151a1a36faba68ef16a2eeb03088552f4aa5e2e`를 그대로 참조한다.
[공식 JATS 공표/권리 필드](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml).
이번에 논문을 새로 네트워크 수집했다는 기록이 아니다.

공식 종자 목록의 관측은 아래 조회 시점의 웹 표시다. 제품 공표·갱신일, 최초 `available_at`,
제품 vintage/revision은 미확인이다. footer의 `2019` 저작권 연도는 제품 공표일이 아니다.
수량 단위/QC는 이번 품종 식별 대상 밖이며 농장 원자료·원측정 hash는 없다.

| 사설 공개 HTML / 공식 경로 | 직접 GET 완료 UTC / bytes / SHA-256 |
| --- | --- |
| `farmhannong-seed-list.html` / [종자 목록](https://www.farmhannong.com/kor/product/product_ct03/list.do) | `2026-10-07T05:43:49.799680Z` / `66712` / `c4eaf54f73ea143a9b72be48a5729be027e83fcd902479a63c46cf6efb218955` |
| `farmhannong-exact-name-search.html` / [영문명 검색](https://www.farmhannong.com/kor/product/product_ct03/list.do?productCt1=PRODUCT_CT03&productName=Joeungyeo&pageIndex=1) | `2026-10-07T05:44:22.192827Z` / `31951` / `8f95b5c5f40a253cf24f7e90ee3b4e0ece906ee72be5269eed2966b355cd9780` |
| `farmhannong-tomato-list.html` / [공식 작물 필터](https://www.farmhannong.com/kor/product/product_ct03/list.do?productCt1=PRODUCT_CT03&crops_crops46=CROPS46&pageIndex=1) | `2026-10-07T05:44:22.383521Z` / `66191` / `fef22e1011547478f0a477a0cdc16854c878d10508311dc6995d124774ef9d37` |

모두 익명 HTTP 200이다. 공개 제품명·분류·검색 결과를 읽어 식별 사실만 검토했다.
FarmHannong 목록 footer는 `ALL RIGHTS RESERVED`이며 명시적 재사용 라이선스는 확인하지 못했다.
원문/사진의 표시·재배포, 전체 본문의 외부 CLI 처리 허락은 **미확인**으로 남긴다.
[공식 목록의 권리 표시](https://www.farmhannong.com/kor/product/product_ct03/list.do).
논문은 CC BY 4.0 표시가 있으나 이를 종자 회사 콘텐츠에 전이하지 않는다.
[논문 license](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/xml).

## 실행 근거와 남은 hold

이번 native CLI `turn_context`를 독립 확인했다: `2026-10-07T05:42:31.155Z`,
정확히 `gpt-6.1-sol` / `xhigh`. 원 JSONL 줄 SHA-256은 **끝 LF 포함**
`a30e308e7bcd30537943b25e698699e98ee71238df4f85b2abdc534d3b99e137`,
LF 제외 `74ff603fbb4e369d242a30dce33e2deab974b99006df0adaf2b60049012b3f86`이다.
실제 실행은 기존 native 턴의 `web.run`과 `python3 - <<'PY'`/bounded urllib GET이며 재귀 CLI는 없다.
사설 경로 `/home/sunghoonk/.local/state/OpenSmartFarmSim/20261007-hr24-identity-research/`는
`0700`, 파일은 `0600`; `metadata-manifest.json`은 7개 조회/문맥 파일의 해시를 기록하며
자체 SHA-256은 `a12da0a5e03684e456330422314e1acf03f17ad5bf7211066390fe8f1d6f9f1d`다.

다음 식별 근거는 `Joeungyeo`와 한국어명/공식 제품·등록 ID를 함께 명시한 제공자 문서나
원 시험 종자의 가명 lot/라벨 대응표다. 그 근거가 확보되기 전에는 **연결 실패/미확인**으로 유지한다.
검토자는 현재 native CLI 연구자이며 최종 품종·권리 검토자는 미지정이다.
이 문서만 새로 작성했다. 기존 보고서·프로필·작업/관문·실험 파일과 프로세스는 변경하지 않았고,
계정·연락·원 농장 자료 다운로드·시험·서버·계산·commit/push는 수행하지 않았다.
