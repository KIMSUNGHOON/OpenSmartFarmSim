# 일사 작업자의 일시적 custody 잠금 충돌 — v1

선행: [독립 실행 계약](crop-greenhouse-solar-execution-runtime-v1.md),
[호스팅 정상/선택 진단](crop-solar-unpaused-hosted-v1.md).
진단 CI39028662821의 worker trace는 `run_once → advance → _open`의
`SolarCustodyPending`을 확인했다. 이 시도는 정상 수용이 아니다.
기존 worker는 일시 잠금 충돌에서 즉시 transient 시도를 종료했다.

## 변경 경계

- Solar worker 내부에서 `_adopt`/advance/confirm/finish의 custody pending만 다룬다.
- 첫 pending 뒤5초의 monotonic 재시도 시작 예산과최대50ms 대기 간격을 둔다.
  이는 저장소 충돌 처리이며 수치 시간 간격·worker chunk·API 조회 주기나 시험 pause/barrier가 아니다.
  이미 시작한 기존 권리 검사/호출의 실행 시간은 이 예산으로 강제 중단하지 않는다.
  검사 뒤 예산이 소진됐으면 추가 호출이나 sleep을 시작하지 않는다.
- 매 재시도 전에 기존 `_before`로 현재 입력/권리·취소/임대를 확인하고 갱신한다.
  대기 중 파일/DB 거래를 보유하지 않는다. 취소/임대 상실·권리/다른 오류를 재시도하지 않는다.
- 예산을 소진하면 원 pending을 다시 발생시켜 기존 transient 종료 정책을 따른다.
  서명 HEAD·확정 사건·원자 게시/결과 계산을 우회하거나 재시도 성공을 가정하지 않는다.
- API·custody 잠금/서명/권리·수식/계수/입력과 기존5root/자원 상한을 유지한다.
  앞선 시험 부모 교체는 계속 미채택이다.

## 수용 기준

1. 일시 충돌→같은 호출의 성공, 영구 충돌→원 예외/유한 대기, 대기 중 취소/권리 오류→즉시 전파를 검증한다.
2. 기본 진단False인 원 prototype에서 별도 API/작업자의 원64걸음/start1/CLI0·성공 사건1/attempt1,
   두 전진 prefix·원 값/UTC·모든 원 후검사·DB/FD/소유 정리와 실제 감독 종료0을 통과한다.
3. 호스팅 기능과 로컬5root 용량은 별도다. hold/취소/계산 중3D·S2/S3/S4 부모·새 Solar 사용자 적용·
   외부 자료/실측·G0–G4는 이 수정이나 단위 검사로 수용하지 않는다.

새 잠금 대기 예산은 운영 동작이며 농업 매개변수나 정상 완료 보장이 아니다.
진단 기록을 근거로 현재 native Codex gpt-6.1-sol/xhigh에서 판단했고 재귀 CLI를 사용하지 않았다.
