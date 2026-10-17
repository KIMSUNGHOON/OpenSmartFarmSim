# 일사 독립 실행의 진행/시간 진단 — v1

선행: [잠금 충돌 수정](crop-solar-worker-custody-contention-v1.md).
수정 source63baae8의 trace-OFF CI39029133073은 원 정상64걸음을 수용하지 못했다.
379.784초·자식1·자원 중단 사유 없음·두 actor -15이며 정상 proof는 없다.
원 부모의 계산360초 상한을 소진했으며, 확보한 기록만으로 완료 걸음이나 병목은 알 수 없다.

## 다음 한 단계

- 선택 진단 모드에서 기존 `_before`/adopt/advance/confirm/finish의 실제 진입·종료 시간,
  호출 수·원 반환 progress의 확정 steps/planned_steps/status만 제한해 기록한다.
  signed HEAD/실제 반환값에 없는 시점이나 진척률을 만들지 않는다.
- 원 입력·64걸음·chunk1·API 조회 주기·현재 권리/취소/임대·원 판정과360/600초·RSS 상한을 유지한다.
  이 단계에서 상한 증가·sleep 조절·fixture 축소·context 캐시나 수식 변경을 하지 않는다.
- frame locals·원 결과/예외 메시지·입력/환경·접속 정보를 내보내지 않는다.
  기록은 최대 용량/건수, monotonic 시각, 원 source/actor hash 및 실제 종료와 연결한다.
- 관찰 파일은 최대64KiB, 최근32사건·동시16단계·최근16예외로 제한한다.
  단계별 누적/최대 시간은 중첩을 포함한 시간이며 합산하지 않는다. 관찰 자체 비용도 포함한다.
  `_confirm`의 실제 반환 checkpoint만 `last_confirmed`로 기록하고 adopt/advance는 따로 기록한다.
  진행 파일은 atomic replace로 남겨 강제 종료 뒤에도 마지막 완결 기록을 수집한다.
- 진단 header가 있는 실행은 정상 수용으로 계산하지 않는다. 원 코드로 돌아온 별도 실행이 선행
  [정상 기준](crop-solar-unpaused-hosted-v1.md)을 모두 통과해야 한다.

## 수용 기준

1. 통제된 단계 전환의 계측과 비밀 문자열/로컬 변수 미노출·유한 기록을 확인한다.
2. 실제 진단 한 사례에서 마지막 확정 단계/시각, 오래 걸린 구간 또는 종료 불가 이유를 원 반환과 대사한다.
3. 실제 resource/종료·FD/PG/임시/passfile 정리와 immutable artifact/run/head/digest를 검증한다.
4. 새 수정을 제안할 때 이 관측을 근거로 범위를 정한다. 같은 조건의 검증 재실행만으로 끝내지 않는다.

로컬5root 용량·hold/취소·실행 중3D·사용자 적용·외부 자료/G0–G4와 전체 완료일은 별도 미완료다.
