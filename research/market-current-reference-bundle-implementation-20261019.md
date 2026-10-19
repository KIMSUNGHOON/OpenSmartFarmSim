# 현재 참조 읽기 묶음 구현 — 2026-10-19 KST

[계약](../contracts/market-current-reference-bundle-v1.md) ·
[기계 증거](artifacts/market-current-reference-bundle-implementation-20261019.json) ·
[선행 후보 미채택/호출 위치](runtime-role-audit-phases-evaluation-20261019.md).

## 변경과 수용 범위

한 등록 입력의 반복 검증에 서버 전용 `verify_current_reads`를 사용한다.
기존의 모든 getter와 중복을 실제로 같은 순서로 실행하고 원문·서명·테넌트/범위·권리/QC를 검사한다.
이 순수 루프 안의 참조 읽기는 현재 principal/pointer·실제 세션/읽기 전용/격리를 계속 확인하며,
전체 role 감사는 루프 전후와 기존 scope 진입/종료에 수행한다. 권한 결과를 캐시하지 않는다.
묶음 밖으로 데이터·서명·게시·권한 ticket을 반환하지 않으며 성공도 `None`만 반환한다.

일반 조회와 일반 read scope의 getter 감사는 그대로다. 공유할 수 없는 바인딩은 기존 읽기 경로를 쓴다.
첫 농장 등록의 전체 검증과 이후 current12·등록 조회24·재구성1을 유지했다. 새 store/verifier를
binding 의존성·현재 코드 pin에 포함했다. 수식·금액/수량 산술·원 입력·역할 정책·worker/query·
원 actor/probe·64/chunk1/조회·재시도/360초/RSS 상한과 DB schema는 변경하지 않았다.

## 실제 검증

| 최종 검사 | 고유 수 | 실제 도구 |
| --- | ---: | --- |
| 새 묶음/원천·권한 변경·수명·대체 경로·닫힌 입력 |17|95352:0|
| 기존 일반 보류/판단 문맥 조회 |49|48354:0|
| 기존 고정 입력 참조 조회 |11|53247:0|
| 기존 등록 입력 현재 검증/권한·코드·수명 |13|29569:0|
| 정상·수치 보류 원 응답/직렬화 중 원천 권리 철회 |3|18079:0|
| 두 취소 지점·임대 만료/확정 구간 채택/남은 계산 |3|97917:0|

**로컬 소프트웨어 범위의 고유96검사를 수용한다.** terminal 조회 시험의 이름만으로
별도 프로세스 reader 수용을 주장하지 않는다. 현재 backend/browser 전체 회귀는 실행하지 않았다.

71347:1은 기존 코드의 메서드 부재 RED다. 86719:1은 스레드/Task만으로는 같은 스레드의 복제
Context를 구분하지 못한 실제 RED였다. 원래 Context의 토큰을 reset/교체해 문맥 소유를 확인하고,
닫을 때 최신 토큰을 정리하도록 수정했다. 같은/다른 실행 문맥·복제 문맥의 close·중첩·오류와
실패 뒤 새 작업을 검사했다. 복제/중첩 시도는 수명을 무효화하며 최종 값은 반환되지 않는다.

초기 넓은 묶음17230:1은 합 RSS1,075,933,184bytes에서 중단됐다. 임시 디렉터리의 감독 종료 후
정리와 소유·단일 링크·0600 passfile4개 제거를 확인했다. 80318:1은30검사가 통과했으나 두 module의
정리 증거 파일명이 충돌해 종료 오류가 났다. 둘 다 수용 수에 넣지 않았으며 DB fixture module을
분리해 위 최종 실행을 통과했다. 초기12검사/성능 표본도 Context 수정 전이므로 최종 수용에서 제외했다.

성공 실행은 실제5root/동적 자식·원본2,148항목·frozen source/assets·두 화면과512MiB/PID/합1GiB를
유지했다. 감독FD4→4·소유 비좀비/PG/임시/passfile0을 확인했다. 최종 수용 검사의 최대 합 RSS는
1,064,165,376bytes였다. 각 최종 실행의 app source pin이 현재 코드와 같다.

## 같은 실제 청크 비교

39148:0에서 같은 실제 fixture/입력·상태의 두 custody를 준비하고 원 current 루프와 새 루프를
ABBA 순서로 비교했다. baseline은 시험에서만 원 함수를 선택하며 권한·원천 검사를 우회하지 않는다.

| 항목 | 기존 | 새 묶음 |
| --- | ---: | ---: |
| current / 등록 조회 / 전체 재구성 |12 / 24 / 1|12 / 24 / 1|
| 실제 role 감사 |528|298|
| 실제 원천 읽기 |1,824|1,824|
| 2단계 관측 초 |14.062889|12.004432|
| 3단계 관측 초 |14.134295|11.752604|

원 수치·UTC·checkpoint/원량과 실제 원천 조회·중복 순서는 같았다. 두 표본의 감소는 약14.6%/16.9%다.
profiler overhead가 포함된 **두 paired 컴포넌트 표본**이며 전체 처리량이나 완료 날짜 근거가 아니다.
guard113.027초·합 RSS1,003,143,168bytes·동일 원본/서비스/FD/소유 정리를 확인했다.

## 검토와 다음

현재 native `gpt-6.1-sol/xhigh`에서 구현·정확성/권한/수명·호환/성능 한계를 검토했다.
CLI 재귀/서브에이전트와 새 외부 자료·농업/경제 계수 채택은 없다.
다음은 변경된 source의 원 계측 OFF 독립 API/worker64 정상·두 전진 prefix·원 값/UTC·
step64/start1/CLI0/attempt1/success event1·두 actor 종료0·조회 계산/쓰기0·FD/DB/프로세스 정리다.
그 뒤 독립 hold→실제 취소→계산 중 WebGL→WSL 용량/사용자 적용을 별도로 통과한다.

현재 새 Solar 미배포·원64 정상 미수용·실제 농장 Run0·권리/관문 승인False/G0–G4 미평가다.
실제 자료 권리·독립 농장 측정·미래 생산/마진/후보 비교와 전체 완료일은 미완료/미정이다. goal은 active다.

66727:0에서 source/syntax·2,267개 로컬 문서 링크·원 actor/query/probe/역할/worker/수식 보존을 대사했다.
96검사와 다음 원64 정상을 두 UI에 no-store 동일 bytes로 게시하고 원 HTML/환기 frozen2,173파일·
5root/원본/상한·FD/소유 정리를 확인했다. UI 코드/DOM/WebGL은 변경하거나 재검사하지 않았다.

source `61543800aeba21bfbfbc3cbf20630a783d3d02f0`의
[원 독립 정상 CI39185424202](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39185424202)를
계측 OFF로 기동했다. 이 기록 시점은 실행 중이며 정상 완료·처리량 수용이 아니다.

실행 중 상태 게시의 첫 시도는 문서 동시 수정으로 source 보존이 False여서 수용하지 않았다.
문서를 고정한 59587:0 재게시에서 source·원본·5root·두 화면·FD/소유 정리를 다시 확인했다.

## 원 독립 정상 결과와 다음 관측

위 CI39185424202는 **실패**로 종료했다. 원360초 계산 제한에서 감독379.456초,
API/worker 각각 -15였다. 종료 뒤 소유 cluster의 읽기 전용/repeatable read 진단은
**25/64·yielded·sequence26·UTC2026-10-01T00:00:50.123456Z·attempt1/simulating**을 읽었다.
이는 저장 메타데이터 관측이며 현재 원천/권리 검증·정상 완료 수용이 아니다.
원 actor2개/query/probe hash와 artifact ZIP/digest/path를 확인했다. hosted 합 RSS364,675,072bytes·
단일128,077,824bytes·resource reason null·FD7→7·소유 비좀비/임시0이다.
정상/DB 정리 proof는 없으며 WSL의5root 동시 용량을 입증하지 않는다.
이전16/64와 이번25/64는 실행별 저장 관측이며 통제된 전체 처리량 비교로 주장하지 않는다.

같은 source로 CI를 반복하지 않는다. 다음 한 단계는
[기존 실제 청크 비용 관측 계약](../contracts/crop-solar-current-binding-cost-v1.md)의 현재 코드 적용이다.
실제1→2단계의 current/등록/role/연결·SQL/원천/수치 계산 비용을 비밀값 없이 집계한다.
원 UTC/값·확정 파일 identity/내용·원천1,824/중복 순서·current12/등록24/재구성1을 확인하고,
원5root·2,148항목·frozen source/assets·두 화면·512MiB/PID/합1GiB·FD/소유 정리를 통과해야 한다.
관측은 컴포넌트 진단이며 원64 정상 수용 수에 넣지 않는다. 결과로 최소 후속 변경을 정한다.
새 Solar 배포·G0–G4·실제 농장0과 전체 완료일 미정/goal active는 유지한다.

[실제 남은 비용 관측18369:0](crop-solar-reference-bundle-remaining-cost-20261019.md)을 완료했다.
144연결/298감사/8,976SQL과 원천1,824/순서·원 UTC/proof3·원본/5root/정리를 확인했다.
다음 후보는 [순수 감사 scope v2](../contracts/market-current-reference-audit-scope-v2.md)이며 현재 미구현/미수용이다.
