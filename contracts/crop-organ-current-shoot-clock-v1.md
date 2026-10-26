# 현재 개별 기관 CP와 저장 초기 줄기의 열적 시계 — research v1

`derive_current_shoot_clock(context,raw_checkpoint,expected_sha256)`는 [개별 기관 재개](crop-organ-funded-continuation-v1.md)의 실제 Context와 외부 신뢰 raw CP SHA를 검증하는 읽기 전용 연구 계산이다. [기존 저장 초기 시계](../backend/app/crop_funded_shoot_clock.py)의 signed/no-clip 방식을 새 상태 배치에 결속한다. 현재 CP 검증의 RHS1회만 수행하고 과거 적분·point 채택·면적 초기화·상태 변경은0이다.

원 crop/stem 선택·선언·권리·code/profile/환경과 현재 global step/exact elapsed/prefix·원 lifetime `indoor_air_temperature_time` (`degC_s`)를 보존한다. 실제 선택 source state의 발달 시작 UTC와 시뮬레이션 시작 UTC를 구분한다. shoot/초기 internode 나이는 각 저장 초기 나이에 `(I_air − T_base × elapsed)/86400`을 더한다. 저장 float64 적분을 Fraction으로 정확 변환하며 해석해/관측이라고 부르지 않는다. 음의 변화를 자르지 않고 결과 나이가 음수면 hold다.

명시 추가 internode는 실제 순서 있는 point history의 event/ID/부모·시각·air integral을 기준으로 `(I_current − I_point − T_base × (t_current − t_point))/86400`을 계산한다. 기준은 `since_declared_material_point`이며 선택 shoot의 기준온도를 사용한다. 선언 시각을 생리적 threshold 출현으로 승격하지 않는다. 초기 internode의 원 emergence 정보는 변경하지 않는다. root_system은 보존하지만 shoot/internode 시계를 부여하지 않는다.

입력 CP/Context·C/A/기존 leaf 나이·D0·장부·원 source bytes를 변경하지 않는다. 단위·비유한값·순서·완전한 ID 대응·나이·원점·source/권리/code/profile의 늦은 변경·결과2MiB를 검사하고 마지막 source fence를 통과한 결과만 반환한다. 원 CP512KiB와 모든 부모 상한을 유지한다. 계산 SHA는 서명/독립 custody를 대신하지 않는다.

수용 기준: 실제6조건 선택 초기 줄기·양쪽 point·초기/중간/완료 CP·복수점/동일 시각 순서·독립 정확 산술·별도 프로세스 재독·RHS1/재실행0·변조/단위/음수/늦은 변경 hold·원 자료/GUI/WSL 보존이다. `software_research_only` / `synthetic_model_clock_not_observation` / G0–G4 `not_assessed`와 원 `redistribute=False`를 유지한다. 자동 interval threshold/분수 후보·탄소 공급 제한 형상·실제 품종/작기/생산·자원/경제·저장3D 연결은 후속이다.
