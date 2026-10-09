# 같은 저장 작기 결과의 실제 runtime/API 수용

상태: **로컬 소프트웨어 수용, 2026-10-06 KST**. 후보 source snapshot
`088ca4d2ec486823e9a97334b6c8838f2ba60d92`의
[긴 실제 검증 영수증](artifacts/crop-cycle-api-runtime-long-reference-20261006.json)을 확인했다.
[초기 진행과 세 실패](crop-cycle-api-runtime-progress-20261006.md),
[원천 읽기 범위 수정](crop-cycle-market-read-scope-implementation.md)의 영수증은 보존한다.
새 framework·상주 service·schema·농업/경제 산식 변경은 없다.

## 실제 검증과 범위

원 등록25시간/11,400걸음 시험이 **1통과·1deselected/1510.65초(25분10초)**에
완료됐다. 원 worker128전이와 응답30초/2MiB, TLS 신뢰 검증을 유지했다.
독립 control flow는 고정된 원 rate 함수를 공유하므로 독립 생물학 검증은 아니다.

| 확인 항목 | 실제 결과 |
| --- | --- |
| 원 시점/사건 | 27 sample·5 event, 원량·UTC·순서/전체 참조 대사 |
| 전체 HTTPS 응답 | 11개: summary2·sample5·event4 |
| 원 페이지 | nonempty7·빈 종단2 |
| 최대 전체 응답 시간/크기 | 15.839875초 / 64,785bytes |
| 재시작 | 1회, 원 요약과 동일, HTTPS server2회 종료 |
| 조회 계산 | RHS0회 |
| native 자원 | nice10·PG16.15, child peak RSS146.8828125MiB |
| 정리 | 역할/schema/test password/server0·custody FD0, PostgreSQL 중지·private cluster/admin password 삭제 |

부분 HTTP 계측도 실제11개 모두 verified/status200으로 완료했다. restart/view/offset/limit·
phase/seconds/status/bytes만 보존하고 인증 값·원천 raw·private 출력은 공개하지 않는다.
긴 성공 raw는 직접 만든 합성 공개 decoded JSON이며 wire bytes나 실제 농장 이력이 아니다.
source7·현재 math/storage/profile49개와 과거 승인 interface4개 hash를 다시 대사했다.
개발 판단은 실제 `gpt-6.1-sol / xhigh` CLI session/원 line hash이며 재귀 실행0회다.

이전 순수 설정/route47개·기존 세 옵션3개·짧은 실제1개와 긴 실제1개는
**고유52개 분할 증거**다. 단일 전체52 실행이나 전체 backend 검증이 아니다.
최종 원천 연결 수정의 고유56개 분할은 별도 선행 보완이며 숫자를 중복 합산하지 않는다.
같은 최종 source의 짧은21 TLS 응답은 최대12.764535초로 현재 권리 철회·DTO 뒤 철회·
file/DB HMAC 변조·live grants·빈 hold·재기동과 정리를 재확인했다.
현재까지 hosted CI는 `2c0f0e6`의 DB/공개 투영까지만 수용했고 이 route/runtime/연결 수정은
그 SHA 밖이다. 이 native PG16.15 실행을 hosted 잠금 환경이나 G4 증거로 재분류하지 않는다.

## 다음 산출물과 수용 기준

[cycle client](../contracts/web-crop-cycle-pages-v1.md)의5 core파일을 구현한다.
실제 short/long의 공개 summary·sample·event·hold JSON fixture, 닫힌 decoder와
한 페이지 단위 iterator, 기존 request factory 연결과 본문 변경 없는 sample helper export다.
원 참조/UTC/양·4개 수지 쌍과 새 한도·출력0/선택 시점·부분/혼합/취소·권리 오류를 검증하고
focused unit/typecheck/build와 기존 startup 의미를 보존해야 한다.
그 뒤 범위 helper → 화면/같은 UTC3D → 실제 PG/TLS/WebGL로 진행한다.

API runtime과 API 부모만 완료로 표시한다. 전체 `crop-cycle-result-pages`와 client/3D,
실제166일 부하·생과·자원/경제는 남아 있다. client2–3집중시간·별도 화면/브라우저4–6시간의
추정은 해당 실행 실적으로 갱신한다. 실제 품종 입력·독립 국내 농장 자료와 crop Run은0건이며
제품 CLI·G0–G4/생산 예측·추천은 계속 미수용이다.
