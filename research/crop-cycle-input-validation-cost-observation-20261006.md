# 원 입력 검사·격자 준비의 비용 분해

2026-10-06 KST. [원본 byte/hash 관측](crop-cycle-input-byte-cost-observation-20261006.md)의 후속이다.
동일한 자작166일 입력에서 원 reader/context를 실행하고, 반복 검사 비용의 위치를 측정했다.
농장·자료 권리·artifact·HTTPS·3D 성능 수용은 이 측정 범위 밖이다.

## 실행·대사

[측정 코드](crop-cycle-input-validation-cost-reference.py),
[원 영수증](artifacts/crop-cycle-input-validation-cost-reference-20261006.json)을 보존했다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`의 실제 context는
`2026-10-06T07:28:43.236Z`, 원 줄 SHA256은
`cd1ad45f69e3cee70c9728e1f0d1c8099e5b9a7705aa8466ae6dfb80feb0dfed`다. CLI 재귀0회.

```bash
nice -n 15 backend/.venv/bin/python research/crop-cycle-input-validation-cost-reference.py \
  --run /tmp/ossf-cycle-full-rhs-166day-20261006 \
  --spec-sha256 9f0415126674a2ab1dd4ccd6fc216c27cdd8cfadf063735c3053d25bc1ee5df6 \
  --cli-context /tmp/ossf-cycle-input-validation-cost-cli-20261006.json \
  --output research/artifacts/crop-cycle-input-validation-cost-reference-20261006.json \
  > /tmp/ossf-cycle-input-validation-cost-20261006.log 2>&1
```

실제 Python session22815는 종료0. 상세 입력 wrapper 없는 기준 실행(RHS guard만) 다음,
별도 열린 reader에 상세 wrapper를 붙여 실행했다. 두 실행의 원 manifest·초기/seed·Fraction clock·
계획·context는 정확히 같았다. 공통 semantic SHA256은
`d84f4b5447f9e7de917ff11047758f5f8705b18a98d9a8a8b893eb57ffa731b5`다.
spec/51개 의존성과 측정 소스를 전후 확인했고 진행 중인 계산의53개 소스를 보존했다.

| 범위 | 기준 wall / CPU초 | 상세 계측 wall / CPU초 |
|---|---:|---:|
| 원 입력 열기·전체 preflight | 22.910339 / 22.858963 | 31.531077 / 31.526072 |
| 원 context/격자 index 준비 | 10.137720 / 10.098052 | 13.164350 / 13.163276 |
| 해당 실행 전체 | 33.049444 / 32.958395 | 44.696294 / 44.690214 |

각 실행 RHS0·FD4→4. 이 프로세스 peak RSS47,575,040bytes·nice15다.
기존 nice10 전체 RHS 프로세스는 동시에 계속 실행됐다. 입력/artifact 변경·PG/서버/브라우저 기동은 없다.
OS cache를 통제하지 않았으며 기준 실행이 상세 계측보다 먼저다. wrapper overhead가 포함되므로
두 실행 시간의 차이를 성능 퇴행이나 개선 여지의 정확한 값으로 해석하지 않는다.

## 실제 상세 관측과 코드 경로

| 관측 함수 | 호출 수 | 포함 wall초 |
|---|---:|---:|
| bounded 원본 `_read` | 3,369 | 0.571008 |
| duplicate-key/nonfinite 검사를 포함한 `_json` | 3,370 | 9.113643 |
| 단위/배열/원값 정규화 `_normalise` | 432,658 | 13.825161 |
| 원 입력 `_canonical` | 147,926 | 10.720141 |
| 기록 chain `_chain` | 143,431 | 4.562895 |
| UTC 해석 | 911,254 | 2.432667 |

위 포함 시간은 중첩되므로 합산하지 않는다. 영수증의 exclusive도 **관측한 직접 자식**만
차감한 값이며 모든 하위 비용의 완전한 분해가 아니다. `_read` 시간은 byte 읽기 범위이고
SHA·schema/QC 전체를 포함하지 않는다.
입력 열기에서 root1회/블록2,245회·229,808,998bytes,
context 준비에서 블록1,123회·115,089,617bytes를 실제 읽었다.
이는 고유749블록/113,920,841bytes와 구분하는 반복 I/O다.

[원 `_preflight`](../backend/app/crop_cycle_input_stream.py)는 각 stream의 chain·시간/clock을
검사한 다음 원 boundary 합집합을 다시 순회한다. [원 `prepare_context`](../backend/app/crop_cycle_stream_execution.py)는
같은 원 격자를 페이지로 다시 순회해 index를 만든다. reader는 각 stream 한 블록만 cache하며,
블록을 새로 읽을 때 JSON·정규화·canonical 동등성을 다시 확인한다.
[현재 농장 결합](../backend/app/crop_cycle_farm_binding.py)은 `_input`에서 cache/seen을 비우고
원 preflight를 다시 수행하며 `_bind` 앞뒤에 이를 호출한다. 이 농장 경로의 추가 시간은 이번에 측정하지 않았다.

반복 JSON·정규화·canonical 검사의 비용을 줄일 근거를 얻었다. 현재 권리·등록은 매 조회에 새로
검사해야 하고, 이전 검토는 동일한 원 bytes·전체 chain/clock/grid·프로필/코드에만 적용할 수 있다.
영수증은 QC 생략, 임의 cache/서명 증명, reader 판본 호환성을 승인하지 않는다.
다음 집중 수정은 [기존 조회/복원 수용 기준](../contracts/crop-cycle-burden-v1.md)을 유지하고
코드 SHA에 결합된 input root/manifest·과거 재현을 별도 확인해야 한다.

## 보존·남은 작업

영수증 관측 `2026-10-06T07:32:09.314481+00:00`, SHA256
`c06bb3e3da64c8fc37557c199fc04d11c799ae9793b22685e156254761cfff89`.
private 로그 SHA256 `ee3b018880ac700f246650d378f73f50c1dc53bb70fccd2edf9986723a0e73f0`.
측정 실행과 원 context 대사를 확인했다. 전체 backend/web/browser 시험은 실행하지 않았다.
전체166일 계산과 농장/공개 page/3D 수용은 남아 있으며 checkbox를 변경하지 않는다.
실제 품종·독립 국내 검증 자료 채택0건, G0–G4 `not_assessed`, 생산 예측·추천은 보류다.
