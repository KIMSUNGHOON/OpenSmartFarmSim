# 현재 농장·원 서버 이력의 저장 조회 결속

2026-10-07 KST. [조회 계약](../contracts/crop-cycle-current-query-v1.md)의 농장/DB 결속을
로컬 수용했다. [원 증거](artifacts/crop-cycle-query-authority-reference-20261007.json)는
3 core source·실제 명령 인자/로그 SHA·native CLI 문맥·정리 결과를 고정한다.
Codex CLI `gpt-6.1-sol / xhigh`의 현재 세션에서 판단/구현했고 재귀 CLI는 실행하지 않았다.

## 구현한 범위

`CurrentCycleQuery`는 기존 store/farm/custody 및 계산 타입을 변경하지 않는다.
원 DB HMAC/column·등록·현재 Scope/계정·원천/입력 권리와 새 입력/result QC를 대사한다.
원 intent 및 선택된 head의 전체 부모 서명을 소유 no-follow FD로 읽고 원 progress/실제
bytes·파일 수와 대사한다. 참조 QC를 server trace로 바꾸거나 새 progress를 발행하지 않는다.

같은 원 summary/page/UTC와 원 math 판본을 반환하며 새 조회 code·QC/원 DB/서명 SHA를 보존한다.
`open` 안에서 소비한 뒤 다시 현재 등록/DB/권리·trace·입력/result를 확인한다.
원 parser/context 준비/terminal QC/RHS는 읽기에서0회다. QC 발행은 원 검사를 실제 실행한다.

## 실제 검증

- 최종 실제 SCRAM/PostgreSQL16.15 **8개/631.33초**, 종료0.
  원120걸음·3시점/0사건의 원값/manifest·현재 철회/계정/Scope/등록·실제 DB 서명/등록자 변조,
  intent/선택 및 부모 proof/HEAD/입력/result/링크·조회 중 변경 거부와 재구성/fork를 확인했다.
- 마지막 입력 권리 검토 중 원천 권리 철회를 반환하는 실제 **1실패/60.24초**를 재현했다.
  검토 후 등록 및 DB 행 재대사를 추가했고 최종8개에 해당 회귀 시험을 포함했다.
- 첫 분할 시험의 DB 변조 값은 기존 SQL CHECK가 먼저 거부했다. 제한은 유지하고
  실제 등록자 column 변조로 바꿔 검증했다. 중간5/2통과를 최종8개에 더하지 않는다.
- 반복 농장/DB 구성을 줄이도록 변조·철회를 한 fixture에서 복원하며 검사한다.
  앞선 중단 시험은 수용 증거가 아니며 그 시험/PG PID의 부재를 확인했다.
- 최종 FD 누수0, 스키마/역할/pgpass0, PG process/data directory 부재를 실제 확인했다.
  원 수학52개와 선행12 primitive source, 기존 farm/store/custody를 보존했다.

## 다음 수용과 보류

다음은 [API/runtime 명시적 선택](../contracts/crop-cycle-query-runtime-v1.md)의 실제 TLS다.
관리 사건이 있는 완료 결과와 출력 없는 hold를 원 모든 page/UTC와 대사하고,
투영 후 철회·계정/권리·서버 trace 거부·재시작·30초/2MiB·정리를 확인한다.
이 보고서로 현재 조회 부모나 실제166일/3D·부하를 수용하지 않는다.

운영 기반은 `d19f7c0`으로 고정한다. 새 조회는 관측된 긴 결과 검증 비용을 해결하는
작물 계산→저장→같은 UTC3D 경로의 작업이다. 원166일 종료 상태는
[확인 불가](crop-cycle-full-rhs-missing-state-20261007.md)이며 같은 실험/예산을 재설정하지 않았다.
실제 품종/독립 국내 농장 자료와 실제 작물 Run은0건, G0–G4는 `not_assessed`다.
전체 완료 날짜는 별도 실제 전체 실행·조회/3D와 자료 확보 실적 뒤 갱신한다.
