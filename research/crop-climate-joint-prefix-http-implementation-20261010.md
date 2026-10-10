# 계산 중 확정 페이지의 보호 HTTP — P3a 로컬 수용

2026-10-10 KST. core `8da1776`의 명시 route installer·집중 시험2파일을 수용했다.
[원 실행 증거](artifacts/crop-climate-joint-prefix-http-reference-20261010.json)는 18,982bytes,
SHA-256 `ed67891911df895387a5b4f065e309f6c8b020c5bca571a6988c1209aa4e752a`다.
짧은 합성 작물·기후 계산의 실제 SCRAM/검증 TLS 응답이며 제품 runtime 활성화/사용자 화면 수용은 아니다.

## 산출물·조립 경계

검증된 P1 reader가 있을 때 `install_joint_prefix_routes`로 다음 GET을 명시 등록한다.

- `/v1/jobs/{job_id}/crop-climate-joint-execution/prefix`: 최신 수용 summary 또는 none/closed
- 위 경로의 `/samples`, `/events`: 명시 publication sequence·HEAD/proof selector와 start/limit

같은 jobs/server/result store/farm/principal 객체와 source binding을 확인한다.
query가 없거나 다른 객체가 섞이면 installer를 거부한다. 현재 기본 App은 새 installer를 호출하지 않으며
기존 56경로/262스키마의 OpenAPI와 기본 source를 보존했다.
P3b에서 명시 옵션이 켜지고 실제 reader를 조립한 경우에만 새 경로를 등록한다. 생략/False의 기본 경로 부재를 유지한다.
새 모듈만 import하는 별도 Python은 prefix 운영 모듈/연결0·FD 동일을 확인했다.

metadata+crop_result_read와 요청 전후 계정을 검사하고, 변환 뒤 현재 DB 작업/cancel·농장 입력/표시권을 다시 읽는다.
이 마지막 재검사는 기존 pinned `_bundle`, `_input`, `_current`·공개 JobStatus를 재사용하며 readonly SQL snapshot이다.
변환 중 취소/작업 변경은 Pending으로 버리고 늦은 표시권 철회는 hold로 거부한다.
P1의 HMAC/계보·현재 자료 검사를 HTTP helper가 대신하지 않으며 새 수치 계산/서명/수용/결과 쓰기를 하지 않는다.

canonical UUID/hash/정수·필수 selector·중복/추가 query·본문/연결 종료·64/8/끝 범위·UTF-8 전체2MiB를 검사한다.
401/403/404/409/422/503과 고정 오류 envelope·no-store를 사용한다. 권리/변조 거부를 일시 대기로 바꾸지 않는다.
OpenAPI에는 필수 selector와 기본 start/limit·응답 판본/범위가 명시되어 있다.

## 통과한 검증

최종 같은 두 source SHA의 **고유110개, skipped0**를 두 그룹으로 통과했다.
105개는 수치 투영을 대체한 HTTP 제어 fixture이고,5개는 실제 SCRAM/검증 TLS의 원 P1→P2→HTTP다.
첫 그룹의 앞선99개 중복 통과와 실패1개는 최종 고유 수에 더하지 않았다. 전체 module 단일 실행/전체 backend 회귀가 아니다.

| 범위 | 실제 확인 |
| --- | --- |
| 요청/조립 | 잘못된 객체·누락/변조된 binding 거부, UUID/selector·정수/범위/본문/중복·추가 query 거부, metadata/read·인증 없으면 dispatch0 |
| 응답/계정 | 고정 오류·late token/tenant의 성공/실패 차단; missing과 invalid bytes 구분; 순차 기본64/8·no-store/판본 headers |
| 연결/계약 | 요청 전 disconnect, 취소된 async 요청/송신 실패의 thread 종료·identity 정리; 기존 기본 API 계약 동일·fresh import 연결0 |
| 실제 running | 읽기 scopes만으로 none→수용 summary/sample/event·원 응답 bytes/selector/UTC; 끝 페이지200/범위422·미수용409·없음404·실제 파일 잠금503 |
| 늦은 표시권 | 실제 직렬화 뒤 source rights 철회 시422·수치 미전달; 표시/read권 없어도 기존 owner cancel은 가능 |
| 늦은 취소 | 별도 Python/SCRAM이 직렬화 뒤 실제 취소; 현재 DB 재검사에서503·이미 만든 수치 미전달 |
| 기존 결과 | 정상 완료/수치 hold의 prefix는 closed; 기존 진행 GET의 결과 ID 동일·DB 무변경 |

실제 읽기 경로의 수치 준비·복원·RHS·advance·수용·결과/작업 쓰기21계수는 모두0이다.
무변경 검사의 DB digest는 동일하며 별도 actor의 실제 취소는 그 주장에 포함하지 않는다.
표시권/취소의 관측 hook은 제어된 시험이며 사용자 서비스의 계산 장벽이 아니다.
실제 fixture 종료의 schema/role은 각각0이다.

## 실패 수정·지연·자원

첫 제어 그룹은 잘못된 직렬화 반환 None을 대상 없음404로 분류해1개가 실패했다.
수치 record가 있는데 직렬화 bytes가 없거나 상한을 넘으면503이 되도록 먼저 검사했다.
실패 receipt/log와 수정 전 source2파일의 정확한 SHA를 보존했고 최종110개를 다시 검증했다.

실제 TLS 응답은 총18회이며 최대8.235초·25,087bytes였다.
최초 running 묶음의 성공 응답은 4.937–7.841초였다. 인증·원 읽기·투영·마지막 권리/DB 재검사와 전송을 포함한다.
모든 관측 응답은30초/2MiB 안이었다. 누적 prefix 비용·전체166일·운영 용량이나 자동 worker와의 동시 화면 관측을 수용하지 않는다.
후자는 P3b의 실제 자동 소비/재시도와 P6의 장벽 없는 브라우저 관측에서 확인한다.

native CLI `gpt-6.1-sol/xhigh`의10:33:22.288Z context를 확인했다. 재귀/runtime CLI0이다.
native→최종 guarded terminal은 1037.090초(약17분), 문서/commit은 별도다.
nice19/threads1/.25초 표본의 최대 단일172,859,392/소유+보호 합766,271,488bytes로512MiB/1GiB 안이었다.
원 source17파일·원본2,148항목·두 사용자 guardian/source/assets를 보존했고 실제 종료0·FD4→4·소유 process/PG/temp/passfile0을 확인했다.
전체 backend/web·기존 route runtime suite 재실행·typecheck/build·새 runtime 옵션/자동 worker 조립·브라우저·사용자 서버 전환·166일 공동 계산·remote CI/fetch/push는 실행하지 않았다.

## 다음 단계와 외부 의존성

다음 P3b는 기존 API/runtime/operator 설정과 집중 시험을5파일 이하로 대조·조립한다.
기본 생략/False·기존 계약/원 결과·같은 권한/factory, 별도 자동 worker의 running prefix/일시 충돌 재조회→정상/hold·취소를 실제 TLS에서 확인한다.
P4 SDK→P5 같은 저장 UTC의 부분3D→P6 실제 브라우저/사용자 기동 순서를 유지한다.
남은 작업 분해 합계 **4.5–9집중시간 잠정**, 작은 합성 사용자 화면의 **2026-10-11 KST**는 연속 작업·검증/WSL 여건의 조건부 범위다.
현재5174의 작업 상태 자동 조회/완료 저장3D와5173의 완료166일 재생은 그대로이며 새 route를 사용자 서비스에 배포하지 않았다.
계산 중 성장3D/전체 U3·최종 UI, 실제 Run0/독립 국내 농장 자료0·G0–G4 not_assessed·생산/구매 자원/미래 마진/추천 보류를 유지한다.
독립 자료 확보·기후 경계/자원·Decimal 경제 연결은 병행하며 전체 제품/현장 관문의 완료 날짜는 미정이다.
