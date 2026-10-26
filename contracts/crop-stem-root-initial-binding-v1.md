# 명시 초기 기관 탄소와 선택 저장 source의 결속 — 연구 v1

상태: [신규46/관련134·별도6문맥의 합성 검증 수용](../research/crop-stem-root-initial-binding-20261027.md). [기관별 재개](crop-stem-root-stock-continuation-v1.md) 뒤의 초기 source 결속이다. `bind_initial_stem_carbon(context, crop_directory, stem_directory, access, *, crop_root_sha256, stem_root_sha256, stem_start_index, declaration)`는 원 저장 개별 잎/aggregate stem 탄소의 **초기 sample0**와 실제 선택 저장 줄기를 새 Context의 초기 상태에 결속한다. 임의 중간 crop sample을 초기 면적으로 재정규화하는 채택은 제공하지 않는다.

두 root는 호출자가 외부에서 신뢰한 해시이며 기존 CAS/file-policy reader·원 코드/profile/권리/QC를 검사한다. stem_start_index는−1(원 initial_state) 또는 실제 저장 sample index다. 원 crop 상태의107+3n 벡터와 새 초기106+3n+m 벡터의 파생 aggregate projection을 **canonical 값 그대로** 대사한다. 원 요청에서 stem 집계/제거를 뺀 나머지, 정규 program·초기 면적 요청/영수증/D0·leaf ID/curve/stock·나머지 상태/forcing/단위/profile도 같아야 한다. 새 C_i는 Context에 명시된 완전한 입력이며 원 aggregate/길이/면적에서 만들지 않는다.

declaration은 닫힌 schema_version=`stem-root-initial-source-binding-input-v1`, input_id/origin=synthetic/context_sha256/crop_root_sha256/crop_initial_state_sha256/stem_root_sha256/stem_start_index/stem_source_state_sha256/time_origin_utc/model_floor_area/tracking_basis/rights/reviewer다. context/원 상태/root/index·원 crop의 합성 UTC 기준일과 실제 stem 선택 시각이 일치해야 한다. 명시 internode 행을 원 stem 순서/ID와 완전히 맞추고 정확히 하나의 별도 root_system ID를 요구한다. 원 source를 별칭으로 수리하거나 누락 기관을 생성하지 않는다.

저장 stem에는 면적/탄소 기준이 **없다**. tracking_basis는 별도 명시 선언이며 kind=`one_tracked_shoot_on_declared_model_floor_research_v1`, 원 shoot_id, 같은 model_floor_area, tracked_shoot_count={value:1,unit:tracked_shoot}다. 이는 한 추적 shoot를 명시 모델 footprint에 연결하는 자체 합성 가정이지 원 stem의 측정 면적/재식밀도/기관 실질량 증거가 아니다. 생체량 변환·다른 밀도의 자동 scale·allometry를 제공하지 않는다. 누락/미지원 basis는 hold다.

원 aggregate C/removal과 정확 binary64 개별 합계를 한번 반올림한 값을 각각 대사한다. 같으면 exact signed residual도 분수로 기록해 반올림을 숨기지 않는다. 다르면 signed 잔량·원/선언 합계를 hold evidence로 남기고 승인 결속을 반환하지 않는다. 마지막 기관/root에 잔량을 몰거나 계수를 역산·rescale하지 않는다. 잔량의 다른 재고 분류/전진은 후속 별도 모델이다.

declaration rights는 기존 자체 합성 선언의 declaration_id/revision/declared_at_utc/ownership_asserted/access/store/use/transform/display=True·redistribute(bool)와 명시 reviewer다. 양쪽 원 source 권리와 함께 검사/보존하고 하나라도 redistribute=False면 출력의 재배포도 승인하지 않는다. 이 선언 검사는 법적 권리 진본/농장 현재 권한·G0 승인을 발급하지 않는다.

한 호출 동안 두 store handle을 유지해 원/현재 root·program/선택 result·입력/권리/코드를 반환 직전 다시 대사한다. 원 Context bytes/선택 state·age/curve/anchor/length·C_i/leaf·source/notice/profile/선언/전체 계산 hash를 보존한다. 결과는 초기 식별자/명시 basis/재고 대사뿐이며 source 원 시계를 전진·재적분하거나 Context/CP를 수정하지 않는다. ODE/초기 재정규화/과거 전진·DB/CLI/network/쓰기0, 출력/선언2MiB와 하위 caps를 유지한다.

scope=software_research_only, claim=synthetic_initial_stored_source_identity_and_declared_footprint_binding_only, time_kind=synthetic_model_clock_not_observation, G0_G4=not_assessed이며 길이 feedback/실제 품종/생물학적 초기 정합/농장 승인은 없다. 원 stem의 floor 부재·명시 가정·현재 권리/원본 변경과 미배정 hold를 결과/증거에서 숨기지 않는다.

수용: 실제 owned crop/stem CAS의 초기/후기 선택·원 완전한 IDs/시각/footprint 선언·원 나머지 요청/상태/영수증·profile·독립 정확 합계/잔량/0·rights/code/hash/late file/directory/단위/순서·원 잘못된 mapping 보존/hold·fresh 원 bytes·growth/외부 side effect0·원 코드/자료/GUI/WSL 보존이다.
