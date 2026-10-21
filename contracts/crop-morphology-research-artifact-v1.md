# 합성 형태 계산의 불변 artifact와 typed 재생 — v1

상태: [새26/기존286검사로 내부 합성 경로 수용](../research/crop-morphology-research-artifact-20261022.md). 선행은 [기관 목록 계산](crop-shoot-internode-inventory-v1.md)과
[내용 주소 파일](crop-morphology-artifact-io-v1.md)이다. 자체 합성 소프트웨어 fixture 전용이며
농장/테넌트 등록·현재 원천 권리·독립 승인이나 제품 Run 게시를 대체하지 않는다.

## 입력/producer

`produce_morphology_artifact(directory, access, *, program_raw)`는 canonical UTF-8 JSON16MiB 이하를 받는다.
닫힌 program 필드는 `schema_version=morphology-software-program-v1`, `origin=synthetic`,
`program_id`, `rights`, `initial_state`, `segments`, `output_times`다.
initial_state는 명시 기관 목록 계약 그대로다. 기온 구간은 원1–512개, 출력 시각은
현재 시각보다 큰 whole-second UTC1–64개·중복 없는 오름차순이며 마지막 시각은 원 구간 끝이다.
모든 구간을 소비하며 임의 보간/자동 초기조건·실제 자료 대체는 없다.

rights는 `declaration_id`, `revision`, `declared_at_utc`와
`ownership_asserted/access/store/use/transform/display=true`, `redistribute:boolean`이다.
선언은 자체 합성 프로그램에 관한 것이며 원측정 이용 가능 시각·G0 승인 서명이 아니다.
source/관문 상태는 미평가다. 공개 fixture export에는 redistribute=true가 별도로 필요하다.

producer는 같은 원 구간을 출력 시각에서 나누어 기존 결정적 계산기를 순서대로 실행한다.
입력/각 전체 결과/마지막 root를 원 bytes의 내용 주소 파일로 보관한다. root는 모든 시점 보관 뒤에만 반환한다.
원 bytes·모델/의존 코드 SHA-256·입력 state/단계/결과 state의 hash chain과 원 UTC를 보존한다.
같은 입력/코드의 재생성은 같은 root다. 내부 producer 재호출은 계산을 다시 수행할 수 있으나
파일을 덮어쓰지 않는다. 공개 접수/작업 멱등성·중단 producer의 자동 재개는 이 내부 export의 수용 범위가 아니다.
실패 중 남은 비공개 내용 주소 객체는 완성 artifact/정상 prefix로 게시하지 않는다.

## root/reader

root는 `schema_version=morphology-research-artifact-v1`, `scope=software_research_only`,
`claim_scope=synthetic_crop_math_only`, `gates=not_assessed`, `status=completed_software_fixture`,
`time_kind=synthetic_model_clock_not_observation`를 고정한다.
program SHA/bytes·initial state SHA, program rights,8개 model_versions·의존 코드 지문,
원 논문/권리·명시 합성 매개변수 경계, samples descriptor와 terminal state SHA를 포함한다.
각 descriptor는 `index,at,result_sha256,result_bytes,input_state_sha256,state_sha256,input_sha256`다.
직전 출력 state hash가 다음 입력 state hash여야 한다. root128KiB/전체 파일64MiB/시점 결과2MiB 상한이다.

`read_morphology_manifest(directory, access, root_sha256)`와
`read_morphology_frame(directory, access, root_sha256, *, index)`는 **호출자가 신뢰한 root SHA**를 필수로 받는다.
root/원 program/선택 결과의 canonical bytes·hash·연결/모델/형식·단위·UTC를 대사한다.
프레임은 같은 원 UTC/ID·순번·출현 UTC/나이·원 length quantity와 원 tracked_axis_length를 제공한다.
readonly DTO는 `schema_version=morphology-replay-frame-v1`, 기존 scope/claim/gates·root/result/input SHA,
`index,at,shoot_id,internodes,tracked_axis_length`다. 기관 항목은
`sequence,internode_id,emerged_at,birth_age_exact,age_exact,length`만 포함한다.
잎/화방/과실·숙기·생산/수익과 실제 키는 만들지 않는다.

reader는 생장 모듈을 import/실행하거나 F(a)·신장 적분·기관 생성·길이 합계를 다시 계산하지 않는다.
숫자/단위/순서/유리수의 형식 검사는 transport QC다. root는 단독으로 농장 게시 권한/독립 진실성 서명이 아니다.
같은 OS owner가 모든 파일/신뢰 root를 새로 위조하는 것을 이 계층에서 인증하지 않는다.

## 수용

원 시점/값/길이/해시·단계 연결과 동일 재생성, 모델 호출0/DB 연결0·별도 프로세스의
생장 모듈 import0을 확인한다. 원 bytes/연결/미지원 모델/관문·권리·파일 변조와 크기/순서 오류,
0으로 채운 초기조건/소수 초 출현 보류·실패 시 정상 root 없음, 원6서비스/WSL 상한과 기존286검사를 유지한다.
최초 예시는 기존 자체 합성 fixture로 검증하며 실제 Axiany 초기/계수·독립 관측은 미확보다.
