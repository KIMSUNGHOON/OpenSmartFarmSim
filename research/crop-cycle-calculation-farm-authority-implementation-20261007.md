# 새 계산 판본과 현재 농장 권한 결속

2026-10-07 KST. [첫 계약](../contracts/crop-cycle-calculation-farm-binding-v1.md)의3 core파일을 구현했다.
**현재 농장 authority 자식만 로컬 수용했다. 서버가 서명한 계산 이력과 새 판본 DB 게시는 후속이다.**

## 구현

[140줄 새 모듈](../backend/app/crop_cycle_calculation_farm_binding.py)은 정확한 등록 농장 서비스·authority
SCRAM/전체 grant 감사와 설치된 `InputEvidenceAuthority`를 받는다.
그 authority 객체가 발행한 정확한 `CalculationContext`만 결속하며 원/조회/닫힌 타입과
다른 authority 객체의 문맥을 거부한다. 같은 키로 만든 다른 authority 객체도 설치 경계를 대신하지 않는다.
새 서비스가 동일 서버 구성으로 새 문맥을 만드는 재접속은 허용한다.

원 `_request`/`_registration`을 같은 함수 객체로 명시 재사용한다. 새 클래스는 원 클래스의 subclass가 아니며
원 reader/token이나 module globals를 주입하지 않는다. 원 source·새 계산/context/evidence를 dependency SHA로 고정한다.
원 닫힌 요청/권리 schema와128KiB를 유지하고, 결과는 새 `crop-cycle-verified-farm-binding-v1` 판본이다.
원8개 input key에 검증 provenance8개의 `input_validation`을 추가하고,
binding top key는 원8개에 `binding_dependency_sha256`을 추가한9개다.

현재 증명/모든 입력 bytes를 연산 전후각1회, 권리 provider를2차례 관측한다.
write는 각 관측마다 계산·표시를 확인해 총4callback, read는 표시만 총2callback이다.
선언 변경·첫 callback 뒤 철회와 마지막 callback 중 입력 변경을 검출한다.
여러 외부 권리와 등록을 하나의 원자 snapshot으로 잠근다는 주장은 하지 않는다.
실제 계산 전후·서명 게시·DB 거래의 추가 검사는 뒤의 두 자식에 유지한다.

## 실제 검증

[시험](../backend/tests/test_crop_cycle_calculation_farm_binding.py)은 소유한 합성 원천/등록 농장과
실제 PostgreSQL16.15의 runtime SCRAM 로그인을 사용했다.
**고유12개를 분할 수용**했다. 최초3개/76.29초는 중간 실행이며 합산하지 않는다.
12개/242.84초·종료0 뒤 조회 전용 문맥 거부를 추가한 해당1개/21.46초·종료0을 다시 통과했다.
제품 소스는 세 실행 모두 동일하고, 나머지 시험 함수의 AST는 같다.
최종 시험 파일의 단일12 GREEN이나 전체 backend 수용으로 표시하지 않는다.

| 확인한 범위 | 실제 증거 |
| --- | --- |
| 등록/provenance | tenant·farm job/SHA·crop/batch·zone/floor·기간/plan·검증 context/evidence SHA, 같은 prepare/current bytes |
| 현재 권리 | 읽기/쓰기 scope 차이, 외부 tenant·input provider·원천 철회, 첫 callback 뒤 read/write 권리·source/scope 철회와 선언 변경 거부 |
| 입력 검사 | 각 공개 호출2회·parser/prepare 재호출0, root/blob/mode/symlink 및 마지막 callback 중 root 변경 거부·context/cache 정리 |
| 형/설정 | 원 reader/context·조회/닫힌/다른 authority 타입, key/policy/code/고지/서비스/identity·expected bytes 변경 거부 |
| 요청/달력 | 비 canonical/중복/NaN/UTF-8/빈/oversize·closed schema·root/program/권리/등록/crop/availability·실제 occupancy 밖 기간 거부 |
| 계산/DB 행 | RHS/advance0; authority 연산의 jobs/events 불변, 새 작물 결과/Run0 |

정상 binding은**5,654bytes**, 최종12개 실행의 prepare2.710977초/current2.713417초다.
작은 입력의 실제 농장/권리 조회 비용이며 전체166일이나 HTTPS 지연으로 확대하지 않는다.
새 authority는 계산 준비/권리를 대사할 뿐 작물 생장·수확 결과를 생성하지 않는다.

fork한 실제 child에서 새 authority/farm-binding wrapper와 DB 연결을 만들고 같은 binding bytes를 대사했다.
child PID331990·실제 종료0, child FD18→18과 context/cache 정리를 확인했다.
fork에 상속된 기존 Python 객체·FD가 있으므로 **fresh Python exec 증거가 아니다**.
parent의 반복 current도 FD가 같았다. actual process 재시작 후 등록/이력 연결의 추가 증거는 server/DB 자식에서 확보한다.

세 실제 SCRAM 실행의 스키마·역할·비밀번호 파일 잔존은 모두0, 각 PG PID/데이터 directory와
임시 test tree가 사라졌음을 확인했다. 자작 증거 JSON과 source/로그는 사설0700/파일0400으로 보존했다.
원55 source SHA와 실행 중 원166일 입력/spec은 보존했다. 새 runtime service/queue나 DB schema/role를 추가하지 않았다.

실제 native CLI `gpt-6.1-sol / xhigh`·재귀 CLI0과 소스/시험 판본·실제 정리·검토는
[불변 receipt](artifacts/crop-cycle-calculation-farm-authority-reference-20261007.json)에 결속한다.
미구현 import RED는 collection 오류이며 assertion body 실패로 세지 않는다.

## 다음 단계

`crop-cycle-calculation-farm-authority`만 체크한다. 다음은 새 계산/저장 판본의 실제 RHS를 실행하고,
현재 결속을 계산 전후와 서명된 intent/HEAD/progress에 연결하는 `crop-cycle-calculation-server-custody`다.
그 뒤 새 판본의 SQL/역할·HMAC/metadata·원자 게시/재조회와 이전 이력 공존을 검증한다.
기존 parent `crop-cycle-calculation-farm-binding`과 전체166일/저장·API/같은 UTC3D는 미수용이다.
첫 authority의1–3시간/10월7–8일 잠정 추정은10월7일 로컬 수용 실적으로 대체한다.
다음 server/DB의 날짜는 해당3–4파일 계약·실제 비용 대사 뒤 갱신한다.
생과 → 물/양분·구매 에너지 → Decimal 경제 순서와 운영 기반 동결은 유지한다.
실제 품종 입력/국내 독립 자료/actual crop Run은각0, G0–G4는 `not_assessed`이며 생산 예측·추천은 보류다.
