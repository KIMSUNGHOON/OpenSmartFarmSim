# 한 절간의 순간 신장률 — 연구 v1

상태: [49개 집중/20개 독립 참조의 연구 커널 수용](../research/tomato-morphology-primary-sources-20261021.md#부모의-현재-코드-대조와-커널-수용).
[원문·단위·적용성 검토](../research/tomato-morphology-primary-sources-20261021.md)의
Smoleňová 등(2025), DOI `10.1093/insilicoplants/diaf022`, §2.5.3 Eq(4)를 직접 작성한다.
논문의 CC BY4.0 출처를 표시하며 권리 미확인 저자 저장소의 코드/자료를 가져오지 않는다.

## 개발 경계

`backend/app/crop_internode_elongation.py`의 `calculate_internode_elongation(*, inputs)`는
열적 나이 한 점의 **m/degC_day**만 계산한다. solver·저장/API·3D에 연결하지 않는다.
현재 탄소 모델의 수관 온도 합은 이 식의 기관 출현 이후 기준온도 thermal clock이 아니다.
시간 적분, 초기 길이, 절간 생성/phyllochron, 절대 키·수직 높이와 기관 배치는 후속이다.

입력은 정확한 `input_id`, `origin=synthetic`, `thermal_age_basis=since_internode_emergence`,
`values`다. ID는 1–200자의 기존 ASCII 식별 형식이며 아래 네 quantity를 각각 한 번 받는다.
실제 자료/품종 프로필은 이 판본의 입력 범위가 아니다.

| quantity | 단위 | 계산 정의역 |
| --- | --- | --- |
| `thermal_age` | `degC_day` | 유한·비음수 |
| `maximum_length` | `m` | 유한·양수 |
| `steepness` | `1/degC_day` | 유한·양수 |
| `inflection_age` | `degC_day` | 유한·비음수 |

각 quantity는 정확히 `{value, unit}`이며 bool·문자 수치·추가/누락 필드·단위 혼합을 거부한다.
이 범위는 수학적 평가 범위다. 원 Table1의 최적화 탐색 구간이나 타품종 보정값을
Axiany의 생물학적 유효 범위/기본값으로 채택하지 않는다.
원 표의 `klen` 단위 `–`와 별개로 지수의 차원상 필요한 `1/degC_day`를 사용한다.

```text
z = steepness * (thermal_age - inflection_age)
dL/d(thermal_age) = steepness * maximum_length * exp(-z) / (1 + exp(-z))^2
```

큰 음/양의 z에는 동등한 log-domain 평가를 쓴다. 비유한 중간값·출력 overflow 또는
양의 참값이 binary64의0으로 underflow하면 `InternodeElongationHold`다.
clip·임의0·기본 계수로 바꾸지 않는다. 변화율은 시간당/하루당 길이와 다르다.

출력은 `model_version=internode-logistic-thermal-rate-research-v1`,
`scope=software_research_only`, `claim_scope=synthetic_crop_math_only`, `gates=not_assessed`,
정규화한 입력/모델의 SHA-256과 `elongation_per_thermal_age {value, unit:m/degC_day}`다.
입력을 바꾸지 않으며 초기/현재 길이·키·개화·과실·숙도·수확은 생성하지 않는다.

## 수용

1. 원 논문 Eq(4)·기관별 열적 나이·차원과 현재 모델 상태의 부재를 실제 원문/코드로 대조한다.
2. 제품 함수를 import하지 않는 Decimal 100자리 원식 계산으로 고정 합성 참조를 만든다.
   일반/변곡점/대칭·큰 지수에서의 유한 결과를 relative `1e-12`, absolute0으로 대사한다.
   이는 binary64 수식 평가의 허용 오차이며 작물 정확도의 기준이 아니다.
3. 변곡점 최대값 `steepness*maximum_length/4`, 대칭, 잘못된 provenance/단위/입력과
   overflow/underflow 거부, 입력 불변·재현 hash를 검사한다. 실패 재현 후 구현한다.
4. 원6서비스·입력/저장 결과를 보존하고 기존 WSL 상한 아래 집중 검증한다.
   전체 회귀·시간 적분·실제 품종/3D·독립 농장 수용은 별도로 보고한다.

이 연구 커널의 수용은 실제 관측·매개변수 승인이나 G0–G4 해제가 아니다.
