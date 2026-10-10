# 공동 작물·기후 보호 HTTP — E6b 로컬 수용

2026-10-10 KST. core `384733f`의 일곱 파일을 수용했다.
[원 실행 증거](artifacts/crop-climate-joint-execution-http-reference-20261010.json)는
42,884bytes, SHA-256 `3e36b0c9569400da36b4f04decac30d746d3618cc3d0677149aa5291a703c200`다.
원32초·16걸음 합성 구성의 소프트웨어 증거이며 현재5173의 서버 전환은 아니다.

## 연결과 실제 검증

인증 문맥의 tenant로 접수·진행·취소 세 경로를 조립했다.
접수는64KiB 이하의 닫힌 JSON과 기존 E1을 사용해202의 기존 JobStatus를 반환한다.
진행은 E6a의 원 canonical bytes를 최대16KiB로 전달한다.
취소는 요청 수락과 실제 종료 상태를 구분하며 cancel scope만 사용한다.
작업 호출 뒤 인증 tenant/scope를 다시 검사하고 오류는 공개 고정 문구로 반환한다.

신규 HTTP **108개**, OpenAPI 권한 **3개**, 기존 관련 **140개**, **고유251개**를 통과했다.
실제 HTTP4개와 ASGI104개를 구분하며 기본 schema 대조도 별도 기록했다.
기존 API/OpenAPI136개에는 새 권한3개가 포함되고, E6a 집중 회귀7개를 더했다. 전체 backend 실행은 아니다.

| 검사 | 실제 확인 |
| --- | --- |
| 요청/권한 | 중복 JSON·비정상 숫자·알 수 없는 필드·잘못된 권리 선언·UUID·본문/query·413/415/422·scope/인증 거부 |
| 원 접수/진행 | 실제 SCRAM·검증 TLS의 같은 E1 job·원 확정 counts/UTC/최초 DB 시각과 query 반환 bytes 일치 |
| 실행 중 취소 | cancel_requested/수락 후에도 simulating; 실제 소유 임대의 worker 확인 뒤 canceled; terminal 재요청은 수락false |
| 완료/수치 hold | 같은 result/farm/batch/zone; 원 진행 bytes와 기존 저장 GET bytes 일치; terminal 취소로 원 상태를 바꾸지 않음 |
| 권리 철회 | 실제 진행/접수422; metadata·자료 읽기/쓰기 없이 cancel만 가진 소유자 취소200 |
| 늦은 응답 | ASGI의 계정/tenant 변경 후 정상·오류 응답 차단; 요청 task 취소/전송 실패 뒤 thread·principal 정리 |
| 기존 계약 | 기존53개 API path 동일; 새3개만 추가; 닫힌 schema·각 권한 거부·credential 없는 OpenAPI check |
| E6a 보존 | 네 확장 구조화 schema 동일(제목/required 순서 제외); 원 checkpoint/heartbeat·시도2/최초 시각·미확정/잠금과 계산0 |

정상/hold 진행·저장 조회의20개 호출 계수는0이다. 명시 취소 명령은 허용하고 다른 계산/등록/작업 쓰기를 막았다.
실행 중 확정 진행 GET에서는21개 계수가0이었다. fixture의 수치 준비와 소유 임대 확인은 이 조회0 주장에 포함하지 않는다.
실제 종료 확인은 현재 임대의 `ack_cancel` 호출이며 사용자 runtime의 자동 worker 확인은 E6c/E9의 후속 조립이다.
ASGI의 계정/전송 제어 검사를 실제 외부 계정 서비스 장애 시험으로 확대하지 않는다.

## 경계 보완·실패 기록

예정 네 파일에 query의 공개 타입 이동, 생성 OpenAPI, 기존 권한 mapping 검사를 추가해 일곱 파일이 됐다.
기본 schema 생성에서 작업자를 불러오지 않도록 HTTP 모듈에 공개 형식을 두고 query가 같은 타입을 가져온다.
query는 공개 checkpoint 상한/입력 판본을 원 실행 계약과 대사한다. 기존 작물 수치 모델/worker/store와 서명 원본은 수정하지 않았다.

첫 unit 수집은 기존 결과 모듈의 운영 설정 import가 `create_app` 정의 전에 돌아오는 순환 import로 실패했다.
운영 모듈 없는 HTTP 형식으로 수정하고 fresh import의 작업자/reader/DB/socket 연결0을 확인했다.
첫 native 검사는 시험 함수 `http`가 import 모듈을 가려 요청 전에 실패했다. helper 이름을 수정하고 같은 lifecycle을 재검증했다.
원 실패 두 개와 source/로그/원 종료를 보존했다. 초기100개 통과는 추가4개/최종104개와 중복이므로 고유 수에 더하지 않는다.
실제 lifecycle 묶음은 생성 OpenAPI와 기존 권한 mapping 추가 전이며 route/API/query 코드는 모든 수용 묶음에서 최종 SHA다.
schema 묶음의 OpenAPI 쓰기는 그 파일만 허용한 감시 안에서 수행했다. 그 뒤 최종 export/권한/회귀를 통과했다.

## 관측 시간·자원

native Codex CLI `gpt-6.1-sol/xhigh`의04:44:12.429Z context를 확인했다.
원 LF 행 SHA는 `eab830725f271e788be2251d596d732b8a47a630279596cf874e33d376f4d390`다.
recursive/runtime CLI 실행0; native→최종 집중 terminal1,522.129초(약25분), 기록/commit은 별도다.

| 실제 로컬 HTTPS 요청 | 관측 초 |
| --- | ---: |
| 같은 E1 접수 |1.827|
| 미실행 진행 |2.960|
| 확정 구간 진행 |7.490|
| 완료/hold 진행 |7.735 / 8.079|
| 기존 완료/hold 저장 GET |4.845 / 5.067|
| 취소 요청/terminal 재요청 |0.068–0.080|

각 값은 작은 합성 fixture의 관측이며 평균·상위 분위수·전체 작기/운영 용량 수용이 아니다.
단일 요청 정산 후 대기하는 polling과 마지막 확인 시각을 E7/E8에서 연결하고 실제 화면 지연은 E9에서 측정한다.

.25초 표본·child nice19에서 최대 단일168,701,952/소유+보호 합350,474,240bytes로512MiB/1GiB 안이었다.
열한 controller의 원 종료·FD4→4·소유 process/PG·임시 PG directory/passfile 잔존0과 실제 시험 schema/role0을 확인했다.
TLS 시험은 서비스 정리 뒤 FD inventory 동일을 확인했다. 원본2,148항목·source·사용자 source/assets·보호3 identity와5173 HTTP200을 보존했다.
전체 backend/web·빌드·166일 계산·hosted CI·운영 설정 활성화/사용자 서버 전환은 실행하지 않았다. push hold를 유지한다.

## 다음 사용자 경로와 외부 의존성

다음 E6c는 명시 runtime/config의 같은 authority·store·worker 조립과 기본 비활성/누락 거부다.
그다음 E7 typed client→E8 자동 갱신/완료 저장3D→E9 실제 사용자 기동을 따른다.
남은 작은 합성 사용자 연결은 문서/검토 포함 **4–8집중시간** 잠정이다.
10월10일 오후부터 연속 착수·하루6집중시간 가정의1–2집중일/10월10일 밤–11일 KST이며 runtime/브라우저 관측 뒤 수정한다.
현재5173 자동 갱신·계산 중 prefix3D·최종 UI/전체 U3·전체 작기 forcing/자원/Decimal 경제는 미수용이다.
실제 농장 crop Run/국내 독립 자료0건·G0–G4 not_assessed와 생산/미래 마진/추천 hold를 유지한다.
