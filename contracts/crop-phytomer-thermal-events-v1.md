# 공통 발달 시계의 phytomer 문턱 사건 — 연구 v1

상태: 합성 문턱 사건 새34/기존170검사 수용. [원문 의미와 미확인 초기조건](../research/crop-phytomer-emergence-primary-sources-20261021.md)을 따른다.
한 절간 길이와 독립인 **generic phytomer 출현 순서**만 계산한다. 잎/화방 개수·실제 키·생장 예측은 없다.

## 닫힌 순수 입력

`advance_phytomer_emergence(*, inputs)`는 `input_id`, `state`, `end_age_exact`를 받는다.
state는 `origin=synthetic`, `age_basis=since_shoot_development_origin`, `shoot_id`,
`development_origin_id`, `schedule_id`, `at_age_exact`, `next_threshold_exact`,
`phyllochron_exact`, `next_sequence`만 포함한다. 식별자는 기존1–200 ASCII 규칙이다.
나이/문턱/간격은 `{numerator,denominator,unit:degC_day}`의 음이 아닌 기약 유리수 문자열이다.
각 정수는1–1024자리이며 분모는 양수다. 간격은 양수, 다음 문턱은 현재 나이보다 커야 한다.
종료 나이는 시작 이상이다. 순번은 명시한0–2,147,483,647 정수다(bool 제외).
순번0이나 최초 문턱/P·최초 기관 개수를 자동 선택하지 않는다.

## 사건/재개

`q_j = next_threshold + j*phyllochron` 중 `(at_age,end_age]`만 포함한다.
사건은 `{sequence,thermal_age_exact}`이며 문턱 오름차순·연속 순번이다.
한 호출 최대512사건을 **초과하면 전체 hold**하며 일부를 정상으로 잘라내지 않는다.
다음 순번이 정수 상한을 넘거나 정확 carry가 자리 상한을 넘을 때도 hold다.
상한은 소프트웨어 처리 예산이며 생물학적 제한이 아니다.

출력은 `model_version=phytomer-thermal-events-research-v1`, 기존 합성/연구/관문 미평가 표식,
정규 입력 SHA-256, `events`, 새 `checkpoint`다. checkpoint는 같은 식별자/시계/간격을 유지하며
현재 나이와 다음 문턱/순번만 전진한다. 같은 문턱까지 분할한 실행은 사건 연결/최종 상태가 전체 실행과 같다.
0증가는0사건이며 같은 시작 문턱을 재처리하는 상태는 거부한다.

## 수용과 남은 경계

독립 정수 공통격자/반복 나열 기준으로 직전/같음/직후·다중/분수·큰 나이의 작은 변화·아주 작은
정확 문턱을 대사한다. 분할합/중복0·512/513/순번·기약/단위/타기관 시계 혼합·입력 불변과
기존170집중검사, 원6서비스/WSL 상한을 확인한다.

UTC/기온 역변환, 최초 기관 목록·새 절간 초기 길이와 전체 길이 합, leaf/truss·가지/유인/내림,
저장/현재 권리/같은 UTC3D와 실제 Axiany 계수·독립 검증은 별도다. 이 함수는 UTC를 만들지 않는다.
공통 발달 시계의 처음 phase는 호출자가 명시한 합성 가정이며 실제 계측이나 승인 자료가 아니다.

원 RED/자원·지문과 독립 기준은 [수용 증거](../research/artifacts/crop-phytomer-thermal-events-20261021.json)에 있다.
