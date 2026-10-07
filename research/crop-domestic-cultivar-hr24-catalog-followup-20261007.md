# HR24 품종 식별: FarmHannong 현재 카탈로그의 제한 후속 대조

조사일: 2026-10-07 KST. 검토자: native Codex CLI `gpt-6.1-sol` / `xhigh` 배경 조사 에이전트. 부모 검토 대기. 이 문서는 검토 가능한 CLI 판단이며 데이터·품종·계수 채택 또는 관문 승인 증거가 아니다.

## 결론과 조사 경계

**공식 한국어명·제품 ID와 HR24/`Joeungyeo`의 연결은 `unconfirmed`다.** [선행 식별 조사](crop-domestic-cultivar-hr24-identity-20261007.md)의 남은 목록과 상세를 대조했다. [공식 목록 1](https://www.farmhannong.com/kor/product/product_ct03/list.do?productCt1=PRODUCT_CT03&crops_crops46=CROPS46&pageIndex=1)은 총21건 중20개, [목록 2](https://www.farmhannong.com/kor/product/product_ct03/list.do?productCt1=PRODUCT_CT03&crops_crops46=CROPS46&pageIndex=2)는 누적21개를 반환했다. 새로 확인한 항목은 `seq=5042`다.

두 목록의 고유21개 상세를 각각 한 번씩 순차 GET했다. 모두 HTTP200으로 실제 제품명·본문 HTML이 열렸고 목록명, 상세 `pdTit`, `og:title`이 일치했다. 전체 응답 HTML에서 대소문자를 무시한 `HR24`, `HR 24`, `HR-24`, `Joeungyeo` 문자열은 모두0건이었다. 아래21개 제품명에는 그 명칭을 직접 잇는 별도 영문 동의어가 확인되지 않았다. 영문 약자·숫자 자체를 논문의 품종 식별자로 해석하지 않았다. 각 행은 실제 조회한 공식 상세 URL이다.

## 조회한 제품명과 공식 사이트 ID

| `seq` | 공식 제품명 |
|---|---|
| [5453](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=5453) | TS탑스타토마토 |
| [5480](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=5480) | TS강열토마토 |
| [5481](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=5481) | 레드큐토마토 |
| [5437](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=5437) | 헤르메스골드토마토 |
| [5436](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=5436) | BW초강 토마토대목 |
| [4008](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4008) | 244토마토 |
| [4094](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4094) | 339토마토 |
| [4088](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4088) | 7160방울토마토 |
| [4093](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4093) | 라피토토마토 |
| [4012](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4012) | 맥시포트 토마토 대목 |
| [4013](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4013) | 신청강 토마토 대목 |
| [4086](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4086) | 올레티와이방울토마토 |
| [4085](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4085) | 유니콘방울토마토 |
| [4045](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4045) | 탐스런토마토 |
| [5043](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=5043) | BW찰떡궁합 토마토 대목 |
| [4011](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4011) | TY레벨업방울토마토 |
| [4095](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4095) | TY시선집중토마토 |
| [4092](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4092) | TY썬업토마토 |
| [5031](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=5031) | TY열강토마토 |
| [4087](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=4087) | TY유니콘방울토마토 |
| [5042](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=5042) | TY타이푼방울토마토 |

## 식별 범위와 적용 보류

- 공식 조회 분류는 `PRODUCT_CT03` / `CROPS46`, 화면명 `토마토(방울토마토)`다. 같은 목록에는 일반 토마토명과 대목 제품도 포함되므로21개를 모두 독립 방울토마토 품종으로 세지 않는다. `seq`는 사이트 제품 ID이며 국가 품종 등록번호라는 근거는 없다. [공식 목록](https://www.farmhannong.com/kor/product/product_ct03/list.do?productCt1=PRODUCT_CT03&crops_crops46=CROPS46&pageIndex=2)
- 음역·유사 상표·숫자·과형으로 `Joeungyeo`를 위 한국어명에 자동 연결하지 않았다. HR24의 원/타원 분류, 한국어 대추형 명칭, 대목·접목 여부와 토경/배지 적용을 이 제품들로 확정할 수 없다. 논문의 HR24·상용명·타원형·토경 실험 관찰과 이 카탈로그 제품의 동일성은 미확인 상태다. [원 논문](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1730694/full), [선행 접근 조사](crop-domestic-validation-access-followup-20261007.md)
- 조회한21개 현재 공개 HTML에서 명시 연결을 찾지 못한 결과다. 품종 부존재·단종, 과거 목록 또는 공급 목록 전체의 완전성을 증명하지 않는다. 이미지·첨부·OCR·다른 언어 페이지·등록기관은 조사하지 않았다. 이미지 속 별칭의 존재 여부도 미확인이다.

## 시각·판본·QC·권리

| 항목 | 관측 또는 미확인 |
|---|---|
| 제공기관·채널 | FarmHannong 공식 종자 카탈로그, 익명 공개 HTML |
| 카탈로그 관측/회수 | 목록1 회수완료 `2026-10-07T06:19:31.184182Z`; 목록2 정확한 완료시각 미기록. 목록2 파일 저장시각 `06:19:32.276712Z`는 회수시각 대용으로 쓰지 않는다. |
| 상세 회수창 | `2026-10-07T06:20:22.577428Z`–`06:20:48.537780Z`; 각21개 완료시각·상태·응답 헤더는 사설 receipt에 보존 |
| 품종 관측·공표·갱신시각 | unknown. 현재 페이지를 읽은 시각과 실제 품종·제품의 공표시각을 구분한다. |
| `available_at`, 판본/vintage | 모두 unknown. footer의2019 및 이미지 경로의 날짜를 공표·당시 가용 시각으로 쓰지 않는다. |
| 단위 | 제품명은 문자열, `seq`/분류 코드는 식별자. 농업량·수확 계수·측정단위 자료는 확보하지 않았다. |
| QC | 고유ID21개, 목록/상세/OG 제목21개 일치; 모든 상세 raw SHA256 대사. 목록2가 누적21개라 초기 `≤20` parser 가정이 실패했고 저장 HTML을 재해석했다. 재요청0회. 최초 목록 HTTP 헤더는 보존되지 않았으며 목록2 정확한 회수완료시각도 unknown. |
| 이용·표시·재배포 | footer에 copyright2019 / all rights reserved 표시. 명시 재사용 라이선스, 제품 본문·사진의 표시/재배포 허가는 미확인이다. 보고서는 식별 사실·제품명·ID·링크만 기록한다. [실제 상세](https://www.farmhannong.com/kor/product/product_ct03/view.do?productCt1=PRODUCT_CT03&seq=5453) |
| CLI 처리 | 익명 GET이 기술적으로 가능했음을 관측했다. 외부 CLI·TDM 처리에 대한 명시 권한은 미확인이다. 이 제한적 식별 검토를 허가 확인으로 채택하지 않는다. 논문의 CC BY는 업체 카탈로그 권리를 부여하지 않는다. |

상세 경로는 공식 페이지의 `data-controller`와 연결된 [site.js](https://www.farmhannong.com/common/js/site.js), [productController.js](https://www.farmhannong.com/common/js/controller/products/product/productController.js)의 GET form `./view.do`·`seq` 처리에서 확인했다. 전체 조회는 목록2회+상세21회+공개 인터페이스 스크립트2회, 합계25회 순차 GET이다. 계정·연락·우회·원 농장 기록·사진/문서 다운로드는 없었다.

## 사설 회수 증거와 실제 native 문맥

사설 위치: `/home/sunghoonk/.local/state/OpenSmartFarmSim/20261007-hr24-catalog-followup-research/` (`0700`, 모든 파일 `0600`). 공개 HTML·조회 메타데이터·식별 대사·native whitelist만 보존했다. manifest는 자신을 제외한54개 파일의 바이트수·SHA256·권한을 결속한다.

- `manifest.json` SHA256: `f5e1c341c87534dc836a8d940fca90f3a0a9510067ab0e60ef8d230ed7b2d6d6`.
- 목록1: 66,191B / `fef22e1011547478f0a477a0cdc16854c878d10508311dc6995d124774ef9d37`; 목록2: 67,503B / `31b8e6ca17a53cadd080b211fbf551f10e542353a0131b9cadf93de2a458b495`.
- `identity-review.json` SHA256: `29a664463f448b5523c37e1991acb811bd84eb6855dbcb94dff7f272f50693f8`. 각21개 상세의 URL/ID/시각/바이트수/SHA는 이 파일 및 개별 retrieval receipt에 있다.
- 실제 native `turn_context`: `2026-10-07T06:16:18.257Z`, `model=gpt-6.1-sol`, `effort=xhigh`. 이미 실행 중인 세션을 직접 검증했으며 재귀 CLI는 실행하지 않았다. whitelist는 event type·timestamp·model·effort·source JSONL 경로/줄번호·두 SHA만 보존한다.
- 원 `turn_context` JSONL 한 줄 SHA256 **끝 LF 포함**: `d19aba247e84b824050d35351a5ead0fe9babbf74cc834d92e167e4859c6f92a`; **LF 제외**: `8a00789222512d2f03378d8b7412a3657b25a23a2ebb507434cd637261b0bad6`.
- 원 세션 바이트와 두 SHA를 다시 대조한 `native-context-recheck.json` SHA256: `2845ee2a622941b439e12d4243ba781d989ea186fc6f5ff4ee1a1d67577709a7`. `bounded-review-receipt.json` SHA256: `9a9ad76a2335201ebe506fb8ed9ebcc9ea3cf511e3c79b6811f2918e743cc607`.

## 남은 의존성과 다음 단계

현재 카탈로그 HTML 범위의 연결 시도는 **실패/미확인으로 종료**한다. 다음 식별에는 `HR24` 또는 `Joeungyeo`를 공식 한국어명과 제품/품종 등록 ID에 직접 잇는 별도 공개1차 근거가 필요하다. 해당 근거가 생기기 전에는 같은 품종이라는 연결을 보류한다. 이 조사는 독립 농장 검증자료·승인 계수·대목 또는 재배 방식의 증거를 추가하지 않는다.

문서·링크/사설 해시·권한 대조만 수행했다. 시험·서버·계산·CI·커밋·push는 실행하지 않았으며 기존 보고서·프로필·작업 문서·receipt·고정 소스·실행 중166일 실험은 수정하지 않았다.
