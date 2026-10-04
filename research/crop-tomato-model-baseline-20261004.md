# 방울토마토 생산 모델 조사 — 2026-10-04

상태: **모델 개발 기준 조사 완료, 작물 프로필·실제 자료 G0·예측 수용 전**.
사용자 요청에 따라 작물 생장 계산 → 저장 결과/성장 3D → 생산량·자원·경제 연결을
우선한다. [구현 계약](../contracts/crop-growth-research-v1.md)과
[출처·매개변수 등록부](crop-tomato-source-register-20261004.json)를 함께 읽는다.

## 조사 실행과 판단

기존 Codex CLI 세션 `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`에서 수행했다.
실제 turn context `2026-10-04T04:53:25.507Z`의 모델 `gpt-6.1-sol`, effort `xhigh`를
확인했다. 재귀 CLI나 별도 모델 호출은 없었다. 공식 연구기관/저자·출판사·코드·
데이터 DOI 메타데이터를 읽고, 공개 파일을 제한된 크기로 `/tmp`에 받아 SHA-256을
계산했다. 아래 선택은 검토 가능한 설계 판단이며 승인 데이터나 관문 통과가 아니다.

## 첫 품종·작기

**개발 참조 사례: Axiany / Maxifort 대목, 2019-12-16 정식부터 2020-05-29까지,
네덜란드 Bleiswijk의 Reference 구역(303) 한 작기.** 실험 논문은 배지·고설 유인,
정식/관리·수확 및 기후 측정을 설명한다. 이 공개 사례를 개발 입력/QC 후보로
고른 것이며 국내 품종·종자 구매·현장 적합성을 승인한 것은 아니다.
[Hemming 등, 2020, 실험 방법](https://pmc.ncbi.nlm.nih.gov/articles/PMC7698269/).

Reference도 전체 작기를 개발/보정에 사용하면 독립 검증 자료가 아니다. 나머지
동일 시설 구역은 개발 시 사전 분할한 외부 비교에 쓸 수 있으나 같은 장소·작기를
공유하므로 국내 G2나 새로운 작기의 G3a를 대신하지 않는다. 국내 첫 적용 품종은
해당 품종·대목·시설 자료와 종자 확인 뒤 같은 ID로 명시적으로 등록해야 한다.

현재 [종자사의 기존 Axiany 경로](https://www.axiasemillas.com/segments-overview/axiany/)는
페이지 제목이 **AXANTIA XR**로 표시된다. 검색 캐시의 Axiany 설명/평균 과중을
현재 품종의 값으로 채택하지 않는다. 국내 공급 가능성과 품종 동일성은 보류다.

## 모델 후보 비교

| 후보 | 계산 가능한 핵심 | 구현·권리 근거 | 이번 판단 |
| --- | --- | --- | --- |
| Vanthoor 계열 / GreenLight 작물 모듈 | 탄수화물 동화·호흡·잎/줄기/과실 분배·LAI. 원 논문은 과실 발달 구획/개수와 수확 건물도 다룬다. | [원 연구](https://research.wur.nl/en/publications/a-methodology-for-model-based-greenhouse-design-part-2-descriptio/), [저자 구현의 고정 판본](https://github.com/davkat1/GreenLight/tree/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011), BSD-3-Clause-Clear | 첫 생장 수식/참조 실행 기준. 단순화된 수확 함수를 국내 방울토마토 수확 모델로 채택하지 않는다. |
| 축약 TOMGRO (Jones 등, 1999) | 주경 마디수·LAI·총/과실/성숙 과실 질량 5상태 | [원 출판사](https://elibrary.asabe.org/abstract.asp?%3FJID=3&AID=13203&CID=t1999&T=1&i=1&v=42); 열매 발달 매개변수의 지역·품종·관리 차이를 보고. 공개 실행 코드의 권리/완전한 수식 재현은 미확인 | 상태 구조와 계산량의 비교 후보. 현재 인터넷 재구현을 도입하지 않는다. |
| TOMSIM (Heuvelink, 1996) | 광합성·호흡과 기관/화방의 sink 수요에 따른 건물 분배 | [저자 학위논문 등록](https://research.wur.nl/en/publications/tomato-growth-and-yield-quantitative-analysis-and-synthesis/); 실행 코드·매개변수 패키지 재사용권 미확인 | 화방/관리 효과의 장기 비교 후보. 첫 구현 의존성으로 추가하지 않는다. |

**선택 이유:** 온실 계산과 분리한 작물 전용 입력 경계가 있고, 방정식·수치·라이선스를
고정해 대조할 수 있다. 논문의 해외 검증 정확도를 우리 코드나 국내 Axiany에
전가하지 않는다. 기존 Python 수치 모듈에 작은 명시적 수식을 구현하며, 전체
GreenLight 플랫폼의 GUI/배열/해석기 의존성을 제품에 설치하는 결정은 하지 않았다.

## 확인한 입력·매개변수 근거

작물 단독 모듈에는 수관 온도 °C, 수관 위 광합성 유효광량
µmol photons/m²/s, 주변 CO₂ ppm이 필요하다. 기존 온실 실내 기온이나 외기 일사를
수관 온도·PAR로 자동 대체하지 않는다. 고정된 [단독 입력 정의](https://github.com/davkat1/GreenLight/blob/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/extension_crop_vanthoor_2011_for_standalone.json)의
상수 예제는 관측값이 아니다.

등록부는 **39개 const 항목**의 원 값/식·단위·JSON 경로·근거·보류를 보존한다.
방정식 안의 수치, 초기조건, 관리 사건도 첫 입력 감사에서 별도로 고정해야 한다.

| 항목 예 | 확인한 원 값/단위 | 채택 한계 |
| --- | --- | --- |
| 광합성 변환 `alpha`, 곡률 `theta` | 0.385 µmol e⁻/µmol photons; 0.7 | 문헌/일반 토마토 참조값. Axiany 보정값 아님 |
| 비엽면적 `sla` | 2.66×10⁻⁵ m² leaf/mg CH₂O | 잎 면적 환산 가정. 실제 품종·작기 검증 필요 |
| 기관 최대 분배 `rgFruit/rgLeaf/rgStem` | 0.328 / 0.095 / 0.074 mg CH₂O/m²/s | 공급 제한·온도 억제와 함께 적용. 독립 수확 근거 아님 |
| 호흡 보정 `cRgr` | 2.85×10⁶ **s** | 코드 단위 `s⁻¹`는 원 논문과 불일치. 원 학위논문 p256 Eq9.45 / p266 Table9.1에서 s 확인 |
| 수확 관련·초기 밀도 | 일반 코드의 질량 임계 수확/초기 3.12 plants/m² 등 | Axiany의 실제 수확 시점·생과중·줄기수로 자동 채택 금지 |

[GreenLight 고정 작물 파일](https://github.com/davkat1/GreenLight/blob/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json),
[Vanthoor 학위논문 Ch9](https://edepot.wur.nl/170301)에 근거한다.

**단위/QC 쟁점:** 원 논문 p256/266은 `cRgr`를 시간 s로 정의하므로 첫 계약에서
그 단위를 사용한다. 코드의 일부 기관 유량 단위는 m²로 적혀 있으나 원 수지식의
유량은 m⁻²다. 줄기 저장소에는 뿌리도 포함된다. 원 모델의 탄수화물→건물 환산은
별도 가정이며 생과중 환산이 아니다. 평활 24시간 수관 온도는 실제 직전 24시간
산술 평균과 같지 않다. 온도 합은 기준온도를 뺀 GDD로 바꾸지 않는다. 잎 0의
광합성 식 특이점, 평활 제거 함수의 작은 꼬리와 과실 구획 생략은 구현 전 검사한다.

## 자료 권리와 실제 다운로드

데이터 DOI `10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7`, 판본 2의
[DataCite 메타데이터](https://api.datacite.org/dois/10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7)와
[기탁 파일 API](https://api.figshare.com/v2/articles/12764777)가 CC0-1.0을 기록한다.
판본 게시 시각은 2020-09-23T10:41:39Z다. 실제 `24757220` 압축 파일 8,418,715바이트를
다운로드했고 MD5 `2a0c7f3332881caef54ca8f4dc60c9a3`가 제공자 값과 같았다.
SHA-256은 `b889e9ab1663fe3b8a90a3dab71d4340a6ecd49492532c43784cc82d799708ca`다.

4TU 구 UUID API/DOI 일부 연결은 403/404/timeout으로 직접 읽지 못했다. DataCite의
판본 2 링크와 기탁 사본을 함께 기록하며 장애를 숨기지 않는다. **압축 내부 파일,
채널 단위·시간대/DST·기간·결측·관리 사건·면적 분모는 아직 감사하지 않았다.**
다운로드/라이선스 확인이 G0 품질 승인이나 실제 모델 입력 채택은 아니다. 원본은
저장소에 넣지 않았고 모델의 국내 학습/검증 완료도 주장하지 않는다.

코드 판본 `7a7b36870135aa38bbe81e65590dcf5473786bdd`의 실제 파일 SHA-256:

- 작물 JSON: `272a589edf0bb40d1a91b34e883f8e94b9adf747a576be4620c50296c03d7033`
- 단독 입력 JSON: `74bf4f3ebc3100945de834433b210984c7a75c78c58218e5f7d5b4bd1c82ea49`
- 코드 라이선스: `96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a`
- 원 학위논문 PDF: `965ecc5573290d0cc59b514e9766b301f9584d212545dec177efa66dd756ac38`

[BSD-3-Clause-Clear](https://github.com/davkat1/GreenLight/blob/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt)는
코드 재사용 시 원 저작권·조건/면책 유지가 필요하다. 논문은 참고/수식 대조용이고
그 PDF 재배포 권리는 별도로 확인해야 한다. 실험 논문은
[CC BY 4.0](https://pmc.ncbi.nlm.nih.gov/articles/PMC7698269/)이며 저자·논문·라이선스를
표시한다. 종자사 사진이나 모델 기반 생성 자산에 자동으로 같은 권리를 적용하지 않는다.

## 독립 자료 확보를 개발과 병행하는 계획

자료 요청·동의·사전 분할은 전체 운영/G1 완주를 기다리지 않는다. 현재 확보된
국내 농장·동의·미사용 작기는 **0개**다. 외부 메시지는 발송하지 않았으며 담당 농장,
접근 계약과 기간 확보는 외부 의존성이다. [권리/분할 프로토콜](crop-independent-data-protocol.md)과
[필수 채널 체크리스트](crop-independent-data-checklist.md),
[실제 확보 상태](crop-independent-data-status.json)를 준비했다.

| 묶음 | 필요한 자료/권리 | 독립성·검사 |
| --- | --- | --- |
| 농장/품종/관리 | 좌표·시설·작기·품종/대목·식재 및 줄기 밀도, 초기 잎/기관 상태, 유인·적엽·적과·적심·수확 사건 | 직접 동의, 영업정보 비공개 범위. 데이터 공개권과 모델 사용권 구분 |
| 실내/수관/광/CO₂ | 센서 위치·보정·단위·UTC/현지 시각·결측, 수관과 기온 관계, 실제 PAR | 국내 외기 관측을 실내 입력으로 사용하지 않음. 보정 작기와 검증 작기 분리 |
| 생산/품질 | 반복 LAI/잎 면적·건물, 개화/착과/숙기, 수확 생과 kg·건물률·개수·등급/불량·수확 날짜 | 파괴 측정/표본법·면적 분모 기록. 반복 시점을 무작위 섞어 같은 작기를 독립으로 만들지 않음 |
| 자원/비용 | 급액·배액·재순환·배지 저장, 물·성분 질량, 실제 전력/연료/CO₂ 계량·장비, 요금/청구·작업/정산 | 같은 물량/기간 대사. 증산≠급액≠구매 용수, 공급열≠전력, 수확≠판매 |

검증 전에 손실 기준·대상 범위·제외 규칙과 개발/보정/최종 보류 자료를 등록한다.
생장에는 LAI/기관 상태 오차, 생산에는 첫 수확 시점·시점별/누적 생과 kg·편향과
기준선 대비 오차를 사용한다. 자원은 각각 계량된 같은 양을 비교한다. G3a의 미래
작기 평가는 당시 이용 가능한 입력만 사용하고 이후 관측은 정답에만 사용한다.
국내 독립 작기 또는 측정 오차 근거가 없으므로 수치 합격선·통과 날짜는 미확정이다.

## 다음 단계와 일정 근거

후속 **`crop-growth-rates`의 작은 탄소 유량 모듈**과
[작은 수관 적용 정책](crop-photosynthesis-domain.md)은 로컬 소프트웨어로 수용했다.
[상태 적분](crop-growth-integration-implementation.md)·[불변 저장](crop-result-storage-implementation.md)·
[조회 API](api-crop-replay-implementation.md)·[성장 연구 3D](web-crop-replay-implementation.md)도
로컬 합성 연구 소프트웨어로 수용했다. [실제 참조 입력 감사](crop-forcing-audit.md)도
완료했으며 실제 입력/작기 채택은 보류다. 다음은 과실 발달식/구획 계약이다.
모델 전체의 임의 수확값이나 농장 예측을 만들지 않는다.
고정식·단위·독립 수식 대조의 범위를 유지하고 탄소 수지·고갈·수렴·재실행을 확인한다.
실제 Axiany 자료 감사와 독립 자료
요청 패킷은 병행한다. [수정 순서/잠정 작업량](../tasks/plan.md#작물-생산과-성장-3d-우선순위-2026-10-04)을 따른다.
