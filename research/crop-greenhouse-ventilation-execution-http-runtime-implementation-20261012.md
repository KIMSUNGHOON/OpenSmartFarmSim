# 환기 모델 접수·현재 진행·취소 API/서버 — 2026-10-12

상태:377검사·사용자 진행 브라우저·최종 보존으로 로컬 수용. 새 모델의 사용자 배포/3D는 미수용이다.
[계약](../contracts/crop-greenhouse-ventilation-execution-http-v1.md), [기계 기록](artifacts/crop-greenhouse-ventilation-execution-http-runtime-reference-20261012.json).

## 구현과 사용자 산출물

- [현재 조회](../backend/app/crop_greenhouse_ventilation_execution_query.py)는 같은 job의 확정 체크포인트, 최초 기록 UTC, 계산 UTC/단계/건수와 정상·보류 결과 ID를 반환한다. 조회 중 수치 계산/작업·결과 쓰기는0이며 권리/파일·DB 상태를 전후 대사한다.
- [보호 HTTP](../backend/app/api_crop_greenhouse_ventilation_execution.py)는 접수202·진행 GET·취소 POST를 별도 namespace에 연결한다.16KiB 응답/64KiB 접수, no-store, 닫힌 판본/타입·현재 계정·권한 검사를 적용한다. 사용 권리 철회 뒤에도 소유자의 취소는 가능하다.
- [명시 설정](../backend/app/crop_greenhouse_ventilation_operator_config.py)의 별도 실행 판본과 strict bool을 [공통 runtime](../backend/app/api_runtime.py)에 연결했다. 기본 비활성, 같은 jobs/farms/input resolver/server/results, 기존 보호 파일 재확인과 서로 다른 키를 유지한다. 새 schema/role/daemon/package는 없다.

실행 서비스의 결과를 개발용 실제 DB/HTTPS에서 확인할 수 있다. 현재5173/5174는 기존 frozen 서비스이며 이 새 실행 API를 아직 배포하지 않았다. 사용자에게 보이는 산출물은 인증 없는 개발 기록의 새 검증 단계다.

## 검증

| 범위 | 원 도구 | 개수 | 결과 |
| --- | --- | --- | --- |
| 닫힌 DTO/접수·HTTP·설정·공개 명세 |33888|215|실제0 |
| 현재 권리/대기·취소/잘못된 ID/조회 중 변경 |78410|4|실제 SCRAM·0 |
| 원 체크포인트/재시도·잠금·변조 |54600|5|실제 SCRAM·0 |
| 정상·수치 보류/원 시각·fresh reader |61088|2|실제 SCRAM/별도 Python·0 |
| HTTPS 원 진행/취소·권리 철회 후 취소 |72152|2|검증 TLS/SCRAM·0 |
| HTTPS 정상·보류/기존 저장 응답 대사 |43643|2|검증 TLS/SCRAM·0 |
| 명시 runtime의 최초 접수→독립 자동 작업자→정상/보류 |39127|2|검증 TLS/SCRAM/실제 프로세스·0 |
| 실행 중 취소/기본 비활성 |61344|2|검증 TLS/SCRAM/작업자 canceled·0 |
| 기존 공통/구형 실행/환기 읽기 조립 |24208|143|실제0 |

고유 **377개(새 경로234/기존 조립143)**, 실제 DB/TLS·프로세스19개다. 실행 query 전체16개 중 투영5개는 위215개에 포함하며 중복 합산하지 않았다.9 guard 합1,064.34초이며 코드 작성/분석·기록은 별도다.

원 확정 수치/UTC·재시도 최초 기록 시각, 정상 publication1/보류 publication0의 정확한 결과 연결, 동일 공개 응답 bytes, 조회9수치 호출/쓰기0를 확인했다. 정상 fresh reader는 관측 시각을 제외한 DTO가 일치한다. runtime의 별도 작업자는 작업 ID 없이 새 판본을 발견해16걸음을 실행한다. 실행 중 취소는 worker canceled/수치 호출0·결과/게시0이다. runtime 시험은 최초 동작 전 상태/취소 관측을 동기화하고 해제 후 계산하므로 계산 중 WebGL/연속 부분3D 증거로 사용하지 않는다.

기존57경로/313스키마를 그대로 보존하고 새3경로/6스키마만 추가했다. 원본2,148·기존 계산260파일/명시 공유5·두 frozen source/자산·보호4root를 보존했다. 모든 백엔드 성공 guard FD4→4·소유/PG/passfile/임시PG잔여0이다. .25초 관측 최대 단일186,707,968bytes/보호 포함1,049,145,344bytes로512MiB/1GiB 안이다.

원69802 사용자 브라우저도 실제0/5.930초로5173안내→5174인증 없는377검사/미배포/남은2–5시간을 확인했다. 두 화면390px overflow0·API쓰기/pageerror0, 단일259,211,264/합996,323,328bytes였다. 새 작물3D 검증은 아니다. 최종 stdlib 보존 확인은 실제0으로260계산 파일·명시 공유5·현재172/이전171자산·frozen1,911파일/171자산·source194파일·현재 entry/config·4root/권리/안내·두 주소/개발 기록200/no-store를 대사했다.

초기 검사8245는 없는 pytest 대상 경로로0검사/exit4,67840은 구형 헤더를 기대한 새 테스트,31038은 새 projection의 변수명과 schema 이름을 혼동한 query 참조로 실패했다. 원 종료를 수집하고 수정한 최종 core에서 위 검증을 통과했다. 실패를 수용 개수로 세지 않았다.

실제 native Codex CLI `gpt-6.1-sol`/`xhigh`의 현 turn context 시각/원 행 SHA를 기록했다. 재귀CLI0이다. 전체 CI/remote·새 웹/3D·전체 작기 계산은 미실행이다. 앞선 [실행 핵심91검사](crop-greenhouse-ventilation-execution-core-implementation-20261012.md)의 수치·강제 종료 재개 증거를 유지하며 이번377개를 독립 작물 검증으로 취급하지 않는다.

## 다음 단계와 추정

1. **완료 결과 typed client/3D(0.5–1시간)**: 같은 새 result ID/원 UTC의108상태·25장부/10수지·환기 진단을 읽고 장면/표/차트와 대사한다. 새 응답의 닫힌 판본·단위·권리 철회 시 제거와 기존 client 보존을 확인한다.
2. **확정 부분 결과 조회와3D(0.75–1.5시간)**: 현재 API의 요약만으로 부분 장면을 만들지 않는다. 확정 selector에 묶인 원 sample/event 페이지 reader·보호 HTTP→typed web을 연결한다. 최초 기록/전진·권리·취소·조회 계산/쓰기0를 실제 실행에서 확인한다.
3. **실제 브라우저/사용자 적용(0.75–2시간)**: 장벽 없는 정상/보류 계산 중 같은 UTC/원 값/WebGL→terminal, 취소·빈/재접속과 두 사용자 DB/주소/키·권리/자원을 확인한다. 기존 WSL 유지보수/복구 창을 사용하며 검증 전 현재 두 서비스를 교체하지 않는다. 새 모델과 기존 실행을 함께 제공할 명시 조립과 복구 가능성을 실제 사용자 저장소에서 확인해야 한다.

완충을 포함한 **남은2–5집중시간**은 합성32초 새 모델의 화면 연결/적용에 대한 잠정 작업량이다. 실제 작업 분해와 이번 검사 시간으로 갱신했으며 완료 시각을 보장하지 않는다. 전체 제품/전체 작기 생산 예측의 완료일은 미정이다.

실제 농장 Run/독립 국내 검증 자료0, G0–G4 `not_assessed`, 실제 품종·생산/자원 구매·미래 마진/작물 추천 보류를 유지한다. 외부 자료 확보와 생산·자원·경제 통합/최종 UI는 별도 작업이다.
