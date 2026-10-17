# 일사 동시 실행 시험의 대기 부모 — v1

선행은 [현재 resource 관측](../research/crop-solar-current-unpaused-resource-20261017.md)과
[기존 runtime 계약](crop-greenhouse-solar-execution-runtime-v1.md)이다.
제품 runtime/dispatcher 변경이 아닌 소유 검증 실행기의 다음 한 단계다.

## 변경 경계

- 원 preparation·소유 SCRAM DB·고정 입력과 API/worker 생성 원문을 그대로 사용한다.
- 두 actor의 원문/hash·환경·소유 경로를 고정한 뒤,22.4MB를 보유하던 대기 부모를 exec로 교체한다.
  bounded ready/admission 대기→원 API/worker 실행→후검사 순서를 유지한다.
- worker의 실행 중 pause/barrier·sleep이나 입력/청크/조회 주기 변경을 추가하지 않는다.
- actor의 새 검증을 대기 부모로 옮기거나 검증 캐시/부분 조립·fixture 응답으로 대체하지 않는다.
- 소유 PID/boot/start·pidfd 정리와 실제 파일/디렉터리 identity를 유지한다.
  원 source/키/행/서비스와 원5root·자원 감독을 변경하지 않는다.

## 다음 한 단계 수용

1. 실제 별도 configured API와 독립 unpaused worker가 원 정상64걸음을 완료한다.
   원 POST/전진 prefix 두 개 이상·UTC/원 값/최종 응답과 기존 모든 worker/API 후검사를 통과한다.
2. actor 환경/원문 보존과 실행기 exit0·역할/schema·FD/소유 PG·임시/자격 파일 정리를 대사한다.
3. 기존 runtime의 동일 전체 보호/자원 관문을 통과하고 실제 PID별/합 RSS와 종료 코드를 남긴다.
4. 초기 실패/중단을 보존한다. 성공해도 정상 한 사례만 수용하며 hold/취소·계산 중3D·배포/
   G0–G4/실제 농장·전체 제품 완료를 주장하지 않는다.

후검사·정리의 동등성과 소유권을 먼저 검토한 뒤 소유 사설 영역에서 검증한다.
통과 전 원 prototype이나 제품 실행기에 채택하지 않는다. 실패하면 새 근거 없이 반복하지 않는다.
