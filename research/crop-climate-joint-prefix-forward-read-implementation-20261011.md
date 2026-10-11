# 계산 전진 중 불변 판본 읽기 — 로컬 수용

2026-10-11. **P6a2b1 소프트웨어 범위 수용. P6a 실제 브라우저/P6b 사용자 적용은 미완료.**
[계약](../contracts/crop-climate-joint-prefix-forward-read-v1.md),
[후보 단계 기록](crop-climate-joint-prefix-forward-read-candidate-20261011.md),
[기계 증거](artifacts/crop-climate-joint-prefix-forward-read-reference-20261011.json).
기계 증거 SHA256: `0261933a682505277544fe386ac4771a55e1500ff97f58001349bec9cb4267e2`.
실제 native Codex CLI `gpt-6.1-sol`/`xhigh` 문맥을 확인했다. 재귀 CLI0이다.

## 구현과 원 코드 대조

core는 reader v4와 HTTP2파일, 변경 시험은 대응2파일이다. 공개 DTO/입력·수치 모델·writer·custody·checkpoint·결과 저장은 유지했다.
선택 사건/이전 latest의 전체 row·최초 UTC를 다시 읽고 현재 signed HEAD가 관측한 private HEAD와
선택 사건들의 후손임을 확인한다. 같은 active 작업의 정상 전진에서 원 페이지를 반환한다.
작업/취소/입력/권리 변경, signed rollback/fork, 사건 변경은 기존 거부 경계를 유지한다.
직렬화 후에도 원 payload hash·비공개 witness에서 같은 검사를 수행한다.

실제 후속 작업자의 보류에서 DB 역할 연결 한도 초과를 확인했다.
초기 readonly 거래에서 선택 사건을 읽은 뒤 연결을 반환해 후속 파일/DB 검사와 겹치지 않도록 했다.
역할 한도·SCRAM·사용자 DB 설정은 변경하지 않았다.
최초 미추적422의 원인은 여전히 미확정이며 후속 연결 한도 초과와 같은 원인으로 단정하지 않는다.

원 v3 조회 중 독립 private/confirmed 전진2개 RED를 보존했다.
직렬화 후 confirmed 전진도 원 HEAD `adf3cdf`의 두 core를 별도 소유 source에서 그대로 사용해503 RED를 확인했다.
이 HTTP 대조는 v4 GREEN 뒤 실행했으며 구현 전 실행으로 표시하지 않는다.
현재 v4는 조회 중/직렬화 후 각각 private/confirmed 전진4개에서 원 page bytes/hash·binary64/UTC·최초 확정 시각을 유지했다.

## 최종 동일 core의 고유265개

| 범위 | 통과 | 주요 증거 |
| --- | ---: | --- |
| HTTP |158| 실제 SCRAM/TLS9개, 원 응답·독립 전진/임대 갱신·늦은 권리/취소·비공개 witness8 fault·종료 |
| 원 reader |17| signed rollback/fork·감사 불변성·원 페이지/UTC·older/fresh·빈/64행·권리/취소/변조·정상/hold |
| 공개 투영 |44| 실제 reader/fresh·64+1행 경계·원 수치/단위·닫힌 schema·UTF8 상한 |
| runtime/설정 |43| 명시 설정·기본 비활성·fresh 기본 schema·private 파일 재검사 |
| 별도 unpaused worker |3| 실제 자동 정상/hold/cancel·원 terminal·정리 |

수용된 원 guard10개는 모두 exit0이고 skip0이다. 총 guard 실측2,581.062초(약43분)이며 조사·수정·실패 진단·문서/commit 시간은 포함하지 않는다.
이전 연결 반환 수정 전의 GREEN은 최종265개에 합산하지 않았다.
증거 저장 파일 `schema.json`의 HTTP/투영 충돌로 최초 합친 회귀는234pass/1fail이었다.
소유 시험 controller의 저장 경로를 분리한 뒤 같은 제품 코드의 해당235개 전체를 통과했다.
원 실패 로그/receipt를 보존하고 실패 묶음을 추가 통과 수로 세지 않았다.

실제 정상 경로는 공개 summary에서 발견한 **동일 selector의 events/samples 각1행200**을 계산 중 읽었다.
각 canonical records/hash·binary64/UTC가 원 terminal의 동일 records와 일치했다.
원 terminal summary bytes도 독립 current query와 같고 worker exit0이다.
API/worker trace·계산 지연/정지 장벽0이며 내부 DB 선택자 discovery를 공개 성공으로 세지 않았다.
실제 hold/cancel도 같은 최종 core와 제한된 소유 scratch PG에서 통과했다.
실제 감사 row의 변경/삭제는 기존 DB trigger가 거부했으며 별도 returned-row fault는 합성 주입으로 구분했다.

## 검토·자원·보존

정확성은 위 원 판본/현재 권리 대사로 확인했다. 전진 판정을 reader에 두고 HTTP는 같은 후검사를 호출한다.
공유 수치/저장 모듈을 변경하지 않았고 공개 schema/권한/SQL 인자 경계를 유지한다.
비공개 witness와 원 payload hash를 결속하며 새 private HEAD·token/row/key를 응답에 넣지 않는다.
초기 DB 연결 반환과 기존 유한 이력/페이지 상한을 유지한다. 운영 부하/SLA·전체 작기 검증은 이 시험 범위가 아니다.

단일/합산 최대 RSS168,427,520/1,030,877,184bytes로512MiB/1GiB 이내다.
각 guard의 source·원본2,148개·두 사용자 frozen source/dist와 보호 root4를 보존했다.
FD4→4, 소유 프로세스/PG·임시 PG/인증 파일 잔여0이다. 사용자 서버 중지0·원격 작업0이다.
원격 CI·전체 저장소 CI는 실행하지 않았다.

## 다음 사용자 확인 단계

1. **P6a:** 실제 제품 브라우저/WebGL에서 unpaused 계산 중 같은 selector/UTC의3D·표·사건을 원 응답 및 terminal과 대사한다. 정상/hold/cancel·빈/재접속·현재 권리를 포함한다.
2. **P6b:** 수용된 frozen 후보를5174에 적용하고 기존 결과/현재 키·권리·두 주소와 접속 안내를 확인한다.

현재5173은 완료 합성166일 저장 재생,5174는 상태/확정 checkpoint 자동 조회와 종료 뒤 저장3D다.
이번 수용으로 사용자5174의 계산 중3D를 활성화하지 않았다.
기존 WSL 실측에 따른 두 서비스의 유지보수/복구 검증 창을 후속 브라우저에 적용한다.
P6a0.5–1.5시간·P6b/복구0.5–1시간은 후속 잠정 작업량이며 완료 날짜는 실제 WebGL/자원 관측 뒤 갱신한다.
최종 UI·전체 작기·실제 품종/독립 자료의 일정과 구분한다.
실제 농장 Run/독립 국내 자료0, G0–G4 `not_assessed`, 생산/미래 마진/추천 보류를 유지한다.
