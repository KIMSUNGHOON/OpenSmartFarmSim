# 공동 작물·기후 결과의 DB 저장 계약 — 2026-10-10

상태: **새 불변 metadata schema를 로컬 수용**했다.
core `c07cf83c6f484a6640bb3070ecd2d1efd804570f`다. 새 역할·등록 store/API·3D/U3는 미완료다.
사용자5173은 완료된 기존 합성166일 결과를 계속 읽으며 이번 변경을 실시간 표시하지 않는다.

## 검토 가능한 산출물

- [저장 계약](../contracts/crop-climate-joint-result-schema-v1.md),
  [설치 코드](../backend/app/crop_climate_joint_result_schema.py),
  [실제 SQL 검사](../backend/tests/test_crop_climate_joint_result_schema.py).
- [실제 원 종료·검사·보존·자원 기록](artifacts/crop-climate-joint-result-schema-reference-20261010.json):
  19,053bytes, SHA-256 `23d3ed6afd23ed8fa0f0319885faf7c3848e036ec2ad66eb83a23b37ef85f75c`.
- 새 테이블 `crop_climate_joint_research_results`에 source/context/UTC/evidence와
  intent/farm binding/HEAD/proof/root 참조를 고정한다. 원 bytes·SHA와33개 JSON/컬럼 pin을 검사한다.
  crop/batch/zone도 고정하며 이전 두 작물 결과 테이블을 변경하지 않는다.
- 실제 농장 등록과 원 HMAC·현재 권리·관문 검사는 후속 store가 수행한다.
  schema FK는 같은 tenant의 jobs 존재를 확인하는 구조적 제약이다.

## 실제 검증

최종 원 도구 `65cb20`/명령67605를 `e4fa9b`에서 종료0으로 회수했다.
**5개 pytest 그룹**, pytest4.26초/guard5.068초다. 세 번 실행한 결과를15개 검사로 합산하지 않는다.

| 범위 | 실제 확인 |
| --- | --- |
| 설치/정상 조회 | provisioner도 TCP SCRAM 사용; 원128KiB bytes·37입력 컬럼·마이크로초 UTC 보존 |
| 기존 공존/권한 | 각 DB 그룹에서 이전2테이블의 각1행 동일; 기존 runtime4역할 SELECT/INSERT/UPDATE/DELETE/TRUNCATE20건 거부; 기존 grant audit 통과 |
| 컬럼 제약 | 잘못된 식별자/SHA/정수/시각108개; raw SHA1개/크기2개 거부; 정확한 정수·600초 상한 허용,1µs 초과 거부 |
| 원 JSON | 다시 해시한 변조92개 거부;33개 pin 각각 변경, 닫힌 객체, 소수/지수/bool/string/null, 최상위·중첩·Unicode escape 중복 key와 잘못된 UTF-8/JSON |
| 식별/불변성 | 다른 tenant/없는 작업 FK2개·PK/결과/의도 고유성3개·수정/삭제2개·중복 설치 거부 |
| 원자 설치 | 새 table 생성 뒤 기존 function 충돌을 일으켜 전체 롤백; 원 행 보존;0걸음 hold 저장 허용 |

첫 실행 `446ad7`/3947→`f8227d`는 순수1개 통과/DB fixture4개 setup 오류였다.
로컬 설치용 Unix 소켓 trust 연결에 `used_password`를 요구한 테스트 가정을 수정했다.
임시 test provisioner의 TCP SCRAM 연결을 만들고 별도 passfile·계정을 정리했다.
이 계정의 시험용 SUPERUSER는 실제 배포 권한 조립을 입증하지 않는다.
수정 뒤 `11a9c9`/30857→`819c6a`는5개 통과/4.798초였고,
최대 raw bytes·Unicode 중복·중간 설치 롤백을 추가한 최종5개 수용으로 갱신했다.
SQL 제품 모듈은 최초 작성 bytes를 유지했다.

## 종료·자원·판단 범위

세 원 명령 모두 소유 PG/schema/role/passfile/임시 PG 디렉터리 잔여0·FD4→4다.
최종 .25초 관측의 단일/소유+보호 최대 RSS147,255,296/428,863,488bytes로512MiB/1GiB 안이다.
원본2,148항목·source1,744개·기동 source/assets와 기존3프로세스를 보존했고 frontend200을 확인했다.
8개 수치 진입점을 금지해 식·적분·사건·UTC 준비 호출0을 확인했다.
원128KiB fixture에는 whitespace가 포함되며 DB가 canonical JSON을 승인한 증거가 아니다.

현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 설계/검토했다.
turn_context `2026-10-09T19:42:50.735Z`, LF 포함 SHA
`8a3bcff9919d2ac8a8de28dcbb3a0289cccb51374bd2ed1914154d548b361cac`다.
재귀 CLI0·신규 제품 runtime CLI0이며 코드/계약/검증 기록이 검토 가능한 산출물이다.
fixture의 dummy hash/서명·일반 research 작업은 실제 농장 등록·작물 Run·자료 승인 증거가 아니다.
이전82/993 전체 회귀·166일 producer·새 API/WebGL은 재실행하지 않았다.
2026-10-10 04:51 KST 확인의 선행900288b CI는4개 성공/Backend37981057415 진행 중이다.
원 CI를 보존하기 위해 이번 새 core는 로컬 커밋으로 유지하며 hosted 수용으로 표시하지 않는다.

## 다음 단계와 남은 의존성

새 명시 권한/기본 false→서명 결과 원자 등록·fresh 현재 조회→2MiB API→같은 UTC3D→사용자 실행/U3다.
schema의 기존1–2집중시간 추정은 이번 약10분 구현/검토와 최종5.068초 검사 관측으로 갱신한다.
다음 역할은 기존321줄 계약 대조 기준1–2집중시간, store는 기존266줄 기준2–4집중시간의 잠정 작업량이다.
새 오류·API/3D 실측 전에는 UI 연결 완료 날짜를 확정하지 않는다.
실제 품종 입력·농장 작물 Run·국내 독립 자료0건과 G0–G4 `not_assessed/hold`를 유지한다.
