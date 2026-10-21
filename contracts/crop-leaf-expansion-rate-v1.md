# 한 잎의 순간 면적 확장률 — 연구 v1

상태: [51집중 검사/독립20점 수용](../research/crop-leaf-expansion-rate-20261022.md). [원문·저자 구현의 식과 차원 대조](../research/tomato-leaf-expansion-equation-20261022.md)를 따른다.
타품종 계수·저자 코드/자료는 채택하지 않는다. 원 논문의 logistic 설명과 고정 저자 구현에서 확인한
수학적 관계를 자체 합성 입력에 대해 독립 구현한다. 논문 실행본과 동일한 전체 모델이라고 주장하지 않는다.

## 한 점의 계산

`backend/app/crop_leaf_expansion.py`의 `calculate_leaf_expansion_rate(*, inputs)`는
기관 열적 나이 한 점의 **m2/degC_day**만 반환한다.
입력은 정확히 `input_id`, `origin=synthetic`, `thermal_age_basis=since_leaf_emergence`, `values`다.
ID는1–200자 기존 ASCII 형식이다. 네 quantity는 각각 정확히 `{value, unit}`다.

| quantity | 단위 | 수학적 정의역 |
| --- | --- | --- |
| `thermal_age` | `degC_day` | 유한·비음수 |
| `maximum_area` | `m2` | 유한·양수 |
| `steepness` | `1/degC_day` | 유한·양수 |
| `inflection_age` | `degC_day` | 유한·비음수 |

이 범위는 계산 정의역이며 실제 생물학적 적합 범위가 아니다. 기본 계수/자동 단위변환은 없다.
cm²로 기록된 원 계수 수치를 SI 입력으로 넘겨 쓰지 않는다. 기울기의 역온도일 단위는 지수의
무차원 조건에서 도출한 계약이며 원 표의 `–` 표기를 원문 단위라고 변경하지 않는다.
현재 수관 온도합·절간 나이·달력 일수를 잎의 출현 후 나이로 대신 받지 않는다.

```text
z = steepness * (thermal_age - inflection_age)
R_area = steepness * maximum_area * exp(-z) / (1 + exp(-z))^2
```

출력은 `model_version=leaf-logistic-thermal-area-rate-research-v1`,
`scope=software_research_only`, `claim_scope=synthetic_crop_math_only`, `gates=not_assessed`,
정규 입력/모델의 `input_sha256`과 `expansion_per_thermal_age {value, unit:m2/degC_day}`다.
입력을 변경하지 않는다. bool·문자 수치·추가/누락 필드·다른 출처/단위·비유한 입력을 거부한다.
log-domain 평가로 불필요한 중간 exp/곱 overflow를 피한다. 지수/결과가 비유한이거나 양의 결과가0으로
underflow하면 `LeafExpansionHold`다. clamp·임의0으로 바꾸지 않는다.

## 분리한 후속 조건

순간율은 현재 잎 면적·잎 수·LAI·누적량이 아니다. 초기면적·시간/열적 구간 적분·시계/출현/관리·기관 목록,
면적→길이/폭·소엽/표면 geometry·저장/API/3D는 뒤따르는 별도 수용이다.
저자 구현의 끝점율×구간 누적을 정확 적분이라고 부르지 않는다. 초기면적의 암묵0을 도입하지 않는다.
현재 동결된3D의 고정3복엽/수치와 기존 수치 모듈/판본은 유지한다.

## 수용

1. 원 논문/보충자료와 고정 저자 구현을 구분하고 식·단위·초기조건 공백, 코드/자료 권리·품종 적용 보류를 기록한다.
2. 제품 모듈을 import하지 않는 Decimal100자리 참조를 고정 자체 합성 probe로 만든다.
   일반/변곡점·대칭/크기 비례·큰 지수/중간 곱 overflow지만 최종 유한인 값을 상대1e-12/절대0으로 대사한다.
   이는 참조 probe의 수식 평가 허용차이며 작물 정확도의 기준이 아니다.
3. 잘못된 입력·현재 탄소/절간 시계 혼합·overflow/양수 underflow를 거부하고 입력 불변/재생성/hash를 확인한다.
   제품 모듈 부재 RED 뒤 구현한다. 기존 절간율·동결 형태 입력/프레임을 보존한다.
4. 보호7root와 원 자료/화면을 유지하고 .25초 감시/지정 WSL 상한 아래 집중 검증한다.
   전체 회귀·실제 농장/품종·관문/사용자3D 적용은 새로 수용하지 않는다.
