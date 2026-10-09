# 긴 합성 작기 입력의 불변 분할 reader — v1

상태: **불변 분할 입력/원 clock·grid reader의 로컬 수용**, 2026-10-05 KST.
[집중64개·48,000구간/별도 Python 검증](../research/crop-cycle-input-stream-implementation.md),
[큰 입력/독립 대사](../research/artifacts/crop-cycle-input-stream-reference-20261005.json),
[실제 CLI/현재 파일·초안·검토](../research/artifacts/crop-cycle-input-stream-implementation-reference-20261005.json).
선행은 [실제 짧은 continuation](crop-cycle-continuation-v1.md),
상위 의미는 [작기 실행 계약](crop-cycle-execution-v1.md)이다. 현재 실제 CLI `gpt-6.1-sol / xhigh`로
설계한다. 입력 reader 수용은 긴 실제 RHS/농장 작기나 G0–G4 수용이 아니다.

## 목적과 작은 구현 범위

`backend/app/crop_cycle_input_stream.py`, 대응 시험과 이 계약의3파일이다.
기존 seed/profile/forcing·UTC/단위/관리 사건과 계산 anchor를 분할해 보존한다.
기존 짧은 v1의 원 입력/API/한도·source hash를 바꾸지 않는다. 실제 archive는 UTC/QC·초기/관리/
권리/품종 미채택이므로 이 단계는 `synthetic` 블록만 받는 `software_research_only` 입력이다.
origin/scope 문자열과 SHA는 권리나 원천의 진본·검토 승인을 증명하지 않는다. 실제 release/custody는 후속이다.

## packet과 공개 경계

`write_input_packet(directory, *, initial_state, segments, events, anchors, outputs, solver,
growth_profile, cohort_profile, transport_profile, program_id)`는 새 전용 directory에 packet을 만든다.
iterable을 최대128기록으로 묶은 canonical UTF-8 JSON 배열을 `sha256.json` 파일에 쓴다.
실패하면 이 호출이 새로 만든 directory만 정리한다. 기존 directory에는 쓰지 않는다.
기존 `_block/_utc` 정규화를 재사용하고 각 블록의 synthetic origin/닫힌 값·단위/배열을 검사한다.
root.json은 profile·정규화 code/environment, original initial state/solver/period/program ID와
segments/events/anchors/outputs의 순서 있는 분할 descriptor·전체 정규화 record chain hash를 고정한다.
descriptor는 sha256/start_index/count/first_at/last_at이며 segment에는 exact `clock_prefix`를 추가한다.
온도 prefix는 원 initial에서 Fraction으로 이어지고 float 온도 누적을 새 seed로 쓰지 않는다.

`open_input_packet(directory, expected_root_sha256, *, profiles...)`는 expected root hash·닫힌 schema,
전체 분할 hash/chain·원 연속성/순서·endpoint·profile/code/정확한 clock/solver budget을 검사한다.
context manager가 전용 읽기 directory FD를 닫는다. 파일명은 hash로만 만들고 symlink/비정규 파일을
거부하며 정해진 크기까지 읽는다. constructor 실패도 FD를 정리한다. HTTP/credentials/worker를 받지 않는다.
schema/hash/resource/권리·QC 미채택 등 지원하지 않는 입력은 `CycleInputRejected`다.

root는 `version/scope/program_id/initial_state/profile_sha256/normalization_sha256/python_version/
solver/period/streams`의 닫힌 객체다. stream은 `count/record_chain_sha256/blocks`다.
원 program_id는 bounded input ID이고 모든 provenance origin은 synthetic다.
초기/forcing/event의 농업 domain 검사는 실제 RHS가 이어서 수행한다. reader가 crop 출력을 만들지 않는다.

| 자원 | 이 연구 판본의 명시 한도 |
| --- | --- |
| 각 stream | 131,072기록, 최대1,024분할; 비최종 분할128개 |
| 분할/root/전체 bytes | 분할2MiB, root1MiB, packet512MiB |
| 기간 | 연속 UTC≤366일 |
| 원 solver | rk4-fixed-v1/64-ulp-per-operation-v1, max_step_seconds1–3,600, max_steps1–40,000,000 |
| 한 페이지/cursor | boundary≤128개, UTF-8 cursor≤64KiB |

이는 source 형태와 reader 자원을 유한하게 정한 개발 범위다. production 처리 한도와 실제 RHS
wall-time/전체 작기 수용은 별도 측정 뒤 고정한다. 짧은 기존 solver의 한도를 올리는 변경은 없다.

## 읽기·clock·원 계산 경계와 cursor

reader의 `record(kind,index)`는 원 정규화 기록의 복사본을 반환한다. `segment(index)`는
그 기록과 원 `start/prefix/slope` Fraction 문자열을 반환한다. 최대128개 기록과 각 stream의
한 분할 cache, bounded root descriptor만 메모리에 둔다. caller의 수정은 cache를 바꾸지 않는다.
다른 분할을 읽을 때 hash를 확인한다. 캐시된 bytes는 확인한 root의 원 snapshot이며 현재 권리 증거가 아니다.

`boundary_page(cursor=None, limit=128)`는 segments의 end·anchors·events의 순서 있는 합집합을
읽어 `at/forcing_end/anchor/event/output`을 최대limit개 반환한다. outputs는 anchors의 부분집합이고,
선택 변경이 계산 boundary를 추가·삭제하지 않는다. 계산 identity는 outputs를 제외하고 root에서 유도한다.
reader plan은 원 합집합에서 예정 RK4 걸음 수/경계 수를 계산하고 caller의 전체 max_steps를 검사한다.

cursor는 닫힌 `version/root_sha256/positions/last_at/cursor_sha256`이다. positions는 네 stream의
전역 다음 record index다. last_at은 null 또는 확인된 원 boundary UTC다. 각 위치는 해당 시각까지
소비한 원 prefix와 일치해야 한다. page 끝을 새 계산 boundary로 넣지 않는다.
`cursor_bytes(cursor)`/`restore_cursor(raw_bytes)`는 root·hash·typed 위치/원 prefix·UTF-8/중복 key/NaN/
크기를 검사한다. 별도 Python 프로세스가 같은 packet에서 다음 페이지부터 복원할 수 있어야 한다.
이 cursor는 수치 y121/checkpoint나 진본·권한 증거가 아니다. 긴 실제 RHS 연결은 다음 모듈이다.

## 수용 기준

- 실제 기존6합성 프로그램을 변환한 segment/event/anchor/output·정확한 clock와 원 boundary/grid
  순서를 독립 divmod/range 또는 원 source에 대사한다. 출력 부분집합은 같은 계산 identity/grid다.
- block128 경계의 gap/overlap, unordered/duplicate/outside UTC, 잘못된 단위/array/finite 값·bool,
  잘못된 profile/code/root/clock/chain, 예상 걸음 초과, symlink/큰 파일/재해시 변조를 거부한다.
- 임의 합성 온도 .1/.3 등에서 Fraction prefix를 독립 합산하고 분할 경계에서도 binary float가 같다.
  값은 software-only clock 사례이며 실제 기후/작물 계수를 채택하지 않는다.
- 원47,809시점 형태 이상인 자작 합성 입력의 원량/시각·유한 window/페이지·메모리·disk·시간을
  측정하고, 별도 Python 재시작의 cursor/다음 원량·순서를 검증한다. 임시 파일/FD/process를 정리한다.
- frozen source/profile/API/짧은 continuation을 보존하고 실제 CLI/출력 hash·집중 시험과 위 범위의
  수용/미실행·외부 의존성을 보고한 뒤 task 체크한다. reader 시험으로 crop/long RHS를 주장하지 않는다.

```bash
cd backend
nice -n 10 .venv/bin/python -m pytest -q tests/test_crop_cycle_input_stream.py
```
