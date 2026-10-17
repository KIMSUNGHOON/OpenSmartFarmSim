# 종료된 합성 시험의 저장 checkpoint 메타데이터 v1

선행: [진행 조회 잠금 수명](crop-solar-progress-lock-lifetime-v1.md).
sourcef6b3bde/원 정상 CI39037993173은381.069초·자식1·두 actor -15로 종료했다.
원360초 계산 상한 안에 완료하지 못했고 정상/DB 정리 proof와 완료 단계 정보가 없다.
원 actor의 실행 중 계측 없이 다음 비용 개선의 근거를 확보한다.

## 경계

- 원 prototype/actor 본문·인수·입력·64걸음/chunk1·조회 주기·5초 재시도·360/600초·RSS 상한을 유지한다.
- 원 정상 증명이 이미 있거나 actor가 실행 중이면 수집하지 않는다. 원 실패 정리에서 actor 종료를 확인한 뒤,
  기존 `pg_ctl stop` 전에 한 번 자체 시험 DB를 읽는다. 계산 중 추가 조회나 계측을 삽입하지 않는다.
- private config 소유/권한·같은 owned temporary cluster/data directory·provisioner 신원·test namespace를 대사한다.
  Read Only/Repeatable Read, connect2초/statement2초와 제한된 행/출력 크기를 사용한다.
- 합성 작업 state/attempt·허용 reason code와 저장 checkpoint의 steps/planned/status/UTC/sequence·메타데이터 hash만 수집한다.
  DSN·경로·테넌트/작업 ID·원 입력/결과·메시지/인증값은 내보내지 않는다. 수집 오류도 종류만 기록한다.
- 이 기록은 종료 뒤 DB 관찰이며 원천/권리/모델을 재검증한 결과가 아니다. 정상 완료·Run·생산·관문 증명으로 승격하지 않는다.
  원 정상 기능은 기존 원 증명·후검사/정리 모두가 성공한 경우에만 별도 수용한다.

## 수용

1. 실제 자체 DB에서 원 저장 checkpoint 필드·read-only/isolation·다른 cluster 거부·계산/SQL 변경0·연결/DB 정리를 확인한다.
2. 실행 중 actor/기존 정상 증명에서는 수집이 없고, 실제 process 종료 뒤에만 허용된 큐레이션 파일을 만든다.
3. 기존 정상 driver 로직은 수집 호출1개 외 AST가 같고, 원 actor 해시·application·workflow 실행 단계/환경/상한이 같아야 한다.
4. 실제 hosted 사례에서 run/head/digest/경로·actor/source hash·저장 메타데이터 또는 수집 실패 사유를 대사한다.
   이후 실제 관측으로 다음 작은 수정을 고른다. 같은 실패를 근거 없이 반복하지 않는다.

로컬5root/두 UI/원본·FD/소유/PG/임시/passfile과 자원 상한을 유지한다.
S3/S4·새 Solar 적용·실제 자료/G0–G4와 전체 완료일 보류는 유지한다.
