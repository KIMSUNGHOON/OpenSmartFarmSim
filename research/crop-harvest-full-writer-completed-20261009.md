# 전체 합성 수확의 정상 저장·등록·복원 수용

2026-10-09. [실행 계약](../contracts/crop-harvest-full-writer-v1.md)의 전체 writer/registry 자식을 로컬 수용했다.
[불변 영수증](artifacts/crop-harvest-full-writer-completed-reference-20261009.json)의 SHA256은
`b47df6130e34a7db09cd963a60ef935f17cfaeb3ce5fc090cda0cd6518442969`다.
기존 [19:00 실행 관측](crop-harvest-full-writer-running-20261009.md)은 당시 기록으로 보존한다.

## 완료 증거

- 같은 원 명령96517의 실제 종료0을 확인했다. 고정 source `c0cc687`에서 정상 `HarvestRegistry.put`을 실행했다.
  producer5,919.306초·후속 fresh211.753초·전체6,131.177초이며 각각10,800초/900초 상한 안이다.
- 보존된 전체166일 부모의47,809sample/5event에서47,813수확 행을 등록했다.
  전체47,808구간/5사건의 원 UTC·수량·목적·미배정과 모든 반올림 수지를 독립 Decimal2200자리로 대사했다.
  생장 RHS나 새 생장 결과/증명을 만들지 않았다. 선행 집중81개/원93770 종료0도 같은 core3의 증거다.
- 실제 artifact는751파일/309,399,098bytes다. 새 source/profile 판본의 정상 저장으로 생긴 별도 hash이며,
  과거 capacity artifact나 signed 영수증을 덮어쓰지 않았다.
- 정상 등록 직후 인증 백업을 보존했다. 원 DB 정지 뒤 별도 Python/새 PostgreSQL의 실제 SCRAM 현재 조회에서
  동일 record/최초 시각·summary·첫64/마지막1행의 원 hash를 확인했다. 다른 tenant와 현재 표시권 철회를 거부하고 복원했다.
  공유 권리/계정 파일은 변경하지 않았다. raw 인증 백업522,495bytes와 원 key/입력/artifact를 비공개로 보존한다.
- 별도 root 명령3349의 실제 종료0으로 원2,148항목의 bytes/inode/mode·FD3→3·미리보기 생존/frontend200을 확인했다.
  두 정지 소유 DB의84,497,733bytes를 제거하고 인증 복구 자료의 재검사를 통과했다.
- 0.25초/23,789표본에서 단일 PID143,360,000bytes·명시 관측 tree 합516,091,904bytes로512MiB/1GiB 안이다.
  관측 범위는 소유 실행/PG와 보호 미리보기이며 전체 WSL 또는 일반 운영 용량 수용이 아니다.
- 연구·설계는 실제 native Codex CLI `gpt-6.1-sol / xhigh`의 turn-context 시각/해시로 기록했고 재귀 CLI는0회다.

## 다음 경계

전체 저장·등록·복원만 완료다. [실제 보호 API 비용](crop-harvest-api-cost-20261009.md)의
전체 summary는30초를 넘었으므로 API/대표3D 수용은 보류한다. 기존 사용자 화면은 완료된 생장 결과를 계속 읽는다.
실시간 계산 상태·새 checkpoint·완료 결과 자동 전환은 U3의 후속이며 이 저장 완료로 체크하지 않는다.

다음은 중복 부모 조회의 비용 보완→같은 전체 보호 API/대표 UTC3D→기후/물·양분/구매 에너지→사용자 실행/Decimal 경제다.
이미 완료한 전체 RHS/writer를 다시 실행하지 않는다. API 비용 보완의1–3집중시간은 계약·거부 시험·동일 부하 재측정의
잠정 작업량이며 성공 시각이나 최종 제품 완료일 보장이 아니다.
실제 품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4 `not_assessed`, 생산/미래 마진/추천 hold를 유지한다.
