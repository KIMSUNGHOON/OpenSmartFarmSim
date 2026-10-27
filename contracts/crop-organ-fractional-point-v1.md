# 실제 분수 후보의 첫 기관 탄소 조달점 — research v1

`apply_fractional_material_point(context,raw_checkpoint,expected_sha256,time_tolerance_seconds_exact,inputs)`는 [새 분수 후보](crop-organ-fractional-candidate-v1.md)를 실제로 계산한다. inputs는 schema/input ID/origin/policy·실제 Context/CP/candidate/initial binding SHA·exact 시각/공통 floor·원 source event/threshold/sequence·현재 부모·새 internode/optional leaf 선언·권리/reviewer의 닫힌 객체다. 후보 SHA/시각/원 첫 미소비 기준이 다르면 거부한다. 생물학적 초기 질량을 기본 생성하지 않는다.

원 `crop_rational_new_internodes`의 논리 entity `(shoot_id,development_origin_id,schedule_id,started_at,sequence,birth_age_exact)`와 digest를 재사용해 새 `internode:<digest>`를 만든다. 실제 출현 후보 시각은 고정22도 forcing의 과거 시각과 구분한다. event ID는 `shoot-event:<digest>`이고 subevent `/internode`, `/leaf`를 구별한다. optional leaf는 같은 entity에 `organ=leaf,slot=0`을 더한 자체 research ID 정책이다. 한 수치 사건에 절간1개·명시 잎0/1개만 허용하며 품종 형태/잎 수 검증으로 부르지 않는다.

부모는 실제 현재 inventory의 internode로 명시한다. Root와 임의 placeholder·같은 점의 자기 부모는 허용하지 않는다. 이 선택을 검증된 해부학적 axis 배치로 승격하지 않는다. 새 leaf가 있으면 새 internode에 연결한다. 원 source/history의 event 또는 새 기관 ID가 이미 있으면 hold다. 같은 before/input의 읽기 전용 재계산은 같은 결과를 반환하며 그 자체가 일정/기관 채택이나 두 번째 차감은 아니다.

기존 새 벡터 `_jump` 두 개를 원 p/실제 dense state/현재 profile/D0에 적용한다. 순서는 internode→optional leaf다. 각 명시 C에 원 cStemG/cLeafG를 적용해 해당 subevent 비용을 한 번씩 buffer에서 차감한다. 부족/비영 underflow·소실 debit은 hold이고 전체 결과를 발급하지 않는다. 두 번 반올림되는 순차 buffer와 per-kind 비용을 보존하고 합성 비용률을 만들지 않는다. old107 CP/handle/public point를 가장하지 않는다.

원 C_i/leaf age/area/과실·기후/D0와 root 하나를 보존한다. 새 internode C만 append하고 새 leaf만 age0/canonical F(0)/명시 C로 초기화한다. leaf ΔK/유입 현열과 U103은 원 leaf 점 산술을 따른다. 새 leaf를 제외한 현재 면적/곡선/초기 영수증을 다시 초기화하지 않는다. 새 stem 길이/공급 제한 형상은 계산하지 않는다.

per-kind 원 flow/영수증/장부와 합산 float/정확 flow를 함께 기록한다. buffer·whole C·new/aggregate stem C·new leaf C·K/U·air/vapor/과실수/reduced energy의 exact point residual을 원 `64*ULP(max(abs(terms)))` 예산으로 검사한다. source prefix/pending 연속 장부는 그대로 보존하며 post-point global checkpoint로 채택하지 않는다. 원 상태/단위·event identity/현재 source/권리/code/profile의 늦은 변경·2MiB와 부모 cap을 유지한다. 단계 실패/RHS/domain/수지/한도에 부분 결과를 발급하지 않고 RuntimeError는 숨기지 않는다.

후보37+internode1(+leaf1)=38/39 RHS다. 과거 전진·기존 초기화·geometry 초기화·DB/CLI/network/쓰기·일정 채택·새 integrator CP0이다. 원 exact 시각은 전후 같고 새 기관 나이는 명시 numerical material point 기준0이다. 생리적 정확 출현 시각/실제 관측으로 부르지 않는다.

수용: 실제 single/mixed 후보·양쪽 원 source/원 canonical ID·명시 C/T·원 비용 한번/순서와 buffer 부족·point 전후 exact C/K/U/기타 상태·동일 입력 재현·중복/부모/단위/순번/시각/source/권리/late/cap·독립 산술/fresh/no effects·자료/GUI/WSL 보존이다. 후속은 별도 exact birth/time/일정 소비·Context/CP/원 격자 잔여/분할 재개이며 G0–G4/R2/생산·추천 승인은 별도다.
