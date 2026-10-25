# 개별 탄소 상태 다음의 새 잎 조달 — 2026-10-26 KST

이 판단은 현재 실행 중인 **Codex CLI gpt-6.1-sol / xhigh**에서 수행했다.
native turn_context2026-10-25T23:06:09.888Z, raw LF SHA
`d6f1058250d4d06d688c63857657d915eff839111e09278bb92fad5e17de9094`;
관측2026-10-25T23:12:20.020200Z, 재귀 CLI0. 출력은 아래 계약/코드와 증거다.
[코드 지도](crop-leaf-funded-births-code-map-20261026.md)는 research 스킬이 요구한
background 독자의 기계적 조사이며, 부모가 변경 전60지문을 확인했다.
독자의 모델 호출을 이 native 증명으로 주장하거나 관문 검토자로 삼지 않는다.

## 근거와 권리

[GreenLight 고정 판본](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json)은
buffer→기관 구조 탄소와 별도 성장호흡을 계산한다. 기존 cLeafG를 재사용한다.
이는 연속 집계식이며 새 기관 출현의 순간 초기 질량을 결정하는 식은 아니다.
원 JSON26741byte/SHA272a589edf0bb40d1a91b34e883f8e94b9adf747a576be4620c50296c03d7033,
Clear BSD 고지 SHA96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a와
기존 profile/notice를 유지한다. 새 수치·계수 채택0.

[Smoleňová 등(2025), §2.1.3–2.1.4](https://doi.org/10.1093/insilicoplants/diaf022)는
온도에 따른 기관 출현과 동화산물 공급/기관 수요에 따른 생장을 구분한다.
공통 동화산물 pool·기관별 유지비·상대 sink 배분을 설명하지만,
우리 현재 상태의 출현점 초기 Ci나 공급 제한 면적의 법칙을 제공하지 않는다.
[WUR 설명](https://research.wur.nl/en/publications/development-of-a-tomato-functionalstructural-plant-model-for-digi/)은
어린 토마토의 형태/생장과 계측 동기화·키 보정을 다룬 범위를 명시한다.
국내 방울토마토 한 작기/수확·미래 경제/대응 후보 검증으로 취급하지 않는다.
논문2025-11-26 출판/2025-12-08 typeset, 기존 PDF2319684byte/SHA
`a950a3458d902bf0d7c142ce202f5db48d9bc81fa1c2ca3e62daca626887e49b`, CC BY4.0.
이전 불변 원본의 조회 시각/권리는 [출처 기록](artifacts/leaf-carbon-sink-sources-20261024.json)에 있다.
이번 직접 OUP 열기는 접근 오류, edepot은403이며 검색 색인과 WUR 메타데이터로 보완했다.
원 HTTP bytes의 재수집 성공을 주장하지 않는다.

논문의 공개 이용권은 별도 VTC 코드/CSV의 이용권이 아니다.
[앞선 권리 조사](leaf-carbon-sink-primary-sources-20261024.md)의 미확인 상태를 유지한다.
저자 코드/CSV 다운로드·실행/재사용·GroIMP 설치0.
관측/available_at·단위는 서지 기록에 해당 없거나 미확인이고 새 측정 자료 채택0이다.
검토자는 native 부모이며 독립 농업 검증자/G0 승인자가 아니다.

## 선택한 첫 계산과 미채택 대안

다음은 원문에서 확정된 생리 법칙이 아니라 **별도 명시된 합성 연구 가정**이다.
새 Ci를 buffer에서 새로 구조화하는 경우에만 B=ΣCi와 cLeafG·B를 함께 차감한다.
이미 자금이 조달된 미출현 기관을 공개하는 경우에는 이 차감을 쓰면 이중 비용이 된다.
후자는 숨은 기관 재고/이전 조달 이력의 명시 모델이 없어 미구현이다.

현재 정규화는 sigmoid의 하한 점근선0이며 **F(0)>0**이다.
따라서 curve/0나이/요청 초기 A와 양의 초기 Ci를 각각 받아 검사한다.
면적→질량/SLA 역산·기본 seed mass0, actual 품종 추론0.
현재 독립 면적 팽창은 Ci 공급 제한을 받지 않으므로 이 점 계산을 추가해도
공급 제한 생장이 완성되는 것은 아니다.

열수지는 기존 k_leaf·A/floor와 명시 T_in의 기준온도 상대 현열만 추가한다.
호흡의 화학 에너지를 임의 계수로 현열로 바꾸지 않는다.
기존 Ci/a/A·과실/기후·D0·과거 장부/정확 시각은 보존한다.
빈 수관은 기존 양의 LAI/열용량 domain 밖이며, 새 조달점은 양의 기존 수관만 대상으로 한다.

## 구현 순서와 수용 범위

1. [조달점 계약](../contracts/crop-leaf-funded-birth-point-v1.md): trusted 원 CP에서
   1회 현재 검증→동시 새 잎/원 cLeafG 비용·유입 현열→1회 새 상태 RHS.
   같은 floor의 탄소/열수지, 독립 Decimal, 512경계와 원 상태/시각 보존을 검증한다.
   변경된 목록의 재개 CP는 발급하지 않는다. 실제 증거는 [구현 기록](crop-leaf-funded-birth-point-20261026.md).
2. 변경 목록의 versioned context/사건 이력과 연속+점 장부를 결속하고 같은 전역 시계로 재개한다.
   원 D0·누적량·prefix·새 출현 좌표를 재초기화 없이 보존한다. 원 attachment/시계 증거의
   결속, 빈 수관 시작/동시 제거와 중복 적용 정책도 별도 작은 하위 단계로 수용한다.
3. 수용한 계산만 불변 저장/무계산 reader→strict SDK→같은 ID/상태의 실제 잎3D에 연결한다.
   이후 생산량·자원 사용·경제/거시·수급·자율 비교를 기존 명세와 관문에 따라 연결한다.

2–3은 미완료다. 기존 저장3D의 실제 표시 창/R2 보류는 [이번 관측](leaf-carbon-stock-visible-window-20261026.md)에
기록하며 핵심 모델 개발의 새 선행 조건으로 삼지 않는다. G0–G4/실제 품종·독립 자료0,
개발과 독립 농장 자료 확보의 병행, 전체 목표와 자료 기반 완료일 미정 상태를 유지한다.
