# 등록 연결 수명의 통합 회귀 — 2026-10-19 KST

상태: **같은 최종 application source의 관련58검사·검토로 로컬 통합 수용**.
[본체52검사](registration-connection-lifetime-core-20261019.md) ·
[연결 계약](../contracts/farm-registration-connection-lifetime-v1.md) ·
[기계 증거](artifacts/registration-connection-lifetime-integration-20261019.json).

application 기준은 `c08d56453a7d95d87c29462aec5cfe206cebff6e`다.
이번 단계에서 제품 코드를 더 수정하지 않았다. 본체의 실제 paired19.81%/21.30% 감소는
앞선 두 구간의 한정된 관측이며 이번 회귀 시간으로 일반 처리량을 추정하지 않는다.
조사·검토는 현재 native Codex CLI `gpt-6.1-sol/xhigh`에서 수행했고 실제 문맥 시각/해시를 기록했다.
재귀 CLI·하위 에이전트는 사용하지 않았다.

## 같은 source의 원 회귀

[앞선 capture Pending58](crop-solar-capture-pending-http-implementation-20261019.md)의 대상과
수용 단언을 그대로 현재 코드에서 실행했다. 본체52는 여기에 더하지 않는다.

| 경로 | 검사 | 실제 도구/종료 | guard 초 |
| --- | ---: | --- | ---: |
| HTTP 접수/조회/취소 오류 분류 | 24 | 16857:0 | 2.401386 |
| 실제 인증 SCRAM/TLS Pending/복구·권리/접근 | 1 | 67429:0 | 41.469598 |
| 읽기 current/잠금/HEAD/사용량/권리 | 7 | 4085:0 | 207.464668 |
| worker 정상/수치 hold·청크 취소·임대 재개 | 5 | 85335:0 | 259.104403 |
| worker 검증 도중 취소·입력 변경·임대 만료 | 8 | 32711:0 | 230.394748 |
| query 현재 권리·원 UTC·늦은 권리/입력 변경 | 6 | 34636:0 | 164.396209 |
| query 잠금/서명/디렉터리·정상/hold 원 결과 | 7 | 12839:0 | 250.166165 |

합58건·guard1,155.397초(약19.3분)다. 이전58/본체52·중간 게시를 중복 합산하지 않았다.
각 stage에서 본체의 최종 제품6파일/새 검사 SHA와 현재 bytes가 같음을 대사했다.
실행 순서·원 test node/parameter·단언·actor/입력/chunk/retry/RSS를 바꾸지 않았다.

실제 TLS에서 일시 상태 변경은503·복구 뒤200, 권리 hold는422·접근 거부는403이었다.
반환 수치·UTC와 DB 불변을 확인했다. 권리 실패를 일시 Pending으로 낮추지 않았다.
작업자의 정상/수치 hold와 원 checkpoint·모든 저장 상태/UTC·원자 결과/사건 등록을 대사했다.
취소·입력 변경·임대 만료는 잘못된 결과를 게시하지 않았고, 재개는 기존 prefix를 채택한 뒤
남은 구간만 계산했다. 조회는 현재 권리/서명·늦은 변경을 검사하며 계산/SQL 변경0을 유지했다.
이것은 기존 합성 입력의 제어된 로컬 경로이며 독립 원64 수용이 아니다.

## 자원과 검토

모든 stage에서5root·원본2,148항목·두 기존 UI source/assets·512MiB/PID/합1GiB,
FD4→4·소유 프로세스/PG/임시/passfile0을 확인했다.
합산 최대 RSS1,063,387,136bytes, 단일169,320,448bytes다.
실제 DB를 쓴 관련 stage의 정리 증거도 확인했다. 보호 서비스를 중단하지 않았다.
중간37/58 진행 기록은67852:0에서 두 UI에 동일 no-store JSON/HTTP200으로 게시했다.
원 HTML과 환기2,173파일은 보존했고 UI code/DOM/WebGL은 변경·재검사하지 않았다.

정확성은 실제 현재 권한·자료/세션·트랜잭션 경계와 위 실패/정상 사례로 검토했다.
단순성은 등록 수명 안의 물리 연결 하나·여섯 명시 읽기 위치이며 범용 pool이나 전역 method 교체가 없다.
기존 `.connect()` 메서드와 typed 오류 경계를 보존하고 현재 역할 감사를 생략하지 않았다.
수식/모델/매개변수·money 계산·패키지/lock·원 독립 actor는 변경하지 않았다.
확인한 로컬 통합 범위의 미해결 지적은 없다. 독립 처리량·사용자 배포·자료/관문은 별도다.

## 다음 수용

다음은 변경 source의 원 계측 OFF64 독립 API/자동 worker 정상이다.
원64/chunk1/조회·retry360/RSS·64/start1/CLI0/attempt1/success1,
두 전진 prefix·원 수치/UTC·두 actor 종료0·FD/역할/schema/소유 PG/임시 정리 proof를 대사한다.
동일 미완료 source를 근거 없이 반복하는 실행이 아니라, 본체 변경과 현재58 회귀를 통과한 실행이다.
원360초에 준비/정리·CI 대기가 추가된다. 통과를 미리 단정하거나 전체 완료일을 확정하지 않는다.

이후 독립 hold→실제 HTTP 취소→계산 중 WebGL→WSL 용량/사용자 적용 순서다.
전체 backend/browser·새 Solar 배포/계산 중3D·실제 농장 Run/자료 권리·독립 현장/미래/대응 비교,
G0–G4·실제 생산/경제 추천은 미수용이다. 실제 농장 Run0·전체 완료일 미정·goal active를 유지한다.

94880:0에서 현재58·source/원 actor/header·로컬 링크2,371개를 대사하고 두 UI의 최종 진행 기록을
HTTP200·같은 no-store JSON bytes로 게시했다. 원 HTML/환기2,173파일을 보존했다.
게시 guard1.366722초·합 RSS888,389,632bytes·5root·FD4→4·소유 프로세스/PG/임시/passfile0이다.
UI code/DOM/WebGL은 수정·재검사하지 않았다.
