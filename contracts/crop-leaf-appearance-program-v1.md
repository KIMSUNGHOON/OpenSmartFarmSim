# 초기 잎/정책을 묶는 자동 출현 program — 연구 v1

상태: [신규46/관련269·총315검사와 원본 준비/호환 계산 수용](../research/crop-leaf-appearance-program-20261023.md).
[원 출현→잎 입력](crop-stored-shoot-leaf-birth-inputs-v1.md) 뒤의
합성 program 작성 단계다. 기존 저장/서명/worker와 완료 결과는 보존한다.

## 원 입력과 계산 없는 파서

`leaf-appearance-software-program-v1`의 닫힌 필드는 schema_version/origin/program_id/rights/stem/
initialization/policy/leaf_profile/display_policy다. origin=synthetic이며2MiB 이내 canonical UTF-8 JSON bytes다.
권리·원 stem root/program SHA·초기 population 입력은 기존 계약의 닫힌 형식을 사용한다.
정책과 새 잎 프로필은 위 출현 입력 계약처럼 모두 필수다. `redistribute=False`는 내부 처리와 구분한다.
display_policy는 기존 제작 삼각형/단면 면적 대응과 같고 leaf_count=`computed_from_explicit_phytomer_policy_v1`다.

`parse_leaf_appearance_program(program_raw=...)`는 형식/단위·원점·필수 가정/권리만 검사한다.
생장/분류/준비 모듈을 import하거나 곡선/기온을 평가하지 않는다. 농장·실제 자료 또는 policy의 승인을 발급하지 않는다.
별도 fresh에서 생장 import/DB/CLI/파일쓰기0을 확인한다.

## 전체 준비와 초기 결속

`prepare_leaf_appearance_program(stem_directory, access, program_raw=...)`는 위 parser 뒤
원 stem의 manifest/program·모든 sample bytes를 확인한다. parent의17소스와 현재 고정 code가 같아야 한다.
현재 준비/분류/입력 작성과 기존28소스의32개 지문을 시작/계산 전/반환 전에 대사한다.

초기 population은 기존 초기화로 검증한다. 원 UTC 원점/초기 정확 초가 원 stem과 같아야 한다.
초기 절간 순번을 같은 정책으로 분류하고, 영양 위치마다 정확히 잎 한 개를 원 순서대로 요구한다.
누락/중복·순서 변경·다른 부착/생식 위치의 잎은 보류하며 기존 잎을 자동 삭제/추가하지 않는다.
각 leaf ID는 고유하며 출현 정확 초는 원 부모의 출현 초와 같아야 한다.
초기 잎의 열적 나이·곡선/면적·기준온도는 명시 입력이다. 줄기의 나이에서 잎 나이를 복원하지 않는다.
이 판본은 기존 kernel의1–512 초기 잎을 지원한다. 빈 초기 잎을 자동 생성하지 않는다.

그 뒤 저장 전체 구간에서 위 builder로 영양 위치의 새 선언을 만든다.
초기+새 ID의 고유성과 총512개, 초기 잎의 이후 기온 정의역도 확인한다.
기존 `leaf-population-software-program-v1`을 계산용 출력으로 작성하고 기존 reader 형식과 대사한다.
모든 선언은 원 policy/profile·source program과 묶으며 생성 목록만 단독으로 승인하지 않는다.

## 출력과 다음 저장 경계

버전 `leaf-appearance-program-preparation-research-v1`과 연구/합성/관문 미평가 표식,
원 source program SHA/크기·생성 program SHA/본문·모델/32code·초기 state/결속 SHA와
전체 파생 입력/사건을 반환한다. 같은 원 bytes/코드/원본은 같은 결과다. 시간·ID·매개변수를 자동 선택하지 않는다.
반환 직전 원본 모든 sample bytes와 code를 다시 확인하며 파일/SQL/CLI·성장 advance는0이다.
입력/출력은 각각2MiB 이하다.

다음 producer는 원 source program과 이 파생 증거·생성 program/계산 root를 같은 별도 불변 판본으로 묶어야 한다.
이 준비 결과나 기존 v1 계산 root만으로 자동 출현 원본의 조회/게시 수용을 대신하지 않는다.
새 불변 producer/무계산 reader·SDK/같은 UTC3D와 실제 품종/관리·생산/자원/경제는 후속이다.

## 수용

실제 모듈 부재 RED 뒤 원14blob의 초기3/영양2새 선언·같은 SHA를 대사한다.
초기 영양/생식 혼합 정책과 정확 초기 부착/시각·독립 생성 목록, 초기/새 충돌·권리/코드/원본 변경을 확인한다.
기존 실제 producer/reader로 같은 생성 program의12시점/47면적·독립 Decimal 수치를 확인하되 별도 계산 호환 시험으로 구분한다.
계산 없는 파서의 fresh·준비의 생장/DB/CLI/쓰기0과 원3root/자료·WSL 상한/소유 정리를 확인한다.
사용자 화면/전체 backend·hosted CI·실제 농장 관문은 이 자식의 수용으로 확장하지 않는다.
