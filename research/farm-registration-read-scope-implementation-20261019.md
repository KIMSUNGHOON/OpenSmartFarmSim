# 한 custody 작업 안의 농장 입력 재구성 — 2026-10-19 KST

[계약](../contracts/farm-registration-read-scope-v1.md) ·
[기계 증거](artifacts/farm-registration-read-scope-implementation-20261019.json) ·
[선행 관측](crop-solar-current-binding-cost-20261018.md).

## 변경과 경계

Solar custody의 명시적 `_open` 수명 안에서 첫 농장 등록 조회만 원래의 전체
입력 검증·결정적 재구성을 수행한다. 이후 조회도 실제 farm/research 행과 현재
registry/context·thermal snapshot을 읽고, 처음 기록한 시장 getter를 중복까지 같은
순서로 실제 저장소에서 호출한다. 값·인자·판본과 principal/scopes/pointer/code/Decimal
문맥이 모두 같을 때만 재구성 결과를 복사해 사용한다.

권한·원천·role 감사 결과나 DB 연결을 캐시하지 않는다. 잘못된 계정·판본·중첩·다른
실행자·닫힌 수명·변경된 자료/권한은 거부한다. 오류 때 수명을 폐기하고 다음 작업과
일반 조회는 다시 전체 검증한다. 원 current 경계·HMAC/ancestry·수식·worker·query와
원 입력/64단계/chunk1/재시도/조회 주기/360초 및 RSS 상한을 바꾸지 않았다.
새 의존성은 없다. helper도 불변 binding의 코드 의존성 해시에 포함한다.

## 통과한 검증

- 최초 시험 fixture의 dict 검증은 strict 날짜 전송 형식 때문에 실패했다.
  JSON 전송으로 교정한 뒤, 원 코드의 scope 누락을 실제 RED로 확인했다.
  원천 오류가 그대로 노출되는 별도 RED도 확인하고 일반 FarmAuthoringHold로 정리했다.
  이 실패·교정·중복 실행은 아래 고유 검사 수에 더하지 않는다.
- `94107:0`: 신규13/기존3의 **16검사**. 재구성1회/다음 수명 재검증·복사 격리·SQL 변경0·
  원천/권한/연구/snapshot/추가 grant·늦은 철회·계정/판본/중첩/오류/스레드·코드/pointer/
  Decimal 문맥 변경 차단을 확인했다. guard184.939초·합 RSS1,038,716,928bytes다.
- `regression-registration-scope-solar-terminal-v1`의 실제 controller45038/종료0:
  정상·수치 hold·직렬화 도중 원천 권리 철회의 **3검사**. pytest137.29초,
  guard143.287초다. 최초 도구 handle은 문맥 축약 중 유실됐으며 실제 terminal/로그
  해시로 대사했다. 시험 이름과 달리 이3개 자체는 별도 프로세스 reader 증거가 아니다.
- `79811:0`: custody 현재 권리/입력/잠금·두 취소 지점·임대 만료 후 확정 구간 채택과
  남은 계산·완료 직전 scope/rights/resolver 변경 시 게시 rollback의 **7검사**.
  pytest341.70초·guard357.336초·합 RSS1,041,297,408bytes다.

**고유26검사를 로컬 컴포넌트 범위로 수용한다.** 각 실행에서 실제5root와 동적 자식,
불변 원본2,148항목·frozen source/assets·두 화면을 보존했다. 감독 FD4→4,
소유 비좀비/PG/임시/passfile0 및512MiB/PID/합1GiB를 확인했다.
현재 전체 backend/browser 회귀와 현재 DOM/WebGL은 실행하지 않았다.

## 같은 실제 advance의 paired 관측

`8120:0`은 같은 DB·binding·입력으로 별도 custody 두 개를 만들고 먼저 같은 경계를
준비했다. 시험에서만 scope를 열지 않는 원 전체 검증 경로와 후보를 ABBA 순서로
비교했다. 원 수치·UTC·checkpoint/시점/원량과 실제 원천 조회 순서·중복이 같았다.

| 항목 | 원 전체 재구성 | 후보 |
| --- | ---: | ---: |
| current / registration 호출 |12 / 24|12 / 24|
| 전체 재구성 / 경제 계산 |24 / 24|1 / 1|
| 현재 role 감사 / 실제 원천 읽기 |528 / 1,824|528 / 1,824|
| 실제2단계 관측 초 |13.663053|12.526265|
| 실제3단계 관측 초 |13.395898|12.247703|

약8.3–8.6%의 **두 paired 컴포넌트 표본**이다. profiler/중첩 시간을 포함하며 합산하지
않는다. 전체 처리량·64단계 정상 완료·완료 날짜 근거가 아니다. 감사 비용은 여전히
약6.1–6.4초였다. guard115.766초·합 RSS1,000,124,416bytes·동일 보존/정리를 확인했다.

## 검토와 다음 수용 기준

현재 native `gpt-6.1-sol/xhigh`에서 구현/정확성·보안·구조·측정 한계를 검토했다.
CLI를 재귀 실행하거나 subagent를 실행하지 않았다. 일반 경로와 현재 검사 수를
보존하며 이번 변경은 반복 재구성만 줄인다. 조사 자료나 농업 계수를 새로 채택하지 않았다.

다음은 변경된 source의 **계측하지 않은 원 독립 API/worker 정상64단계**다.
입력/chunk1/조회/재시도/360초/메모리 상한을 유지하고 두 전진 prefix·원 값/UTC·
step64/start1/CLI0/attempt1/success event1·actor 종료0·조회 시 새 작물/기후 계산·
CLI/SQL 변경0·FD identity/역할/schema/PG/임시 정리를 모두 대사한다.
원 정상 뒤 독립 hold→실제 HTTP 취소→계산 중 WebGL→WSL 용량/사용자 적용 순서다.

원 정상 미수용·새 Solar 미배포·실제 농장 Run0·권리/관문 승인False/G0–G4 미평가를
유지한다. 실제 자료 권리·독립 농장 측정·미래 생산/마진·후보 비교는 외부 의존성이다.
전체 완료일은 미정이며 goal은 active다. [기존 UI 복구](post-boot-preview-recovery-20261019.md)는
별도 운영 기록이며 새 모델 배포나 joint 독립 감독/G4 수용이 아니다.

`58106:0`에서 현재 source/syntax와 원 actor/query/probe 해시를 대사하고26검사·다음
원64 정상/기존 보류를5173/5174에 no-store 동일 bytes로 게시했다. 원 HTML과 환기 frozen
2,173파일·5root/원본/상한·감독FD/소유 정리를 보존했다. UI 코드/DOM/WebGL은 바꾸거나 재검사하지 않았다.
