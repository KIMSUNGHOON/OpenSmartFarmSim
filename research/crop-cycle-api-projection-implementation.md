# 긴 작물 연구 결과의 공개 투영 수용

상태: **2026-10-06 KST 로컬 소프트웨어 수용**. 구현 판본은
`7e9bbe8e115044ff4109e32acac3053effb4c375`이며
[영수증](artifacts/crop-cycle-api-projection-reference-20261006.json)에 파일·시험·CLI 증거를 고정한다.
[DB 저장](crop-cycle-db-custody-implementation.md) 뒤 첫 API 자식이며,
인증 route·실제 runtime/TLS·client·새 성장3D 수용은 아니다.

## 구현과 확인한 결과

`api_crop_cycle_replay.py`는 원 DB packet, 검증된 terminal metadata와 원 context manifest,
선택한 원 sample/event page를 닫힌 공개 DTO로 투영한다. manifest·ID·hash·판본·단위·UTC·
원 float64 양을 대사하고 tenant·권리 선언 원문·checkpoint·경로·입력 사건 ID는 공개하지 않는다.
summary와 page는 별도 응답이며 reader의 byte budget으로 짧아진 page도 원 next를 보존한다.
API가 실제 농장/입력 권리를 승인하는 기능은 다음 route/runtime의 서버 저장 문맥이 담당한다.

| 실제 검증 | 결과 | 범위 |
| --- | --- | --- |
| 짧은 투영 시험 | 42개, 9.73초 | 실제 불변 합성 artifact 6프로그램, 원 UTC/양, 잘못된 참조·타입·수지·미래/중복 page 거부 |
| 긴 투영 시험 | 1개, 106.09초 | 실제25시간/11,400걸음, 원27sample/5event, 7순차 page, 읽기 중 RHS0회 |
| 전체 고유 목록 | 43개 | 두 실행의 분할 합계. 단일43 GREEN 또는 HTTP/DB 권한 검증으로 표시하지 않는다 |
| 기존 파일 | 53개 hash 일치 | 기존 계산·프로필·저장·API 판본 그대로 |

완료지만 출력0인 프로그램, 시작 전/사건/분수 solver 시각의 numerical hold도 실제 artifact로
확인했다. 실패 trial을 정상 sample로 만들지 않고 last_confirmed/원 진단을 보존한다.
첫 RED는 새 module 부재의 import 실패였으며 기능 반례 RED로 표시하지 않는다.
DTO 한도는40,000,000step/131,072record, sample64/event8, 응답2MiB다.
한도 최대 규모의 실제 계산·전체 작기 부하를 이 투영 시험으로 수용하지 않는다.

시험용 binding/progress는 닫힌 형태의 합성 metadata다. 실제 서버 HMAC·농장 권리·Bearer·
TLS/SCRAM 검증이 아니며 G0–G4는 모두 미평가다. 순수 artifact 시험에는 PG cluster를 만들지
않았다. WSL에서 native 시험은 순차 실행했고 긴 실행은 nice10이었다. 별도 RSS 측정은 하지 않았다.

## 다음 한 단계

[API 계약](../contracts/api-crop-cycle-pages-v1.md)의 `api-crop-cycle-route`를5 core파일로 구현한다.

1. exact store·같은 jobs/farm/principal에서 한 `_read` 문맥으로 원 terminal/page를 선택한다.
2. Bearer 권한, 닫힌 query·본문 거부, 기본 비활성503과 오류 비노출을 확인한다.
3. 전체 DTO bytes 생성 후 현재 권리와 선택 progress를 다시 검사하고 GET RHS0회를 확인한다.
4. OpenAPI snapshot/전체 route·권한 시험 및 기존 startup 경로를 보존한다.

실제 TLS30초/2MiB·재시작/철회/변조·자원 정리는 다음 `api-crop-cycle-runtime`에 남는다.
세 자식 뒤 client → 같은 저장 ID/UTC 성장 연구3D → 작기 부하 → 근거 있는 생과·자원·경제 순서다.
일정은 기존 API 전체4–6집중시간, client2–3시간, 장면/브라우저4–6시간의 작업 분해를 유지하되
현재 투영 실적을 반영한다. **새 긴 결과 연구3D10월6–10일 KST 잠정**은 CI 대기와 실측 응답
실패 시 갱신한다. 실제 품종/작기 입력·국내 독립 검증 자료0건으로 생산 예측/추천 날짜는 미정이다.

## 판단 도구

후속 `2c0f0e6`의 [CI5개](artifacts/crop-cycle-api-projection-ci-20261006.json)는
Backend4,081개·별도 UID4개·여섯 동일 전체 목록·DB/비밀 정리·집계와 작성 첫 시도7job가
모두 성공했다. DB 저장과 이 공개 투영의 hosted 증거이며 후속 인증 route/runtime·
client/3D와 실제 작물 입력은 해당 SHA 밖이다. 취소/재실행/시간 한도 변경은 없었다.

현재 Codex CLI `gpt-6.1-sol / xhigh`에서 판단했다. 실제 turn_context 시각
`2026-10-05T23:09:43.527Z`, 원 line SHA
`a980a103ab9c728f1c722c9656ec02fe10f5ed9f5eaa5a0d9aa235f486aa97ea`이며
재귀 CLI 실행0회다. 초기 투영 설계의 별도 context도 영수증에 남긴다.
제품 런타임 CLI/G0–G4 승인을 이 개발 세션 기록으로 대신하지 않는다.
