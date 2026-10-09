# 등록 수확의 명시 runtime·기본 App 연결 개발 수용

2026-10-08 23:01 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[공개 영수증](artifacts/crop-harvest-runtime-assembly-implementation-reference-20261008.json)에
원 명령/종료·440 source·실제 SCRAM reader 조립·기존 ASGI bytes·OpenAPI·실패/정리를 결속했다.
선행 [인증 route 수용](crop-harvest-route-openapi-implementation-20261008.md)은 보존한다.

## 구현과 사용자 확인 산출물

[기존 runtime](../backend/app/api_runtime.py)의 선택적 `crop_harvest_current_query_factory`는 기본None이다.
기존 calculation storage/factory가 구성된 상태에서 명시적으로 선택하면 원 query를 전달하고,
정확한 수확 query/reader·같은 부모·별도 schema·실제 SCRAM의 같은 host/port/DB와 ACL을 검사한다.
기존 역할의 SQL grants는 바꾸지 않는다. 원 private passfile/root/key의 검사는 registry/query 계약을 재사용한다.
[기본 App](../backend/app/api.py)은 실제 reader를 인증 route에 연결하고 미구성 시 인증 뒤503을 반환한다.
[생성 OpenAPI](../contracts/openapi-v1.json)는 새 경로와 닫힌 응답을 포함한다.

사용자는 영수증에서 실제 reader의 INSERT 거부, 정상/재조립/미구성·혼합 거부와
원 DB 이력/입력/FD·schema/role/비밀 정리, 표준 OpenAPI와 기존 ASGI 원 응답을 확인할 수 있다.
실제 조립 시험은 crop/harvest row0건이며 새 crop Run·생산량을 만들지 않았다.
ASGI 값은 선행 소유 합성 실제 DB 조회 기록이며 현재 권한은 명시 stub/오류 주입이다.

## 통과한 검증

| 대상 | 실제 범위 |
| --- | --- |
| 집중 시험 | [새 runtime](../backend/tests/test_crop_harvest_runtime.py)17개(실제 SCRAM1 포함)+적응 route72개+기존 calculation runtime 순수18개+API runtime 순수31개·고유138개/43.40초·원 종료0. 기존 DB10개 명시 제외 |
| 명시 구성 | factory 기본None/repr 비공개·noncallable/원 calculation 선행 누락을 연결 전 거부·실제 App 전달·기본 인증503/401 |
| 실제 SCRAM | 같은 DB endpoint·원 query/jobs/farm/principal·reader ACL·독립 key5개·INSERT 거부·같은 프로세스 재조립·미구성 복귀·작물/수확 row0 유지 |
| 거부10가지 | untyped/다른 부모/publisher/변경 key/다른 DB policy/부모 schema/재사용 key, 실제 SCRAM 뒤 소유 endpoint metadata 오류 주입, 실제 reader INSERT grant 추가, 실제 passfile0644 |
| 보존 | 원 jobs/events/crop/harvest counts·불변 입력 hash/mode/inode·ASGI summary/6행 bytes/같은 UTC와 조회 종료/계정 순서·FD12→12·조립 중 parser/RHS/행 생성/증명/등록0 |
| OpenAPI/import | 원49 path/156 schema 의미 그대로·새50 path/201 schema·생성 bytes 일치·세 fresh Python import 종료0/connection0/FD4→4·계산 모듈 lazy loading |
| 정리 | 원/수확 schema·역할·passfile0·임시 PG 종료/제거·자식 프로세스0·440 source 불변 |

실제 정상 조립은0.294초였다. HTTP 지연이나 운영 부하 측정은 아니다.
최종 실행22:59:50→23:00:35 KST, 준비부터45.044초였다. 원600초 상한·nice19·0.1초 감시421표본에서
primary RSS222,466,048bytes≤512MiB, PG/controller/자식 포함 RSS 합326,643,712bytes≤1GiB였다.
공유 page 중복 가능 RSS 합이며 WSL 전체/production 용량 수용은 아니다.
23:01:23 KST 별도 감사에서 원 정적 OpenAPI와 새 표준 계약·DB/ASGI/자원 정리·시험된5 core파일+생성물 snapshot을 대사했다.

첫 native 묶음은137통과/DB1건너뜀/10제외·원 종료0이었고 DB 환경변수 누락을 확인해 실제 수용에서 제외했다.
실제 전용 실행은 잘못된 연구 context 속성으로 준비 단계에서 실패1이었다. 같은 catalog·plain context dict·scope resolver를
기존 계산 조립에 맞췄다. 다음 실행은16통과/실제1실패·원 종료1로, grant probe의 `login_database` fixture 인자 누락을 수정했다.
제품 구현은 이 과정에서 바꾸지 않았다. 원 실패·소스 snapshot·각 DB/비밀/PG 정리를 보존했고 최종138개만 수용한다.

## 다음 한 단계와 남은 의존성

[조립 계약](../contracts/crop-harvest-runtime-assembly-v1.md)의 `crop-harvest-runtime-assembly` 자식만 체크한다.
`crop-harvest-runtime-factory` 부모는 보호된 운영 설정의 실제 dependencies factory·별도 Python 같은 DB 복원 뒤에 평가한다.
같은 프로세스의 재조립과 fresh import를 그 복원으로 표시하지 않는다.
다음은 기존 명시 loader와 private config/key/DSN/소유권을 사용하는 보호된 factory의 새 프로세스 복원이며,
착수 시3~5 core파일로 고정한다. 그 뒤 실제 HTTPS summary/원6행·분할/권한 철회·30초/2MiB·자원 정리로 API 부모를 평가한다.
이후 SDK→같은 UTC 표/3D→기후/물·양분/구매 에너지→Decimal 경제 연결을 진행한다.

이번 조립 자식의 완료 시각만 위 실측으로 확정한다. 후속 완료 추정은 실제 분해/검증과 외부 자료 상태에 따라 갱신한다.
보호된 별도 프로세스 복원·실제 HTTP/TLS·SDK/WebGL·전체166일 질량 조회·전체 backend/web suite·hosted CI/push·제품 CLI는 실행하지 않았다.
실제 계수/품종 입력·국내 독립 자료·실측 농장 작물 Run0건, G0–G4 `not_assessed`, 생산/미래 마진/추천·
원격 Backend·구형 native25시간 원 종료 기록 보류를 유지한다. 독립 자료 확보 일정이 없어 최종 production 날짜는 확정하지 않는다.
