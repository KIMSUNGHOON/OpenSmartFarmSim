# 사용자5174의 계산 중 저장3D 활성화 — 2026-10-11

**20:35 KST에 P6b를 제한된 합성 소프트웨어 범위로 수용했다.**
`http://localhost:5174/`는 같은 사용자 DB의 계산 상태와 확정 부분 결과를 자동 조회한다.
`http://localhost:5173/`는 완료166일 생장·수확의 저장 재생을 유지한다.
[현재 접속 절차](../web/README.md#joint-execution-user-preview)를 따른다.

[기계 증거](artifacts/crop-climate-joint-prefix-user-activation-reference-20261011.json)의 SHA-256은
`e6d4eeb7e47f3968483a2ad86467c6542e3f258c7dd10dcd27fd0be06f382189`이다.
native Codex CLI `gpt-6.1-sol`/`xhigh` context SHA는
`9dac55ae0e2c5a63aa52b21e44b50f05fe40355d42e13230906eb1ffcfd35062`이며 재귀 실행은0이다.
checkout `f6be60654aab6d83d0b371905a3a11ec7f787067`의 불변1911파일을 사용했다.
backend/app203·web/src115의318제품 파일은 수용된 P6a와 같고 기존171개 빌드 자산을 그대로 제공한다.
제품 코드·계수·새 빌드 변경은 없다.

## 연동 범위와 실제 화면

| 화면 | 실제 연결 | 남은 범위 |
| --- | --- | --- |
|5173|완료166일의47,809생장 시점·47,813수확 행과 같은 UTC 수치3D|실행 중 계산 자동 조회 없음|
|5174|같은 DB의 접수→자동 worker→상태/확정 부분 결과의 표·그래프·3D→완료 저장 결과|이번 실제 running 관측은1시점. 여러 중간 시점의 연속 전진/전체 작기 미검증|

정상 응답이 끝난 뒤10초를 기다려 다음 조회를 시작하며 서버 처리 시간이 추가된다.
일시 오류는 최대60초 간격으로 재시도하고 숨긴 탭에서는 조회를 멈춘다.
새 마지막 저장 UTC를 받으면 최신 시점으로 선택을 갱신한다. 원 저장 시점이 없으면 장면이 없고,
새 저장값을 받기 전에는 마지막 확인값을 유지한다. 보간하거나 미래 프레임을 만들지 않는다.
개발·검증용 별도 DB에서 실행한 계산은 이 사용자 DB에 자동 노출되지 않는다.

![실제 사용자5174의 계산 중 확정 수치3D](artifacts/crop-climate-joint-prefix-user-running-20261011.png)

이 이미지는 실제 브라우저 캡처 원본이다. LAI·50과실 구획·온도를 나타내는 수치 모식도이며
현실적인 품종 외형이나 검증된 생산 예측 장면이 아니다.

## 실제 사용자 서버 검증

원 tool4786의 browser/child/guard/tool exit0을 확인했다. 같은 지속 사용자5174의 실제
SCRAM PostgreSQL·TLS API·별도 자동 worker(chunk8)를 사용했고 API mock·worker 정지/지연은 없다.
원 사용자 입력과 수치가 같으며 시험용 study/revision 식별자만 달리했다.

- 빈 상태에서 장면 없음→공개 동일 selector의 사건/생장200→running 원값·UTC/WebGL109회를 확인했다.
- 실제 계산 중 읽은 sample은 `2026-10-01T00:00:00.123456Z` **1개**다.
  완료 결과에는 같은 시작 시각과16초·32초 뒤의 원 sample3개가 있다.
  이번 검증을 여러 running 프레임의 연속 성장 관측으로 보고하지 않는다.
- 원 LAI·50구획 C/개수·온도·사건/표/그래프와 binary64·UTC를 대사했다.
  원 prefix→completed 저장 결과와 재접속 시 같은 결과를 확인했다.
- 소유 합성 권리를 철회했을 때422와 장면 제거, 정확한 원 권리 파일 복원 후 같은 결과 재조회를 확인했다.
  페이지 오류0이며 일시503 리소스 오류와 GPU 경고는 별도로 기록했다.
- worker는 새 소유 시험 작업만 attempt1 `succeeded`로 처리했다.

guard170.253초·0.25초 관측 단일/합산 peak RSS390,512,640/1,010,683,904bytes다.
512MiB/1GiB 이내이며 원본2,148항목·frozen source/자산·FD4→4와 소유 잔여0을 확인했다.
지속 사용자 서버25933/82928은 의도적으로 실행 중이며 종료0으로 세지 않는다.

## 기존 결과와 두 주소 보존

유지보수 전 활성/대기 공동 계산0과 DB 기준선을 확인했다.
정확한 pid/start_ticks/boot의 기존 두 guardian만 pidfd로 정상 종료했고 원74111/35477 모두 exit0이다.
새5174를 유지한 채 기존 frozen5173을 `run-v10`으로 복구했다.
legacy 원 생장/수확 인증 probe82944는 exit0/16.592초다.
두 주소 HTTP200·원 legacy HTML/새 accepted HTML 해시와 보호 root4의 현재 생존,
prefix guardian의 legacy root3 동적 합산과 임시5175 폐쇄를 확인했다.

기존 jobs110/job_events336/job_attempts35행과402파일·키·DSN·현재 권리를 보존했다.
기존3작업의7원 응답과 이전 token401을 확인했다. 새 시험 작업1건만 추가됐으며
성공 결과1건·publication1건의 같은 실행/결과 연결을 실제 SCRAM 읽기 전용 거래로 대사했다.
`registration_job_id`는 농장 등록 작업의 ID이고 계산 실행 ID와 다르다. 최종 검증은 공개 result ID와
계산 publication manifest를 함께 확인한다.

검증 도구 오류2건은 실패로 남겼다. 첫 준비 assertion에서 빈 정리 목록을 정수0으로 비교한 뒤
이전 읽기 probe를 중복 실행해 불변 보고서의 exclusive 생성이 거부됐다. 다음 private verifier는
농장 등록 ID를 실행 ID로 오인해 실패했다. 원 보고서/DB를 바꾸지 않고 비교를 고친 v3/tool54823에서 통과했다.
두 실패 모두 source·서비스·FD/소유 정리는 보존됐다.
원 query41113의 tool 반환은 context 재개 시 복구하지 못해 `null`로 남겼다.
불변 guard child0·41.209초·현재 서비스/원본 보존·정리와 생성된 원7응답 보고서는 확인했다.

## 사용자 확인과 다음 수용

새 보호 안내는 `serve-v10/OPEN-UI-PREFIX.private.txt`, 새 미접수 입력은
`requests/normal-user-prefix-v1.json`이다. 같은 파일을 다시 접수하면 같은 작업으로 연결된다.
토큰은2026-10-12 20:19 KST까지 유효하며 새로고침 뒤 다시 연결한다.
기존 완료 시험 작업의 재접속 필드도 안내에 있다. 토큰/농장 필드는 공개 증거에 넣지 않았다.

P6b는 완료했다. 다음 사용자 연동 수용은 **실제 계산 중 서로 다른 저장 UTC가2회 이상 전진하고
각각 같은 원값으로3D·표·그래프가 갱신되는지** 확인하는 것이다. 현재1시점 관측만으로 완료 처리하지 않는다.
기존 방정식·검토된 새 입력 판본과 정상 worker를 사용하고 관측을 위한 인위적 지연은 넣지 않는다.
그와 별개로 기후 경계/물·양분/구매 에너지→생산량·Decimal 경제의 계산 순서를 유지한다.

native context→root 수용은1,483.532초(약25분), 수용 guard/probe 합231.557초다.
준비·분석 시간과 실패 guard는 별도이며 문서/commit은 이 측정 뒤다.
P6b의 앞선0.5–1시간 추정은 실제 수용으로 대체했다. 연속 전진 검증과 전체 UI의 남은 작업량은
[계획](../tasks/plan.md#joint-prefix-view-20261010)을 따른다.
전체 UI·실제 품종/농장 Run/국내 독립 자료0·G0–G4 `not_assessed`와 생산/미래 마진/추천 보류는 유지한다.
새 build·전체 작기 재계산·전체 CI/remote·독립 농장 검증은 실행하지 않았다.
