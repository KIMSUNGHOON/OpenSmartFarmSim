# 전체 수확 정상 writer 실행 중 — 2026-10-09

19:00 KST 관측. [core3 계약](../contracts/crop-harvest-full-writer-v1.md)의 c0cc687을
별도 고정 source에서 실행했다. [시작·준비·관측 기록](artifacts/crop-harvest-full-writer-started-reference-20261009.json).
전체 writer/등록·독립 대사·fresh 조회의 수용 기록은 아직 아니다.

## 확인한 내용

- 원93770 도구 종료0, 집중81개(새7/기존74)를 통과했다.
- 원96517을18:52:18 KST 시작했다. 원 전체 부모47,809sample/5event와 artifact SHA,
  명시 새 합성 profile `full166-preserved-parent-synthetic-v2`의 연결 사전 검사를 통과했다.
- 같은 원 controller/producer/소유 PG 및 보호 미리보기3개 identity가19:00 KST 현재 살아 있다.
  실행480.404초의 감독 기록은 registry의 durable JSON53개/22,904,596bytes다.
  DB 등록·인증 backup·전체 독립 대사 완료 marker는 모두 false이며 원 도구 종료도 아직 없다.
  JSON 개수를 완료율이나 최종 수확 합계로 표시하지 않는다.
- 현재까지 단일/관측 합 RSS136,151,040/493,912,064bytes다. 감독 표본 간격0.25초,
  한도512MiB/1GiB이며 controller·소유 자식/PG·지정 기존 미리보기 범위다. 최종 자원 감사는 남았다.
- native Codex CLI `gpt-6.1-sol`/`xhigh`의 실제 문맥·판단을 기록했고 재귀 CLI0이다.
  원 생장 RHS를 다시 실행하지 않는다. main 수정은 가능하며 실행 source와 기존 미리보기는 고정한다.

## 종료 뒤 수용할 내용

정상 writer/서명 DB 등록 직후 **인증 backup을 먼저 보존**하고, 모든47,813행의 원 위치/UTC·
질량/배분·수지/합성 비교를 독립 Decimal2200으로 대사한다. 정상 manifest와 대표 현재 조회 뒤
원 DB를 정지하고, 감독자가 별도 Python/fresh DB에서 같은 서명 record/최초 시각·현재 권리/계정을 대사한다.
원 도구 종료0·별도 root 감사·FD/원본/source/미리보기 보존·소유 정리 후에만 전체 writer 자식을 평가한다.
실패하면 새 DB data/key/artifact/backup을 보존해 복구하며, 관측 실패만으로 전체 작업을 재시작하지 않는다.

[부분 실측](crop-harvest-writer-prefix-cost-20261009.md)에 근거한 producer 감독 상한은10,800초다.
마감은 **2026-10-09 21:52:18 KST**이며 완료 약속이 아니다. 이어지는 fresh reader는 별도900초 상한이다.
실제 전체 wall과 대사/복원 결과가 나오면 후속 수확 API/대표3D 일정을 갱신한다.

## 사용자 화면과 후속 순서

`http://localhost:5173/`은 기존 별도 DB의 **완료된 합성166일 생장 결과**를 조회한다.
현재 작업의 중간 JSON/진행률을 자동으로 읽거나 새 수확으로 전환하지 않는다.
최종 제품의 같은 실행 상태·확정 checkpoint/계산 시각·갱신 시각과 완료 결과 연결은
[U3 수용 기준](../tasks/todo.md#최종-제품-ui-통합-2026-10-09)에 남아 있다.

전체 writer/보존/fresh 수용 → 같은 결과의 보호 API/대표3D → 기후/물·양분/구매 에너지
→ 사용자 실행/Decimal 경제의 순서를 유지한다. 전체 수확이 등록돼도 API/3D 검증 없이 미리보기를 바꾸지 않는다.
실제 품종/농장 Run·국내 독립 자료0건과 G0–G4/생산/미래 마진/추천 보류는 그대로다.
