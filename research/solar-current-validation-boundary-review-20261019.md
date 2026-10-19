# 일사 실행의 현재 검증 연결 재검토 — 2026-10-19

[기계 증거](artifacts/solar-current-validation-boundary-review-20261019.json) · [현재 제품88검사](solar-input-binding-metadata-20261019.md) · [기각된 역할 SQL 후보](runtime-role-audit-phases-evaluation-20261019.md).

현재 native Codex CLI `gpt-6.1-sol` / `xhigh`의 실제 turn_context 시각·해시를 기록했다. 재귀 CLI/하위 에이전트는 실행하지 않았다. 이전 goal turn은 제품94e11a4/88검사·실제 비교·게시·커밋으로 진척이며, 이번에도 실제 관측과 후보 기각으로 다음 작업을 바꿨다.

## 상태와 관측

제품 app/tests는 **94e11a4 원 bytes 그대로**다. backend app261파일 집계 SHA를 각 stage 원 source pin과 대사했다. 추가 진단/시험의 고유5건을 완료했고 기존88/46을 재실행하거나 합산하지 않았다. 실행 중인 소유 stage는 없다. 이전 독립 CI39250605987·39249166964는 실패로 완료됐고 이번 source의 독립64는 실행하지 않았다.

- CPU: 원 quantum·step2/UTC04.123456Z에서1537표본·누락0, 요청2ms/최대12000/48프레임 제한과 timer/handler 복원을 확인했다. wall8.980668초/client CPU6.122028초다. C 확장·신호 스케줄링·표본 편향이 있어 정확한 CPU 백분율이나 처리량 수용으로 쓰지 않는다.
- 별도 SQL 관측: Python call profiler/CPU sampler 없이 원 SQL12,919/권한 감사343/원천3,040을 유지했다. 전체 quantum wall9.253057초/client CPU6.475240초, 배타 SQL execute wall4.550637초/client CPU1.889665초, fetchone/fetchall 합wall0.123296초다. wall−client CPU를 DB 서버 CPU로 부르지 않는다. 관찰 오버헤드는 포함한다.
- 현재 드라이버는 이미 Psycopg3.3.6의 binary/libpq180006·C adaptation이며 Python3.12.3이다. 설치/lock/환경을 바꾸지 않았다.

## 두 미세 후보: 제품 미채택

두 후보 모두 원 SQL/감사/원천·counts와 단계2→5/UTC04/06/08/10.123456Z를 유지했다. 같은 실제 작업의 ABBA 비교이며 별도 profiler는 없다. 판단 기준은 평균 감소2% 이상과 두 짝 모두 감소다. 영수증 후보의 기준은 결과를 열람하기 전에 기록했으며 허용 목록 후보는 실행 전에 기록했다.

| 후보 | 기존 wall초 | 후보 wall초 | 평균 감소율 | 짝별 감소율 | 판단 |
|---|---|---|---:|---|---|
| 한 canonical payload로 닫힌 envelope/HMAC 검사 | 8.707105 / 8.808204 | 8.868354 / 8.841521 | -1.1108% | -1.8519% / -0.3783% | 미채택 |
| 감사 안에서 허용 테이블 집합 한 번 생성 | 8.695414 / 8.830934 | 8.816678 / 8.765598 | -0.3191% | -1.3946% / +0.7399% | 미채택 |

허용 목록 함수 호출은62,769→686으로 줄었으나 실제 계산 개선이 일관되지 않았다. 영수증 후보도 두 짝 모두 느렸다. 후보의 위조/철회/보안 회귀와 실제 제품 구현·추가 비용 검사를 진행하지 않았다. 판정은 비용 미충족이며 정확성/보안 수용이 아니다. 제품에 새 helper/cache/서명 알고리즘/SQL 변경을 추가하지 않았다.

[Python3.12 JSON 공식 문서](https://docs.python.org/3.12/library/json.html)는 sort_keys·separators·ensure_ascii 동작을 확인하는 소프트웨어 참고로만 읽었다. 이 프로젝트의 원 정규화 bytes와 동등성은 문서 링크만으로 승인되지 않는다. 원 웹 문서를 저장/재배포하거나 농업 입력 자료로 채택하지 않았다.

영수증 raw 증거의 scope 문장에는 이전 투영 시험에서 복사된 설명 일부가 남았다. 실제 실행 AST/probe SHA·timing/SQL/UTC를 기준으로 판정했으며, 투영만 바꾼 시험이나 별도 callback-count/음성 경계 검사를 실행한 것으로 주장하지 않는다. 정정은 기계 증거에 명시했고 원 증거를 수정하지 않았다.

## 권한 감사가 발생하는 실제 경로

원 메서드·SQL/반환값을 그대로 전달하는 별도 관찰1건으로343감사를 대사했다. 원 quantum의 쓰기 SQL은3문장이었고, 다음은 감사의 직접 호출자다.

| 호출자 | 횟수 |
|---|---:|
| `app.job_store.connect` | 123 |
| `app.market_candidate_store._reference_guard` | 52 |
| `app.market_candidate_store.read_scope` | 8 |
| `app.market_runtime.connect_market` | 40 |
| `app.market_source_store.read_scope` | 40 |
| `app.thermal_run_store.connect` | 80 |

전체 audit 포함 wall합3.067617초/clientCPU1.101763초다. 원 quantum wall9.039766초와 중첩하므로 더하지 않는다. 이것은 감사 생략이나 새 묶음의 수용 증거가 아니다. 관측한 conn.read_only 속성None은 서버의 실제 transaction_read_only 상태를 증명하지 않는다. 원 table/column 별도 SQL 사이의 철회·관계 삭제 거부 계약도 유지한다. 15→4 SQL/pipeline/직접 ACL·세션3→1/기각 getter 후보는 재적용하지 않았다.

## 생장 계산과 경제 검증 연결: 정적 코드 대조

`codebase-design` 스킬로 `FarmAuthoringService → SolarFarmBinding`의 Interface를 추적했다. source SHA와 AST 소비 필드를 기계 증거에 고정했다.

| 위치 | 실제 소비/검증 |
|---|---|
| `SolarFarmBinding._registration` | registration의 farm/binding만 읽는다. 작물·batch·점유/재배일·decision_at·zone·floor_area·farm/등록 hash와 전체 source_binding hash를 만든다. compiled/경제 계산 결과를 수치 계산에 사용하지 않는다. farm 전체 hash에는 경제 pin/목표·현금/CAPEX 제약·판매 달력도 포함된다. |
| `FarmAuthoringService._read/_prepare` | 위 요청을 처리하면서 연구 authority/snapshot과 전체 MarketScenarioService.validate_pinned_context·경제 scope·물리 입력 compiler를 다시 검증한다. |
| `RegistrationRead._current` | cache hit에서도 현재 등록/연구/snapshot과 모든 기록된 참조 getter를 다시 확인한다. 원천3,040회가 이 경로에 연결된다. |
| 결과 저장 | 원 binding 전체를 보존하고 원 crop/batch/zone·등록/입력·계산 artifact·정책을 연결한다. 경제 검증을 통과한 수익/예측으로 승격하지 않는다. |

현재 v1의 full source_binding hash는 경제 후보/rights_manifest/context 등을 포함하고, 기존 등록 계약은 현재 경제 참조/권리도 재검증하도록 요구한다. 따라서 현재 호출을 raw farm row 조회나 과거 승인 receipt로 대체할 수 없다. 이번 검토로 그 검사를 생략하는 것을 승인하지 않았다.

제품 명세의 물리 Run/시장 시나리오 분리와 생장→저장3D→자원/Decimal 경제 순서를 근거로, **다음은 생장 계산용 현재 농장 정보의 별도 판본 계약을 먼저 설계/대조**한다. v1과 기존 API/현재 경제 검증은 유지한다. 실측 병목이 연결된 실제 Module의 책임을 검토하는 작업이며 새 운영 서비스/프레임워크 도입은 아니다.

### 다음 한 단계의 수용 기준

1. 물리 계산이 소비하는 모든 원 농장·지역/연구·crop/batch/zone/area·작기/점유·decision_at·source/권리/검토·model/profile facts를 표로 고정하고 각 현재 검증의 책임을 명시한다. label·계획·해시와 실제 입력 수치를 구분한다.
2. 원 full binding/등록/경제 v1의 현재성과 철회 의미를 보존한다. 새 물리 전용 capability가 필요하면 별도 판본·명시 선택·기본 거부를 정의하고, 독립 authority/증거 없이 활성화하지 않는다. 과거 receipt·서명·보관 cache로 현재 권한을 대신하지 않는다.
3. 경제 자료 철회와 실제 물리 입력/농장 권리 철회가 계산·저장·표시·경제 평가에 미치는 영향을 각각 정의한다. 현재 v1 계약의 실패를 성공으로 바꾸지 않는다. G0–G4·예측/추천 게시 조건은 유지한다.
4. 전환 전에 원64/chunk1/조회·retry360초/RSS·원 숫자/UTC·actor의 수용 시험 적용 관계를 고정한다. 기존 실패를 보존하며 새로운 더 쉬운 시험으로 대체하지 않는다. 기존 actor/input을 바꾸지 않는 연결 가능성이 입증돼야 한다.
5. 구현 작업은 최소 reader→실제 SCRAM/별도 fresh·현재/늦은 권리·grant/source/code/lease/cancel·원자 게시/hold/정리→같은 실제 paired→독립 정상/hold/HTTP취소→계산 중WebGL/WSL 용량/사용자 적용으로 나눈다. 어느 단계도 아직 완료로 표시하지 않는다.

현재5건의 guard합254.448초와5root/원본2,148/두 frozen UI·512MiB/PID/합1GiB·FD4→4·소유 PG/schema/role/임시/passfile 잔여0을 확인했다. 전체 backend/browser/독립64·새 Solar·실제 품종/농장/미래/대응 비교 검증은 미실행/미수용이며 실제 농장 Run0·G0–G4 보류·goal active다. 외부 자료 권리/독립 검증과 원360초 완료 증거가 없어 전체 완료일/남은 시간은 미정이다.

최종 게시 `focused-validation-boundary-review-status-v1`은 자식0/guard1.379802초였다. app261파일/원 tests·단계별 증거/소비필드 source SHA·로컬 링크2,391개·원 actor 해시를 확인했다. 두 HTTP200/동일bytes/no-store·frozen HTML/환기2,173파일·5root/FD/정리를 유지했다. 기록 시각은2026-10-19T14:58:21.880419Z이며 UI 코드/DOM/WebGL은 재검증하지 않았다.
