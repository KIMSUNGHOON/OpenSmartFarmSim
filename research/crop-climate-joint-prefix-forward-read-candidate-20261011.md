# 계산 전진 중 불변 판본 읽기 — 후보 검증 중

2026-10-11 후보 단계 기록. **기록 당시 P6a2b1 미수용, P6a/P6b 미완료.**
이후 [최종265개/로컬 수용](crop-climate-joint-prefix-forward-read-implementation-20261011.md)을 별도로 확인했다. 아래는 당시의 제한된 증거를 보존한다.
[계약](../contracts/crop-climate-joint-prefix-forward-read-v1.md)의 reader v4/HTTP 후보를 구현했다.
현재 사용자5173/5174의 frozen source/dist는 변경하지 않았다.
5173은 완료 저장 재생,5174는 상태/확정 checkpoint 자동 조회와 종료 뒤 저장3D다.
개발용 별도 DB 계산이 이 화면에 자동 노출되지는 않는다.

## 후보 변경과 실제 관측

- 같은 선택 사건·이전 latest의 전체 row와 최초 UTC를 재검사하고, 현재 signed HEAD가
  처음 관측한 private HEAD와 선택 사건의 후손인 경우 원 페이지를 반환한다.
  현재 권리·입력·작업/취소 검사를 유지하고 공개 DTO·수치·writer/원 custody는 변경하지 않았다.
- 직렬화 후에도 비공개 witness에서 같은 검사를 수행한다. 새 값으로 원 응답을 덮어쓰지 않는다.
- 실제 요청별 진단의 독립 작업자 보류에서 DB 역할 연결 한도 초과를 확인했다.
  초기 readonly 거래에서 선택 사건을 읽은 뒤 연결을 반환하고 파일/후속 조회를 수행하도록 조정했다.
  역할 한도·SCRAM·scratch PG32연결·사용자 DB 설정은 변경하지 않았다.
- 최초 미추적 생장 페이지422의 원인은 별도로 미확정이다. 후속 작업자의 연결 한도 초과와
  같은 원인이라고 단정하지 않는다. 중간 진단의 tuple 적응/저장 누락 및 진단 factory의
  들여쓰기 실패도 성공 검증으로 세지 않는다.

## 통과한 범위

[기계 판독 증거](artifacts/crop-climate-joint-prefix-forward-candidate-reference-20261011.json)
SHA256 `c9f5144aa49ac71a24bd5aab0264738416fd20687e0274ae9b5588d21c7a903f`.

최종 두 core에서는 **실제 자동 정상 경로1개만 통과**했다. 원 session23781/guard0,
pytest125.42초·guard141.958초다. 실제 SCRAM/TLS·독립 unpaused worker이며 API/worker trace나 지연이 없다.
공개 요약에서 발견한 동일 selector의 사건1행/생장1행을 계산 중200으로 읽고,
원 terminal의 canonical records/hash·binary64·UTC와 각각 일치했다.
원 terminal summary는 독립 current query의 bytes와 같고 작업자 exit0이다.
이 작은 합성 시험은 전체 작기·브라우저3D 검증이 아니다.

단일/합산 RSS 최대153,387,008/1,009,041,408bytes,512MiB/1GiB 이내다.
사용자 서버4개 보호 root·두 source/dist·원본2,148개를 보존했고 FD4→4,
소유 프로세스/PG·임시 PG/인증 파일 잔여0이다. 사용자 서버 중지/원격 작업0이다.

초기 연결 반환 수정 **전** private/confirmed 전진과 rollback3개, signed fork 확장1개,
실제 감사 변경 거부 및 별도 합성 returned-row fault1개도 통과했다.
이들을 최종 core의 통과 개수에 더하지 않는다. 실제 감사 row는 기존 불변 trigger로 변경/삭제가 거부됐다.

## 다음 검증과 게시 조건

1. 최종 core의 독립 전진/heartbeat·signed rollback/fork·감사 row·원 reader/HTTP 회귀를 확인한다.
2. 같은 최종 core의 실제 자동 hold/cancel·원 종료/정리·자원 검증을 완료한다.
3. P6a의 실제 제품 브라우저/WebGL에서 계산 중 같은 selector/UTC의3D·표 일치를 검증한다.
4. P6b에서 사용자 frozen 후보를 전환하고 기존 결과/두 주소·현재 권리/키와 재접속을 검증한다.

P6a2b1 체크박스는 유지한다. 첫 공개 page200을 얻었지만 후속1–2가 남아 있어 수용/배포를 완료 처리하지 않는다.
완료일은 이 검증 뒤 실제 브라우저의 자원·관측 결과로 다시 산정한다.
실제 품종/농장 Run·독립 국내 자료0, G0–G4 `not_assessed`, 생산/미래 마진/추천 보류를 유지한다.
조사·설계 CLI 증거는 artifact의 `gpt-6.1-sol`/`xhigh` 실제 문맥을 따르며 재귀 CLI0이다.
