# 저장 줄기의 출현 사건→잎 생성 입력 — 연구 v1

상태: 합성 입력 작성 소프트웨어 구현.
선행은 [분류 커널](crop-phytomer-kind-v1.md),
[정확 출현 시각](crop-shoot-air-event-timeline-v1.md),
[원 줄기 저장 v2](crop-rational-morphology-artifact-v2.md)와
[명시 잎 생성](crop-declared-leaf-births-v1.md)이다.

## 호출과 원본 결속

`build_leaf_birth_inputs_from_stored_shoot(directory, access, root_sha256, *, start_index, end_index, inputs)`는
호출자가 신뢰 범위를 확인한 자체 합성 줄기 root만 받는다. 입력의 닫힌 필드는 `input_id, policy, leaf_profile`다.
policy는 기존 분류 계약 그대로이며 원 프로그램의 shoot/schedule과 같아야 한다.
leaf_profile의 필수 필드는 `base_temperature, curve, normalization, initial_area`다.
이 한 프로필을 새 영양 위치들에 적용하는 명시 합성 정책이며 실제 품종의 rank별 면적을 추정하지 않는다.
초기 면적은 기존 잎 초기화 함수로 나이0의 곡선값과 대사한다. 새 잎이0개여도 잘못된 프로필을 수용하지 않는다.

start_index=-1은 원 프로그램의 초기 상태다. 그 밖의 start_index와 end_index는 실제 저장 frame 순번이다.
두 값은 bool을 제외한 정수이고 `-1 <= start_index < end_index < 저장 시점 수`다.
처리 구간은 원 시작/끝 UTC의 `(start,end]`다. 원 초기 기관은 새 출현으로 재생성하지 않는다.
manifest/프로그램·선택 상태/프레임은 기존 reader/소유 blob store로 읽어 원 SHA·권리/스키마/시각을 확인한다.
앞선 절간의 ID·출현/곡선 anchor는 양 끝에서 같아야 한다.

원 프로그램 기온을 해당 구간으로 자르고 기존 exact timeline을 전진한다.
그 checkpoint는 원 끝의 timeline state 전체와 같아야 한다. 끝에 추가된 절간의 개수·연속 순번·출현 나이/정확 초는
그 사건 목록과 같아야 한다. 새 절간 ID는 기존 entity의 canonical SHA 규칙과도 대사한다.
줄기 길이/잎 생장 전진이나 전체 원 작기 재적분을 실행하지 않는다. 이는 GET reader가 아니라 새 계산 입력 작성 단계다.

## 분류와 안정 ID

원 출현 순번을 같은 정책으로 분류한다. vegetative 사건만 아래 선언으로 바꾼다.
generative는 화방 위치 표식이며 꽃·착과·과실을 생성하지 않는다.

```text
leaf_id = "leaf:" + SHA256(canonical JSON({
  model_version, stem_program_sha256, policy_sha256,
  sequence, attachment_internode_id
}))
```

canonical JSON은 sort_keys·구분자 `,`/`:`·유한 JSON의 UTF-8이다.
출력 구간/index·배치 input_id와 프로필은 이 기관 ID에 넣지 않는다. 같은 원 프로그램/정책의 분할에서 ID가 같다.
각 선언은 기존 EVENT_KEYS의 leaf ID/원 부착 ID·원 정확 출현 초와 명시 프로필 사본이다.
각 잎 출현 뒤의 기온만 그 잎 기준온도 이상인지 검사한다. 출현 전 저온은 잎 출현 후의 저온으로 취급하지 않는다.
배치 결과는 stateless다. 서로 겹치지 않는 저장 구간의 사건을 한 번씩 사용하며 전체 이력/중복 방지는 후속 population이 담당한다.

## 출력과 수용

버전 `stored-shoot-leaf-birth-inputs-research-v1`과 연구/합성/관문 미평가 표식, 원 root/program/양 끝 state SHA,
하위 모델 판본·timeline/policy/profile/입력 SHA, 원점/구간과 분류된 사건을 남긴다.
`leaf_inputs`는 기존 `create_declared_leaves`에 직접 전달할 수 있는 닫힌 입력이다.
입력/출력2MiB·최대512출현/잎 상한을 유지한다. 입력/원 blob과 기존 수치/reader/worker/API/UI는 변경하지 않는다.
반환 직전 원 manifest/program·선택 endpoint blob을 재검사한다. 도중 원본 변경 때 결과를 내보내지 않는다.

모듈 부재 RED 뒤 실제 원 stem14blob/12시점과 손으로 대사한 순번/분수 초·ID/생성 목록,
독립 Decimal 면적을 확인한다. 전체/저장 경계 분할의 같은 잎 선언/최종 population·중복0, 빈 구간/끝 경계·512를 검사한다.
다른 shoot/schedule·잘못된 프로필/순번/index·변조된 endpoint/부착/시간·누락/교체/초과를 거부한다.
해시를 다시 맞춘 시험 판본에서도 원 timeline/사건 불일치를 막는지 확인한다.
builder의 줄기/잎 advance·DB/CLI/파일 쓰기0, 원3root/자료·WSL/소유 정리를 대사한다.

초기 잎 inventory와 정책의 별도 대사·새 전체 program/불변 저장/현재 farm 권리·같은 UTC3D는 후속이다.
실제 Axiany 계수·관측/독립 작기, 관리/노화·생산/자원/경제와 G0–G4를 이 입력 작성으로 수용하지 않는다.
