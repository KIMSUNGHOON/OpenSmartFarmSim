# 현재 환기 계산의 서버 서명 이력·재개 — 2026-10-12

상태: 집중 검증·최종 보존 확인 뒤 로컬 수용. 합성 소프트웨어 계산 범위다.
새 모델은 사용자 UI/worker/제품 API에 아직 배포하지 않았다. 실제 농장 Run/국내 독립 검증 자료는0이며 G0–G4는 `not_assessed`다.

## 사용자에게 보이는 범위와 다음 순서

현재 [5174 계산 상태](http://localhost:5174/#crop-execution)는 기존128초 합성 작업의 상태와 저장 결과를 제공한다.
해당 원 작업은64/64걸음·9시점/3사건으로 이미 완료됐다. 개발용 검증 DB의 실행이나 Codex 개발 과정이 이 작업의 진행률로 표시되지는 않는다.
5173의 완료166일 저장 재생과 두 사용자 서비스는 유지한다. 개발/배포 상태 패널은 빌드 시점 기록이며 실시간 개발 중계가 아니다.

이번 단계는 새 환기 모델의 원 입력·현재 농장 결속·25장부/UTC artifact를 trusted 서버 서명 이력으로 연결한다.
다음은 결과 등록/보호 API(잠정1–2집중시간) → worker/typed web/같은 UTC3D(2–4) → 실제 사용자 적용(1–2)이다.
남은 합계4–8집중작업시간은 위 작업 분해의 잠정 작업량이며 연속 작업·검증 통과 조건이다. 완료 시각 약속이나 전체 제품 일정은 아니다.
전체 작기 온실/물·양분/구매 에너지·Decimal 경제/최종 UI와 독립 농장 검증은 남아 있어 전체 제품 완료 날짜는 미정이다.

## 구현

- [서버 모듈](../backend/app/crop_greenhouse_ventilation_server_custody.py), [검사](../backend/tests/test_crop_greenhouse_ventilation_server_custody.py), [계약](../contracts/crop-greenhouse-ventilation-server-custody-v1.md).
- 정확한 새 farm binding·input evidence·storage/time/continuation을 사용한다. 기존22장부 custody/서명 domain·reader와 구분한다.
- 원 실외 입력과 다른 forcing을 보존하고 초기 `{rhs,boundary}`·원 context/UTC를 입력 증거와 byte 대사한다.
- 서버 소유 intent와 각 HEAD/직전 proof를 새 domain HMAC으로 서명한다. proof fsync 뒤 원자 HEAD를 게시하며 현재 권리/입력/검토를 전후에 확인한다.
- 조회는 Context/UTC 준비·RHS·환기·적분·관리·checkpoint 복원을 호출하지 않는다. 새 HTTP 상태/부분 결과 API는 이번 범위에 포함하지 않는다.
- 기존 권한/SCRAM/파일 상한과 원자 storage helper를 재사용했다. 제품 DB/역할/서비스·의존 패키지는 추가하지 않았다.

## 실제 검증

한 번의 전체 backend/CI 실행으로 합산하지 않았다. 집중 새7/기존4 = 고유11개 pytest 그룹이다.

| 범위 | 원 도구 세션 | guard wall(초) | 확인 |
| --- | --- | --- | --- |
|정상·fresh 재개|`75665`|76.999|원16걸음·3시점/3사건·동일 checkpoint/UTC·조회0|
|현재 권리/변조/hold/구 판본 거부|`33769`|178.220|새4그룹·late 철회/원 HEAD·실패 trial 미게시|
|실제 HEAD 전후 SIGKILL·재개|`94150`|115.290|새2그룹·실제 child -9·선택 prefix1/2→원 최종 checkpoint|
|기존 custody 회귀|`15224`|214.884|기존4그룹·SCRAM/fresh/철회/변조/hold|

정상 최초 boundary는 RHS6/환기3회(준비2/1·checkpoint 확인1/1·관리3/1)다.
fresh 재개는 RHS106/환기85회이며 이미 확정된 사건을 다시 실행하지 않았다. 최종 checkpoint SHA는 `581efd5846d191f1d24857de6da8af61b606bcc85eabf8ed9a9e0c5dfa0b5f8b`다.
상태·terminal 재호출·원 페이지의9개 수치 진입점은0이다. 원108상태·25연속/6사건/10수지와 원 UTC를 확인했다.
실제 hold는 원 실패 시각 `2026-10-01T00:00:32.123456Z`와 마지막 step-end를 보존하며 실패 trial/관리 후 출력은 게시하지 않았다.

실제 SIGKILL의 before/after HEAD에서 선택 commit은 각각1/2였다. 두 fresh 프로세스는 실제 -9로 종료됐고 재개 후 원 최종 checkpoint/last_confirmed와 같았다.
선택되지 않은 blob/proof는 용량에 포함하며 정상 결과로 제시하지 않는다. 파일 lock·같은 revision 충돌·권리/검토/원 bytes 철회·canonical HMAC/HEAD/commit/page 변조와 구 authority/domain을 거부했다.

### 실패 기록과 검사 코드 수정

첫 smoke `49650`은 수치 계측이 이전 driver의 속성을 참조해 실제1로 종료했다. 새 driver.stage.joint로 고친 정상 검사는 위 `75665`다.
crash v1 `46624`의2그룹은 실제 -9/선택 prefix 확인 뒤 비교 oracle이 packet tuple을 Binding으로 참조해 실패했다.
수정은 crash 검사 함수의 tuple 인덱스2곳뿐이며 AST 대사로 이전 통과5개 함수·생산 코드/계약 불변을 확인했다.
수정된2그룹은 `94150`에서 통과했다. 따라서11그룹 전체가 한 번에 같은 검사 파일 bytes로 실행됐다고 주장하지 않는다.
전후 검사 SHA/AST 변경 범위·원 guard/log 해시는 [영수증](artifacts/crop-greenhouse-ventilation-server-custody-reference-20261012.json)에 남겼다. 실패를 성공으로 집계하지 않는다.

## 자원·보존·CLI·남은 조건

위 성공4명령 모두 실제 종료0·FD4→4·schema/role/소유 PG/임시 PG/passfile 잔여0이다.
.25초 관측 최대 단일 RSS139,223,040bytes/소유+보호 합970,399,744bytes로512MiB/1GiB 안이다.
최종 보존 원8486 실제0(0.608초)에서 원본2,148항목·기존239계산 파일·accepted frozen source1,911/원 자산171·현재5174 자산171/설정·두 주소200/4보호 root·권리/키/접속 안내를 대사했다. 현재5174 자산은 이번 단계에서 채취한171개 해시와 같고 index는 기존 수용 해시와 같다. 로컬 링크2,020개도 확인했다.
기존 사용자 DB/결과·worker/백엔드는 재기동하지 않았고 token/권리는 변경하지 않았다.

현재 native Codex CLI `gpt-6.1-sol`/`xhigh`의 실제 turn context 시각 `2026-10-11T15:18:34.455Z`와 raw-line SHA를 영수증에 기록했다. 재귀 CLI 실행0이다.
새 원문/계수/자료 권리를 채택하지 않았고 기존 source review SHA를 고정했다. CLI 제안은 검토 증거이며 관문 승인이나 실제 품종 보정으로 취급하지 않는다.
전체 CI/remote fetch/push·새 API/worker/WebGL·전체 작기 재계산은 실행하지 않았다.
다음 수용은 새 결과 등록과 실제 SCRAM/TLS 보호 API의 원 수치/UTC·현재 권리·조회 수치0·completed/hold 및 기존 결과 보존이다.
