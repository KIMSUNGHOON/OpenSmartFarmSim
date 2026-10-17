# 원 시험 종료 뒤 저장 metadata 관찰 — 2026-10-17

[계약](../contracts/crop-solar-failed-checkpoint-metadata-v1.md) · [기계 증거](artifacts/crop-solar-unpaused-postmortem-20261017.json) ·
[선행13검사](crop-solar-progress-lock-lifetime-implementation-20261017.md).

## 원 정상의 실제 종료

[CI39037993173](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39037993173),sourcef6b3bde는
381.069초·자식1·API/worker -15로 종료했다. 원360초 계산 상한 안에 완료하지 못했다.
원 API/worker SHAab5a93a…/14fe24d…는 같고 정상/DB 정리 proof·완료 단계 정보는 없다.
단일133,406,720/합369,020,928bytes·FD7→7·소유 비좀비/임시0이며 resource 중단 사유는 없다.
artifact12102453497/1,930bytes의 actual run/head/ZIP digest·안전 경로를 대사했다.
잠금 수명 수정의 로컬13검사는 유지하지만 정상 기능·처리량 개선을 주장하지 않는다.

## 추가한 관찰과 검증

sourcec757a95는 실패한 원 시험의 actor가 모두 종료한 뒤 pg_ctl stop 전에만,
자체 임시 test DB의 저장 작업/체크포인트 metadata를 한 번 읽는다.
원 정상 증명이 있거나 actor가 실행 중이면 수집하지 않는다. 계산 중 계측·추가 조회는 없다.
private config/같은 temporary cluster·data directory·provisioner 신원·test namespace를 대사하며,
Read Only/Repeatable Read와 connect2초/statement2초·행/출력 상한을 유지한다.
state/attempt·허용 reason·steps/planned/status/UTC/sequence·payload hash와 관찰 시각만 기록한다.
DSN/경로/테넌트·작업 ID/원 입력·결과/메시지·인증값은 내보내지 않는다.
이 metadata는 원천·권리·모델을 종료 뒤 재검증한 결과나 정상 완료 증명이 아니다.

- 44362:1은 미구현 module의 실패다. 30850:0의 실제 DB 비교를 보존했다.
- 39684:0은 실제 DB 비교와 live actor/기존 원 정상 증명일 때 수집 생략의3검사를 통과했다.
- 72558:0에서 실제 process 종료 뒤에만 큐레이션 파일이 생기는 조건을 확인했다.
- 24744:0에서 최종 Read Only/Repeatable Read·실제 저장 field/다른 cluster 거부·연결 종료·
  조회 모델/CLI/SQL 변경0·원 DB 보존·private 값 제외를 포함한 **고유4검사**를 통과했다.
- 50434:0은 수집 호출1개 외 원 driver 로직의 AST, 원 actor 해시·application·workflow 실행 단계/환경/상한 불변을 대사했다.
  허용 artifact 경로1개만 추가했다. 제품 application은 f6b3bde와 같다.

최종4검사는38.635초·합 RSS1,061,666,816bytes였다.
기존5root·원2,148항목·두 UI/frozen 소스·자산·512MiB/PID/합1GiB·감독FD4→4,
실제role/schema0·소유 비좀비/PG/임시/passfile0을 유지했다.

## 다음

[CI39039991262](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39039991262), sourcec757a95가 진행 중이다.
원 actor/입력·64걸음/chunk1·조회 주기·5초 재시도·360/600초·RSS 상한을 바꾸지 않았다.
실패하면 종료 뒤 저장 metadata를 근거로 다음 작은 비용 개선을 정한다. 같은 실패를 근거 없이 반복하지 않는다.
성공 수용은 기존 원 정상 proof·두 prefix·원 값/UTC·후검사/정리 전체가 필요하며 metadata로 대체하지 않는다.
S3/S4·계산 중 WebGL·WSL 용량·새 Solar/실제 자료·G0–G4·전체 완료일은 미완료/미정이며 goal active다.

최신 원 상한 종료/수집 진행 기록은18216:0에서5173/5174 HTTP200·no-store·원 HTML/source·5root/원본·FD/소유 정리를 확인해 게시했다. 브라우저/디자인 재검사는 하지 않았다.
