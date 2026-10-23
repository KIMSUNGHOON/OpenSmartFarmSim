# 명시 발달 순번의 영양/생식 분류 — 연구 v1

상태: [신규67/관련115·총182검사 수용](../research/crop-phytomer-kind-20261023.md).
[원문 구조/시계](../research/crop-phytomer-emergence-primary-sources-20261021.md)와
[generic 출현 사건](crop-phytomer-thermal-events-v1.md)의 후속이다.
phytomer는 절간+잎 또는 절간+화방이라는 문헌의 구분을 유지한다.
아래 순번 정책은 호출자가 명시하는 합성 가정이며 실제 Axiany 구조나 논문의 일내 알고리즘이 아니다.

## 입력과 분류

`classify_phytomer_sequences(*, inputs)`의 닫힌 입력은 `input_id`, `policy`, `sequences`다.
policy는 `origin=synthetic`, `sequence_basis=explicit_emergence_schedule`, `policy_id`, `shoot_id`,
`schedule_id`, `first_generative_sequence`, `vegetative_between_generative`만 가진다.
식별자는 기존1–200 ASCII 규칙이며 정수 두 개는 bool을 제외한0–2,147,483,647이다.
첫 생식 순번/간격과 초기 phase·품종을 기본값으로 정하지 않는다.
출현 schedule 순번은 실제 마디 rank나 최초 잎 수가 아니다. 원 schedule/shoot의 결속은 후속 adapter가 검사한다.

sequences는0–512개 순번의 list다. 원 출현 순서대로 연속·오름차순이며 각 순번은 같은 정수 범위다.
`F=first_generative_sequence`, `V=vegetative_between_generative`로 두면 다음과 같다.

```text
n < F                         → vegetative
n ≥ F and (n − F) mod (V+1)=0  → generative
그 밖                         → vegetative
```

V=0은 호출자가 선언한 연속 생식 위치의 합성 사례다. 생물학적 타당성 승인으로 쓰지 않는다.
빈 입력은 빈 분류이며 기본 잎을 추가하지 않는다. 분할은 같은 정책/절대 순번을 사용한다.
해당 배치만 분류하며 누락된 앞선 사건을 생성하거나 현재 phase를 추정하지 않는다.

## 출력과 경계

버전 `phytomer-kind-research-v1`과 연구/합성/관문 미평가 표식,
정규 모델+입력 SHA와 별도 모델+정책 SHA, 원 policy 사본과 `phytomers`를 반환한다.
항목은 `{sequence, kind: vegetative|generative}`다. 입력 순서/순번을 그대로 유지한다.
배치 input_id는 입력 지문에 포함하며 정책 지문에는 포함하지 않는다.
입력/출력은 닫힌 필드·512개 정수/유한 길이 문자열로2MiB 이하다.

generic 출현의 기온/정확 초·열적 문턱은 기존 계산이 담당한다.
이 함수는 잎·화방/꽃·과실·초기 면적/질량을 생성하거나 계산하지 않는다.
generative 위치 하나를 실제 꽃/과실 개수·착과·수확으로 바꾸지 않는다.
기존 출현/길이/잎 코드·수치/저장 판본·현재 API/사용자 화면은 변경하지 않는다.

## 수용

모듈 부재 RED 뒤 손으로 나열한 초기/주기 경계·0/큰 순번을 대사한다.
나머지 연산을 사용하지 않는 독립 상태 카운터로 여러 합성 정책을 비교하고
부분 배치의 연결이 전체 분류와 같은지, 정책 변경 시 지문/분류가 바뀌는지 확인한다.
닫힌 필드/잘못된 문자열·bool/float/음수/상한·중복/역순/누락/513개는 전체 hold다.
입력 불변·출력 별도 사본·원3root/자료·WSL 상한과 관련 기존 출현/잎 검사를 확인한다.
실제 품종 계수·독립 관측/자동 잎 생성·관리·저장/3D와 G0–G4는 별도다.
