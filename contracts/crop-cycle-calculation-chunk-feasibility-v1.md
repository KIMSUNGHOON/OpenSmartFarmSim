# 계산 구간을 묶는 경계의 가능성 — v1 관측 계약

2026-10-08 KST. 작업 `crop-cycle-calculation-chunk-feasibility`.
선행은 [prefix 증명/최종 권한 경계 수용](../research/crop-cycle-calculation-prefix-attestation-implementation-20261008.md)이다.
판단은 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 하며 재귀 CLI는 실행하지 않는다.

## 확인할 문제

원 전체 작기는 1,816,704 적분 걸음에 경계 처리를 더한 1,864,515 전이다.
현재 artifact의 한 호출 128전이 제한 때문에 원 전체 실행은 14,567 commit을 만들었다.
prefix 증명 뒤에도 현재 전체 파일 bytes/HMAC/metadata 순회는 남는다.
순수 계산 엔진은 이미 최대 10,000전이를 받지만 artifact/서버는 128전이를 넘으면 거부한다.

다음 후보는 **순수 엔진의 4,096전이 한 호출**이다. 기존 128전이 32호출과
같은 논리적 경계에서 값을 대조할 수 있어 선택했다. 적분 간격을 늘리거나 출력 시점을 줄이지 않는다.
이 관측은 artifact/서버 한도를 변경하거나 큰 budget을 게시 경로에 허용하는 구현이 아니다.

## 변경과 실제 실행 범위

core는 이 계약과 `backend/tests/crop_cycle_chunk_feasibility_smoke.py` 두 파일이다.
기존 입력·물리 모델·context·artifact·prefix·서버·DB/API/UI/CI source는 보존한다.
기존 manual 시험의 packet/원행 reader, 실제 page packer와 비용 계측기를 재사용한다.
page packer는 메모리 안에서만 호출하며 artifact/HEAD/proof를 발행하지 않는다.

고정 root는 `05a58cc9092682f663bb3e2f827003f51ec8a778f746bb429126a663e841fc04`다.
최종 권한 경계 수정판의 실제 32회 profile SHA를 고정하고 새 순수 호출과 대조한다.
한 소유 계산만 nice19로 실행한다. 새 PG/브라우저/컨테이너/네트워크 작업은 없다.
실제 RHS 비용 약 36초였던 같은 경계에 근거해 명령 관측 예산은 240초다.
감독자가 만료 시 소유 명령에 중단을 요청하고 실제 종료·PID·source·임시 경로 정리를 기록한다.
관측 만료만으로 명령을 재시작하지 않는다. primary RSS 표본과 FD도 기록한다.

## 수용 기준

1. 현재 artifact가 4,096전이 budget을 거부하는 것을 실제 확인하고 제품 한도를 보존한다.
2. 같은 입력/8초 RK4/300초 출력에서 실제 4,096전이를 계산한다.
   고정 32회와 121상태/seed/clock/cursor/누적·출력/사건 prefix를 대조한다.
   묶음에 따라 달라지는 `parent_sha256`/`checkpoint_sha256`만 구분하며 다른 checkpoint 필드는 같아야 한다.
3. 기존 원 전체 순수 결과와 명시한 +273일 이동 뒤 모든 해당 sample/event 및 semantic checkpoint를 대조한다.
   참조 조회는 RHS0이며 실제 신규 계산의 RHS 수와 비용을 별도로 기록한다.
4. 실제 page packer로 해당 행을 메모리 직렬화해 단일 page 2MiB/128행, delta 8MiB,
   commit당 16page/metadata 128KiB의 기존 한도와 비교한다.
   이 후보의 관측을 다른 입력·사건 밀도의 안전성이나 서버 수용으로 일반화하지 않는다.
5. 원/새 각 750개 입력·원 29,141개 artifact, 고정 baseline/source의 hash·mode·identity를 보존한다.
   context/cache/FD·실제 명령 종료/감독자/PID·임시 경로 정리를 확인하고 보고서·불변 receipt를 남긴다.

통과하면 다음은 명시 판본의 artifact/서버 budget 설계와 원량·hold·자원/권한·복원 검증이다.
그 증거 전에는 현 128전이 제한을 완화하지 않는다. 전체 등록 작기/저장/같은 UTC3D와
생과/자원/경제 연결은 후속이며 이 관측을 전체 실행 시간·완료 날짜의 예측으로 쓰지 않는다.

10월8일 [실제 관측 수용](../research/crop-cycle-calculation-chunk-feasibility-observed-20261008.md):
1통과/종료0·55.567초, 실제4,096전이/3,990걸음·원105출력/2사건·비계보 checkpoint 전체 일치,
실제 page packer2page/954,171bytes·metadata4,779bytes·268 source/FD12→12·정리를 확인했다.
순수 context/start/advance37.853초는 등록 서버/전체 작기 처리량이 아니다. 제품128전이 제한은 유지했다.
