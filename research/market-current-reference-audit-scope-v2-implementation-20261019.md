# 현재 참조 검증의 감사 scope v2 — 2026-10-19 KST

[계약](../contracts/market-current-reference-audit-scope-v2.md) ·
[기계 증거](artifacts/market-current-reference-audit-scope-v2-implementation-20261019.json) ·
[선행 실제 비용](crop-solar-reference-bundle-remaining-cost-20261019.md).

## 변경과 로컬 수용

`verify_current_reads`의 호환 경로는 기존 source store의 읽기 전용 Read Committed scope가
순수 검증 작업을 소유한다. 실제 source 연결 진입/종료의 전체 role 감사는 유지하고, 같은
작업 안의 candidate/reference 중복 감사만 합쳤다. 모든 getter/중복은 실제 같은 순서로 읽고,
각 held 읽기의 현재 principal/범위·pointer·실제 세션/격리·원문/서명/권리/QC 검사를 유지한다.
최종 source 감사와 종료 뒤 현재 바인딩/권리 검사를 통과하기 전에는 성공을 반환하지 않는다.
외부 반환은 `None`뿐이며 데이터·연결·권한 결과나 ticket을 캐시하지 않는다.

일반 getter/read scope의 감사는 유지한다. 공유할 수 없는 바인딩과 원래 bound scope/connector가
아닌 경우는 기존 감사 경로를 사용한다. 공통 `_shared_profile`을 재사용해 실제 source/view
scope·connector의 함수와 수신자 identity를 현재 바인딩에 포함하고, farm reader의 현재 코드
pin에도 새 helper를 포함했다. 기존 source store·역할 정책·수식·금액/수량 계산·worker/query·
원 actor/probe·schema·입력·64/chunk1/조회·재시도/360초/RSS 상한은 변경하지 않았다.

**아래 고유116검사와 최종 실제 paired 관측으로 로컬 소프트웨어 범위에서 채택한다.**

| 최종 검사 | 고유 수 | 실제 도구 |
| --- | ---: | --- |
| 실제 source 전후 감사·종료 변경/오류·메서드 교체·초기 감사 |13|69049:0|
| 정상·대체 경로3·다음 작업·Task·기존 scope 보호 |7|32461:0|
| 기존 묶음·변경/복제/중첩/예외·닫힌 입력 |17|81180:0|
| 기존 일반 보류/판단 문맥 조회 |49|23806:0|
| 기존 고정 입력 참조 조회 |11|25523:0|
| 등록 입력 현재 권리/판본/코드/수명 |13|99339:0|
| 정상/수치 보류 원 응답·직렬화 중 권리 철회 |3|65993:0|
| 취소 두 지점·만료 후 확정 구간 채택/재개 |3|85320:0|

각 최종 실행의 app source pin이 현재 코드와 같다. 실제5root/동적 자식·원본2,148항목·
frozen source/assets·두 화면·512MiB/PID/합1GiB, FD4→4·소유 비좀비/PG/임시/passfile0을
확인했다. 최대 합 RSS1,052,790,784bytes, 최종 검사 guard 합1,267.834초였다.
현재 backend/browser 전체 회귀는 실행하지 않았다. terminal 시험 이름만으로 별도 프로세스
reader 수용을 주장하지 않는다.

## 재현한 실패와 보완

26576:1은 기존 내부 감사5회가 남아 있는 최초 RED다. 초기 구현/31검사/성능 관측은
메서드 교체 보호를 보완하기 전이므로 최종 수용 수나 최종 source 증거에 넣지 않았다.

43478:1에서 시험용 source/view scope가 최종 감사를 생략하도록 교체됐을 때 실제 grant 변경을
거부하지 못하는 두 경우를 재현했다. 64286:1은 첫 감사를 생략한 connector에서 잘못된 grant가
원천 읽기 이후에야 거부되는 경우다. 원래 bound 메서드 여부에 따라 기존 감사 경로를 선택하고,
메서드 함수/수신자 변경을 현재 profile에 고정해 보완했다. 최종13검사는 이 세 경우와 종료 중
grant/principal/키·scope/connector/provider/slot 변경, 오류 후 실제 연결/slot 정리를 포함한다.
역할 증거는 실제 소유 SCRAM DB의 GRANT/REVOKE로 검사했다.

## 최종 같은 실제 청크 비교

25608:0에서 같은 실제 합성 fixture/입력·상태의 두 custody를 준비했다. baseline은 시험에서만
기존 v1 `verify` 함수를 선택하며 공통 현재 helper/코드 pin과 실제 source 검사를 유지한다.
전체 commit 두 개의 독립 성능 비교가 아니다. 초기/1단계 이후 2·3단계를 ABBA 순서로 관측했다.

| 항목 | 기존 v1 검증 | v2 검증 |
| --- | ---: | ---: |
| current / 등록 / 전체 재구성 |12 / 24 / 1|12 / 24 / 1|
| 전체 role 감사 |298|183|
| 실제 원천 읽기 |1,824|1,824|
| 2단계 관측 초 |12.583626|10.638996|
| 3단계 관측 초 |12.354195|10.658933|

원 수치/UTC·counts/checkpoint/times·artifact/provenance와 원천 중복/순서가 같았다.
두 표본의 감소는 약15.5%/13.7%다. profiler overhead를 포함하는 중첩 시간이며
**두 컴포넌트 paired 표본**을 전체 처리량·원64 정상 완료·완료 날짜 근거로 쓰지 않는다.
guard101.053초·합 RSS995,598,336bytes·원본/5root/FD/소유 정리를 확인했다.

## 검토와 다음 한 단계

현재 native `gpt-6.1-sol/xhigh`에서 정확성·원 권한/수명·호환·코드 구조와 실제 비용을 검토했다.
순수 검증 모듈에 조립을 두고 공통 profile을 재사용했다. 역할 정책이나 일반 조회의 감사 축소,
새 인증 체계·권한 캐시·외부 농업/경제 계수 채택은 없다. 재귀 CLI/서브에이전트를 실행하지 않았다.

다음은 변경된 source의 원 계측 OFF 독립 API/worker64 정상이다. 원 입력/chunk1/조회·재시도/
360초/RSS를 유지하고 두 전진 prefix·원 값/UTC·64/start1/CLI0/attempt1/success event1,
두 actor 종료0·조회 계산/SQL 변경0·FD/역할/schema/소유 PG/임시 정리를 확인한다.
이후 독립 hold→실제 취소→계산 중 WebGL→WSL 용량/사용자 적용을 별도로 통과한다.

선행 v1 CI39185424202의25/64 미완료는 이 변경으로 해소됐다고 주장하지 않는다.
원64 정상·새 Solar 배포·실제 농장 Run0·권리/관문 승인False/G0–G4 미평가를 유지한다.
독립 현장/미래 생산·마진/후보 비교 자료와 전체 완료일은 미완료/미정이며 goal active다.
위 guard 시간은 최종 검사/관측만 포함한다. 준비·분석·이전 실패·문서·후속 CI 대기는 별도다.

76422:0에서 최종116검사/다음 독립 정상 상태를5173/5174에 no-store 동일 bytes로 게시했다.
현재 source/syntax·문서 링크2,283개·원 actor/query/probe/역할/worker·원 HTML/환기 frozen2,173파일,
5root/원본/상한/FD·소유 정리를 확인했다. UI 코드·DOM/WebGL은 변경하거나 재검사하지 않았다.

source `eb943d9d44c7bcf369758b2015a0889d360a99ef`의
[원 독립 정상 CI39190518816](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39190518816)를
계측 OFF로 기동하고 실제 같은 head의 실행 중 상태를 확인했다. 정상 완료/처리량은 아직 미수용이다.

59672:0에서 같은 원 CI 실행 중 상태를 두 UI에 게시하고 source/원본/5root/상한/FD·소유 정리를 보존했다.
