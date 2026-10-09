# 저장 생장·수확 결과 목록의 서버 자식 — 2026-10-09

상태: `crop-result-catalog-metadata`만 로컬 수용. 상위 U1·보호 API·SDK·목록 화면은 미완료다.
[계약](../contracts/crop-result-catalog-v1.md)과
[원 종료·자원·소스/CLI 증거](artifacts/crop-result-catalog-metadata-reference-20261009.json)를 따른다.
판단은 현재 native CLI `gpt-6.1-sol / xhigh`에서 수행했고 CLI를 재귀 실행하지 않았다.

## 구현과 사용자가 받게 될 기능

[서버 목록 모듈](../backend/app/crop_result_catalog.py)은 현재 선택한 작성 농장/판본·등록 hash·
crop_id에서 verified 생장 또는 등록 수확 metadata를 찾는다. 같은 계정/농장 조건과
현재 등록·display 권리·HMAC/hash·원 부모 결속을 검사하고 저장 시각/ID의 keyset 페이지를 반환한다.
기존 작성 농장 목록·결과 조회를 재사용하며 새 DB/role·queue·증명·결과는 만들지 않는다.

목록에는 완료/hold, 원 저장 시각, 생장 연구/판본·작기/시점 수 또는 수확 부모/행 수가 있다.
원 payload/서명·key·credential은 반환하지 않는다. 결과 선택 때는 기존 현재 query가
파일/수치·원 서명·현재 권리를 다시 검증해야 한다. metadata 목록이 파일 가용성이나 관문 승인은 아니다.
현재 미리보기의 수동 ID 입력은 이 단계로 바뀌지 않았다. 보호 API→SDK/목록 선택→실제 3D/수확의
후속 자식이 끝나야 사용자가 목록에서 결과를 열 수 있다.

## 통과한 검증과 범위

- [집중 시험](../backend/tests/test_crop_result_catalog.py): 원26744 종료0,
  **30 passed / 0.78초**. 닫힌 필터/limit/cursor, UTC·동률 키/SQL 바인딩,
  lookahead/빈/마지막 페이지·스냅샷/권한 변경과 반환값 변조 격리를 확인했다.
- [실제 보존 DB 시험](../backend/tests/crop_result_catalog_preserved_smoke.py):
  별도 SCRAM 복원 DB에서 원48842 종료0, **1 passed /57.81초**, 준비/정리 포함 **58.297초/600초**다.
  원 생장 3시점/3사건과 수확 5행의 metadata 각1건을 조회했다.
  생장 저장 시각은 변조하지 않은 원 dump의 복원 레코드와 비교했고, 수확은 선행 보존 매니페스트의
  독립 `original_record.recorded_at`와도 비교했다. 부모 보존 매니페스트에는 생장 시각 필드가 없었다.
- 첫 실제 시험 원56104는 그 생장 시각 필드가 매니페스트에 있다고 가정해 `KeyError`/종료1이었다.
  비교 기준만 수정했다. 실패 DB는 정상 정지했고 실패 기록은 보존했다.
- 두 kind에서 같은 시각/ID cursor 이후 빈 페이지, 다른 계정·등록·작물,
  현재 scope/display 철회·투영 뒤 철회·실제 복원 DB HMAC 변조 거부와 복구를 확인했다.
  부정 시험은 소유 복원 DB/복사한 제어 파일만 바꿨다. 원 자료/미리보기 제어 파일은 보존했다.
- 목록은 실제 생장 **5.440940초/786bytes**, 수확 **4.753369초/764bytes**였다.
  실제 DB는 각1건이다. 다수 결과·동률/여러 페이지의 실제 DB 용량과 30초 transport는 후속 API 수용에서
  별도 확인하며 이 값으로 20항목의 운영 성능을 승인하지 않는다.
- 원 파일·수치 조회, 입력/결과 생성, RHS·게시·증명 발행을 금지한 guard 아래 **0호출**이다.
  보존 자료/입력·artifact **60 source entries 동일**, FD **12→12**, 소유 복원 PostgreSQL 정지를 확인했다.
  기존 전체 producer 고정3파일은 isolated 원본과 같고 전체/미리보기 프로세스도 유지됐다.
- 0.1초/560표본에서 controller/시험/복원 DB와 실행 중인 전체 producer·미리보기/두 DB를 포함한
  소유 RSS 합 최대 **810,688,512bytes**, 단일 최대 **140,951,552bytes**로 지정1GiB/512MiB 안이다.
  표본 관측이며 일반 운영/브라우저/전체 결과 용량 수용이 아니다.

```sh
PYTHONPATH=backend nice -n 19 backend/.venv/bin/python -m pytest -q backend/tests/test_crop_result_catalog.py
# 별도 소유 보존 매니페스트·해시·stage를 환경변수로 지정한 수동 실제 DB 시험:
PYTHONPATH=backend nice -n 19 backend/.venv/bin/python -m pytest -q --tb=short \
  backend/tests/crop_result_catalog_preserved_smoke.py
```

이 자식에서 전체 백엔드·API/웹/브라우저 시험은 실행하지 않았다.
현재 전체 계산의 live 진행 상태/확정 prefix 3D와 자동 완료 결과 선택은 미구현이다.
다음은 같은 query/인증/권리의 보호 GET·typed 응답/OpenAPI·no-store·시간/bytes 검사다.
이후 SDK/기존 농장 목록에 결과 선택을 연결하고 실제 DB/API/브라우저 재접속/재시작을 확인한다.
실제 품종/농장 작물 Run/국내 독립 자료0건과 예측/추천·G0–G4 hold는 유지한다.
