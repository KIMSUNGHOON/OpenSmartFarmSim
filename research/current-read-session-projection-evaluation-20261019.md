# 현재 세션 SQL 한 투영: 미채택 — 2026-10-19

[기계 증거](artifacts/current-read-session-projection-evaluation-20261019.json) · [직전 제품46검사](market-current-connection-parameters-20261019.md).
현재 native Codex CLI `gpt-6.1-sol` / `xhigh`의 실제 turn_context를 기록했다. 재귀 CLI/하위 에이전트는 실행하지 않았다.

## 후보와 실제 판단

공유 읽기의 실제 identity/Read Only/isolation3질의를 한 SELECT로 결합했다. 일반 로그인의 원 client 인증 전제·3열 SQL/반환·connect_runtime AST를 보존한 작은 공통 인증 함수와 내부 세션 함수로 시험했다. 현재 값5개·원천/권한/클라이언트 설정 검사는 매번 실제로 수행했고 값/권한 cache는 없었다. 후보는 [PostgreSQL16 current_setting/SHOW](https://www.postgresql.org/docs/16/functions-admin.html#FUNCTIONS-ADMIN-SET)를 API 근거로 삼았다.

같은 실제 작업에서 baseline/candidate/candidate/baseline을 실행했다. 원 SQL12,919→11,719·감사343/원천3,040/순서·매개변수2,163회/원 counts·step2~5/UTC04/06/08/10.123456Z를 보존했다.

| 비교 | baseline wall초 | candidate wall초 | 판단 |
|---|---|---|---|
| 사설 feasibility | 9.304420, 9.637897 | 9.085514, 9.189379 | 평균 3.523% 감소 |
| 실제 제품 source | 8.863033, 9.144551 | 9.026342, 8.978578 | 평균 0.0148%·짝별 -1.843%/+1.815% |

제품 결과에서 한 쌍은 더 느렸으며 일관되고 유용한 비용 감소를 입증하지 못했다. **미채택**했다. 사설 표본의 감소나 SQL 수 감소를 제품/독립 처리량 개선으로 보고하지 않는다. 같은 후보를 다시 실행해 통과 표본을 고르지 않는다.

## 검증·복원 범위

후보의8경계 검사와 실제 제품 비교1이 통과했다. 실제5값/설정 조회·호출마다 fresh SQL, 일반 로그인 None 규약, Read Only/Read Write/Repeatable Read의 실제SHOW 일치, 관리자 신원 위장/tuple row factory/실제SET ROLE 변경 거부와 정리를 확인했다. 첫 RED는 원3질의였다. 초기8 뒤 active-transaction 시험 조건을 보완하고 최종8을 다시 실행했으며 중복 합산하지 않는다.

이는 후보의 전체 보안/통합 수용이 아니다. 비용 관문 실패 뒤 계획된 일반 로그인10/이전 매개변수9/공유29/늦은 변경5/normal·hold2 회귀는 실행하지 않았다. 독립64·전체backend/browser·새fresh exec/SIGKILL도 미실행이다.

제품2파일과 새 시험·후보 계약은 고정 source/hash로 사설 보존했다. 제품 파일은30f8104 원 bytes로 복원했고 새 시험/계약은 활성 트리에서 제거했다. app261파일 집계 SHA `8ab6e2dbfc808c212a18e21cdcdcfc524f51df5a364cfaab3b4228c7c3c7fff9` 및 app/tests diff0을 확인했다. 기존46은 같은 app source의 기록으로 유지하며 재실행 수로 세지 않는다. 새 API/후보가 제품에 남아 있지 않다.

## 복원한 현재 코드의 실제 비용

actual before→advance→confirm 한 묶음의 벽시계는9.485538초, 클라이언트 스레드 CPU는6.691992초였다. 실제 SQL 실행12,919회의 wall4.517090초/클라이언트CPU1.871472초, fetch의 wall0.122320초/CPU0.108891초다. 측정한DB호출 밖 클라이언트CPU는4.711629초이며 관찰자 비용도 포함한다. 배타적 outermost 실행/읽기만 합산했다. wall-클라이언트CPU를 서버CPU로 해석하지 않는다.

| SQL 위치 | 호출 | wall초 | client CPU초 |
|---|---:|---:|---:|
| 원천 SELECT | 3,040 | 0.679299 | 0.384298 |
| column 권한 행렬 | 343 | 0.526532 | 0.153201 |
| table 권한 행렬 | 343 | 0.461046 | 0.166135 |
| DDL/definer 검사 | 343 | 0.410699 | 0.051784 |
| ACL identity 검사 | 343 | 0.377939 | 0.053082 |

후속 owned-process CPU 샘플은 요청2ms 주기·최대12,000개에서 1584개를 기록했다. 원9.104856초/CPU6.448959초·step2/UTC04.123456Z·timer/handler 복원과 정리를 확인했다. OS 전달 해상도/지연·C 확장의 Python frame 귀속 편향이 있으므로 표본 수를 정확한 CPU 비율/처리량으로 쓰지 않는다. 앱 메서드/반환을 대체하지 않았다.

JSON iterencode209, 입력JSON pairs의 주요 위치92/22, joint canonical의 가까운앱 위치160 등의 관측과 상위 stack은 입력 증거의 signature/record_hashes/verify 경로를 가리켰다. 파일 해시/PG metadata/권한 행렬도 남아 있다. 동시 전체 시간의 중첩/샘플 수를 합산하지 않는다.

## 다음 범위와 보류

다음은 입력 증거 verify와 binding._input의 JSON decode/canonicalization 호출·비용을 먼저 분리하는 것이다. 그 뒤 이미 검증된 결속 메타데이터를 작은 불변 투영으로 전달해 불필요한 재파싱만 줄이는 시험 후보를 비교한다. 서명·schema·검토자·현재 파일/해시·software pin·권리 검사의 실제 호출, 원 공개record의 의미·원 수치/UTC·감사/원천 읽기·수명·정리를 보존해야 한다. 현재 입력 증거 검증을 생략하거나 권한 결과를 저장하지 않는다. 새 투영 구현/수용은 아직 없다.

기각된 역할SQL15→4/pipeline/ACL/v4/이번session3→1 및 변경 없는 native64를 반복하지 않는다. 독립64/chunk1/조회/retry360/RSS 정상→hold→HTTP취소→계산 중WebGL→WSL 용량/사용자 적용은 남아 있다. 실제 농장Run0·실제 자료/독립 농장/미래/비교·G0–G4/새Solar/전체완료일은 미수용/미정이며 goal active다.

5개 성공 실험 stage 모두 보호5root/원본2,148/두frozenUI·512MiB/PID/합1GiB·FD4→4·소유PG/임시/passfile 잔여0을 확인했다. 원 단계/UTC와 현재 권리 검사를 바꾸지 않았다. 총 guard는 234.387초이며 현재 성능/전체 완료 추정이 아니다.

최종 게시 `focused-read-session-rejection-status-v1`은 실제 자식0·guard1.379042초였다. 원 app/tests 복원·전체app261파일·미채택/원 증거 해시·원 actor/로컬 링크2,380개·두 HTTP200/동일bytes/no-store·frozen HTML/환기2,173파일/5root/원본/FD/정리를 대사했다. UI 코드/DOM/WebGL은 변경/재실행하지 않았다.
