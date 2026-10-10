# 계산 중 확정 페이지의 공개 투영 — P2 로컬 수용

2026-10-10 KST. core `376c774`의 새 응답 모델·집중 시험2파일을 수용했다.
[원 실행 증거](artifacts/crop-climate-joint-prefix-projection-reference-20261010.json)는 16,803bytes,
SHA-256 `9bd9eb224bb232419759f0817c4b0322a3cf61e3c17401ee3bdd0e89cc365e70`다.
짧은 합성 계산의 P1 내부 record를 공개 응답으로 투영하는 단계이며 HTTP/사용자 화면 수용은 아니다.

## 산출물과 경계

`project_prefix(PrefixRead)`와 `_public_bytes(PrefixReplay)`는 닫힌
`joint-crop-climate-prefix-replay-v1` 응답을 만든다. 최상위 prefix_status의 accepted/none/closed와
page kind의 samples/events를 discriminated union으로 구분한다. accepted의 summary/page는 하나만 존재하고
none/closed의 reference/summary/page는 모두 null이다. 이 투영 자체가 표시권·서명·관문 승인은 아니다.
현재 권리·HMAC·계보·DB 수용 검증은 같은 P1 reader가 맡고, 다음 P3가 요청 전후 인증과 결합한다.

같은 selector/최초 checkpoint 시각·attempt, study/revision, 기존 공개 Farm/Input/Manifest/TimeGrid를 전달한다.
기존 Sample/Event 타입과 event allowlist를 재사용해 원108상태/50구획·장부·단위·UTC를 보존한다.
내부 farm binding/권리·검토 원문·tenant/registration job·원 event 입력·서명/자격증명·가짜 result ID는 전달하지 않는다.
원 사건 입력의 hash를 대사한 뒤 before/after 수치만 기존 `_event` 규칙으로 투영한다.
64 sample/8 event·전체 UTF-8 응답2MiB를 제한하며 끝/빈 페이지·계산/마지막 저장 시각을 구분한다.
기존 numerical/worker/custody/result/완료 DTO·DB schema·패키지 의존성은 바꾸지 않았다.

## 통과한 검증

최종 두 source SHA가 같은 **고유44개, skipped0**를 순차2그룹으로 통과했다.
42개는 권리/서명이 승인되지 않은 owned projection fixture의 타입·원 값 검증이며,
2개는 실제 PostgreSQL/SCRAM의 현재 P1 읽기→공개 응답 연결이다. 앞선 smoke의 중복2개와 실패2개는 고유 수에 더하지 않았다.

| 범위 | 확인 |
| --- | --- |
| 원 값·공개 범위 | summary/sample/event의 원 수치·단위·UTC·selector/최초 시각; event 입력·private 필드 제외; 원 입력/FD 보존 |
| 타입·혼합 거부 | bool/int/string/NaN/Inf 수치, 잘못된 단위/50구획/음수 재고, UTC/elapsed/order, count/offset/limit/다음 페이지, 혼합 summary/page, binding/manifest/grid, attempt/작업/취소, event 입력/code/state 거부 |
| 빈 상태/상한 | none/closed/ready 행0·UTC null·가짜 프레임0; 끝 페이지·limit64/8; 모델의 list 변경 뒤 재직렬화 재검증; 닫힌 JSON schema |
| fresh fixture | 별도 Python에서 같은 공개 응답·계산/쓰기0. 인증된 조회로 주장하지 않음 |
| 실제 SCRAM | running의 원 P1 값과 같은 공개 응답·새 tail 뒤 이전 판본·현재 표시권 철회 거부·취소 후 closed |
| 실제 fresh | 별도 Python/SCRAM에서 현재 DB/서명 파일을 읽고 투영해 조회 시각 외 같은 응답·DB 무변경·계산/쓰기0 |
| 실제64+1 |65개 원 sample을64+1로 읽고 oneshot 원 값/UTC와 대사; 원 페이지/next offset·DB 무변경 |

조회/투영의 수치 준비·복원·RHS·advance·수용·결과/작업 쓰기21계수는 모두0이다.
실제 read 검사의 DB digest는 동일하며 새 tail 수용/취소는 검사 경계 밖의 명시적 쓰기다.
실제 DB fixture의 최종 schema/role 잔존도 각각0이다. 전체 module 단일 실행/전체 backend 회귀가 아니다.
응답2MiB 경계는 직렬화 결과를 주입한 상한 시험이며 실제2MiB 계산 결과로 주장하지 않는다.

## 발견한 실패·비용·자원

첫 정상 fixture2개는 내부 record의 JSON canonical 비교에서 거부됐다. 내부 불변 페이지의 ASCII escape 형식과
농장 결속의 UTF-8 형식이 달랐다. 각 원 저장소의 canonical 규칙을 사용하도록 수정하고 원 포맷은 보존했다.
실패 receipt/log와 수정 전 source2파일의 정확한 SHA를 private로 보존했고 최종44개를 재검증했다.
진단은 예외 유형/함수/행만 기록했으며 권리 원문이나 자격증명을 출력하지 않았다.

실제 P1 read 이후의 투영+직렬화는 6.361–11.793ms였다.
실제 summary/sample/event 응답은 5,149/13,682/25,087bytes,
64/1 sample의 전체 응답은 663,085/15,470bytes다. P1의 앞선 원 조회6.877–6.905초는 별도 비용이다.
새 HTTP/순차 UI 갱신 지연은 P3–P6에서 측정해야 한다. 이 수치로 장기 작기·운영 용량을 수용하지 않는다.

native CLI `gpt-6.1-sol/xhigh`의10:13:16.532Z context를 확인했다. 재귀/runtime CLI0이다.
native→최종 guarded terminal은 883.695초(약15분), 문서/commit은 별도다.
최대 단일152,834,048/소유+보호 합785,899,520bytes로512MiB/1GiB 안이었다. nice19/threads1/.25초 표본을 사용했다.
원 source15파일·원본2,148항목·두 사용자 guardian/source/assets 보존, 실제 종료0·FD4→4·소유 process/PG/temp/passfile0을 확인했다.
전체 backend/web·기존 terminal 투영 suite 재실행·typecheck/build·새 HTTP/브라우저·사용자 서버 전환·166일 공동 계산·remote CI/fetch/push는 실행하지 않았다.

## 다음 단계와 사용자 상태

다음 P3a는 인증된 prefix summary/sample/event GET이다. 현재 계정/scopes·같은 reader 객체,
selector/query/body·오류 상태·원 응답과 현재 권리를 실제 SCRAM/HTTPS에서 확인한다.
P3b 조립→P4 SDK→P5 같은 원 UTC의 부분3D→P6 실제 브라우저/사용자 기동 순서를 유지한다.
남은 작업 분해 합계는 **5.25–10.5집중시간 잠정**, 작은 합성 화면의 **2026-10-11 KST**는 연속 작업/검증·WSL 여건의 조건부 범위다.
현재5174의 상태 자동 조회/완료 저장3D와5173의 완료166일 재생은 그대로이며 P2를 사용자 서비스에 배포하지 않았다.
계산 중 성장3D·전체 U3/최종 UI, 실제 Run0/독립 국내 농장 자료0·G0–G4 not_assessed·생산/자원 구매/미래 마진/추천 보류를 유지한다.
독립 자료 확보와 기후 경계/자원·Decimal 경제 연결은 병행하며 전체 제품/현장 관문의 날짜는 미정이다.
