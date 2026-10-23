# 정책 기반 잎 실행 화면 — v1

상태: [실제 UI/CI 기능 수용](../research/leaf-appearance-execution-web-20261024.md). 선행은 [실행 SDK](web-leaf-appearance-execution-v1.md)와
[현재 API](../research/leaf-appearance-execution-live-20261024.md)다.
기존 실행 화면/재생·작물 외형과 CSS/geometry를 재사용한다.

별도 leaf-appearance-execution.html에서 현재 입력 확인→명시 새 접수→같은 작업 상태/취소→저장3D를 연결한다.
새 작업은 명시 클릭 때만 고유 study ID를 만들고 미확정 요청을 먼저 저장한다.
응답 지연/메뉴/reload는 같은 pending body/job ID를 유지하며 POST를 자동 반복하지 않는다.
별도 JOB/PENDING/FRAME 저장 키와 job_id/frame URL로 기존 다른 모델의 상태를 보존한다.
현재 세션의 기존 leaf/morphology token을 재사용하되 연결 해제는 새 화면에 유지한다.

현재 SDK의 원 result/root/parent·UTC/잎 면적과 같은 시점의 실제 삼각형 면적·표/그래프를 대사한다.
provided replay만 표시하고 static 연구 fixture로 대체하지 않는다. API에 없는 정책 수치는 만들지 않는다.
실제 queued/simulating/succeeded/hold/failed/canceled와 응답 대기 시간만 보여 주며 임의 완료율은 없다.
현재 권리/인증·연결/무결성 거부 때 결과 장면/수치를 제거하고 같은 ID 재조회를 제공한다.
조회 503의 제한된 GET retry와504/접수 오류의 명시 확인을 구분한다. 기존 요청별30초 예산을 유지한다.
대기 작업의 즉시 취소는 `canceled / cancel_accepted=true / cancel_requested=false`도 정상 응답이다.
실행 중 취소 요청과 완료된 취소를 구분해 종결 상태를 표시한다.

수용은 focused type/unit/browser와 필요한 CI, 실제 같은 job/원12시점·47면적/UTC·mesh/table/chart,
새 실제 접수/자동 완료·취소·메뉴/reload/재연결/추가 POST0, 현재 권리 철회 제거,
모바일/유휴/실제 전용 Chrome·기존 데이터/키/화면·WSL 보존과 불변 배포다.
12ui의 기존 승인 target/실제 viewport 대조를 사용하고 실제 WebGL을 raster로 대체하지 않는다.
이 합성 연결의 기능 수용과 최종 사실감 R2/첫 cold 경고·실제 품종/작기/생산·경제/추천·G0–G4는 구분한다.
