# 저장된 기관·50과실 구획의 성장 연구 3D 수용

2026-10-05 KST. [계약](../contracts/web-crop-coupled-replay-v1.md),
[수용 영수증·코드/화면 해시](artifacts/web-crop-coupled-replay-reference-20261005.json).
현재 Codex CLI turn `2026-10-04T22:52:33.768Z`의 `gpt-6.1-sol / xhigh`를 확인해
구현·판단했다. 재귀 CLI와 새 패키지/프레임워크는 사용하지 않았다.
수용 범위는 **합성 연구 결과의 로컬 소프트웨어 경로**다.

## 사용자가 확인할 산출물

- [실제 SCRAM/HTTPS 데스크톱](artifacts/coupled-crop-replay-desktop.png),
  [모바일](artifacts/coupled-crop-replay-mobile.png),
  [확인된 과거가 있는 보류](artifacts/coupled-crop-replay-past-hold.png),
  [빈 보류](artifacts/coupled-crop-replay-empty-hold.png).
- [기록 합성 데모의 3D·원값](artifacts/coupled-crop-replay-recorded-demo-geometry.png).
  이는 아래 첫 저장 시험에서 기록한 공개 합성 응답의 별도 재생이며 운영 DB 목록이 아니다.
- `08 성장 연구 3D`에서 **저장 결과 판본 v2**를 선택하면 결과 ID·등록 farm/crop으로
  저장 결과를 읽는다. v1 조회와 기존 토큰의 메모리 보관을 유지한다.

512개 sample의 최대 8페이지를 순서대로 모두 확인한 뒤 고정 척도와 장면을 표시한다.
페이지/시점 진행과 취소를 표시하고, farm·계정·ID 변경/거부·늦은 응답에는 이전
결과/장면/manifest를 지운다. 사건은 필요할 때 별도 8개 페이지로 읽으며 거부 시
이전 결과까지 지운다. 한 페이지의 30초를 전체 페이지의 완료 기한으로 표현하지 않는다.

한 저장 인덱스/UTC를 기관 5개·LAI·총 과실 C, 두 50개 배열, 12개 누적량/두 수지,
표·시간 그래프·C/N 그래프·3D가 공유한다. HTML은 서버 원 숫자와 단위를 표시한다.
3D는 잎 한 면 삼각형 면적과 단위별 고정 scale의 C/N 100개 mesh다.
영 값은 숨겨진 영 높이이며 안전한 GPU 표현이 불가능하면 HTML을 유지한다.
서버의 생장/수지·총 과실 C를 다시 계산하지 않는다. 재생은 다음 저장 인덱스만 선택한다.

`mg_CH2O/m2_floor`는 생과 kg가 아니고 `fruits_equivalent/m2_floor`는 실제 열매 개수가 아니다.
배치·패치·막대의 크기/색은 실제 키·착과 위치·숙기·수확량이 아니다.
보류는 과거 output만 탐색하며 소수 초 평가/마지막 확인 상태를 별도 진단으로 표시한다.
빈 보류에는 정상 수치 장면이 없다. terminal/관리 제거도 실제 수확·판매로 이름 붙이지 않는다.

## 통과한 검증

| 검증 | 실제 결과 |
| --- | --- |
| 집중 단위 | 페이지/geometry·기존 request/canopy **129 passed**, 4파일·단일 worker·6.37초. CLI 출력으로 확인했고 별도 JSON 로그는 없음 |
| Chromium | 새 화면 9개 + 기존 화면 10개, **19 passed / 0 failed / 0 skipped**, 60.248초·단일 worker |
| 실제 저장 → HTTPS/Bearer → WebGL | **1 passed**, PostgreSQL 16.15/SCRAM·125.407초, 완료 6 sample·과거 hold 1 sample·빈 hold |
| 실제 화면 대사 | 9번 프레임 확인·C/N 900개 mesh 값/단위/구획/height/y/visibility·두 그래프/표·기관/LAI·같은 ID/UTC |
| 잎 면적 | 실제 한 면 삼각형 면적의 최대 절대 오차 **8.881784197001252e-16** |
| 현재 권리/계정 | 응답 `200,200,200,200,422,403,200`·성공 본문 5개, 최대 전체 본문 9.5357초·no-store·재연결 |
| 변하지 않는 저장/정리 | 결과 행 3→3·GET 재적분 금지·브라우저 오류 0·서버 thread/frontend 종료·임시 DB/역할/password 파일 제거 |
| 접근성/장애 | 512페이지 전체성·부분 결과 비표시·취소/늦은 응답·혼합 manifest/사건 거부·키보드·모바일/320px·200% 글자 확대·reduced motion·실제 WebGL loss/restoration·HTML fallback/양수 underflow |
| 빌드 | typecheck/Vite build 성공. 기존 SVG chunk 520.20kB의 500kB 경고를 유지 |
| 기록 합성 로컬 데모 | 완료/과거/빈 보류 3개 상태·기록 응답 동일성·200/403/404·no-store·브라우저 3 context 정리 |

실제 RED는 v2 선택 화면 부재였다. 이어 구획 번호와 option value가 겹친 시험의
모호한 선택을 `{value:'49'}`로 고쳤고 모바일 표의 외부 폭을 제한했다.
확대 검증은 CSS zoom으로 390px을 195px처럼 만드는 임시 시험 대신
320/768/1536px에서 200% 글자 확대와 키보드/표 사용을 확인한다.
512개 긴 UI 사례는 cardinality shape 시험이다. 실제 DB/브라우저 생산 계산이 512개였다는 뜻이 아니다.
별도의 선행 API/CPU 검증은 실제 512/128 페이지·24시간 artifact를 해당 영수증에서 확인한다.

```bash
cd web
npm run typecheck
npm test -- --maxWorkers=1 src/coupledCropGeometry.test.ts src/coupledCropReplay.test.ts src/cropGeometry.test.ts src/api.test.ts
npm run test:browser -- coupled-crop-replay.spec.ts crop-replay.spec.ts
npm run build
```

실제 DB 시험은 `backend/tests/web_crop_coupled_replay_smoke.py`를 독립 저메모리
loopback SCRAM DB에서 실행했다. hosted 작성 browser 경로에도 이 시험을 추가했다.
이는 작물 기능의 직접 검증이며 새로운 일반 운영 기반을 확장하지 않는다.
로컬 Docker Engine/새 hosted 이미지·CI는 실행/수용하지 않았다.
기준 e70a7f2의 C0·Web·Application·Authored는 성공이며 Backend 전체 집계는 진행 중이다.
이 기준 CI가 새 UI 변경을 검증한 것으로 표시하지 않는다.

## 로컬 기록 합성 데모 열기

```bash
cd web
npm run demo:3d
```

기본 주소 `http://localhost:5173`에서 내부 시험 연결 토큰
`synthetic-demo-token-only`를 입력하고 `08 성장 연구 3D` → `v2`를 선택한다.
서버 조회·시점·그래프·3D 컴포넌트는 제품 코드지만 응답은 명시적 로컬 기록이다.
데모와 운영 API/TLS 구성은 함께 켤 수 없다. 데모는 실제 저장 목록이나 현재 농장 자료가 아니다.

| 조회 입력 | 기록 데모 값 |
| --- | --- |
| 결과 ID | `crop-result-v2:23e61b93d37a59925c9115458688f0d757484d470ede6a9d79d26dd3ded60cbe` |
| 농장 ID | `farm-1` |
| 농장 판본 | `r1` |
| 등록 SHA-256 | `0d4c0563d537e57a3e0f82dc5449253eaafe5b2ecdbaabfbc68a151746f86a10` |
| 작물 ID | `crop-1` |

첫 데모 원본은 첫 실제 저장 시험의 기록이다. 최종 수용 시험의 세 ID와 시각은 영수증에 별도로 남겼다.
시험 DB는 제거됐으므로 어느 ID도 살아 있는 운영 저장 기록이라고 안내하지 않는다.

## 12ui 디자인 적용·한계·비용

12ui-design으로 후보 4개를 직접 보고 C를 선택했다. responsive HTML/LayerDoc의
시각화/기관 상태·두 C/N 도표·정확한 값 표 구조와 색/간격을 적용했다.
상태는 C에서 branch했고 완료/과거/빈 hold의 localhost 화면을 원 승인 LayerDoc에
`12ui improve --target`으로 대사했다. main 23.0%, 빈 hold 21.5%, 과거 hold 21.8%의
낮은 anchor overlap이며 **pixel fidelity를 수용했다고 보고하지 않는다**.

생성안의 N 합/밀도·지도/설정·placeholder ID/수치·확정 생산 문구를 채택하지 않았다.
식물/그래프 raster는 실제 Three/ECharts로 대체했다. `clean-0` 배경에도 예시 글자와
그림이 남아 있어 소프트웨어 scope 문구와 겹쳤으므로 배포하지 않았다.
원 export의 표면색과 유효 cutout 4개만 사용했고 추가 spinner/과실 장식/가짜 화면을 넣지 않았다.
빈/과거 LayerDoc 파생본의 누락 raster도 모델의 값으로 그리지 않았다.
이것은 사용자 요구/PROJECT_SPEC의 계산·주장 경계를 유지하기 위한 기능 수정이다.
새 폰트나 원격 loader를 추가하지 않았다.

과거 hold의 생성 화면/HTML은 완료됐지만 12ui의 추가 prototype 조합은
`Holding composition has no content area inside 1536x1024`로 실패했다.
제품은 그 prototype을 사용하지 않으며 실제 React 화면/브라우저 검증은 통과했다.
나머지 스타일 제안은 위 기능 경계를 보존해 검토했고 전체 kit는 private `/tmp`에 유지한다.

원 kit의 spend ledger는 다음과 같다.

| purchase | stage | invocation | price ceiling |
| --- | --- | --- | --- |
| `crt-8dcaabeedc443b01e12adb343e9da905ea29381c` | draft | `improve` pid 1099416, started 2026-10-04T22:35:05.755Z | $0.12 (stage ceiling) |
| `28036367-0361-434a-a3af-8ab73db2bedd` | convert | `improve` pid 1100364, started 2026-10-04T22:37:50.867Z | $0.55 (stage ceiling, shared by 2 purchases) |
| `2b0b0420-3da4-45b2-926b-5ec934016ed9` | convert | `improve` pid 1100364, started 2026-10-04T22:37:50.867Z | $0.55 (stage ceiling, shared by 2 purchases) |

3 purchases across 2 runs. Ceilings are per stage, not per purchase; the distinct ceilings above total $0.67.
추가 empty branch `crt-07104048cd8a60fb220704b699b6848ebfb0ce35`의 기록 ID는
`4ef5f1ed-b009-48b6-a31b-70ad7bd74249`, `cd9410f5-0c4d-431b-aad1-83e6007bf102`,
`1ea3f74a-9b7b-49f0-8fb3-228b6d909b1a`다.
과거 branch `crt-acde3e589ba879515e75504a10f4e8d1d2d86961`은
`964f581a-480e-4bce-a3cc-cc419511f547`, `f82ad30e-4f38-430d-90fe-eb888b668d5d`,
`93cc6a24-c351-4c1a-a1e9-fe9d289a18fb`를 기록했다.
LayerDoc 파생/네 closeout kit는 새 구매 없이 완료됐다.
read-only `12ui spend`의 일곱 이름 있는 branch/변환 기록은 sponsored·chargedMicros 0이며
provider cost는 비공개다. 네 package ID는 검색 기간에 charge row가 없었다.
미반환 charge/provider cost를 0으로 간주하거나 ceiling을 실제 청구액으로 합산하지 않는다.

## 남은 범위와 다음 작업

운영 기반 완료 범위는 d19f7c0에 고정한다. 국내 독립 자료/실제 forcing 채택/실제 작물 Run은 0이며
전체 작기·자동 착과/startup·실제 방울토마토 품종·생과 kg·물/성분·구매 에너지·경제/순위와
G0–G4는 보류다. 새 UI의 원천/계수 검증을 디자인이나 합성 시험으로 대신하지 않는다.

다음은 [초기/자동 착과 정책](../contracts/crop-fruit-startup-policy-v1.md)의 원식/초기 상태·
W1/S/RGR·빈 tail/생식기 이전 근거와 독립 보존/hold 사례를 정리하는 작은 단계다.
이미 고정한 문헌/배분·짧은 적분 근거를 재사용하는 조사/정책에는 집중 2–4시간을 잠정 배정한다.
자료가 충분하면 다음 순수 startup 모듈을 따로 계획한다. 국내 접근·측정 확보와 병행하며,
실제 생산/미래 마진·추천 완료 날짜는 독립 작기·계량·판권/검증 자료 확보 전에는 산정하지 않는다.
