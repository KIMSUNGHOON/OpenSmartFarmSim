# 일사 조회의 명시 runtime 로컬 수용 — 2026-10-17

[계약](../contracts/crop-greenhouse-solar-runtime-v1.md) · [기계 증거](artifacts/crop-greenhouse-solar-runtime-implementation-20261017.json).

## 구현과 통과 범위

새 `operator-greenhouse-solar-api-config-v1` 로더와 기본 None인 결과/현재 조회 factory를 추가했다. exact bool/닫힌 설정·보호 파일 reader·factory 전후/조립 뒤 파일 재검사를 사용한다. True는 두 factory와 cycle authority가 모두 필요하며 불일치는 I/O 전에 거부한다. 정확한 SolarResultStore/SolarCurrentQuery·동일 jobs/farm/current_principal·query.store·기존 binding/code/현재 역할·입력/서버/DB의 서로 다른 키를 확인한다. 같은 객체를 보호 HTTP에 전달한다. 기존 설정의 생략/False와 공개 HTTP/스키마·수치/계수·서명 저장/현재 query 코드는 보존했다.

**새62/기존173=고유235검사**를 통과했다. 예비52개를 다시 계수하지 않았다.

| 배치 | 원 tool session | 통과 |
| --- | --- | --- |
| 새 설정58·기존 환기70/원 operator69/공통 runtime31 | 96888 | 228 |
| 기존 solar 역할/9설정 판본·미조립 거부 | 68618 | 3 |
| 새 로더/runtime의 독립 import | 41013 | 2 |
| 실제 SCRAM·검증된 TLS의 보류 runtime | 90497 | 1 |
| 실제 SCRAM·검증된 TLS의 정상·오조립/철회/전송 | 13065 | 1 |

기존9loader는 solar 생략/False18건을 허용하고 그 외63건을 거부했다. 새 로더는 선택 joint/ventilation/calculation과의 조합·타입/선행 조건·보호 파일 변경·잘못된 factory/환경 진입점도 검사했다. 기존 역할 시험의 “설정에서 True 거부”는 새 명시 지원에 맞춰 “factory 없는 조립을 I/O 전에 거부”하는 검사로 갱신했다. JobStore 호출에 실패하도록 해 다른 파일/DB 오류 때문에 잘못 통과하는 것을 막았다.

실제 소유 DB에서 준비·계산·등록 A가 종료된 뒤 B가 별도 production 런타임을 새 설정 로더로 조립했다. 같은 서명 결과의 normal/hold summary/samples/events를 실제 SCRAM과 검증된 loopback TLS에서 원 공개 bytes/단위/마이크로초 UTC와 대사했다. 기존 cycle authority는 조립만 하며 그 입력 resolver와 custody는 사용하지 않았다. 기존/새 결과 행과 설정/DSN/TLS/키 파일을 보존했다.

잘못된/다른 store·query, 재사용한 입력/서버/DB 키, 변조된 현재 query 코드 판본, 실제 SELECT 권한 철회를 포함한9종을 거부했다. 권한 fault 주입/복원은 소유 임시 DB의 owner가 수행한2건의 의도된 GRANT/REVOKE다. 이를 제품 조회의 SQL 쓰기로 숨기거나 전체 프로세스의 SQL 변경0으로 주장하지 않는다. 제품 조립/조회 카운터의13수치/복원/CLI와 SQL 변경 시도는0이었다. 권리·검토·농장 원천·인증의12늦은 철회와 요청 취소/전송 실패·같은 원 응답 재조회를 새 runtime의 실제 인증 앱으로 검사했다.

## 자원·보존과 한계

필수5root/동적 자식·원본2,148항목·원 API/worker·두 사용자 서비스의 frozen source/자산·키/배포 역할을 유지했다. 소유 프로세스/PG/임시 PG/passfile·시험 schema/roles0, 감독 FD4→4/native FD3→3을 확인했다. Python assertions를 유지한 동일 시험 함수의 준비 A→런타임 B를 가벼운 stdlib 부모에서 순차 실행했다. 재귀 Codex CLI는 실행하지 않았다.

512MiB/PID·합1GiB·명목0.25초·numeric thread1/nice19를 준수했다. 관측 합 최대1,070,526,464bytes·단일 PID 최대175,144,960bytes이며 합 상한까지 약3.1MiB만 남았다. 후속 API/worker/브라우저 동시 검증은 이 한도에서 별도로 입증해야 한다. 현재 결과가 전체 작기/동시 사용자/운영 용량 수용은 아니다. 소유 시험 PG만 shared_buffers1MiB/JIT off를 사용했다.

첫 private 감독 준비가 중복 evidence 디렉터리 생성으로 자식 시험 시작 전에 실패했다. 중복 생성을 제거한 다음의 감독으로 검증했으며 실패한 준비를 통과 수에 넣지 않았다. 실제 native 감독 시간은 보류104.91초/정상190.13초였다.

## 사용자 산출물과 다음 단계

새 설정 계약·코드·235검사/기계 증거와 두 주소의 개발 진행 기록을 확인할 수 있다. 원 session95670 실제 종료0으로 최신 기록 HTTP200/no-store·원 bytes, 두 기존 HTML·환기 frozen2,173파일을 확인했다. 기록 시각2026-10-17 04:06:49KST·SHA8038ffee2aaa90990b74f2b41f28b114fb7245a5177cfa2fb6fd84aa715073ea다. 현재 브라우저 DOM/WebGL·새 일사 사용자 적용은 아직 수용하지 않았다. 기존 환기 사용자 적용은 유지한다.

다음은 **solar 자동 실행의 내부 접수·임대 worker 연결**이다. 기존 jobs/lease와 새 binding/custody/store를 묶어 실제 접수→독립 자동 소비→원 checkpoint 재개→완료/hold 원자 등록을 검증한다. 중복/현재 임대·권리/실행 중 취소·강제 종료 재개·미종결/철회 때 결과 미게시·기존 행/원문/서비스/자원/소유 정리가 수용 기준이다. 이어 확정 prefix/현재 진행과 보호 API→typed 웹/같은 UTC3D→사용자 정상/hold/취소·재접속/재시작을 연결한다.

합성32초·실제 농장 Run0·G0–G4 not_assessed·rights_or_gate_approval=False이며 새 일사 모델은 미배포다. 실제 국내 한 품종/작기·독립 농장/시설/광학·시장 자료/권리/QC 확보는 병행한다. 전체 CI·생산/구매 자원/경제/추천·최종 UI와 전체 완료 날짜는 미정이며, 현재 native 실행 시간을 후속 구현의 완료 시간으로 전환하지 않는다. 전체 goal은 active다.
