# 정상 수확 writer의 두 페이지 비용 — v1

2026-10-09. native Codex CLI `gpt-6.1-sol`/`xhigh`, 재귀 CLI0.
core3: 이 계약, `research/crop-harvest-writer-prefix-cost.py`,
`backend/tests/test_crop_harvest_writer_prefix_cost.py`.

## 실제 경로와 중단

보존한 전체166일 부모의 원 DB/key/input/artifact를 별도 PostgreSQL에 복원하고
현재 query와 정상 `HarvestRegistry.put`을 사용한다. 기존 합성 계수/배정은 유지하며
질량·배정 revision과 그에 따른 mass hash 참조만 명시 새 판본으로 만든다.
원 source/전체 기간/선택 범위는 이미 검증한 보존 helper에서 가져온다.

측정 hook은 현재 query의 원 응답을 변경 없이 전달하고 실제 호출 시간/범위만 기록한다.
정상 `_put`이 두 번째 불변 page를 fsync한 직후 통제 예외를 발생시킨다.
root/HEAD나 DB INSERT는 도달하지 않아야 한다. 정상 경로를 임의 행·가짜 authority로 바꾸지 않는다.
최소130sample의 현재 부모를 선행 확인해 작은 완결 결과를 우연히 게시하지 않는다.
hook은 해당 private artifact 디렉터리의 원 inode와 정상 bytes/SHA만 허용하고 context 종료 때 복원한다.

현재 계산 권리 거부는 이 복원 query의 권리 제공자 인스턴스에만 적용한 소유 시험 hook으로 확인한다.
표시 권리를 유지하고 실제 registry가 게시를 거부해야 한다. 공유 권리/principal/원 자료 파일을 바꾸지 않는다.
실제 제공자의 계약 변경이나 자료 권리 확보 증거로 표시하지 않는다.

## 대사와 수용

1. 첫 두 blob의 실제 canonical bytes/SHA/count/순서·원 위치/UTC를 확인한다.
   writer가 실제로 읽은 bounded sample/event 사본을 사용하고 독립 Decimal2200 검사로
   각 제거·질량·정확 분수 배정과 누적 반올림 예산을 대사한다. 전체 작기 합계/관측 비교를 주장하지 않는다.
2. hook의 다른 디렉터리·기존 HEAD/잘못된 raw, 부분 blob/수량/원 시각 변조를 거부하고 FD를 닫는다.
   원 계수/배정·raw 판본 참조 보존과 실제 stop/미게시를 집중 시험한다.
3. 실제 SCRAM/current query의 원 record/권리 거부·복원, DB 수확0과 HEAD 부재,
   원 backup/입력/artifact·기존 미리보기·FD, schema/role/passfile/소유 PG/임시 정리를 확인한다.
   원 명령 종료0·native CLI 문맥/판단·source/hash와600초·단일512MiB/관측 합1GiB를 기록한다.
4. 초기 summary/선택 조회/페이지 쓰기와 부분 전체 wall을 분리해 기록한다.
   원 전체 용량/계수 근거와 합쳐 정상 전체 writer 예산을 정하며 부분 비용을 전체 완료 시간으로 표시하지 않는다.

이 자식은 전체 writer/등록·전체47,813행 Decimal·인증 보존/fresh reader·수확 API/3D의 수용이 아니다.
전체 RHS는 재실행하지 않는다. U3와 실제 품종/독립 농장 자료·G0–G4 보류는 유지한다.
