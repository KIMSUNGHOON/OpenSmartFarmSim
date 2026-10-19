# 현재 권한 감사 SQL 묶음 후보: 미채택 — 2026-10-19 KST

[기계 증거](artifacts/runtime-role-audit-phases-evaluation-20261019.json) ·
[검토 가능한 후보 patch](artifacts/runtime-role-audit-phases-candidate-20261019.patch) ·
[선행 비용](crop-solar-role-sql-cost-20261019.md).

## 실험과 판단

15개 현재 SQL 중 앞단의 database/owner/creator/object/role/membership/CONNECT/ACL/
DDL/definer/sequence를 한 SELECT로, 끝의 routine/default를 한 SELECT로 묶었다.
기존 table·column 행렬 SQL 두 개와 순서·0행 성공·NULL 거부를 그대로 유지해 총4개였다.
권한 결과 캐시·연결 수명 확대·수식/원 입력·청크/조회/시간/RSS 한도 변경은 없었다.
정책·설치·discovery helper AST와 두 행렬의 SQL bytes도 같았다.

현재 catalog 조회를 CTE로 구성하는 것과 Read Committed에서 각 statement를 별도 현재
조회로 다루는 것은 PostgreSQL16의 [WITH](https://www.postgresql.org/docs/16/queries-with.html),
[권한 inquiry](https://www.postgresql.org/docs/16/functions-info.html#FUNCTIONS-INFO-ACCESS-TABLE),
[격리](https://www.postgresql.org/docs/16/transaction-iso.html)를 확인했다. 전체 transaction이
한 snapshot이라는 주장은 하지 않는다. 묶음 경계와 채택 판단은 이 프로젝트의 설계 판단이다.

같은 실제 SCRAM 연결에서 ABBA3·표본마다21감사로 비교했다. 각 방식6표본의 중앙값은
0.161177→0.142326초였다. 모든254감사의 metadata와 두 행렬0행/순서는 같았다.
그러나 같은 실제 custody2·3단계의 비교는 다음과 같았다.

| 실제 항목 | 기존 구현 | 후보 |
| --- | ---: | ---: |
| 현재 role 감사 |528|528|
| role SQL execute |7,920|2,112|
| 실제 원천 조회·중복/순서 |1,824·동일|1,824·동일|
| 2단계 관측 초 |9.439526|9.250015|
| 3단계 관측 초 |9.431700|9.449523|

한 쌍 약2% 감소/다른 쌍 약0.2% 증가로 **실제 청크의 개선 근거가 부족하다**.
감사 컴포넌트의 감소를 전체 처리량으로 확대하지 않는다. SQL 복잡성도 늘어 이 후보는
**미채택**했다. 제품 파일을 HEAD의 원 bytes로 복원했고 후보 시험·계약은 활성 트리에서
제거했다. patch로 재검토할 수 있지만 현재 실행 코드나 수용된 계약이 아니다.
`git apply --check`로 복원한 baseline에 patch가 적용 가능한 것도 확인했다.
같은 application의 원64 CI를 다시 실행하지 않았다. 원16/64 보류는 그대로다.

## 검증 범위와 자원

- `44062:1`: 기존 구현에서 실제15회이므로 새4회 예산2사례가 실패한 RED다.
- `3882:0`: 새 호출 수2/기존 행렬12 =14검사. 중간 철회/객체 삭제를 포함한다.
- `88005:0`: 기존 NOLOGIN/SCRAM·PUBLIC/column/default/membership·DDL/definer·rollback 등39검사.
- `52100:0`: database/schema/owner/creator/object/USAGE 보류 이유9검사.
- `98795:0`: 네 역할의 table/column/schema/sequence/routine20검사와 위 paired 감사 관찰1개.
- `79475:0`: 실제 두 advance의 값/UTC·checkpoint/원량/원천 순서·감사 수/SQL 수 대사 관찰1개.

**후보의 고유 정확성82검사**다. 채택이나 전체 backend/browser/현재3D 수용이 아니다.
최종 코드가 아니라 실험 후보의 검사이며, 별도 Solar 정상/hold 조회 회귀는 수행하지 않았다.
실제 청크 관측에서 성능 채택 기준을 충족하지 않아 추가 후보 시험을 중단했다.

처음 넓게 묶은 실행 `93670:1`은 합 RSS1,102,217,216bytes로 중단됐다.
직접 전체 role module을 선택한 `65843:1`도 대용량 schema 행 시험까지 포함돼
1,085,517,824bytes로 중단됐다. 둘 다 수용 수에서 제외한다. 필요한 역할 검사를 기존
선별 wrapper로 실행해 성공했고 서비스나 한도를 변경하지 않았다.
감독 종료 후 남았던 시험 임시 디렉터리의 자동 정리를 실제 확인했고, 두 번째 중단의
소유·단일 링크·0600 passfile4개도 확인 후 제거했다. 잔여 PG 비좀비/해당 임시·passfile0이다.

성공 실행은 원5root/동적 자식·원본2,148항목·frozen source/assets·감독FD4→4·
512MiB/PID/합1GiB와 시험 소유 정리를 유지했다. 현재 제품 runtime은 원본으로 복원돼 있다.

## 복원한 현재 코드의 실제 경계

`41880:0`에서 실제1→2단계에 call-path profiler를 적용해 **current12/감사528/연결144**를
확인했다. guard82.911초·관측 advance44.029초이며 profiler overhead가 커 성능 수치로 쓰지 않는다.
원 bytes/코드 hash·5root/원본/상한·FD/PG/임시 정리도 확인했다.

| 실제 감사 호출 위치 | 횟수 |
| --- | ---: |
| MarketCandidateStore._reference_guard |312|
| JobStore.connect |72|
| ThermalRunStore.connect |48|
| MarketCandidateStore.read_scope 진입/종료 |24 + 24|
| connect_market |24|
| MarketSourceStore.read_scope 종료 |24|

12개 current는 open1, prepare 전후2, advance 앞/중간/끝4,
publish 전후3, progress 전후2다. 자세한 호출 위치/중복은 기계 증거에 보존했다.
SQL 전달 수만 줄이는 대신 **312회인 내부 참조 읽기 경계**를 다음 대상으로 고정한다.

## 다음 한 단계의 수용 기준

1. 같은 current 경계 안의 보류 보고서/판단 문맥 읽기를 서버 전용의 순수 내부 작업으로
   묶는 최소 계약을 정한다. 현재 원문·서명·테넌트/범위·권리/QC 검증을 계속 수행한다.
2. 각 읽기의 현재 principal/scope/pointer 검사를 유지하고 작업 전후 실제 role 감사를
   수행한다. 권한 결과를 저장하거나 다른 작업에 재사용하지 않는다. 묶음 종료 전에
   결과·서명·게시를 외부로 반환하지 않으며, 실패 시 전체 결과를 차단한다.
3. 도중 source/context/권한/grant·만료/취소 변경, 잘못된 계정·중첩·연결 교체·오류 정리와
   기존 current12·원 값/UTC/HMAC/ancestry/조회 계산·쓰기0을 실제 DB 검사로 대사한다.
4. 같은 실제 advance에서 반복 수와 paired 비용을 확인한다. 컴포넌트나 SQL 수만으로
   채택하지 않는다. 채택된 변경 뒤 원64 정상→독립 hold→취소→계산 중 WebGL→WSL 용량/
   사용자 적용을 각각 통과한다. 현재 그 단계들은 미완료다.

현재 native `gpt-6.1-sol/xhigh`에서 판단했고 CLI 재귀/서브에이전트는 실행하지 않았다.
실제 농장 Run0·권리/관문 승인False·G0–G4 미평가·새 Solar 미배포·전체 완료일 미정과
goal active를 유지한다. 실제 자료 권리·독립 현장/미래 생산·경제·후보 비교의 외부 의존성도 남아 있다.

`11163:0`에서 제품 baseline의 원 bytes/syntax·후보 patch 적용 가능성·원 actor/query/probe 해시를
재대사하고 미채택 판단/다음 범위를5173/5174에 no-store 동일 bytes로 게시했다.
원 HTML·환기 frozen2,173파일·5root/원본/상한·FD/소유 정리를 보존했다. UI 코드/DOM/WebGL은
변경하거나 재검사하지 않았다.
