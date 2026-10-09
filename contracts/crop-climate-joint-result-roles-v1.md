# 공동 작물·기후 결과의 명시 권한 v1

선행은 [새 DB 저장 계약](crop-climate-joint-result-schema-v1.md)이다.
`RuntimeLoginPolicy.crop_climate_joint_result_storage`는 keyword-only 정확한 bool이며 기본값False다.
명시True가 아니면 `crop_climate_joint_research_results`를 runtime 대상 table에 추가하지 않는다.
None·정수0/1·문자열·list/dict 등으로 bool을 대신하지 않는다.
기존 선택 옵션과 runtime 역할/접속/권한 감사 정책은 유지한다.

기존 `operator-api-config-v1`/`operator-calculation-api-config-v1`은 dataclass 직렬화에
추가된 이 필드의 누락·정확한False만 허용한다. True/다른 타입은 의존성 factory 실행 전에 거부한다.
그 두 로더로 새 결과 runtime을 활성화하지 않는다. 새 결과의 operator/API 조립은 후속 계약이다.

## 설치와 권한 행렬

새 schema는 provisioner가 먼저 설치한다. 새 옵션True로 fresh runtime 역할을 설치하면
기존 설치 함수가 아래 grant를 추가한다. 기존 역할이 존재하면 재설치는 거부한다.
배포된 역할의 변경은 별도의 migration 절차이며 이 계약의 fresh 설치 시험으로 대신하지 않는다.

| 새 결과 테이블 | authority | request / worker / supervisor |
| --- | --- | --- |
| SELECT / INSERT | 옵션True일 때만 허용 | 거부 |
| UPDATE / DELETE / TRUNCATE / REFERENCES / TRIGGER | 거부 | 거부 |
| MAINTAIN (PG17+) / WITH GRANT OPTION | 거부 | 거부 |

함수 실행·schema CREATE·owner/다른 runtime 역할로의 승격을 추가하지 않는다.
사용자 HTTP 요청은 `authority`의 검증된 서비스 경로를 거쳐야 한다.
SQL 권한만으로 tenant 행 격리·현재 권리·서명 검증이나 서비스 경로 강제를 보장하지 않는다.
그 범위는 후속 결과 store/API와 배포 권한 조립에서 검증한다.

## 감사

새 옵션True에서 table이 없거나 SELECT/INSERT grant가 빠지면 기존 전체 감사가 거부한다.
옵션False에서도 schema 안의 새 table·column·routine에 예상하지 않은 권한이 있으면 거부한다.
PUBLIC·column grant·grant option·role membership·DDL·함수 권한도 기존 감사에 포함된다.
새 table과 함수는 전용 NOLOGIN owner에 속해야 하며 runtime은 소유자가 아니다.

## 수용

실제 SCRAM에서 누락/명시False/명시True의 설치·실행 권한과 원 bytes/UTC 조회를 확인한다.
기존 두 작물 결과의 grant/원 행 보존, 잘못된 타입, 미설치/누락 grant,
추가 table/column/PUBLIC/routine·grant option·membership 변경 거부, 실제 종료·소유 정리를 검증한다.
기존 설정 로더의 원 정상 사례와 누락/False 호환·True/잘못된 타입 거부도 검증한다.
검사 fixture는 schema-only 합성 metadata다. 자료 권리/G0–G4·실제 농장 등록·생산 Run의 승인이 아니다.
새 결과 등록/API/3D·실시간 U3·실제 품종/독립 자료는 후속이다.
