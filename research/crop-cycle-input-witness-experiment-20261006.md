# 원 입력 검증 증명의 반복 원본 대사 실험

2026-10-06 KST. [비용 분해](crop-cycle-input-validation-cost-observation-20261006.md)에서
원본 읽기보다 반복 JSON/정규화/직렬화의 비용이 컸다. [연구 계약](../contracts/crop-cycle-input-witness-experiment-v1.md)의
3 core파일로, 기존 검증의 context 기록을 보존하고 모든 현재 bytes를 대사하는 비용을 확인했다.
**실험의 동등성/비용만 수용했다. 제품 권리·server proof·전체 API/3D는 미수용이다.**

## 구현·검증

[새 연구 helper](crop-cycle-input-witness-reference.py)는 원 `open_input_packet`/`prepare_context`를
그대로 수행해 원 manifest/plan·initial/seed/Fraction clock·grid index 기록을 묶는다.
실험용 메모리 키의 HMAC·측정 code/spec/원 source/profile/Python/notice를 확인하고,
현재 root와 모든 참조 블록의 bounded/no-follow 읽기·SHA·정확한 목록/총 bytes를 확인한 뒤
그 **JSON 기록**을 반환한다. `InputPacket`/`StreamContext`나 제품 Run을 대체하지 않는다.

[집중 시험](../backend/tests/test_crop_cycle_input_witness_reference.py)의 최초 RED는 helper 미구현16오류/0.35초였다.
구현 후16통과/0.84초, 유효 MAC의 미지원 판본 거부까지 구분한 최종은 **16통과/0.82초**다.
서로 같은 시험의 재검증 수를 합산하지 않는다. root/blob 변경·누락·파일/디렉터리 symlink·여분 파일,
payload/MAC/잘못된 key·크기·중복 key/NaN·판본과 experiment/helper 코드 변경을 거부했다.
실패한 원 preflight에서는 증명을 발행하지 않으며 실제 FD가 남지 않았다.

```bash
cd backend
nice -n 15 .venv/bin/python -m pytest -q tests/test_crop_cycle_input_witness_reference.py
```

사설 RED/최종 로그는 `/tmp/ossf-cycle-input-witness-red-20261006.log`,
`/tmp/ossf-cycle-input-witness-focused-final-20261006.log`다. 최종 로그 SHA256은
`ceb1f43f9a00610a82f72126bc690b6420161f359f18a310946ec0e049593a78`.
전체 backend/web/browser 시험은 이 단계에서 실행하지 않았다.

## 같은166일 입력의 실제 측정

현재 native CLI `gpt-6.1-sol / xhigh`의 실제 문맥은 `2026-10-06T07:44:05.494Z`,
원 줄 SHA256 `8ffbbba50c397e938f285f5eb139460d517b97cb2f88741d4642f5ee1c2472c2`다.
재귀 CLI0회. 다음 별도 Python은 원166일 계산을 중단/재시작하지 않고 같은 입력만 읽었다.

```bash
nice -n 15 backend/.venv/bin/python /tmp/ossf-cycle-input-witness-measure-20261006.py \
  > /tmp/ossf-cycle-input-witness-measure-20261006.log 2>&1
```

실제 session41447 종료0. 사설 측정 script SHA256은
`50f194fa2d6c39f4f7dda61944c9e66cc263e334c0ab0ca246d0738e17f278e4`,
로그 SHA256은 `2262e0ef86385d47dfcf0011e74a3079000e49335dddd37f13fc976eadd8345e`다.
[불변 영수증](artifacts/crop-cycle-input-witness-reference-20261006.json)의 시각은
`2026-10-06T07:53:46.842766+00:00`, SHA256은
`75c3027cc0d57072c0f8fe466c81d6f47f2c7757770ea53537b3d5740b0495ba`다.

| 실제 범위 | wall초 | CPU초 |
|---|---:|---:|
| 원 전체 preflight/context·실험 증명 발행 | 31.611948 | 31.330961 |
| 모든 현재 bytes/기존 증명 대사1 | 0.172137 | 0.172135 |
| 같은 대사2 | 0.180158 | 0.180115 |

대사마다 고유749블록/113,920,841bytes를 확인했다. 원 context/plan·초기/seed·clock은
앞선 기준/계측 실행과 정확히 같았고 공통 semantic SHA256은
`d84f4b5447f9e7de917ff11047758f5f8705b18a98d9a8a8b893eb57ffa731b5`다.
원 grid index hash도 같았다. RHS0·FD4→4·nice15·해당 프로세스 peak RSS48,406,528bytes.
원 입력/artifact와 기존53개 source는 그대로이며 PG/서버/브라우저를 기동하지 않았다.

실험 증명은147,362bytes, SHA256은
`fe6894944645cbf1beb981e177c06aceb730380107b70bc9e42d8f60ad279629`다.
사설 원 바이트는 `/tmp/ossf-cycle-input-witness-raw-20261006.json`에 보관했다.
키는 프로세스에서 만든 무작위32bytes이며 보관/로그/공개하지 않았다. 종료 뒤 이 증명을
제품 재시작에서 재검증할 수 있는 키 관리나 서버 발행자 증명이 존재한다고 주장하지 않는다.
OS cache 미통제이며 앞선 입력 조회와 원 발행 뒤 측정했다. nice10 전체 RHS는 동시에 진행됐고,
이는 cold-cache·다른 장비·전체 HTTP latency나 안전한 상한을 측정한 결과가 아니다.

## 판단·다음 단계·외부 의존성

같은 bytes·검증 code/profile/environment·원 context에 한정해 기존 구조/단위/chain/clock/grid
검사 증명을 재사용할 실측 근거를 얻었다. 현재 farm/등록/자료 권리는 매 조회에서 별도로 확인해야 한다.
제품 적용에는 실제 검증 worker의 발행 증명·키/권한·불변 보관/재시작, 같은 원 typed reader/context,
현재 bytes/권리·변조/철회 거부와 code SHA/root/manifest·과거 재현의 계약/증거가 추가로 필요하다.
처음의 전체 검증31.61초나 artifact 검사 비용은 이번 결과로 없어진 것이 아니다.
실험 HMAC이나 반환된 JSON만으로 이를 우회할 수 없다.

원166일 계산 종료 증거 뒤 필요한 작은 제품 수정과 전체 farm/공개 page/3D의30초/2MiB를 확인한다.
`crop-cycle-burden-replay-restore`와 전체 부하 체크는 유지한다. 생과·자원·경제 순서도 유지한다.
실제 품종 입력/국내 독립 자료 채택0건·G0–G4 `not_assessed`, 생산 예측·추천은 보류다.
