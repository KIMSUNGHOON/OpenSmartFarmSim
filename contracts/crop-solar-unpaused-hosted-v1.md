# 독립 일사 계산의 호스팅 기능 검증 — v1

선행: [원 실행 계약](crop-greenhouse-solar-execution-runtime-v1.md),
[대기 부모 시험](crop-solar-unpaused-probe-parent-v1.md).
원5root를 보존한 로컬 재시험은 부모 RSS를 줄여도 합 RSS로 중단됐다.
계산 기능과 기존 WSL 서비스 동시 용량의 증거를 별도로 확보한다.

## 한 단계 경계

- 기존 공개 `crop-greenhouse-solar-unpaused-probe.py`의 준비·API·독립 worker·후검사를 그대로 실행한다.
  합성 정상64걸음·chunk1·원 조회 주기·SCRAM/TLS·unpaused를 유지한다.
- 새 수식·계수·입력·제품 실행 설정을 도입하지 않는다. 로컬 부모 exec 후보는 채택하지 않는다.
- 기존 수동 Web workflow에 명시 선택한 backend 전용 job을 추가한다.
  잠금 backend와 기존 검증 PostgreSQL16.15 hash를 사용한다. 이 선택은 웹 회귀 통과를 뜻하지 않는다.
- 기존 Linux 소유 identity/pidfd helper로 시험 자식만 감독한다.
  512MiB/PID·합1GiB·0.25초·600초, 실제 종료/FD/PG/임시/passfile 정리를 검사한다.
  호스팅에는 로컬 원5root가 없음을 증거에 명시한다.
- 원문 로그·환경·키·접속 파일을 artifact에 게시하지 않는다.
  원 정상 proof·DB 정리·actor identity/hash와 큐레이션한 자원 증거만 보존한다.

## 수용 기준

1. 실제 API와 별도 unpaused worker의 종료0, 원64걸음/start1/CLI0·성공 사건1/attempt1.
2. 원 POST·두 전진 prefix 이상·최종 저장 응답과 원 값/UTC 일치·API GET 계산/쓰기0·원 FD identity.
3. 원 후검사와 DB 역할/schema0, 감독 종료0·FD 동일·소유 비좀비/PG/임시/passfile0.
4. source commit·실제 CI/run/도구 종료·actor hash와 자원 표본·실패 이력을 보존한다.
5. 통과 범위는 호스팅 정상 한 사례다. hold/취소·실행 중3D·로컬 동시 용량·S2/S3/S4 부모·
   새 Solar 배포·실제 품종/농장·G0–G4·전체 제품 수용을 대신하지 않는다.

착수 시각부터 CI 대기·환경 준비·원 계산360초/전체600초 상한과 실제 종료를 관측한다.
호스팅 한 사례의 시간으로 사용자 적용이나 전체 완료일을 추정하지 않는다.
