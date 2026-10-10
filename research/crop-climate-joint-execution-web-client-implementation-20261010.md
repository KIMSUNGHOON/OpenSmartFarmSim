# E7 작물·기후 실행 웹 클라이언트 — 2026-10-10

상태: **로컬 수용**, core `616b3f5`. 새 웹113/기존 SDK160/실제 SDK·SCRAM·TLS3 = **고유276개**를 통과했다.
[고정 근거 artifact](artifacts/crop-climate-joint-execution-web-client-reference-20261010.json)는40,577bytes,
SHA-256 `2386a1cc81ee51e6f289eb5ec6a28841c63f84dce53b34c9ae991636a07b5dde`다.
[E7 인터페이스 계약](../contracts/crop-execution-link-v1.md#e7-웹-실행-클라이언트)과
[E6c 실제 runtime](crop-climate-joint-execution-runtime-implementation-20261010.md)의 후속이다.

## 구현

[새 클라이언트](../web/src/jointCropClimateExecution.ts)는 기존 `createApi`의 인증 transport와 JobStatus decoder를 재사용한다.
접수202·진행200·취소200의 메서드와 같은 저장 reader로 이어지는 result lookup helper를 제공한다.
진행 선택은 job ID와 원 farm4 참조를 받고, 결과의 farm6 중 같은 네 필드를 대사한다.
취소는 job ID만 받으며 현재 자료 조회권 없이도 명시 cancel 권한으로 호출할 수 있다.
접수 body를 복사하고 늦은 abort/원 요청·선택 변경을 거부한다. 기존 오류 code·16KiB/30초 응답 경계를 유지한다.
완료/hold·null/unavailable·재시도 queued와 취소 후 마지막 checkpoint를 구분하며 성장값/ETA를 생성하지 않는다.

예정 세 파일에 실제 제품 API 조립을 위한 `web/src/api.ts` 두 줄을 더해 core4가 됐다.
나머지는 새 클라이언트/집중 검사와 기존 실행 계약이다. 새 패키지나 backend 변경은 없다.
검증용 Node entry만 별도 비압축 번들로 만들었다. 제품의 SSR 호스팅 도입을 뜻하지 않는다.

## 실제 실패와 수정

최초 실제 접수 응답은202였으나 새 decoder가 기존 JobStatus의 `+09:00` 시각을 거부했다.
원 응답 생성/갱신 시각은 `2026-10-10T14:52:22.438782+09:00` / `.438783+09:00`였다.
작업 시각에 `Z`만 요구한 클라이언트 오류였다. 기존 API 형식은 바꾸지 않고 원 offset 문자열을 보존하며
정렬/상한 검사 때만 마이크로초 instant로 환산하도록 수정했다. 계산 시간축은 벽시계와 비교하지 않는다.
UTC/offset 시각이 같은 instant를 가리키는 집중 사례를 추가하고 실제 동일 경로를 다시 통과했다.

원 실패 phase·출력/종료·이전 번들과, 원 pin에 SHA가 정확히 일치하도록 복원한 실패 source를 private state에 보존했다.
초기112개 통과는 최종113개와 중복 집계하지 않았다. 최종 여덟 검사 묶음에서 core4 SHA가 모두 같다.
전체522개 backend Python pin도 캡처/클라이언트/빌드 동안 동일하다.

## 검증 범위

| 범위 | 통과한 근거 |
| --- | --- |
| 새 웹113개 | 닫힌 DTO/원 ID·farm·정수·시각·상태 조합, 잘못된 입력/응답, idempotent 접수, abort/timeout/늦은 선택 변경, 기존 오류/stream 제한 |
| 기존 SDK160개 | joint 저장 reader·기존 API·farm/economic API의 집중 회귀 |
| 실제 정상/hold2개 | 컴파일한 실제 SDK→검증 TLS runtime 접수→독립 자동 소비→같은 job 진행→선택한 원 저장 결과 조회 |
| 실제 취소1개 | 실행 중 서버 자료 조회권 철회 뒤 SDK 조회422/invalid_request·취소 수락·실제 소비기 확인·canceled와 결과0 |
| 실제 TLS 거부 | 위 세 경로마다 CA를 신뢰하지 않는 Node 호출이network_unresolved로 거부됨; 검증된 CA로만 정상 통신 |
| 타입/빌드 | 최종 TypeScript·검증용 client bundle·소유 출력의 제한된 `minify=false` 제품 빌드 |

실제 SDK의 반환 값은 각 원 HTTP 응답을 JSON 해석한 값과 같으며 진행은 실제 query 반환 값과,
저장 summary는 기존 current reader의 값과 같다. 이 대사는 원 시각 문자열과 count/ID를 포함한다.
새 독립 수치 모델 대사나 SDK 재직렬화 bytes와 서버 canonical bytes의 동일성 주장으로 확대하지 않는다.
접수에는 이미 실행/종료된 원 job도 유효하며, 취소 수락을 즉시 canceled로 바꾸지 않는다.
진행/저장 조회21개 호출 계수는0이다. 정상/hold 소비기는 각각16걸음, 취소 소비기는 수치 호출0·실제 종료0이다.

Node는 실제 loopback HTTPS 요청을 보냈고 인증서 검증을 끄지 않았다. 모의 fetch 응답은113개 unit 범위에만 쓴다.
세 native 시험의 작업자에는 UUID를 전달하지 않았으며 기존 소비기가 작업을 발견했다.
원 private runner/번들/입력·wire/manifest/log/프로세스 identity는 보호 state에 보존하고 공개 artifact에는 비밀 없는 결과와 해시를 둔다.

## 시간·자원·현재 화면

기존 native Codex CLI `gpt-6.1-sol`/`xhigh`의 `2026-10-10T05:40:08.010Z` context를 확인했다.
LF 포함 SHA는 `20c2364d856fc74290fa96d92f65ff3d9697ab327f224ce3d2f755850a2fd336`다.
재귀/runtime CLI 실행0, native→최종 집중 terminal은1,163.651초(약19분), 문서/commit은 별도다.

최종8/앞선4의 총12개 controller가 모두 terminal이다. 예상 밖 pytest 실패는 위 timezone 오류1개다.
실패 포함 단일 PID 최대383,475,712bytes·보호 서비스 포함 합 최대501,788,672bytes로512MiB/1GiB 안이다.
.25초 감시·phase240초 상한을 지켰고 FD4→4·소유 프로세스/PG/임시PG/passfile0·원본2,148항목을 보존했다.
기존 preview source/assets·세 보호 identity와 실제5173 HTTP200/HTML SHA
`5e5ba2733288afc0422a03481431ba4e3804e3fc265a7ac7bd3bdb3167f1c9e1`가 같다.

현재5173은 완료 합성166일의 저장 결과이며 새 실행 UI로 전환하지 않았다.
새 클라이언트는 제품 API에 조립됐으나 E8 자동 갱신 화면·E9 실제 브라우저/사용자 전환이 남았다.
일반 압축 빌드·브라우저·전체 suite·CI는 실행하지 않았다. 제한된 빌드를 운영 용량 수용으로 확대하지 않는다.
남은 E8/E9 raw 합2–4시간에 문서/검토/통합 여유를 포함해 **3–6집중시간 잠정**이다.
10월10일 오후 연속 진행·하루6집중시간 가정의10월10일 밤–11일 KST이며 E9 실측 뒤 갱신한다.
계산 중 확정 prefix3D·최종 UI 전체·공동 전체 작기/자원/경제·독립 자료 확보/운영 날짜는 이 추정에 포함하지 않는다.

실제 crop Run/독립 국내 농장 자료0·G0–G4 미평가·생산/미래 마진/순위 hold와 운영 기반 고정/push hold를 유지한다.
다음 한 단계는 **E8 U3 계산 화면**이다.
