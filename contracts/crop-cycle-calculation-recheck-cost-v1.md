# 서버 입력 재검사의 중복 비용 — v1

2026-10-08 KST. 작업 `crop-cycle-calculation-recheck-cost`의 실행 전 계약이다.
[앞선 같은 입력 측정](../research/crop-cycle-candidate-read-scope-implementation-20261008.md)의
첫3회에는 입력 증명99회/독점9.455초가 포함됐다. 전체 작기 실행 예산의 수용은 별도다.
판단은 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 하며 재귀 CLI를 실행하지 않는다.

## 수정 경계와 근거

제품 수정은 `backend/app/crop_cycle_calculation_server_custody.py`의
`_Journal._guard`로 한정한다. 새 집중 시험은
`backend/tests/test_crop_cycle_calculation_recheck_cost.py`다. 기존 계측기와 수동 전체 입력 시험을 재사용한다.

현재 guard는 `전체 입력 검증 → current() → 전체 입력 검증`을 수행한다.
실제 `current()`는 고정된 서버 closure를 통해 정확한 `CalculationFarmBinding.current`를 호출하며,
그 `_bind`의 입력 검증2회와 현재 권리·등록 검사를 유지한다.
첫 전체 검증을 `engine._require_context`와 기존 입력 디렉터리 FD의 보안 검사로 바꾸고,
`current()`의 반환 binding 비교 뒤 전체 입력 검증을 반드시 한 번 수행한다.
그 뒤 기존 root/intent/디렉터리/intent 원문·artifact pin 검사도 유지한다.

첫 검사는 code/profile/정확한 열린 문맥·token·원 상태/manifest/index를 확인한다.
이 검사를 현재 bytes 검증이라고 표시하지 않는다. current callback이 입력을 검증하지 않거나
검사 도중 입력을 바꿔도 뒤의 완전한 `context.recheck()`가 정상 반환을 막아야 한다.
current callback이 거부하면 guard도 거부한다. 권리 판정을 입력 파일 검사와 원자화한다고 주장하지 않는다.

다음은 변경하지 않는다.

- 공식 context factory·public 계산/복원 연산의 진입/반환 전체 bytes 검사.
- farm prepare/current의 현재 principal·권리/등록 및 입력 전후 검사.
- artifact advance의 public engine 호출·전후 검사와 HEAD 직전 전체 bytes 검사.
- 서버 계산 전후, proof 기록 전후, 조회 전후의 guard 호출 위치와 서명/atomic HEAD 순서.
- 전체 파일 해시·inventory·권한/소유·symlink/link·inode·code/authority/instance 검사.
- 원 입력/증명/과거 결과, RK4 격자·계수·121상태·clock·UTC·관리 사건과 예산.

권리/검증 결과 cache, metadata만의 무결성 확인, 새 서비스/DB schema를 추가하지 않는다.
제품 source SHA가 바뀌므로 새 실험은 새 custody provenance를 기록하고 이전 이력을 재분류하지 않는다.

## 수용 기준

1. 정확한 실제 문맥을 쓰는 journal guard에서 current 호출1회와 전체 입력 검사2→1회를
   실제 호출자 계측의 RED→GREEN으로 확인한다. 계측기는 종료 시 원 함수를 복원한다.
2. root/참조 block의 같은 크기·복원한 mtime 변조를 guard 진입 전과 current callback 중에
   각각 거부한다. 잘못된 문맥/코드·권리 거부는 계산/정상 결과로 이어지지 않는다.
3. proof 기록 전/뒤의 입력 변조는 이전 HEAD를 유지한다. 조회 도중의 늦은 변조도 결과 반환을 막는다.
   FD/cache·소유 자원을 정리한다. 원 context/artifact/server 및 실제 SCRAM farm 회귀를 집중 확인한다.
4. 같은 별도 달력166일 root/증명·첫3회/128전이·원 solver로 실제 등록 계산을 관측한다.
   원47,809시점 중 같은 확정 행과 121상태/seed/clock/cursor를 이전 원 결과와 대사한다.
   fresh 서비스 복원·조회 RHS0·현재 권리/계정 철회·미완료 게시 거부와 실제 명령 종료0이 필요하다.
5. 이전 첫3회와 전체 입력 proof 호출 수·advance 비용을 비교한다. 중첩 비용을 합산하지 않는다.
   소스/입력/과거 이력·FD·SCRAM/DB schema/role/passfile·PG/data/temp/process 정리를 확인한다.
6. 관측 영수증/검토와 문서 링크 뒤 이 자식만 체크한다. 전체166일 terminal/DB/API/3D,
   생산량/자원/경제 연결·실제 CLI 종단 간·G0–G4는 각각 기존 조건을 유지한다.

이 작은 수정의 수용 뒤 초기/증가 prefix 관측과 남은 누적 검증 비용으로 전체 등록 실행 예산을 정한다.
실제 품종 입력·국내 독립 검증 자료·측정 농장 작물 Run은0건이며 예측/추천 게시를 보류한다.

10월8일 [로컬 수용](../research/crop-cycle-calculation-recheck-cost-implementation-20261008.md):
고유199개 분할·실제 SCRAM·같은 첫3회99→85검사/30.737→29.551초,
체크포인트 전체/원행·늦은 변조/철회 거부·복원/RHS0·262 source/정리·실제 종료0을 확인했다.
전체 등록 실행 예산/누적 비용 부모와 전체166일 저장/API/3D 수용은 별도다.
