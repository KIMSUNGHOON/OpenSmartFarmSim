# 공동 작물·기후 결과의 명시 권한 — 2026-10-10

상태: **새 결과 opt-in 권한과 기존 설정 형식의 비활성 호환을 로컬 수용**했다.
core `850d002e11b5549949cb8aa12d0868b726f4c040`다. 새 결과 store/API·3D/U3는 미완료다.
현재 사용자 UI는 기존 완료166일 합성 결과의 저장 재생을 유지한다.

## 산출물과 변경 범위

- [권한 계약](../contracts/crop-climate-joint-result-roles-v1.md),
  [역할 정책](../backend/app/runtime_roles.py), [실제 검사](../backend/tests/test_crop_climate_joint_result_roles.py).
- [원 검사·종료·보존/자원 기록](artifacts/crop-climate-joint-result-roles-reference-20261010.json):
  76,088bytes, SHA-256 `966836bb003d88c4f3e6ef06ad60af1efc7e6c6584fa4d4cfe9a1de86149198f`.
- `crop_climate_joint_result_storage`는 keyword-only 정확한bool/기본False다.
  True일 때 새 table의 authority SELECT/INSERT만 추가한다. 기존 login/owner fixture는 변경하지 않았다.
- 처음 core3로 검토했지만 기존 정상 operator 검사3개의 실제 실패를 재현했다.
  dataclass 직렬화에 생긴 기본False 필드를 기존 닫힌 설정이 거부했다.
  [기존 로더](../backend/app/operator_config.py)와 [계산 로더](../backend/app/calculation_operator_config.py)의
  누락/정확한False 호환을 포함한 core5로 확정했다. True/다른 타입은 factory 전에 거부한다.
  기존 operator 판본으로 새 공동 결과 서비스를 활성화한 증거는 아니다.

## 최종 실제 검사

최종 동일 core5 bytes에서 **새7개+기존226개=233개**를 아래3명령으로 순차 통과했다.
앞선 중간 수용6/94개와 실패3개는 최종 수에 다시 더하지 않는다.

| 검사 | 원 명령 / 실제 terminal | 실제 결과 / guard wall |
| --- | --- | --- |
| 새 명시 권한/호환 |54207 / `4fc29e` |7 passed /5.080초 |
| 기존 두 설정 로더 전체 |76363 / `022e83` |132 passed /21.536초 |
| 기존 로그인·이전/새 저장 schema |27860 / `a9614c` |94 passed,7 deselected /35.036초 |

새 검사는 실제 PostgreSQL16.15 TCP SCRAM에서 누락/False/True를 각각 확인했다.
각 모드의4역할×3테이블×7권한=84개 catalog 검사를 통과했다.
새 table 실행은 누락/False 각각20거부, True에서 authority SELECT/INSERT2허용·나머지18거부다.
현재 실제 DB는 PG16이며 PG17+ MAINTAIN 거부의 새 hosted 실행은 별도다.

정상 authority 삽입/조회는 원 bytes/SHA와 마이크로초 UTC를 보존했다.
각 모드에서 owner/authority로의 승격6건을 거부했고 이전2테이블의 원 행/grant를 유지했다.
미설치 table의 audit/설치는 거부하며 runtime 역할을 부분 생성하지 않았다.
누락 grant와 PUBLIC/table/column/routine/grant option/membership 변경12건을 감사가 거부했다.
각 변경을 rollback한 뒤 정상 전체 audit를 다시 확인했다.
기존 두 operator 판본은 누락/False4건 허용, True/잘못된 타입14건을 factory 전에 거부했고 FD12→12다.

원 호환 실패 probe61045→`8bb3a9`는 실제 종료1/3 failed였다.
기존 정상 테스트를 수정하지 않고 제품 로더를 보완한 뒤 전체132개를 통과했다.
새7개에서는8개 수치 진입점을 금지했다. 기존 회귀의 fixture 계산까지 호출0으로 주장하지 않는다.

## 보존·CLI·관문

모든 원 명령을 실제 회수했고 최종3명령은 종료0·FD4→4다.
PG/schema/role/passfile/임시 PG 디렉터리 잔여0이며 기존 인증 실패 시험이 남긴
소유 private `invalid.pgpass`2개는 신원/경로/단일 링크/600권한 확인 뒤 정리했다.
원본2,148항목·source1,748개·기동 source/assets·기존3프로세스와 frontend200을 보존했다.
최종 .25초 관측 최대 단일/소유+보호 RSS147,255,296/543,592,448bytes로512MiB/1GiB 안이다.
선행 schema core3는 원 SHA 그대로다. 공존은 원 행/grant와 고정 UI의 보존이며 임의 과거 서명 판본의 현재 store 이식 수용은 아니다.

native CLI `gpt-6.1-sol / xhigh`, turn_context `2026-10-09T19:56:50.854Z`, LF 포함 SHA
`137117f4667e65c61fc97f9eaff1b9ad661a153f964b3b8a6c4c45f6572fb241`에서 판단했다.
재귀 CLI0·신규 제품 runtime CLI0이며 core5/계약/검증 기록이 검토 가능한 산출물이다.
전체 backend·이전82/993 전체 수치/저장 회귀·전체166일 producer·새 API/WebGL은 재실행하지 않았다.
실제 품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4 `not_assessed/hold`를 유지한다.

## 다음 한 단계

`crop-climate-joint-result-storage`의 core3는 새 store module/해당 tests/contract다.
현재 farm/자료 권리와 원 signed intent/HEAD/proof/root·source/context/evidence/UTC를
닫힌 metadata·별도 domain HMAC/ID에 묶고, 새 명시 authority 권한으로 원자 등록한다.
실제 DB/fresh 현재 조회·원 bytes/조회 계산0·철회/rollback/중복·이전 결과 공존을 확인한다.
그 뒤 현재 권리2MiB API→같은 UTC3D→사용자 실행/U3를 연결한다.

기존1–2집중시간의 역할 추정은 native 판단부터 최종 종료까지 약12분·최종3명령 관측으로 갱신한다.
store는 기존266줄/현재 작은 실제 farm/custody 검증 비용을 근거로2–4집중시간 잠정이다.
10/10 연속 작업·새 오류 없음 조건이며 UI/제품 완료 날짜는 API/3D 실측과 외부 자료 확보 뒤 갱신한다.
