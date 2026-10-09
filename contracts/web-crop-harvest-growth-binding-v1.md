# 저장 수확과 생장 범위의 결속 — v1

2026-10-09 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
`crop-harvest-view`의 첫 자식은 화면이 사용할 순수 결속 함수다. 선행은
[수확 SDK](web-crop-harvest-client-v1.md)와 기존 계산 생장 SDK/범위 선택이다.
core5파일은 이 계약, `web/src/harvestGrowthBinding.ts`, 그 단위 시험,
두 기존 SDK의 summary/page 대사 함수 공개다.

## 수용 기준

- 기존 닫힌 DTO 검사를 재사용해 계산 summary/선택 sample page와 수확 summary/page를
  검사하고 각 summary/page의 전체 공통 identity를 대사한다. 페이지는 각각 최대64행이며
  현재 생장 page가 없으면 저장 frame을 만들지 않는다. 새로운 HTTP/전체 배열 수집은 없다.
- 농장 네 필드와 부모 result ID, 원 payload/input root/artifact/상태를 대사한다.
  수확의 `math_manifest_sha256`는 계산 조회의 `context_sha256`와 같아야 한다.
  이 등식은 서버의 [원 manifest hash](../backend/app/crop_harvest.py)와
  [공개 계산 투영](../backend/app/api_crop_cycle_calculation_replay.py)이 같은 canonical manifest를
  검사하는 기존 계약에서 온다. 브라우저는 Python 직렬화/hash나 HMAC을 재구현하지 않는다.
- terminal 행은 원 두 sample index와 시작/끝 UTC를 보존한다. 읽은 sample index/UTC와
  모순되거나 원 sample/event 개수를 벗어난 위치, 작기 밖의 시간은 거부한다.
  hold에서는 마지막 확정 sample 이후의 제거를 연결하지 않는다.
- 3D용 frame은 **정확히 같은 UTC의 현재 저장 sample**만 참조한다. terminal은 구간 끝의
  저장 상태와 연결하며 그 상태가 제거 직전 상태라는 주장을 하지 않는다. 명시 사건의
  before/after를 3D sample로 바꾸지 않는다. 현재 범위에 같은 UTC가 없으면
  `outside_loaded_samples`로 표시하며 전체 결과에도 없다고 단정하지 않는다.
- 원 행/수량/단위/정확 분수·배정 목적·미배정·관측 비교와 전체 저장 summary를 그대로
  반환한다. 현재 페이지 범위/부분 여부는 전체 summary와 구분한다. 합성/미평가/hold를
  보존하고 생과·형상·숙기·등급·판매·수익을 계산하거나 추정하지 않는다.
- 다른 농장/부모/해시/상태·같은 시각의 잘못된 index·부분 범위·일치/불일치 사건·hold와
  원 입력 불변을 집중 검증하고 기존 SDK/웹 전체·타입/빌드를 확인한다.
  시험에서 서로 다른 소유 fixture의 metadata/시각을 맞춘 사례는 형식 시험으로만 표시한다.
  실제 같은 DB/HTTPS/WebGL 증거로 사용하지 않는다.

## 후속

이 자식 수용 뒤 현재 범위/취소·권한 실패 제거를 포함한 수확 표와 기존 3D 화면을 연결한다.
실제 DB/API/대표 WebGL·전체166일 질량 부하 수용 전 `crop-harvest-view`와 replay 부모는 미완료다.
실제 품종 계수·독립 농장 자료·G0–G4/생산·마진 예측/추천 보류는 유지한다.
