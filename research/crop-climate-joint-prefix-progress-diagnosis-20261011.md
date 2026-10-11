# 계산 전진 중 조회 보류의 요청별 분류 — 2026-10-11

**P6a2b0 진단을 수용했다. 판본 전진을 허용하는 제품 수정과 실제 running3D는 아직 미완료다.**
선행은 [임대 갱신 수정](crop-climate-joint-prefix-lease-guard-implementation-20261011.md)이다.
[기계 증거](artifacts/crop-climate-joint-prefix-progress-diagnosis-reference-20261011.json)의 SHA-256은
`40d4e2113aced0768b8c8bbb2a1ad0a56b28e6cd990c7f6e7fff7579d5c566bf`다.
실제 native Codex CLI `gpt-6.1-sol`/`xhigh`의2026-10-11T05:40:31.654Z context에서 판단했고 재귀 CLI는0이다.

## 실행과 관측

main `6a3f732`의 reader v3/HTTP를 변경하지 않고 실제 SCRAM/검증된 TLS/별도 자동 작업자로2회 실행했다.
[공개 진단](crop-climate-joint-prefix-progress-diagnosis.py)의 최종 파일은 v2로 실제 실행했다.
v1은 소스 해시와 private 원본을 보존했다. 같은 test node의 두 진단 실행이며 고유2개 시험이라고 합산하지 않는다.
각 GET의 request ID에 실제 응답 bytes/hash·선택자·DB 차이·HEAD·예외/반환·단조 시각을 결속했다.
tracing은 API thread에만 적용했고 worker의 pause/delay는0, 기존 chunk budget8을 유지했다.

| 실제 실행 | 요약 | 같은 선택자의 사건·생장 | 원 terminal summary / 종료 | 전체 guard 시간 |
| --- | --- | --- | --- | ---: |
| v1 / 원 세션36416 |none200×3, closed200×1,503×8 |accepted 요약이 없어 요청0 |독립 current query와 원 bytes 일치 / worker·guard0 |131.122초 |
| v2 / 원 세션23791 |none200×3, closed200×1,503×4 |503×4, 종료 뒤409×2 |독립 current query와 원 bytes 일치 / worker·guard0 |134.219초 |

두 실행 모두 **accepted 공개 요약0·page200 0**이다. 전체 terminal 수치 페이지를 대사하거나 WebGL을 실행하지 않았다.
v2의 page 선택자는 공개 요약에서 얻은 값이 아니다. 해당 요청에서 실제 readonly `_history/_bundle`가 반환한
DB 수용 사건의 선택자를 진단 목적으로 사용했다. 입력 선택자나 성공 응답을 위조하지 않았고 모든 GET은 실제 reader를 통과했다.
이 내부 발견 경로를 제품 UI가 사용하거나 정상 공개 discovery가 성공했다고 보고하지 않는다.

## 요청별로 확인한 지점

| v2 request ID | 관측 | 내부 지점 |
| --- | --- | --- |
|0 |queued→simulating, attempt/token 변경 |reader `read:316`; 기존 lifecycle 거부 |
|4 |none 응답 직렬화 후 첫 DB 수용 사건 등록 |HTTP `_current_after_projection:30`; latest 비교 |
|5 / events, 선택자1 |HEAD commit1→2 |reader `read:328`; final HEAD exact 비교 |
|6 / samples, 같은 선택자1 |같은 active job에서 latest 수용 사건 전진 |HTTP `:30`; row 임대 갱신은 허용됐지만 latest 비교는False |
|7 |HEAD commit2→3 |reader `:328` |
|8 / events, 선택자2 |commit3 유지·terminal artifact 추가 |reader `:328` |
|9 / samples, 같은 선택자2 |latest 수용 사건 전진, job 다른 필드 변화0 |HTTP `:30` |
|10–12 |실제 succeeded 전이와 이후 page 요청 |HTTP `:30`, 이후 selection conflict409; 종료 경계 유지 |

v1의 request5/7/8도 final HEAD,4/6/9도 HTTP latest 변화로 정렬됐다.
lease-only 변화가 허용되는 반환을 실제 trace에서 확인했다. 추가 전진을 허용하는 비교는 아직 없다.
이번 두 실행에서는422가 재현되지 않았다. 선행 기본 scratch PG의 미추적422 원인이나 해결을 이 결과로 단정하지 않는다.
API tracing이 포함된 요청 시간은 약1.216–9.546초이며 성능 보장 수치가 아니다.

## 보존과 범위

선행과 같은 **소유 scratch PG16.15**의 `shared_buffers=16MB`, `max_connections=32`,
`work_mem=1MB`, `maintenance_work_mem=16MB`를 실제 SHOW로 확인했다. 사용자 PG 설정·DB에는 변경/접수하지 않았다.
두 사용자 서비스 중지0, 보호 root4와 자식·두 frozen source/자산·원본2,148항목을 보존했다.
.25초 표본의 최고 RSS는 단일153,710,592/합산1,054,208,000bytes였다.512MiB/1GiB 안이며 운영 용량 수용은 아니다.
각 FD4→4, 소유 프로세스/PG/passfile/임시 PG 잔여0과 실제 guard0을 확인했다.
조회의 금지된 계산/게시 호출 카운터0을 assert했고 terminal summary의 독립 query/HTTP 원 bytes를 대사했다.
전체 CI/실제 브라우저는 미실행이며 원격 작업 hold를 유지했다.

## 다음 구현과 일정

다음 한 단계는 [P6a2b1 불변 판본 전진 계약](../contracts/crop-climate-joint-prefix-forward-read-v1.md)의 reader/HTTP2파일·대응 test2파일이다.
같은 active 작업에서 선택한 DB 수용 사건을 고정한 채 현재 HEAD/새 latest가 검증된 후손일 때 원 snapshot을 제공한다.
기존 strict 비교를 단순 삭제하지 않고 선택 사건·종전 latest·관측한 private HEAD의 계보와 현재 권리를 전후에 확인한다.
실제 시작/종료·취소/attempt/input 교체의 거부는 유지한다.

첫 구현/집중 검증1–2시간 잠정이다. 이번 진단의 실제 guard 합계265.341초와 선행 P6a2a의 검증 비용을 참고했다.
별도 worker의 원 page200이 관측된 뒤 P6 실제 브라우저0.5–1.5시간, 사용자 적용/복구0.5–1시간을 재평가한다.
연속 작업의10/11 KST는 조건부 목표이며 완료일을 보장하지 않는다. 수정/자료 의존성이 남아 전체 제품 완료일은 산정하지 않는다.
두 사용자 화면의 범위는 그대로다:5173 완료 합성166일 재생,5174 상태/checkpoint 자동 조회·종료 후3D.
실제 crop Run/독립 현장 자료0, G0–G4 `not_assessed`, 생산/미래 마진/추천 hold를 유지한다.
