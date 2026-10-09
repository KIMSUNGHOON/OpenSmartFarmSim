# 저장 수확 전체 행의 내부 검증 — v1

2026-10-09. native Codex CLI `gpt-6.1-sol`/`xhigh` 판단, 재귀 CLI0.
전체 수확 등록에 앞선 작은 비용 개선이다. core4파일은 이 계약,
`backend/app/crop_harvest_replay.py`, `backend/app/crop_harvest_registry.py`,
`backend/tests/test_crop_harvest_row_verification.py`다.

## 범위와 검증 경계

현재 registry의 전체 검사는 사용자 `page()`를 반복 호출한다. 각 호출의 전후 guard는
현재 부모 결과 전체를 조회한다. 기존 전체 용량748page에서는 이 순회만 부모 조회1,496회다.
이는 호출 구조의 계산이며 전체 registry 실행 시간의 실측은 아니다.

reader의 `verify_all_rows()`는 외부에 행을 반환하지 않는 하나의 내부 검증 작업이다.
기존 `_operation`의 시작·종료 guard로 현재 부모/권리/원 identity와 디렉터리/HEAD/root를
검사하고, 그 사이 모든 descriptor의 실제 canonical blob bytes/hash/count를 확인한다.
원 순서의 canonical 행과 줄바꿈으로 SHA를 다시 계산해 저장 row_count/row_chain과 대사한다.
한 page씩만 읽으며 기존64행/2MiB·전체512MiB/파일 제한은 유지한다.
bytes 때문에 저장 blob이64행보다 작게 나뉜 경우에도 기존 registry가 검사하던 논리적64행
응답의 envelope 포함2MiB 제한을 대사한다. blob 한도만 통과한 초과 응답을 새로 허용하지 않는다.
성공 뒤 count/chain만 반환한다. 실패·권한 철회는 기존 예외/FD close 규칙을 따른다.

registry의 `full=True` 검사만 이 작업으로 바꾼다. 현재 원문/source/summary 검사,
최종 권리와 원 부모 검사, HMAC/INSERT 뒤 재검사·거래 rollback을 유지한다.
`page()`/`summary()`와 공개 HTTP·DTO·SDK는 변경하지 않는다. 원 부모 파일/권리의
요청 간 캐시나 stat만의 무결성 판단을 추가하지 않는다. 질량·배정/RHS를 재계산하지 않는다.
변경된 writer/dependency/publication hash를 사용한 새 수확 판본만 후속 생성한다.
이미 수용한 원 부모와 이전 수확 산출물을 덮어쓰거나 새 코드로 소급 수용하지 않는다.

## 수용 기준

1. 같은1/3page 합성 저장물에서 기존 page 순회와 새 검사 count/chain이 독립 원 행 SHA와 같다.
   검사 단계의 부모 조회는2회이며 페이지 순회의2×page회와 비교해 기록한다.
2. 첫/중간/마지막 page 변조·행 수/순서 불일치, HEAD/root 교체, 검사 중 현재 권리/계정
   철회와 끝 guard의 거부를 확인한다. 실패한 handle은 닫히고 성공 증거를 반환하지 않는다.
3. 실제 등록 경로의 원6행/서명/동일 재시도·INSERT 뒤 계산 권리 철회 rollback 회귀를 통과한다.
   순수 합성 시험과 실제 SCRAM 증거를 구분한다. 원 부모/입력/FD·미리보기와 소유 PG 정리를 확인한다.
4. 원 명령 종료·native CLI 문맥/판단·소스/출력 hash·단일512MiB/관측 합1GiB를 기록한다.
   전체 수확 writer·전체 행 독립 Decimal 대사/보존·API/3D와 UI U3는 별도 미완료다.

이 변경은 전체 writer의748개 원 sample 조회 비용을 줄이지 않는다. 해당 비용과 별도
측정 결과를 합쳐 전체 실행 예산을 정한다. 실제 품종/독립 농장 자료와 G0–G4 보류는 유지한다.
