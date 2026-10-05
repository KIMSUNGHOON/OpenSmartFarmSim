# 시작 유보 계산의 불변 파일과 재적분 없는 reader

날짜: 2026-10-05 KST. **합성 연구 파일의 로컬 수용**이다.
구현 commit: `bd71823`.
[계약](../contracts/crop-startup-artifact-v1.md),
[실제 파일](artifacts/crop-startup-artifact-empty-entry-20261005.json),
[실제 ID/hash·여섯 결과 대사·세 hold·시험/자원 증거](artifacts/crop-startup-artifact-reference-20261005.json)를 확인한다.

## 실제 CLI와 변경 범위

현재 CLI `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의 실제 turn_context
`2026-10-05T01:34:04.509Z`에서 **gpt-6.1-sol / xhigh**를 확인했다.
현재 세션에서 설계/구현/검토했으며 CLI를 재귀 실행하지 않았다.
actual context line·원 코드/시험/원 참조/로그 hash를 증거에 기록했다.
제품 runtime CLI·데이터/관문 승인은 별도다.

새 `crop-startup-artifact-v1`은 canonical 원 프로그램·고정 profile/notice bytes와
새 적분 manifest/result·코드/정책/입력/결과 hash·파일 ID를 보존한다.
builder가 서버에서 직접 계산하고 reader는 신뢰 digest와 파일/형식/수지를 검사한다.
외부 작성 결과/계수를 입력으로 받지 않는다. 기존 모델/fixture/결과 bytes를 보존했다.
원 canonical/UTC/프로그램/단위/상태/사건 helper만 재사용하며 그 두 파일 hash도 명시한다.
전역 RHS/validator 치환이나 새 dependency·DB/서버는 없다.

reader는 각 시점의 실제 예정 완료 step과 승인 사건 수로 수지 예산을 대사한다.
마지막 확인 상태의 UTC/step/phase가 저장 과거보다 앞서거나 마지막 같은 sample과 다른
경우를 거부한다. 승인 사건의 N/C 제거 비율·상태/누적 제거량도 검사한다.
재적분은 하지 않으며 forcing에서 생장 궤적의 진실을 새로 증명하는 기능은 아니다.
신뢰 hash를 임의로 다시 쓴 caller는 자료/권리/승인을 얻지 못한다. 후속 DB가 현재 farm/
program 권리와 HMAC custody를 검사한다.

## 사용자 산출물과 통과 검증

- 직접 확인할 수 있는 **빈 초기/명시 유입의 61,927 bytes immutable 파일**을 보존했다.
  같은 3개 UTC의 기관/50 N/C·LAI와 요청/실현/유보/생장 호흡·네 수지/manifest가 들어 있다.
  파일 SHA-256은 `784e915f0e0a2eeba0eea5c442ae06bdf995f0c6d3bcc82aceee9118d2557a13`다.
- 독립 Decimal 참조의 **6프로그램/23출력·2,829수치**를 검사했다. 여섯 실제 결과 모두
  [이전 수용 적분](crop-startup-integration-implementation.md)의 결과와 **정확히 동일**하다.
  이전 18개 code/profile/reference pin도 바뀌지 않았다.
- event 제거 초과(15 step/과거 3출력), 소수 초 trial 실패(0 step/과거 1출력), 초기
  pre-onset 실패(0 step/빈 과거)의 실제 hold/마지막 확인 상태를 보존했다.
- 별도 Python reader·동일 bytes 재현·사본/입력 격리·읽기 중 재적분 금지를 확인했다.
- 비합성/ID 충돌·단위/길이/시각/유한성·추가/중복/비canonical/크기, 신뢰 digest 불일치,
  재해시한 코드/모델/정책/manifest 혼합·수지/예산·사건/확인 상태의 변조를 거부했다.
- 새 시험 **79개/10.01초**, 원 artifact 포함 작물 집중 회귀 **799개/49.85초·건너뜀 0**.
  첫 RED는 모듈 부재였다. 첫 GREEN의 solver 변조 시험 하나가 원 값과 같아서
  시험 입력을 고친 뒤 최종 전체 검증을 통과했다. 제품 계산식을 수정하지 않았다.
- 24시간/512출력의 실제 새 파일은 **3,519,579 bytes**, **1,022 step**이다.
  계산+자체 검증 **8.388086초**, 파일 읽기+검증 **0.285888초**,
  과정 전체 최대 **93.01 MiB**(시험 profile/pytest import·계산/packet/읽기 포함)다.
  네 수지와 빈 N/C를 전 시점 확인했다. 일정 광의 합성 자원 시험이며 실제 작기가 아니다.
  큰 원 파일은 private 임시 경로에 두고 원 hash/manifest·실측 비용을 공개 증거에 기록했다.
- 정확성/단순 경계·기존 bytes·입력 보안·bounded 비용을 검토했다. CPU 작업은 한 개씩
  `nice -n 10`으로 수행했고 새 의존성/상주 서버/DB가 없다.

이 단계는 DB/API/새 모델의 브라우저 연결을 수행하지 않았다.
새 파일/코드는 아직 기존 저장 v1/v2 또는 UI에 연결되지 않았다.
기존 기록 데모를 새 시작 유보 모델의 장면으로 표시하지 않는다.
선행 `590fadc` CI는 같은 실행을 취소 없이 완료했다.
[전체5개·백엔드3,157개/별도UID4개·여섯 동일 목록/정리·집계](artifacts/crop-coupled-replay-startup-rates-ci-20261005.json)를
확인했다. 그 SHA에는 이 새 artifact/적분/기관 모듈이 없으며 로컬 검증 커밋을 일괄 push한
뒤 새 hosted 판본의 수용을 별도로 확인한다. 기존 HTTPS timeout의 원인은 확정하지 않았다.

## 남은 한계와 다음 한 단계

새 packet에도 수렴은 `not_evaluated_for_this_program`이다. 원 초기/양의 tail 전환은
4차 수렴을 입증하지 않았고 극히 작은 개별 N 구획은 해석해 대비 최대 약 8.52% 상대 차이가 있었다.
이전 오차 고지와 합계 수지/구획 정확도 구분을 유지한다. 농장 생산/수확 kg·마진/순위 주장은 없다.

artifact의 10월5–6일 잠정 목표는 **10월5일 KST 로컬 완료**로 갱신한다.
다음 [농장 결합 저장 v3 계약](../contracts/crop-result-v3.md)은 두 작은 구획으로 진행한다.
먼저 새 표/명시 role·기본 false/config 호환을 실제 SCRAM으로 검사하고,
그 뒤 원 요청/현재 권리·HMAC/원자성·동일 bytes/별도 프로세스 읽기를 검증한다.
전체 저장 잠정 **2–4시간**, 하루4시간 기준 **10월5–6일 KST**다.
그 뒤 페이지 API → 같은 UTC 원 수치/3D를 별도 수용한다.

국내 독립 자료 0건/actual forcing·Run 0개, cultivar/초기/자동 S/W1/RGR/pre-onset/
전체 작기·수확/자원/경제는 여전히 외부 의존 또는 후속 작업이다.
G0–G4는 미수용이다. 실제 예측/추천의 날짜는 독립 자료/검증 작기 확보 전에 정하지 않는다.
자료 확보와 순수 개발을 병행하며 운영 기반은 `d19f7c0`으로 고정한다.
