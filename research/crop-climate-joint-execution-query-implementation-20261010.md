# 공동 작물·기후 진행 조회 — E6a 로컬 수용

2026-10-10 KST. core `0bfa9dd`의 조회 계층·시험·실행 계약 세 파일을 수용했다.
[원 실행 증거](artifacts/crop-climate-joint-execution-query-reference-20261010.json)는
46,934bytes, SHA-256 `9c7b44861d81b8e0ef864595a221f868488660bb1ebd6da9dac2ce153c870bf5`다.
원32초·16걸음 합성 구성의 소프트웨어 검증이며 실제 농장 예측의 증거가 아니다.

## 사용자가 확인할 연결과 검증

`JointExecutionQuery(checkpoint_store, result_store).read(tenant, job_id)`는
같은 E1 입력·농장·E2 확정 사건·현재 서명 HEAD와 E4 결과 연결을 대사한다.
읽기 권한과 metadata만 사용하며 계산/쓰기 권한을 요구하지 않는다.
최대16KiB의 닫힌 응답에 작업 상태, 확정 걸음/counts, 원 계산 UTC,
DB 최초 수용 시각, 조회 시각과 완료/hold 결과 참조를 담는다.
heartbeat·파일 mtime을 계산 진척으로 사용하지 않는다.

신규 **16개**(닫힌 schema5/실제 SCRAM11)와 관련 기존 **2개**, **고유18개**를 통과했다.
여섯 수용 묶음의 실제 검사 실행은19회다. hold 선택식이 공통 시험 이름에도 맞아 정상 완료를
한 번 더 검사했으며 고유 수에는 중복을 더하지 않았다. 전체 module 단일 실행은 아니다.

| 검사 | 실제 확인 |
| --- | --- |
| 미실행/취소 | queued·claimed·canceled의 checkpoint 없음; 누락/다른 tenant·stage·판본은 결과 없음; 새 intent 생성 없음 |
| 확정 진행 | 원 HEAD/counts/마이크로초 UTC와 최초 DB 수용 시각; heartbeat 뒤·시도2의 같은 HEAD 중복 수용 뒤 원 사건/시각 보존 |
| 미확정 진행 | 서명된 후속 HEAD만 있거나 실제 파일 잠금 중이면 unavailable; checkpoint/result는 null |
| 완료/수치 hold | 현재 attempt의 연결 사건·outcome·서명 registry와 원 terminal checkpoint 대사; 성공 publication1/수치 hold0 |
| 별도 프로세스 | 실제 SCRAM fresh Python에서 조회 시각을 제외한 원 DTO 동일; 계산/등록 호출0 |
| 거부 | scope 누락·늦은 자료 권리 철회·의존 객체 변경; 소유 시험 DB에 추가한 변조 사건3종 거부 |
| 조회 중 변경 | 별도 actor의 작업 취소를 재조회로 검출해 Pending; 부분 응답 없음 |
| 기존 경로 | E2 원 HEAD 중복/heartbeat와 E4 원 terminal 결과 채택의 bytes·최초 시각/계산0 보존 |

조회의21개 호출 계수는 모두0이며 준비/복원/RHS/advance/확정/결과 등록/작업 쓰기를 막았다.
readonly SQL snapshot과 마지막 재조회로 작업/사건/게시/outcome·registry 변경을 검사한다.
각 무변경 검사에서는 다섯 작업 테이블 digest도 동일했다. 별도 actor 취소 검사는 무변경 주장에 포함하지 않는다.
공개 농장 참조에는 검증된 원 packet의 재배 batch/zone을 포함한다.

## 발견한 실패와 수정 범위

첫 정상 완료 조회가 ValidationError로 거부됐다. 접수 farm의 네 필드를 기존 공개 Farm의
여섯 필드 형식에 넣어 batch_id/zone_id가 빠진 제품 오류였다. private 진단은 예외 유형과
파일/행 정보만 기록했다. 서명 registry packet의 원 여섯 필드를 투영하도록 수정했다.
수정 전 실패2회와 로그/소스 SHA를 보존했고 수정 뒤 정상·fresh·수치 hold·닫힌 schema를 통과했다.
publication의 bool attempt와 worker pin 거부는 실제 SQL 조회 뒤 **읽기 view에 주입한 fault**이며
DB에 저장된 공격 자료를 검증한 것으로 확대하지 않는다.

앞서 통과한 checkpoint 묶음은 수정 전 source다. 원 bytes를 역구성한 SHA 일치와 AST 대조로
checkpoint 시험/fixture 및 terminal 반환 전 검사 불변을 확인했다. 변경은 `_terminal`의 공개 farm 반환과
schema/terminal 시험 두 정의다. 그 변경 경로를 최종 source로 재검증했고 모든 묶음이 같은 SHA였다고 주장하지 않는다.
초기 none/isolated 통과6회는 재검증과 중복이며 고유 수에 추가하지 않았다.
잘못된 private launcher prefix1회는 child 생성 전 거부였고 시험 실패와 구분했다.

## 시간·자원·보존

native Codex CLI `gpt-6.1-sol/xhigh`의04:02:33.857Z context를 확인했다.
원 LF 행 SHA는 `97421dc07d5f2d2bc6ef8d67401a7de9cc5f00d5f20a0e7d88b3b9b53580f325`다.
recursive/runtime CLI 실행0이며 native→최종 집중 terminal은2,240.123초(약37분), 문서/commit은 별도다.
묶음 시간에는 입력 fixture·수치 준비·fresh/정리를 포함한다. **조회 응답 지연 실측은 아니며 E6b/E9에 남긴다.**

.25초 표본·child nice19에서 최대 단일132,415,488/소유+보호 합436,039,680bytes로512MiB/1GiB 안이었다.
열 개 실행 controller의 원 종료와 FD4→4·소유 process/PG·임시 PG directory/passfile 잔존0을 확인했다.
수용 묶음의 schema/role0·원본2,148항목·source·사용자 source/assets·보호3 identity와5173 HTTP200을 보존했다.
전체 backend/web·빌드·166일 계산·hosted CI·HTTP runtime 노출/사용자 서버 전환은 실행하지 않았다. push hold를 유지한다.

## 다음 단계와 외부 의존성

다음 E6b는 보호된 접수/진행/취소 HTTP이며 E6c 명시 조립→E7 typed client→E8 자동 갱신/완료 저장3D→E9 실제 기동을 따른다.
현재5173은 완료 합성166일의 저장 결과 재생이다. 진행 상태/새 checkpoint 자동 갱신과 계산 중 prefix3D는 미수용이다.
남은 작은 합성 사용자 연결은 문서/검토 포함 **4–9집중시간** 잠정이다. 하루6시간·10월10일 연속 착수 가정의
1–2집중일/10월11–12일 KST이며 HTTP 비용/실제 브라우저 관측 뒤 갱신한다.
전체 U3·최종 디자인/전체 작기 forcing·물/양분/구매 에너지/Decimal 경제는 이 날짜에 포함하지 않는다.
실제 농장 crop Run/국내 독립 자료0건, G0–G4 not_assessed와 생산/미래 마진/추천 hold를 유지한다.
