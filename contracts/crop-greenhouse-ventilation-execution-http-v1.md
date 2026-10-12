# 환기 실행 현재 조회·HTTP·명시 runtime v1


**2026-10-12 취소 경계 보완:** [환기 범위 잠금 수정·125검사](../research/crop-greenhouse-ventilation-cancel-lock-fix-20261012.md)를 로컬 수용했다. 현재 증거 검증 후 짧은 행 확정 잠금에서 임대/취소/입력·최신 checkpoint를 재확인한다. 환기 typed 취소는 같은 서비스의 NO KEY UPDATE 전이를 사용하고 현재 취소 권한/입력 판본과 기존 사건/상태를 보존한다. 입력 사용 권리 철회 뒤 소유자 취소가 가능하다. 수정본 실제 WebGL·사용자 적용은 후속이다.
상태: [377검사/최종 보존으로 로컬 소프트웨어 수용](../research/crop-greenhouse-ventilation-execution-http-runtime-implementation-20261012.md). 사용자 배포/3D/실제 자료·관문 수용은 후속이다. 선행은 [접수·자동 계산 핵심](crop-greenhouse-ventilation-execution-core-v1.md)이다.

## 사용자 경로

- POST `/v1/crop-greenhouse-ventilation-executions`: 닫힌 농장/입력/권리 요청,64KiB 이하. 기존 simulation queue의 고정 입력 판본을202로 반환한다. 같은 의도 재접수는 같은 작업이며 충돌은409다.
- GET `/v1/jobs/{job_id}/crop-greenhouse-ventilation-execution`:16KiB 이하 `joint-ventilation-execution-query-v1`. 원 job 상태·cancel flag·관측 UTC·확정 체크포인트의 원 기록 UTC/계산 UTC·단계/총단계·건수·최종 결과 연결을 제공한다. 미확정/잠금은 명시적 `none`/`unavailable`이며 임의 진행률을 만들지 않는다.
- POST 같은 경로의 `/cancel`: `joint-ventilation-execution-cancel-v1`. 취소 권한/현재 계정/소유 작업의 정확한 새 입력 판본을 확인한다. 입력 사용 권리 철회 뒤에도 소유자는 취소할 수 있다. 실제 작업자 확인과 최종 canceled는 별도 상태다.

응답은 no-store이며 토큰·임대 자격·원 입력·보호 경로를 포함하지 않는다. 기본 비활성은 인증 뒤503, 미인증401/권한403, 대상 없음404, 입력 거부422다. 현재 계정은 동작 전후 검사한다.

## 현재 결과와 조립

현재 조회는 같은 jobs/server/binding/results의 확정 DB 사건과 서명 파일 이력·현재 입력 권리를 전후 대사한다. 정상 결과의 원자 publication1과 수치 hold의 publication0/결과 연결1을 구분한다. 조회 중 수치 적분·checkpoint 확정·결과/작업 쓰기0이다. 변경된 상태는 부분 응답으로 게시하지 않는다.

별도 `operator-greenhouse-ventilation-execution-api-config-v1`에서 최상위 strict bool `crop_greenhouse_ventilation_execution`을 명시한다. True는 환기 결과 저장/조회와 기존 cycle 전제를 요구한다. 기존 읽기 설정 판본/기존 loader는 새 실행을 기본 활성화하지 않는다. 같은 trusted 결과 factory의 서버/입력 resolver를 사용해 admission/checkpoint/query를 조립하며 별도 키를 추가하지 않는다. 보호 설정 파일은 factory/assembly 전후 재확인한다.

## 수용 기준

실제 SCRAM/검증 TLS 접수→원 진행→독립 자동 작업자→정상/보류 저장 결과 조회, 소유자 취소→작업자 canceled/결과 미게시, 현재 권리/계정·원 시각·조회 계산/쓰기0를 확인한다. 기존57경로/313스키마·구 모델/두 UI·원본/WSL/소유 정리를 보존한다. 새3D/사용자 적용·실제 품종/생산·경제·G0–G4 수용은 후속이다.
