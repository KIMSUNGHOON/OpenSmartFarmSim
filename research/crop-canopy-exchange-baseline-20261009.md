# 기후·자원 연결을 위한 수관 교환식 검토 — 2026-10-09

현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 기존 배경 조사의 원본/보충 감사를 검토했다.
실제 세션/turn event 해시는 [새 등록부](crop-canopy-exchange-source-register-20261009.json)에 있다.
CLI 재귀 실행은 없다. 조사 제안 자체를 승인 데이터나 관문 증거로 사용하지 않았다.

## 참조 선택과 단위

기존 탄소 모델과 같은 GreenLight commit `7a7b36870135aa38bbe81e65590dcf5473786bdd`의
[Chapter 8 코드](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json)를 참조한다.
raw 130,649 bytes/SHA `c0fb7a025533f15b80cb6cd60aafdc19be9fe42df6b8183cf97b83fc086138b3`다.
[BSD-3-Clause-Clear](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt)의
고지 SHA는 기존 [보존 고지](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt)와 같다.
원문 6개 식과 9개 매개변수/식 상수는
[참조 프로필](../fixtures/crop-canopy-exchange-reference-parameters-v1.json)에 포인터·원 단위를 기록했다.
일반 문헌 참조이며 Axiany 전용 보정/국내 품종 적용 승인이 아니다.

원 현열식은 `2*alfaLeafAir*LAI*(Tcan-Tair)`다. `rho*cP/rB`를 현열 계수로 발명하지 않는다.
원 `alfaLeafAir` 단위에는 leaf 표지가 없고 잎→공기 계수라는 설명만 있다.
LAI의 leaf/floor 기준과 함께 W/(m²_leaf K)로 해석하여 W/m²_floor로 계산하는 것은
**프로젝트의 차원 해석**으로 등록했다. 수증기식은 별도의 저항 `rB+rS`를 사용한다.

원 포화압 식의 분모는 `T+238.3`이다.
[원문이 인용한 설명](https://www.conservationphysics.org/atmcalc/atmoclc1.html#svp)도 같은 값을 준다.
기존 NWS 열 모델의 `237.3` 식과 다르므로 기존 `thermal_units.py`를 바꾸거나 혼합하지 않는다.
원문에는 정밀도 보증 구간이 없다. 첫 모듈의 10–34°C는 기존 탄소 계산 창과 맞춘
**합성 시험 구간**이며 식/품종의 경험적 정확도 범위를 뜻하지 않는다.
인용 웹/PDF의 별도 권리는 GreenLight 라이선스로 바뀌지 않는다. 그 원문은 사설 보관하고 제품 재배포에서 제외한다.

## 명시 입력과 남은 판단

- `rhoAirCap`은 원식의 용량용 밀도이며 온도/압력 기반 `rhoAir`와 다르다.
  고도식의 부호/적용 범위까지 이 단계에서 채택하지 않고 양의 명시 입력을 받는다.
  원 sea-level 1.2는 합성 사례 입력의 근거이며 지역별 기본 밀도로 주입하지 않는다.
- `rS`는 명시 양수 입력이다. 광/CO₂/압력차를 쓰는 원 기공 폐쇄식은 아직 채택하지 않는다.
  `sRsSlope` 원 단위와 지수의 차원 불일치를 별도 보류한다. `rSMin=82`는 원 상수의 존재를
  기록하는 사실이며 모든 시설/품종의 검증된 최솟값이 아니다.
- 원 E는 부호가 있다. 음수는 역방향 교환으로 보존하고 검증된 결로/잎 액막으로 표시하지 않는다.
  LAI=0의 순간 교환 0과 전체 수관 열용량 0의 ODE 특이점을 구분한다.
- 기존 열 v1은 단일 집계 온도와 이미 적용한 잠열 항을 가진다. 독립 수관/공기 온도·
  복사/CO₂·열용량·수증기 에너지와 물 저장소의 새 경계/버전 설계 없이 연결하지 않는다.
  이후 동적 결합에서 실제 수관 온도, 열·수증기·탄소 수지/해상도를 함께 검증한다.

## 권리·시간 감사와 개발 의존성

원 배경 metadata의 `published_at`은 commit 시각이었다. **새 등록부는 이를 공개 시각으로
승인하지 않고 `revision_committed_at`으로 구분**, 최초 공개/`available_at`은 null/hold로 둔다.
보조 목록 응답의 권리/단위 누락도 실제 입력 채택으로 승격하지 않았다.
관측 자료가 아닌 권리가 확인된 고정 코드식의 소프트웨어 개발 참조만 채택한다.
정확한 농장 의사결정 시점에 사용 가능한 측정 자료/품종 프로필로는 채택하지 않았다.

`crop-canopy-exchange`는 순수 계산 자식으로 전체 수확 registry 작업과 독립 개발 가능하다.
통과하면 [계약](../contracts/crop-canopy-exchange-v1.md)의 순간 E/H/LE 표·국소 부호/수지가 산출물이다.
전체 수확/저장·3D 후 기후 결합→물/양분→구매 에너지→Decimal 경제라는 통합 순서를 유지한다.
독립 국내 수관/환경/급배액·에너지 계측 자료는 병행 확보하며 현재 0건이다.
이 원식 검토로 G0–G4 또는 실제 생산·자원·미래 마진·추천을 승인하지 않는다.
