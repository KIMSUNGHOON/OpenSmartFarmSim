# 기관 목록20결과·큰 packet의 실제 HTTPS 용량

선행은 [hosted 실제 API/DB/3D 통합](../research/organ-native-integration-20261021.md)이다.
기관 family/U1의 용량 자식이며 실제 농장/전체 제품 수용과 구분한다.

## 정상 입력과 수용 기준

- 기존 synthetic reference의 프로필/초기 상태·forcing/제거율·solver를 재사용한다.
  소프트웨어 부하용 새 판본에서 첫 forcing 구간을 늘려 전체3600초를 만들고,
  뒤 구간/관리 사건을 같은 offset으로 옮긴다. 출력은 정수 초3601시점이다.
  이는 관측 기후나 품종 예측이 아니며 원 입력/결과를 덮어쓰지 않는다.
- 먼저 정상 `CropResultStore.put` 한 결과의 완료·크기·생성 시간과 실제 HTTPS를 확인한다.
  full 자식은 같은 정상 producer로20개의 별도 study 결과를 만든다.
  가짜 결과/바이트 padding·서명 재발급으로 크기나 개수를 대신하지 않는다.
- 실제 SCRAM/표준 ApiRuntime/Bearer/검증 TLS에서 limit20의 원 ID/정렬/개수와 tail cursor를 대사한다.
  목록은64KiB 이하·완료 본문30초 이내, metadata만 반환한다.
  매 연결/요청/헤더/본문 읽기에 남은30초 budget을 적용하고 실제 전체 wall을 기록한다.
- 원 row/payload/hash/서명 fingerprint·선택 DB counts가 보존돼야 한다.
  조회 중 put/integrate/RHS/SQL 쓰기는0이며 현재 권리 거부와 복원을 확인한다.
  실패/timeout을 실제 크기·단계와 함께 보존하고 용량 성공으로 보고하지 않는다.
- 기존5root/자료·512MiB/PID·합1GiB/600초/.25초·FD/소유 PG/프로세스/임시 정리를 유지한다.
  실제 packet별/합계 bytes·시점 수를 기록한다. 미검증64MiB 상한·동시 WebGL/WSL 적용을 통과로 확대하지 않는다.

핵심 시험은 `backend/tests/crop_organ_catalog_capacity_smoke.py`다.
사전1결과와 full20결과는 서로 다른 소유 DB/시험으로 대사하며 원5분6시점 fixture는 유지한다.
`organ-catalog-20-large-HTTPS-capacity`는 full20의 실제 완료·불변성·거부/복원·정리 증거 뒤에만 체크한다.

WSL의 첫 사전 검사는 합산 RSS 보류다. 다음 실행은 기존 hosted 실행기의
`--capacity 1`과, 그 사전 수용 뒤 `--capacity 20`이다.
Web tests의 닫힌 `organ_capacity` 입력만 선택하고 Solar/브라우저 실행을 함께 요청하지 않는다.
같은 PG16.15/잠금 Python·백엔드 설치와 기존 소유 자원/종료 감독을 재사용한다.
생성 시작/반환/검사 완료의 진행 metadata와 최종 JSON만 artifact로 보존하며
원 payload·계정/DSN/passfile/TLS private key나 private log는 업로드하지 않는다.
hosted 성공은 보호5root를 포함한 WSL 동시 용량을 해제하지 않는다.

정상20개가 원30초 응답으로 실패하면 `organ_capacity_diagnostic=true`의 별도 실행은
기존 `_registration`/`_rows`/`_item`의 호출 시작/끝과 시간·개수만 계측한다.
원 producer·SQL·현재 검사·요청/자원 상한을 유지하고 원본/토큰을 기록하지 않는다.
관측 오버헤드가 있으므로 계측 실행은 정상 용량 수용으로 쓰지 않는다.
항목 내부의 다음 관측은 원 store의 get/find/checked/request/current/references와
원 farm read_registration 호출을 그대로 수행하며 완료/오류 개수·wall/thread CPU를 집계한다.
포함 시간은 중첩되므로 합산하지 않는다. 호출 스택에서 계측한 자식 시간을 뺀 exclusive 시간도 따로 기록한다.
항목 완료 시의 집계 snapshot과 HTTP 시작 offset을 보존해 client timeout 전 관측과 그 뒤 작업을 구분한다.
