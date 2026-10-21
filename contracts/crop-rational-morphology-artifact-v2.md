# 정확 출현 시각의 불변 형태 artifact — v2

상태: [505집중 검사/실제 별도 조회 수용](../research/crop-rational-morphology-artifact-20261022.md).
[정확 시각 기관 목록](crop-rational-shoot-inventory-v1.md)과
[기존 파일 운송](crop-morphology-artifact-io-v1.md)을 사용한다.
v1 producer/reader·공개12프레임을 바꾸지 않는 별도 프로그램/root/DTO 판본이다.

`produce_rational_morphology_artifact(directory,access,program_raw=...)`는 닫힌 canonical JSON16MiB 이하의
`schema_version=morphology-software-program-v2,origin=synthetic,program_id,rights,initial_state,segments,output_times`를 받는다.
rights는 자체 제작 선언 ID/판본·UTC와 ownership_asserted/access/store/use/transform/display=true,
redistribute:boolean이다. 농장 원천 자료 승인/현재 권리·서명이 아니다.
초기 상태는 정확 목록의 명시 기관/anchor이며 원 AIR1–512구간과 출력 whole-second UTC1–64시점을 검증한다.
같은 원 구간을 출력 시각에서 나눠 수용된 계산기를 실행하고 입력/전체 결과/root를 내용 주소에 보관한다.

root는 morphology-research-artifact-v2와 software_research_only/synthetic_crop_math_only/not_assessed,
completed_software_fixture·synthetic_model_clock_not_observation·synthetic_software_fixture_only를 고정한다.
원 입력 bytes/hash·초기/각 단계/terminal state chain, 원 UTC/결과 bytes/hash·입력 지문,
실제 의존 모델/adapter 판본과 코드 SHA·논문 출처/합성 계수 경계를 보관한다.
현재 지원 판본은 AIR/point/유리수 clock·length/emergence/timeline/AIR adapter/새 기관/목록의9개와 의존 코드17개다.
root128KiB/시점2MiB/파일 전체64MiB 상한과 같은 환경/입력/코드의 동일 root·덮어쓰기 거부를 유지한다.
후속 단계 실패로 남은 비공개 객체를 completed/prefix로 게시하지 않는다. 자동 중단 재개/제품 접수는 별도다.

`read_rational_morphology_manifest(directory,access,root_sha256)`와
`read_rational_morphology_frame(directory,access,root_sha256,index=...)`는 호출자가 신뢰한 root를 받는다.
원 bytes/hash·지원 판본/관문·권리·상태 chain·선택 결과 형식/단위/원 UTC를 확인한다.
UTC 원점+정확 유리수 출현/현재 초와 anchor를 형식/QC 대사하며 출현 UTC를 추정/반올림하지 않는다.
길이/합계의 원 값만 조회하며 생장 모듈 import/호출·F(a)/기온 적분/기관 생성/축 길이 합계 재계산은0이다.
이 조회의 분수/시각·순서 비교는 transport QC이며 모델 계산이 아니다.

DTO는 morphology-replay-frame-v2, 기존 flags/root/result/input SHA/index/at/shoot_id/추적 축 합계와
time_origin_utc를 갖는다. 기관 항목은 sequence/internode_id/emerged_elapsed_seconds_exact/birth_age_exact/age_exact/length다.
v1의 emerged_at 필드를 가짜 UTC로 채우지 않는다. 잎/과실/키·생산/수익을 생성하지 않는다.

수용: 소수 초 출현을 포함한 원 결과/상태/길이/원점·정확 초와 원 UTC, 단계 chain/같은 root·파일,
fresh 조회의 성장 import/모델 호출/DB0·변조/미지원/크기 보류·후속 실패의 정상 root 부재,
역사 v1 root/12프레임 bytes와 기존473검사/원6root다. 공개 export/3D와 농장 custody/실제 품종/독립 관문은 별도다.
