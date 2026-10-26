# 명시 새 절간 구조 탄소의 같은 시각 조달점 — research v1

상태: [신규54/관련268·별도6문맥/독립752항목 수용](../research/crop-stem-root-funded-internode-point-20261027.md). [초기 source 연결](crop-stem-root-initial-binding-v1.md)·[기관별 재개](crop-stem-root-stock-continuation-v1.md) 뒤의 명시 구조 형성점이며 [근거/단위](../research/stem-carbon-growth-primary-sources-20261027.md)의 기존 cStemG를 사용한다. 자동 열적 출현 판정/분수 근·가변 목록 CP/연속 전진·길이 feedback은 후속이다. 숨은 조직의 재고를 드러내는 사건은 별도 이동 모델이 필요하며 이 추가 조달 정책으로 차감하지 않는다.

`apply_internode_births(context, raw_checkpoint, expected_sha256, crop_directory, stem_directory, access, *, crop_root_sha256, stem_root_sha256, stem_start_index, binding_declaration, inputs)`는 원 Context/외부 신뢰한 canonical CP bytes·SHA와 현재 원 crop/stem source를 사용한다. 실제 초기 source 연결을 호출 전/반환 전 재검증하고 그 전체 canonical 결과 SHA를 inputs.initial_binding_sha256과 맞춘다. CP의 원 context/hash·현재 상태/누적량/장부를 복원 검증한다. 자체 재해시는 권한 발급이 아니며 농장 custody는 별도다.

닫힌 inputs는 schema_version=`stem-root-funded-internode-point-input-v1`, input_id/origin=synthetic/policy=`explicit-new-internode-carbon-from-buffer-v1`, context_sha256/checkpoint_sha256/initial_binding_sha256, at_elapsed_seconds_exact/model_floor_area, events, rights/reviewer다. 실제 CP의 exact binary64 step×정수 index와 reduced seconds가 같고 원 floor여야 한다. 이는 명시된 조달 시점이며 생리적 출현 threshold를 발견했다는 주장이 아니다. rights는 초기 연결과 같은 명시 자체 권리 필드/권한을 요구하고 reviewer를 기록한다. 원 source/선언과 입력 중 하나라도 redistribute=False면 재배포 승인은False다.

각 event는 event_id/parent_internode_id/compartment다. parent는 실제 현재 목록의 internode ID여야 하며 root/새로 추가한 같은 batch 기관을 부모로 삼지 않는다. 새 compartment는 compartment_id/kind=internode/initial_carbon/sink_weight/carbon_removal이며 초기 C>0, sink/removal≥0을 명시한다. 기존과 새 ID/event ID는 중복되지 않고 총 stem/root≤512, 원 root는 하나 그대로다. 새 C/모델 floor는 mg_CH2O/m2_floor이며 길이·면적·기관 수·집계로 추정하지 않는다. 형상/초기 길이·생물학적 밀도는 여기서 승인하지 않는다.

원 pinned growth profile의 cStemG와 명시 새 질량의 정확 binary64 합계 S에 대해 structural=round(S), Rg=round(cStemG·S), debit=round((1+cStemG)·S), B_after=round(B_before−debit)>0이다. cLeafG/순 유지호흡/새 계수를 대신 쓰지 않는다. 연속 유량은 환급/재차감하지 않는다. 새 초기 구조의 추가 조달이므로 이미 지불한 연속 증가분을 새 초기 C로 다시 선언해 차감하는 모델도 아니다. 나타낸 전체 C 변화는−Rg이고 비표현 chemical heat/물질 전체 첫 법칙은 없다.

원106+3n+m 상태에서 buffer0만 바꾸고 끝에 명시 새 C들을 붙인다. 기존 모든 기관 C·leaf age/A/C·과실·기후U103/Ta104/W105·원 초기 면적/D0/anchor·root·곡선은 그대로다. leaf 면적/열용량/수관 현열의 점 변화는0이다. 현재 CP 검증 RHS1회+after RHS1회이며 과거 전진/재준비/재정규화0, 시간 전진0이다. 원 prefix/연속 장부/CP를 보존하고 새 point 전용 buffer/new-stock/whole-C 및 각 새 기관 잔차를 기존64ULP 규칙으로 검사한다.

반환은 before CP/initial binding·원 manifest/입력/권리/현재 source/code/profile hash, after program/sample/rates/layout, 부모/새 기관 영수증·point 흐름/장부/계산 hash다. CP=None이며 새로운 checkpoint/adoption/history를 발급하지 않는다. 같은 불변 입력 재평가는 같은 결과다. 반복 채택 방지/가변 목록 재개는 후속이며 이번 stateless 결과를 그대로 전진 가능한 CP로 취급하지 않는다. 입력/출력2MiB·하위 byte caps/원 최대 요청 hold 유지, 실패 시 부분 결과 없음. DB/CLI/network/write0·G0–G4=not_assessed·time_kind=synthetic_model_clock_not_observation이다.

수용: 실제 owned source의6조건/초기·후기 CP·단일/batch, original cStemG 원가/버퍼와 전체·기관별 C의 독립 Decimal 산술, 모든 비대상 상태/원 장부·source/권리 보존, 부족/누락/중복/타임·부모/root·코드/profile/late source/cap 거부, 별도 프로세스 동일 결과/호출 계측·WSL·기존 GUI/원 자료 보존이다. 자동 threshold/분수 시각 결속과 가변 목록 재개를 계획의 남은 작업으로 유지한다.

내부 `_jump(program, state, profiles, events)`는 이미 검증된 현재 데이터에 적용하는 재료점 산술이다. public wrapper가 원 source/CP/time/권리 검증을 소유한다. 후속 가변 목록 조립은 자신의 typed CP를 검증한 뒤 이 산술을 호출할 수 있으며 원 고정 Context/token을 만들어 가장하지 않는다. 내부 산술 자체는 현재 CP/시간·source 진본을 발급하지 않는다.
