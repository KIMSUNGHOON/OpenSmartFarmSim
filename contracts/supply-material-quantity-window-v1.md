# 저장 material 창의 모형 과실·연속 자원 수치 v1

상태: [41검사·실제 별도 조회·보존](../research/supply-material-quantities-20261031.md)의 수치 조회 수용.
[수용된 원 저장 창](supply-material-public-replay-v1.md)의 읽기 전용 파생이다.
`read_material_quantity_window(directory, access, root_sha256, *, first_frame=0, last_frame=None)`는
기존 material reader의 같은 owned store에서 source/권리·code·frame/수지 검증을 먼저 수행한다.
이 root는 trusted producer 또는 고정 공개 inventory에서 선택한 것이어야 한다.
임의 농장 root의 custody나 G0–G4를 승인하지 않는다.

원 index·시각·phase/source/cursor/event sequence, 원 frame/state SHA·state kind를 보존한다.
옛 Context/CP 참조를 만들지 않는다.50과실 구획의 원 탄수화물/수량 좌표와 binary64를 정확하게
나타낸 Fraction 합계, 다음 연속 lifetime counter를 같은 frame에 결속한다.

| Counter | 단위 | 원 모델 정의 |
|---|---|---|
| terminal_carbon / terminal_number | mg_CH2O/m2_floor / fruits_equivalent/m2_floor | 구획 끝의 모형 유출 누적량 |
| sensible / latent | J/m2_floor | exchange의 현열/잠열 전달 적분량 |
| incoming_heat / outgoing_heat | J/m2_floor | capacity_transport의 유입/유출 열 전달 적분량 |
| canopy_external / air_external | J/m2_floor | 원 forcing의 canopy/air 외부 열 적분량 |
| vapor / external_vapor | kg_water/m2_floor | exchange의 수증기 및 원 forcing의 외부 수증기 적분량 |

원 정의는 `crop_growing_geometry_climate._flux`와 `crop_explicit_lai_climate_rhs`다.
부호 있는 resource 누적량을 절대값/양수 구매량으로 바꾸지 않는다. terminal 누적량은 비음수이며
시간에 따라 감소하지 않아야 한다. 원 floor basis와 단위를 유지하며 총 농장량으로 곱하지 않는다.

포함된 첫/끝 index 창에 대해 인접 interval은 정확 시간차와 각 lifetime의 정확 차다.
같은 정확 시각은 실제 `material_before`→`material_after`이며 event sequence가 한 번 증가하고,
원50구획 저장량과 선택한 연속 counter가 같아야 한다.0시간 경계도 별도 interval로 남긴다.
각 counter의 interval 합은 선택한 양끝 차와 정확히 같아야 한다. 한 frame 창은 interval0/합계0이다.

잘못된 bool/float/index·layout·단위/비유한/음수 stock·양수 C와0수량·시간 역전/거짓 phase/
감소 terminal·source/code/현재 embedded 권리와 늦은 변조를 거부한다. use/display가 필요하며
redistribute 상태는 원 그대로 유지한다. 응답2MiB·기존 frame/scalar/source 한도를 유지하고
최종 code/source fence를 통과한 방어 복사만 반환한다. 새 RHS/모델 전진·CLI/DB/network/CAS 쓰기는 없다.

이 값은 과실 개체 ID·숙기·생과 무게/수확·판매나 관개·난방/전력 구매·요금·마진을 뜻하지 않는다.
`software_research_only` / `stored_synthetic_material_quantities_only`, 원 합성 모델 시계와
G0–G4 `not_assessed`/R2 `not_approved`를 유지한다. 공개 DTO/SDK·같은3D 패널과 실제 품종/
경제·거시/수급·자율 비교는 후속이다.
