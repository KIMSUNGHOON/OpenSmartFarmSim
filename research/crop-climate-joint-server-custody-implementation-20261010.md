# 공동 작물·기후 계산의 서버 서명 이력 — 2026-10-10

상태: **작은 합성 계산의 서버 소유 이력을 로컬 수용**했다.
core `4b1d0e70b649d575590b40a697206d0bcfcfdf60`, 별도 프로세스 검사 환경 보완 `9cd5b2cf0345a300dd6ba8506d99d40309d52ae4`다.
사용자 UI는 기존 완료166일 결과를 계속 읽으며, 이번 새 공동 모델의 DB 등록/API/3D·실시간 U3는 아직 없다.
실제 품종 입력·농장 작물 Run·국내 독립 자료는0건, G0–G4는 `not_assessed/hold`다.

## 구현과 사용자가 검토할 산출물

- [서버 소유 이력 계약](../contracts/crop-climate-joint-server-custody-v1.md),
  [코드](../backend/app/crop_climate_joint_server_custody.py), [검사](../backend/tests/test_crop_climate_joint_server_custody.py).
- [원 수치·UTC·서명 영수증·종료/자원 기록](artifacts/crop-climate-joint-server-custody-reference-20261010.json):
  739,600bytes, SHA-256 `922975556694da737241d28a37a9bb4d93fded4dd5829dd5c8be01751ad2e44d`.
- 새 domain HMAC은 tenant/study/revision의 원 요청·현재 농장 결속과 각 선택 HEAD/직전 proof를 인증한다.
  proof를 fsync한 뒤 원 storage HEAD를 교체한다. 기존121상태 context/reader/authority를 새 모델로 위장하지 않는다.
- 원 source로 공식108상태 Context/UTC를 준비하고 서명된 입력 record와 대사한다.
  재개는 선택된 원 checkpoint만 복원한다. 상태/완료 페이지 조회는 Context 준비·복원·RHS·적분·사건0회다.
- intent/계산/서명·HEAD/조회 전후에 현재 농장·자료·검토 권리를 확인한다.
  조회는 여러 외부 저장소에 대한 원자 snapshot을 뜻하지 않으며, DB의 독립 단조 이력/등록은 다음 단계다.

## 실제 통과 범위

실제 PostgreSQL16.15와 TCP SCRAM 농장을 사용하는 **4개 pytest 그룹을 순차 통과**했다.
한 번의 전체 backend 실행 결과로 합산하지 않는다. 당시 core3 bytes는4그룹에서 동일했다.

| 검사 | 실제 도구 / 명령 세션 | guard wall | 확인한 사실 |
| --- | --- | --- | --- |
| 정상·fresh 재개 | `ce1f4c` /84566 |74.693초 | 원32초/16걸음,3저장 시점/3관리 사건·같은 checkpoint/UTC, 별도 exec1940571 종료0 |
| 현재 권리·입력·잠금 | `f84d3e` /43649 |42.032초 | 현재 read/write scopes·다른 계정·자료/검토/원 bytes 철회, 요청 충돌4·잘못된 raw5/budget7, 실제 잠금,128intent 상한 전 검사 |
| 변조·늦은 철회 | `f641ff` /5476 |53.253초 | intent/proof/HEAD/commit/sample bytes와 canonical HMAC 변조 거부, proof 직후 권리 철회 시 기존 선택 HEAD 보존 |
| 실제 계산 hold | `70b2ba` /94616 |51.982초 | 마지막 관리 사건 실패, 원 실패 UTC `2026-10-01T00:00:32.123456Z`·마지막 step-end 보존, 실패 시점의 사건/출력 행 미게시 |
| 별도 root 대사 | `76ad33` /61505 |1.073초 | 실제 저장 영수증의 HMAC/원 parent SHA·순서3→2→1→0, key/domain/JSON 거부6개, 수치 호출0 |

정상 첫 boundary의 RHS4회는 준비1+checkpoint 검사1+관리 사건2다.
fresh 재개는 준비1·복원1·chunk 검사1+남은16걸음×5+남은2사건×2=**RHS87회**다.
이미 확정된 t0 사건을 다시 실행하지 않았다. 원 최종 checkpoint SHA는
`b4866a7846123c4449b5b46933eb688f21a2390df54970a186feb7931eebeee8`, 진행 응답은22,447bytes다.
정상/hold·재호출/페이지 조회에서8개 수치 진입점0을 확인했다. jobs/events/crop rows/Run은 전후 그대로다.

늦은 철회 뒤 선택되지 않은 불변 blob/proof는 용량에 포함되므로 storage_bytes/file_count는 증가할 수 있다.
선택 HEAD·원 checkpoint·확정 행의 불변성을 검증했으며 진행 bytes 전체가 동일하다고 주장하지 않는다.
root 대사는 정리된 농장 DB를 다시 조회하지 않았다. live SCRAM/fresh 권리는 원4그룹의 실제 증거다.

## 공유 전 별도 프로세스 실행 환경 보완

CI 실행 코드가 부모 `PYTHONPATH`를 제공하지 않는 사실을 확인했다.
동일 조건의 실제 child import가 종료1/ModuleNotFoundError였고(`fed7b7`), 이 probe는 DB fixture를 시작하지 않았다.
6개 공동 계산 검사 파일의7개 subprocess 호출에 backend/tests의 절대 경로를 명시했다.
AST 대사 `bfaaa2`는 변경이 import와 child env 전달뿐임을 확인했다.

부모 `PYTHONPATH`를 제거한 별도 guard에서 **10+1+1=12개 집중 검사**를 통과했다:
순수 복원/UTC/저장/입력10개(`0af08c`,8.539초), 실제 농장 fresh1개(`3953da`,18.418초),
서명 계산 fresh 재개1개(`9d7abc`,73.500초).
실제 저장 HEAD 전후 SIGKILL2사례도 그10개에 포함되며 별도 count로 더하지 않는다.
원 수치 식·입력·제품 모듈은 변경하지 않았다. core/선행38파일 중6개 검사 파일의 전후 SHA를 별도로 기록했고 나머지32파일은 보존했다.
앞선35선행 core·9물리 코드·16oracle의 보존은4b1d core 수용 시점의 사실이다.
이후 환경 보완의 검사 파일 변경을 원 영수증에 덮어쓰지 않았다.
최종 링크 검사에서 새 custody 계약의 UTC 링크 이름1개를 수정했다. 계약의 전후 SHA를 별도 기록했으며 계산/서명 코드 변경은 없다.

## 종료·자원·CLI·CI

원4그룹/root와 환경 보완3명령 모두 실제 종료0·FD4→4다.
각 DB 명령의 schema/role/passfile/PG/임시 디렉터리 잔여0, 원본2,148항목·기동 source/assets와 사용자 미리보기를 보존했다.
.25초 관측의 최대 단일 RSS147,255,296bytes/소유+보호 합605,310,976bytes로512MiB/1GiB 안이다.
사용자 frontend는200·기존 보호 서비스는 생존했다. preview DB에 이번 결과를 삽입하지 않았다.

판단은 현재 Codex CLI `gpt-6.1-sol / xhigh`에서 수행했다. native turn_context는
`2026-10-09T19:05:09.708Z`, 원 LF 포함 SHA
`46ee8245f52fc1045b725e52ecc8c05825b2d078b68462c94a764ef0f8238b85`다.
재귀 CLI0·이번 제품 runtime CLI 신규 호출0이며, 코드/계약/증거가 검토 가능한 판단 산출물이다.

선행703e49c의 [Backend](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37962183498)는6분할/집계 성공으로 종료했다.
같은 SHA의 Web/Authored PG/runtime/Compose도 실제 terminal success를 확인했다.
이 상태는 이번 core SHA의 hosted 수용이 아니다. 기존 전체166일 RHS/writer/API/WebGL·82/993 전체 회귀를 다시 돌리지 않았다.

## 다음 단계와 외부 의존성

기존 결과 SQL은 이전 model/version/ref/scope를 고정하며 새 source/UTC를 받을 수 없다.
따라서 [계획](../tasks/plan.md#구현과-검증-자료의-병행-경로)에 따라 새 결과 schema→명시 역할/grant→등록·현재 권리 조회로 나눈다.
다음 한 단계는 **기존 결과를 보존하는 새 불변 metadata SQL/contract**다.
닫힌 JSON·중복 key·raw SHA·컬럼 대사·현재 tenant/farm FK·고유 intent·수치/용량 범위·수정/삭제 거부를 실제 PG에서 확인한다.
그다음2MiB API→같은 UTC의 수치3D→사용자 실행/U3다. 이 report는 UI 실시간 연동 완료 증거가 아니다.
새3자식은 기존96줄 schema/266줄 store/321줄 roles와 작은 실제 fixture를 근거로4–8집중시간 잠정이다.
10/10 연속 작업·추가 오류 없음 조건의 검토 목표이며 API/3D·전체 제품의 완료일은 아니다.
실제 품종·온실 경계 forcing/물·양분/구매 에너지/경제·독립 농장 자료와 G0–G4의 외부 증거는 여전히 필요하다.
