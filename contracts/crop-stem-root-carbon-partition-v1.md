# 줄기·뿌리 성장 예산의 명시 기관 배분 — 연구 v1

상태: [58집중 검사·독립 fresh72조건 수용](../research/stem-root-carbon-partition-20261027.md)의 순수 산술 자식. [1차 근거 조사](../research/stem-carbon-growth-primary-sources-20261027.md)의 상대 sink 개념을 참고한 프로젝트 정책이다. 원 논문의 생리적 배분 법칙이나 탄소 제한 절간 신장을 재현했다고 주장하지 않는다.

## 첫 계산과 단위

`calculate_partition(*, inputs, growth_profile)`는 기존 고정 `crop_growth_rates.ReferenceParameters`의 `cStemG`를 사용한다. 입력은 닫힌 `input_id`, `origin=synthetic`, `policy`, `model_floor_area`, `requested_stem_root_growth`, `compartments`다.

- `model_floor_area`: 양의 `m2_floor`. 모든 유입은 이 동일한 footprint의 면적당 값이다. 포기당 질량으로 바꾸지 않는다.
- `requested_stem_root_growth=G`: 상위 `allocation.stem_root`의 구조적 탄수화물 유입, `mg_CH2O/m2_floor/s`. 유지호흡/제거 전이며 `derivatives.stem_root`가 아니다. buffer 차감은 이미 `G+cStemG*G`를 포함한다는 조건이다.
- `compartments`: 원 순서의 1–512개 고유 `compartment_id`, `kind`와 비음수 `sink_weight`(`1`). `kind`는 `internode` 또는 `root_system`이며 정확히 하나의 뿌리계 구획을 명시한다. 기관 ID와 가중치를 기본값으로 만들지 않는다.

상대 가중치는 명시한 합성 우선순위다. 절대 수요 상한·현재 C 재고·건물/생체량·밀도·SLA·길이/반지름 계수가 아니다. 현재 모델의 줄기+뿌리 합계를 줄기에만 배분하지 않는다. 원 모델의 다른 조직과 실제 기관 목록의 대응은 후속 source/재고 결속의 검토 조건이다.

## 결정적 정책

정책 ID는 `explicit-stem-root-sinks-and-empty-deferral-v1`이다. `W=Σw>0`이면 `g_i=G*w_i/W`, 실현 성장 F=G, 미사용 D=0이다. `W=0`이면 모든 g_i/F=0, D=G다. 원 binary64 값의 정확한 유리수 비율을 계산해 각 유입을 한 번 반올림한다. 양수 유입·호흡의 0/subnormal 유실이나 overflow는 hold다.

모든 sink가 0인 경우의 보류/환급은 프로젝트의 명시 정책이며 논문에서 검증된 처리라고 주장하지 않는다. `c=cStemG`로 요청/실현/회피 성장호흡은 각각 `cG/cF/cD`다. 상위 상태를 직접 바꾸지 않고 다음 세 조정량을 반환한다.

- buffer 미분: `+(D+cD)`
- aggregate stem_root 미분: `-D`
- 전체 성장호흡: `-cD`

상위 결합은 세 조정을 함께 한 번 적용해야 한다. 이미 차감한 cG를 다시 부과하지 않는다. 배분 합계·G=F+D·호흡 분해·환급·세 조정 합계 0과 전체 원 비용/실현 유입의 수지를 검증한다. `64(n+8) ulp(scale)`은 계산 반올림 예산이며 생물학적 오차 기준이 아니다.

입력/출력 각128KiB, ID 최대200 ASCII 문자, 유한 비음수 정상 binary64/0·bool 제외의 닫힌 형식을 적용한다. 원 입력/정규 입력·코드/기존 source/프로필/정책 SHA와 원 기관 순서·단위·모든 수지/조정을 반환한다. 입력/프로필을 수정하거나 성장 함수를 재호출하지 않는다.

## 수용 기준과 남은 의존성

독립 Decimal 참조와 원6개 합성 RHS의 실제 stem_root 성장 요청·비용으로 0/양수 G, 전부0/일부0/상대 sink, 순서/공통 배율, 명시 root, 512/bytes cap·수치 유실·변조/불변성을 검증한다. 실제 상위 수지에 세 조정을 대입하고 개별 조정만 적용할 때의 반례를 확인한다. 별도 프로세스의 함수 호출과 기존 자료/GUI·WSL 보존을 대사한다.

이 첫 계산은 **순간 성장 유입량만** 다룬다. 초기 stem_root C를 각 기관에 분배하지 않으며 초기 잔량이 모두 기관 재고로 표현됐다고 주장하지 않는다. 유지호흡·제거·고갈, 새 절간의 초기 질량/순간 비용, 공동 RK4/재개와 기존 source ID/현재 권리 결속은 후속이다. 초기 재고를 도입할 때는 명시 기관/뿌리 재고와 원 aggregate의 일치 또는 미배정 잔량의 별도 추적이 필요하다.

길이와 건물량을 별도로 모델링하는 원문을 탄소→길이 피드백 근거로 바꾸지 않는다. 공급 제한 법칙의 개발은 명시 합성 조건·독립 수지 검산으로 진행할 수 있다. 실제 품종 신장의 주장에는 해당 품종/단계의 질량–형태 관계(실측 allometry 또는 근거화한 단면/밀도 모델)·성장 비용과 초기 상태의 독립 근거가 필요하다. 기존 QA 면적/절간 비율과 열적 나이 이력은 자동 보정하지 않는다. 새 계수/품종 자료 채택·농장 승인·실제 생장/생산/자원·경제/추천은 없다. `scope=software_research_only`, `claim_scope=synthetic_stem_root_partition_math_only`, `G0_G4=not_assessed`를 유지한다.
