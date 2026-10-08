# 수확 질량·배정 등록 스키마의 개발 수용

2026-10-08 21:14 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 구현·검토했다.
재귀 CLI 실행은0회다. [공개 영수증](artifacts/crop-harvest-registry-schema-implementation-reference-20261008.json)에
원 명령/종료·416 source·실제 SCRAM/SQL·현재 부모 보존·자원/정리와 실패 기록을 결속했다.
선행 [불변 질량·배정 저장](crop-harvest-artifact-implementation-20261008.md)을 보존한다.

## 구현과 사용자 산출물

[등록 스키마](../backend/app/crop_harvest_registry_schema.py)는 기존 생장 결과와 같은 DB에
별도 namespace·NOLOGIN owner·비특권 publisher/reader를 설치하고 실제 역할·객체·권한을 감사한다.
publisher는 SELECT/INSERT, reader는 SELECT만 받으며 PUBLIC·열별 추가 권한·재위임·membership을 거부한다.
기존 부모의 공유 runtime role/schema/store 코드는 수정하지 않았다. 별도 스키마는 기술 스택의
파일→PostgreSQL metadata 등록에 필요한 경계이며 새 프레임워크나 일반 운영 기반 추가가 아니다.

불변 표는 원 result·farm·artifact key/hash·행 수/순서·두 parameter hash·canonical metadata/SHA·
서명 필드·등록 주체·DB 최초 기록 시각을 보존한다. 최대 metadata128KiB·262,144행이다.
SQL은 닫힌 JSON·유형/열·claim/승인false·hash·중복 key를 검사하고 UPDATE/DELETE trigger를 둔다.
audit는 trigger 활성/대상·함수 본문과 역할 변경도 검사한다. installer는 호출자의 역할을 복원한다.

사용자는 계약·실제 권한 감사·거부 사례와 정리 증거를 확인할 수 있다.
이번1행은 artifact/계수/code/signature에 자리표시자가 포함된 **SQL 형식 fixture**다.
실제 질량·배정 artifact의 서명/서버 등록이나 사용자 이력을 생성한 것이 아니다.
SQL hash/형식 검사는 진본·원량·권리·관문 승인을 대신하지 않는다.

## 통과한 검증과 실패 기록

| 대상 | 확인한 범위 |
| --- | --- |
| 최종 집중 시험 | [시험 파일](../backend/tests/test_crop_harvest_registry_schema.py) 전체17개·원 종료0·36.96초. 순수16개/실제 DB1개이며 중간 시험은 중복 합산하지 않음 |
| 실제 로그인 | PostgreSQL16.15·TCP SCRAM publisher/reader·정확한 로그인 주체·별도 owner·최소 권한. HBA는 provisioner에서 검사 |
| SQL 거부11종 | 추가/누락 key·열 불일치·payload hash·주장/승인·중복 key·bool 행 수·source/code hash·artifact key |
| 감사 거부10종 | reader INSERT·PUBLIC SELECT·schema CREATE·membership·CREATEDB·함수 EXECUTE·열별 INSERT·GRANT OPTION·trigger 비활성·함수 본문 교체. 각 transaction rollback 뒤 정상 감사 복원 |
| 불변/거래 | publisher UPDATE/DELETE/TRUNCATE·reader INSERT/CREATE 거부·owner UPDATE trigger 거부·기존 설치 덮어쓰기 거부·잘못된 DB 거부·호출자 역할 복원·tuple/dict row factory |
| 기존 경로 보존 | 실제 부모 결과 재조회와 runtime role 감사·DB 행 수·입력/custody SHA/mode/inode 보존·조회 RHS0/새 proof0·FD13→13 |
| 최종 감사/정리 | 416 source 불변·metadata canonical/열 대사·새/기존 schema/role/passfile0·소유 PG/controller/임시 경로 종료. 21:14 KST root 감사 뒤 시험 당시3파일 보존/source freeze 해제 |

수용한 v3는21:13:22→21:13:59 KST, 준비부터 정리까지37.494초다.
원600초 상한의0.1초 감시352개 표본에서 primary RSS 최대128,491,520bytes≤512MiB,
PG/controller 포함 소유 PID RSS 합 최대265,433,088bytes≤1GiB였다.
공유 page 중복 가능 RSS 합이며 PSS/WSL 전체/production 동시 부하의 증거는 아니다.

첫 driver v1은 선행 영수증의 잘못된 key로 사전 검사에서 종료1·pytest/PG 시작0이었다.
별도 v2는 실제 DB 시험의 정리에서 CONNECT grant 의존성 때문에 역할 삭제가 실패해 원 종료1이었다.
v2의 전체 임시 cluster/프로세스·비밀 파일 정리를 확인했지만 cluster 종료 전 새 역할 정리는 미수용이다.
해당 실패의 원 도구 종료·소스/정리 감사와 시험 당시 파일을 보존했다.
CONNECT 회수 뒤 삭제하도록 fixture를 수정한 별도 v3만 수용하며 성공을 앞선 실패에 소급하지 않는다.

## 다음 한 단계와 외부 의존성

[계약](../contracts/crop-harvest-current-query-v1.md)의 `crop-harvest-registry-schema`만 체크한다.
다음은 서버가 원 결과·명시 질량/배정 원문에서 artifact를 생성하고, 현재 계산/표시 권리와
원 부모/농장·판본을 검사한 뒤 서명 metadata를 DB에 최초 등록/동일 재시도하는 `crop-harvest-registration`이다.
임의 고객 경로/hash를 등록 증명으로 받아들이지 않고 철회/중간 실패 시 DB 미게시·원 파일/행 보존을 검증한다.
그 뒤 등록 key/hash의 현재 조회·fresh Python 실제 DB 복원→HTTP/SDK→같은 UTC 표/3D로 진행한다.

전체166일 질량/배정 등록 부하·실제 artifact 등록·현재 query/fresh DB 복원·새 API/3D·
전체 Backend/web suite·hosted CI·실제 제품 CLI·실제 품종 검증은 실행하지 않았다. 전체166일 RHS도 반복하지 않았다.
기후/물·양분/구매 에너지와 기존 Decimal 경제 계산 연결은 후속이며 실제 계수/품종 입력·
국내 독립 자료·실측 농장 작물 Run0건, G0–G4 `not_assessed`, 생산/미래 마진/추천 보류는 유지한다.
원격 Backend/push와 구형 native25시간 원 종료 기록 보류도 유지한다.
이 개발 자식의 실제 수용 시각은10월8일21:14 KST이며 외부 자료 확보 일정이 없어 최종 production 완료일은 확정하지 않는다.
