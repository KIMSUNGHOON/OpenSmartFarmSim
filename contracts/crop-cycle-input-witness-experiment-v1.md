# 반복 입력 검증의 원본 대사 실험 — v1

상태: **연구 실험 후보, 제품/runtime/API 수용 전**, 2026-10-06 KST.
[실제 비용 분해](../research/crop-cycle-input-validation-cost-observation-20261006.md)의
기준33.05초·반복 JSON/정규화/canonical 비용이 이 작은 실험의 근거다.
운영 기반 추가나 G0–G4 해제 작업이 아니다. 전체166일 원 계산의53개 source는 그대로 둔다.

## 질문·범위

원 preflight와 원 context가 같은 root의 전체 schema/단위/chain/clock/grid를 검사한 이후,
그 원 증명과 모든 현재 원본 bytes·프로필/코드/환경을 대사하는 비용을 측정한다.
원 입력 loader와 계산식을 수정하지 않고 `research/crop-cycle-input-witness-reference.py`,
집중 시험, 이 계약의3 core파일로 확인한다. 실제 입력·농장 권리·서버 custody/DB·artifact·
HTTPS·3D는 실험 범위 밖이며 별도 수용이 필요하다.

`certify`는 고정 experiment spec의 실제 원 `open_input_packet`/`prepare_context`를 수행한다.
원 manifest/plan·initial/seed/Fraction clock·원 grid index를 묶고 실험 전용 메모리 키로
canonical payload에 HMAC을 붙인다. RHS는 실행하지 않는다. 키는 Git/로그/공개 receipt에 남기지 않는다.
이 HMAC은 연구 코드의 동등성 확인 수단이며 실제 서버 작업자가 검토·승인했다고 증명하지 않는다.

`verify`는 닫힌1MiB 이하 증명·HMAC·정확한 spec/측정 코드와 기존51개 source/profile/
Python/notice·원 입력 root/manifest/plan/index를 대사한다. 원 bounded/no-follow 읽기로
현재 root와 모든 고유 참조 blob SHA·정확한 파일 목록/총 bytes를 확인한 뒤에만
기존 context **JSON 기록**을 반환한다. 실제 `InputPacket`/`StreamContext`를 재구성하지 않고,
제품 reader/worker/runtime에 연결하지 않는다. 현재 권리·등록이나 gate 승인도 반환하지 않는다.

읽기 중 변경은 해당 읽기의 hash로 검출한다. 성공 후의 미래 변경이나 파일 불변 소유권,
현재 farm/rights/모듈 메모리 공격·key custody·서버 재시작의 검토 증명은 이 실험이 보장하지 않는다.
원 파서/프로필의 검증 의미와 code SHA를 다른 판본으로 전이하지 않는다.
과거 결과 root/manifest와 새 reader의 호환은 후속 제품 계약에서 명시적으로 해결해야 한다.

## 수용과 사용자 산출물

- 실제 원 context/격자 index가 보존되고 원 고유 bytes를 모두 대사한 경우에만 반환한다.
- root/blob 변조·누락·symlink/여분 파일, payload/MAC/key/크기/중복 key/NaN/판본,
  experiment/측정 코드 변경을 거부한다. 실패 시 새 증명·부분 context·FD 누수를 남기지 않는다.
- 작은 자체 소유 프로그램의 집중 시험을 먼저 수행하고, 고정166일 입력에서 원 인증/대사
  시간을 각각 측정한다. 입력/artifact와 기존53 source·RHS0·FD/자원/정리를 확인한다.
- 실제 CLI `gpt-6.1-sol / xhigh` 문맥·명령/종료·코드/입력/증명 hash와 결과를 보존한다.
  사용자 산출물은 비용·동등성·보류 보고서다. 새 HMAC/context를 승인 자료나 공개 Run으로 제시하지 않는다.

`crop-cycle-burden-replay-restore`는 이 실험으로 체크하지 않는다. 실제 전체 계산·저장·
현재 권리/변조·원 UTC/page/3D·30초/2MiB 수용과 제품 proof의 발행/키/재시작 계약이 남는다.
실제 품종/국내 독립 자료0건, 생산량·예측·추천 게시 조건은 기존 관문을 따른다.
