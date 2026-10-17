# 독립 일사 작업자의 보류·취소 기능 검증 v1

선행: [원 정상 실행](crop-solar-unpaused-hosted-v1.md)의 호스팅 한 사례 수용.
저장된 정상/hold의 HTTPS·WebGL과 명시 runtime 조립은 독립 계산 중의 보류·취소를 증명하지 않는다.
기존 `test_crop_greenhouse_solar_execution_runtime_native.py`는 준비된 저장 결과의 조립/조회 검증이다.

## 순서와 범위

1. 정상 수용 source의 같은 application code에서 독립 API/worker를 기동한다.
   검증된 SCRAM·TLS·실제 접수·자동 선택/임대·chunk1을 유지한다.
2. 보류 한 사례는 기존 수치 reference의 명시 hold 입력/판본을 사용한다.
   입력/근거/예상 hold와 마지막 확정 UTC를 고정하고, 독립 producer의 같은 입력 결과와 대사한다.
   정상 fixture 축소·수식/계수/실행 조건 변경으로 보류를 연출하지 않는다.
3. 취소 한 사례는 원 정상64걸음을 실행하며 실제 확정 prefix를 확인한 뒤 인증된 cancel HTTP를 보낸다.
   시험을 맞추기 위한 worker pause/barrier·sleep 삽입은 하지 않는다.
   취소 요청보다 먼저 완료된 경우는 취소 수용이 아니며 실제 경합 이력으로 남긴다.
4. 원360초 계산/600초 감독·512MiB/PID·합1GiB·0.25초 자원 표본을 유지한다.
   hosted에는 로컬5root가 없음을 명시하고 로컬 용량/G4로 승격하지 않는다.

## 수용 증거

- API/독립 worker 실제 신원·원 actor/source/input hashes, 실제 HTTP/작업/시도/임대 이력을 연결한다.
- 보류는 실제 수치 hold reason·step/UTC·부분 상태/장부·최종 hold 결과가 원 reference와 같아야 한다.
  성공/생산 예측으로 표시하지 않는다. 공개된 확정 prefix는 최종 저장된 해당 prefix와 일치한다.
- 취소는 HTTP 응답과 실제 canceled 상태/종료가 연결되고, 취소 후 새 checkpoint 확정·성공 게시·완료 결과 등록이 없어야 한다.
  이미 확정된 원 prefix를 고치지 않으며 canceled 응답에 맞게 화면/조회 접근을 폐기한다.
- 현재 권리/계정·참조 변경은 차단하고, API GET의 모델/CLI 실행·SQL 변경은0이어야 한다.
- 원 FD identity·정상 종료, schema/role0·소유 비좀비/PG/임시/passfile0와 실제 CI/run/head/digest를 확인한다.
- 소프트웨어 합성 사례만 수용한다. 보류·취소 각각의 성공 전 체크박스를 닫지 않는다.

두 사례 뒤에만 실제 계산 중 prefix→같은 UTC의 표/그래프/WebGL을 검증한다.
S3 부모·WSL 전체 앱 동시 용량·사용자 적용/재시작·실제 자료/G0–G4는 각각 남는다.
