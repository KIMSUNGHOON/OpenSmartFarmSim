# 긴 합성 작기 입력 reader 수용

2026-10-05 KST. [provider](../backend/app/crop_cycle_input_stream.py),
[계약](../contracts/crop-cycle-input-stream-v1.md),
[집중 시험](../backend/tests/test_crop_cycle_input_stream.py),
[큰 입력/독립 clock·grid/별도 Python 복원](artifacts/crop-cycle-input-stream-reference-20261005.json),
[실제 CLI/최종 파일·초안·검토 영수증](artifacts/crop-cycle-input-stream-implementation-reference-20261005.json).
**불변 분할 입력/원 clock·계산 경계 reader를 로컬 수용**했다. 실제 긴 RHS/작물 Run 수용은 별도다.

## 산출물과 통과한 검증

- 새 전용 packet에 canonical synthetic block을 최대128기록/내용 주소로 만들고, 닫힌 root가
  원 초기 상태·profile/정규화 code/environment·solver/기간/네 stream·hash/index/chain을 고정한다.
  기존 short v1의128 forcing·1일/10,000 step·source hash를 바꾸지 않는다.
- open preflight가 전체 연속성/시각·단위/형식/각 block·전체 chain·clock prefix·예정 걸음 budget을
  확인한다. 검증 후 최대128개 record/page를 읽고 각 stream의 한 분할만 cache한다.
  output 선택은 원 anchors의 부분집합이며 같은 calculation ID/원 경계를 보존한다.
- **집중64개/3.63초·skip0**: 기존6프로그램의 원 record/단위·boundary/event/output·정확한
  Fraction clocks·planned steps, 출력 부분집합/입력 복사·block128 경계·gap/overlap/중복/순서·
  origin/단위/array/bool/예산·재해시 clock/code/profile/index/chain·파일/symlink/FIFO·cursor 변조·
  UTF-8/JSON/중복 key/NaN·FD/실패 정리를 통과했다.
  unavailable directory와 noniterable stream의 실패 시험을 재현해 typed rejection으로 수정했다.
- [별도 연구 script](crop-cycle-input-stream-reference.py)는 **48,000구간/48,001시점 형태**의
  자작 합성 입력을 만들었다. interval300초·기간14,400,000초(166⅔일), anchors4,801/outputs1,601/
  events4개다. 원 외부47,809시점 archive를 채택하거나 복제하지 않았다.
- **48,003개 원 boundary**와 **예정1,440,002 RK4걸음**을 독립 integer range/merge·divmod로
  대사했다. 후자는 계획 산술이며 그 RHS 걸음을 실행하지 않았다. 앞2,176boundary의 cursor를
  **별도 Python 프로세스**에서 복원해 나머지 전체 원값/flag/event/순서의 chain을 독립 결과와 대사했다.
  cursor305bytes, block 최대301,356bytes, 모든 위치/남은 순서가 같았고 FD 수가 보존됐다.
- 8개 index(0/127/128/129/255/256/2175/47999)의 원 prefix를 독립 반복 수/나머지의
  Fraction 식과 비교했다. 값/float64 `.hex()`가 같다. 합성 온도 .1/.3/20.1은 clock 보존 시험의
  입력이며 실제 기후/품종·생장 domain의 채택값이 아니다.

```bash
cd backend
nice -n 10 .venv/bin/python -m pytest -q tests/test_crop_cycle_input_stream.py
```

```bash
nice -n 10 backend/.venv/bin/python research/crop-cycle-input-stream-reference.py \
  --output /tmp/ossf-cycle-input-stream-recheck.json
```

큰 입력은428파일/**113,276,558bytes**, writer+preflight32.734초·전체79.848초였다.
parent/child 최대RSS는 각각30.23MiB였다. 이는 해당 시험 프로세스 측정이며 WSL 전체가 아니다.
관측한 단일 block 최대128record·네 cache 합계 최대388record다. 실제 tempfile/child/FD를 정리했고
새 DB/상주 서버0개다. frozen 기존34파일과 짧은 continuation의 source/test를 보존했다.

## CLI·검토와 게시 경계

현재 CLI turn_context **2026-10-05T06:13:00.514Z**, **gpt-6.1-sol / xhigh**로 설계·구현·검토했다.
실제 line hash/source·출력 log hash를 영수증에 보존했다. Codex CLI 재귀 실행0회다.
별도 Python은 읽기 복원 시험이며 제품 runtime CLI 증거를 대신하지 않는다.

검토는 원 scope/단위/UTC·global record prefix·정확한 clock와 출력/계산 경계 분리, 무한 iterable/
파일·메모리 budget·symlink/FIFO·예외/FD/소유 directory 정리를 확인했다. 새 dependency/일반 운영
service나 범용 agent framework를 만들지 않았다. root/profile·canonical record/전체 chain을 시작 전에
검사하고, 이후 읽는 block의 hash를 확인한다. cache는 확인한 immutable bytes의 원 snapshot이다.
SHA나 synthetic origin은 진본·현재 rights/G0/release/HMAC 승인이 아니다.

실제 archive/농장 입력은 이 synthetic-only 판본에서 거부한다. 실제 초깃값/관리·자동 착과·품종
적용성과 농업 domain 검증은 별도다. actual RHS 실행/생과·구매 자원·경제·수치 결과 저장/HTTP/3D/
worker·production budget·G0–G4는 이 단계에서 실행하거나 수용하지 않았다.
첫 큰 입력 영수증의 contract hash는 `27c0b35`의 구현 중 계약이다. 현재 수용 문구 hash와 초안의
Git 대사는 별도 implementation 영수증에 기록하고 첫 증거를 덮어쓰지 않는다.
live hosted SHA1555610의4workflow는 성공, Backend는 분할 작업이 진행 중이다.
이번 reader/직전 continuation은 그 SHA에 없으며 live CI를 후속 push로 취소하지 않는다.

## 다음 한 단계와 일정

다음은 **`crop-cycle-stream-execution`**: 불변 root/reader를 실제 RHS와 전역 y121/seed·16누적,
exact clock/counters·원 grid/사건/phase·hold에 연결하는 별도 실행 판본이다.
현재 짧은 source/reader hash를 보존하고, 기존6프로그램/여러 chunk·JSON/별도 Python 복원을
원 solver의 전체 물리 payload와 대사한다. 1일/10,000step을 넘는 자작 합성 실행의 실제 RHS·
수지/확인 과거/held trial·부하/정리를 검증한다. 임의 chunk 경계나 interpolation을 추가하지 않는다.
reader만의1,440,002계획 산술을 그 실제 실행 수용으로 표시하지 않는다.

kernel/reader context 연결2–3시간, global checkpoint/위치·budget/phase3–4시간,
6프로그램/긴 합성·hold·별도 Python/검토·보고2–3시간의 **7–10 집중시간** 잠정이다.
하루4시간·CI 대기 제외 기준 **10월5–8일 KST**로 추정하고 구현 계약/실적 뒤 갱신한다.
source166일 실제 부하/저장·생과 날짜는 그 연결/구체적 budget 뒤 추정한다.
실제 forcing/품종/초기·관리 채택0개·국내 독립 자료0건·actual crop Run0개다.
개발과 자료 확보는 병행하며 실제 생산 예측·추천의 완료 날짜는 자료 확보 전 산정하지 않는다.
