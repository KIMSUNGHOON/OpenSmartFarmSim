# 일사 공동 계산 결과의 명시 권한 v1

선행은 [결과 DB 계약](crop-greenhouse-solar-result-schema-v1.md)이다.
`RuntimeLoginPolicy.crop_greenhouse_solar_result_storage`는 keyword-only 정확한
bool이며 기본False다. 누락/False는 새 결과 표를 runtime 대상에 추가하지 않는다.
명시True일 때만 `crop_greenhouse_solar_research_results`의 authority SELECT/INSERT를
허용한다. None·0/1·float·문자열·list/dict/bytes를 bool로 변환하지 않는다.

## 설치·감사

provisioner가 새 schema를 먼저 설치해야 한다. fresh runtime 역할 설치에서
기존 전체 감사와 전용 NOLOGIN owner/접속/권한 정책을 재사용한다.
기존 역할이 존재하면 재설치를 거부한다. 기존 배포 DB/역할의 migration을
이 계약의 fresh 설치 시험으로 대신하지 않는다.

| 새 결과 표 권한 | authority | request / worker / supervisor |
| --- | --- | --- |
| SELECT / INSERT | 명시True만 허용 | 거부 |
| UPDATE / DELETE / TRUNCATE / REFERENCES / TRIGGER | 거부 | 거부 |
| MAINTAIN(PG17+) / WITH GRANT OPTION | 거부 | 거부 |

함수 실행/schema CREATE/owner·다른 역할 승격을 추가하지 않는다.
True에서 표나 필수 grant가 없으면 설치/감사가 거부한다. False에서도 예상하지
않은 표/column/PUBLIC/routine/grant-option/membership 권한을 거부한다.
SQL 권한은 tenant 행 격리·현재 자료 권리·HMAC·농장 등록·서비스 경로를
검증하지 않는다. 해당 책임은 후속 store/API와 배포 조립에 있다.

## 기존 설정·판본

기존 operator9종(기본/계산, joint 읽기/실행/prefix, ventilation 읽기/실행/prefix/
mixed prefix)은 새 필드의 누락·정확한False만 허용한다. True/다른 타입은
dependency factory 이전에 거부한다. 현재 `ApiRuntimeConfig`도 SolarTrue를
거부하며, 새 명시 조립은 후속이다. 이 옵션을 추가했다고 API가 활성화되지 않는다.

공통 역할/설정 코드 SHA 변경은 새 manifest/서명 identity에 반영한다.
이전 signed binding/intent/result는 원 Git 판본과 frozen 실행 영역에 보존한다.
현재 코드에서 자동 채택·재발급·재서명하지 않는다. 현재 입력 증거·농장 결속과
계산 이력은 해당 코드/권한 판본으로 새로 발급해 검증해야 한다.
기존 사용자 API/worker는 원 frozen source/계정/결과를 유지한다.

## 수용

실제 SCRAM에서 누락/False/True 설치·실행 행렬, 원 metadata/progress bytes와
UTC, 기존4결과 표의 grant/행 보존을 확인한다. 새 계정의 과도한 권한·필수 grant
철회·PUBLIC/column/routine/grant option/membership과 미설치/재설치를 거부한다.
설정9종 누락/False 호환과 잘못된 값의 factory 이전 거부, 현재 API 설정의
암묵적 활성화 거부, 공통 계정 경계·이전 설정/모델 회귀를 확인한다.

공통 코드 변경 뒤 현재 농장 결속·custody의 실제 fresh exec/원 bytes/checkpoint/
UTC·조회 계산0을 다시 확인한다. 원본/기존 frozen source·5root/자원·FD와 소유
PG/schema/role/passfile 정리를 통과한 뒤 수용한다. fixture는 합성 software 계약이며
실제 농장·자료 권리/G0–G4·생산·수익/추천의 승인이 아니다.
