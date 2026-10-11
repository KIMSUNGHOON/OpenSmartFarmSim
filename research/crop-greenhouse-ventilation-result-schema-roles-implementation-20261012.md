# 환기 결과의 DB 형식·명시 권한 — 2026-10-12

상태: 집중 검증·최종 보존 확인 뒤 로컬 수용. 새 결과 등록/API의 필요한 선행 경계다.
현재 사용자5173/5174는 기존 source·결과를 유지하며 새 모델/DB 형식은 배포하지 않았다. 실제 자료·생산 Run0, G0–G4 `not_assessed`다.

## 구현과 수용 범위

[DB 계약](../contracts/crop-greenhouse-ventilation-result-schema-v1.md)/[권한 계약](../contracts/crop-greenhouse-ventilation-result-roles-v1.md)은
새25장부 artifact의 원 참조·6자리 UTC·원 metadata bytes/SHA를 `joint-ventilation-result-v1`로 구분한다.
기존 결과 테이블의 bytes/HMAC/최초 시각을 수정하거나 새 코드로 재서명하지 않는다.
metadata 자체의 DB 형식 검증이며 trusted 실제 계산/현재 농장/권리의 결과 등록은 다음 store에서 검증한다.

`crop_greenhouse_ventilation_result_storage`는 기본False·keyword-only 정확한 bool이다. 명시True일 때만 새 table의 authority SELECT/INSERT를 허용한다.
기존 request/worker/supervisor·UPDATE/DELETE/TRUNCATE·PUBLIC/column/routine/grant-option/membership은 허용하지 않는다.
기존 설정5종은 누락·정확한False만 받아 factory 전 True/잘못된 타입을 거부한다. 새 runtime의 명시 활성화는 후속이다.

공통4파일(runtime_roles 및 기존 operator loader3개)만 필요한 opt-in/비활성 호환을 추가했다. 전후 SHA를 영수증에 고정하고 기존236개 계산 파일은 보존했다.
공통 코드 SHA는 새 manifest/서명 identity에 반영된다. 이전 서명 이력은 기존 git 판본에 보존하며 현재 코드로 자동 채택·재발급하지 않는다.
기동 사용자 backend/worker는 원 frozen source를 사용하므로 이번 수정으로 교체하지 않았다. 기존 배포 DB/역할의 migration 시험으로 주장하지 않는다.

## 실제 통과한 검증

[집중 영수증](artifacts/crop-greenhouse-ventilation-result-schema-roles-reference-20261012.json):새12/기존12 +현재 결속 회귀3 = 고유27그룹.

| 범위 | 원 도구 세션 | guard wall(초) | 결과 |
| --- | --- | --- | --- |
|새/기존 schema·roles|`43296`|17.151|24통과·실제 SCRAM·원 bytes/UTC/권한·기존 결과3종|
|현재 농장·새/기존 custody|`58578`|169.255|3통과·fresh 동일·조회 수치0·원 checkpoint|

smoke 원82248은3통과(본 집중 검사와 중복이므로 별도로 합산하지 않음)다.
새 schema는 원131,072bytes/37컬럼·33개 개별 pin,108개 잘못된 컬럼·92개 rehash raw·중복/닫힌 shape/정수 표기·SHA·UTC 1µs 초과를 검증했다.
같은 tenant FK/고유 의도·hold 0걸음·UPDATE/DELETE·재설치/부분 DDL rollback도 통과했다. fixture SQL metadata는 농업 자료·생산 예측 증거가 아니다.
새 roles는 누락/False/True 행렬 각각112 table privilege 대사·권한 상승 거부, 명시True만 원 bytes/UTC 조회를 통과했다.
기존3종 결과 행은 각각1행 그대로 보존했고 grant도 대사했다. 기존 설정5종의 누락/False10허용·다른 값35거부(factory 전),12개 grant/routine/membership drift 거부를 확인했다.
새/기존 custody의 fresh 실제 SCRAM·원 checkpoint/UTC·조회 수치0와 새 농장 결속의 fresh 동일 bytes도 통과했다.

## 자원·보존·남은 작업

성공 명령은 실제0·FD4→4·scratch schema/role/소유 PG/임시 PG/passfile 잔여0이다.
.25초 관측 최대 단일 RSS138,727,424bytes/소유+보호 합972,107,776bytes로512MiB/1GiB 안이다.
최종 보존 원17185 실제0(0.617초):원본2,148·기존236파일/공통4전후 SHA·accepted source1,911/원 자산171·현재5174 자산171/설정·두 주소200/4보호 root·권리/키/접속 안내와 로컬 링크2,021개를 대사했다.
현재 native CLI `gpt-6.1-sol`/`xhigh`의 실제 turn context/원 line SHA를 영수증에 기록했다. 재귀 CLI0이며 새 농업 원문/계수/자료 권리를 채택하지 않았다.
전체 CI/remote·사용자 서버 재기동·새 결과 API/worker/브라우저는 미실행이다.
다음은 signed store의 원자 put/retry·현재 get/page/summary·호출자 transaction/rollback·권리 철회·조회 수치0다. 이후 보호 API→worker/같은 UTC3D→사용자 적용으로 이어간다.
남은4–8집중작업시간 추정은 결과 API1–2·worker/web2–4·사용자 적용1–2의 작업 분해이며 전체 제품 완료 약속이 아니다.
독립 농장 자료0과 온실/자원·경제/최종 UI·G0–G4의 미완료는 유지한다.
