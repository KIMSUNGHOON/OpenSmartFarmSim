# 저장 작물 연구 결과 조회 — 구현 기록

상태: **로컬 합성 연구 조회 API 소프트웨어 수용**, 2026-10-04.
[계약](../contracts/api-crop-replay-v1.md)을 먼저
작성하고 새 모듈 부재의 `ModuleNotFoundError`(1 collection error/0.73초)를 확인했다.

## 실제 조사/설계 실행

기존 Codex CLI 세션 `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의
2026-10-04T12:44:33.373Z turn_context는 model `gpt-6.1-sol`, effort `xhigh`,
현재 workspace를 확인한다. 이 동일 세션에서 계약/코드 판단·수정을 수행했다.
재귀 CLI는 실행하지 않았다. 이는 개발 실행이며 제품의 독립 CLI/G1/G4 증거가 아니다.

## 구현과 공개 경계

`api_crop_replay.py`는 같은 농장/result ID로 검증된 불변 저장 결과를 한 번 읽고
상태·시계열·관리 제거 사건·해시·고정 수치 hold를 typed 응답으로 투영한다.
모든 공개 quantity의 단위·유한 수·완료/실패 상태 경계, UTC와 시간 순서,
sample/output_times 동일성을 검사한다. 최초 DB 저장 시각의 KST offset은 UTC로
변환해 같은 순간을 유지한다. profile/입력 원문, forcing/private source ID,
테넌트/권리 원문/비밀 키·서명은 응답에 없다. API는 생장 적분을 재실행하지 않는다.

명시적 `crop_result_store`를 기존 `create_app`에 연결하고, 기존 표준 runtime에는
기본 None인 factory 하나를 추가했다. 양쪽의 같은 jobs/principal/농장 바인딩을
검사한다. 기본 정책 false이면 이 factory를 요구하지 않으며, true에서는 정확한
factory/실제 권한/표가 필요하다. 새 패키지·큐·서비스·Compose는 추가하지 않았다.

공개 typed 모델은 [Pydantic 모델/extra 검사](https://pydantic.dev/docs/validation/latest/concepts/models/)와
[FastAPI response_model](https://fastapi.tiangolo.com/tutorial/response-model/)의 공식
계약을 대조했다. 응답 validation/filter는 농장 권리나 G0–G4 승인을 대신하지 않는다.

## 실패와 수정

운영자 구성의 실제 앱 기동 회귀는 별도 `9f9195c`로 수정했다
([실패/수정 기록](crop-result-storage-implementation.md#후속-운영자-파일-회귀-수정-2026-10-04)).
그 커밋의 [앱 CI 37203321687](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37203321687)은
기존 앱/수집/조사 RPC 세 경로와 재시작·권한 변경 거부·정리를 통과했다.
새 API 소프트웨어 수용을 증명하는 실행은 아니다.

저장 artifact의 응답 대조/닫힌 OpenAPI 집중 15개는 1.29초에 통과했다.
첫 실제 PostgreSQL 집중 실행은 **312 passed / 3 failed /171.74초**였다.
시험이 광합성 입력을 그대로 두고 buffer만 0으로 만들어 기대했던 hold가 생기지
않은 점, 기존 권한 회귀 시험에 새 result ID/필수 query가 누락된 점을 수정했다.
추가 위치 진단은 시험의 미준비 artifact root로 인한 FileNotFoundError를 확인했다.
제품의 기존 저장소 요구는 유지하고 시험 준비에서만 root를 provision했다.
고갈 hold는 상태가 음수가 되기 전 정확히 0인 buffer에서 발생했으므로 실패 상태를
저장된 진단과 직접 대조했다. 같은 세 반례 재실행은 1 passed/2 failed/98.14초였고
그 원인·기록도 보존했다. 수정 뒤 HTTPS 단독 1개는 56.55초에 통과했다.

## 최종 수용과 사용자 확인 자료

최종 실행은 **316 passed / 0 skipped / 194.11초**다. 구분은 새 API 18개,
운영자 구성 52개, 기존 runtime 40개, OpenAPI 60개, 생장 수식 146개다.
실행 구간은 2026-10-04T13:07:48.069659Z~13:11:04.280620Z이며 전체 runner
시간은 196.21초(임시 PostgreSQL 준비/정리 포함)였다.

```bash
nice -n 10 python3 /tmp/ossf-run-crop-api-tests-20261004.py \
  tests/test_api_crop_replay.py tests/test_operator_config.py \
  tests/test_api_runtime.py tests/test_api_openapi.py \
  tests/test_crop_growth_rates.py tests/test_crop_photosynthesis_domain.py \
  tests/test_crop_growth_integration.py
```

runner는 기존 사용자 PostgreSQL 16.15 바이너리로 임시 loopback/SCRAM 한 개를
기동했다. shared_buffers=32MB, max_connections=24, 병렬 worker=0이다.
기존 SQL/HTTP 제한을 늘리지 않았다. 실제 TLS 서버는 join됐고 임시 DB/role/
비밀번호 파일을 제거한 뒤 `pgrep -a postgres`가 실행 프로세스 없음으로 끝났다.
시험 TLS/계정/권리 제공자는 합성이며 독립 운영 자격증명이나 실제 동의가 아니다.
로그 SHA-256은 `d9f5fe98b138f621bded7ee7798ca3daec736c31f5c8f181ef493497c37f6313`다.

[실제 HTTPS 응답/검증 artifact](artifacts/api-crop-replay-reference-20261004.json)는
10개 전체 응답·순서별 시간·코드/목록/실패 로그 hash·개발 CLI 문맥을 보존한다.
상태는 401,403,404,200,200,422,422,422,422,200이며 정상 재조회 세 응답은
6개 sample/모든 단위·manifest까지 동일하다. 최대 본문 응답 시간은
**5.580219초**, 기존 클라이언트 제한은 30초다. 동시 처리량/큰 작기 성능의 증거는 아니다.
result ID는 `crop-result-v1:3289adab5b96bcdcdb01176edf5f3c61c6e3efd253caef9b7cba3f9ce7bd561d`다.
결과를 담았던 시험 DB는 정리했으므로 이 artifact ID가 현재 운영 DB에 존재한다고
주장하지 않는다. 실제 별도 프로세스 불변 재조회는 선행 저장 단계의 수용 증거다.

권한 부족·타 계정·다른 농장 crop/등록 hash·중복/추가 query·서비스 없음·예외
세부 비표시, 실제 source/program 권리 철회·DB payload 변조 거부, 투영 중 계정
권한 철회도 확인했다. GET 중 적분을 호출하면 실패하는 시험을 통과했고
새 승인 thermal Run은 0건이었다. `app.api_openapi --check`도 통과했다.
전체 hosted backend/새 앱/브라우저는 이 로컬 집중 실행의 수용 범위 밖이다.

최종 검토에서 관련 문서의 상대 파일 링크 761개·누락 0개와 artifact의 실제
코드 hash/316개 수집 목록을 확인했다. `git diff --check`와 고정 OpenAPI 일치
검사가 통과했다. 작업 목록에서는 `api-crop-replay`만 수용으로 바꾸고 다른
자료/관문/3D 작업의 미완료 상태를 유지했다.

## 외부 의존성과 다음 산출물

실제 Axiany 전체 작기의 forcing/초기조건/관리 QC·권리 감사와 국내 독립 자료
확보는 별도 미완료다. 국내 자료는 0건이며 합성 프로그램과 문헌 계수는
등록 농장 품종을 검증하지 않는다. 이후 같은 결과 ID/UTC sample을 사용하는
`web-crop-replay`의 표·그래프·성장 3D가 다음 사용자 산출물이다. 계산하지 않은
키/착과수/숙기/생과 kg/구매 에너지/미래 마진/추천을 표시하지 않는다.

## 앞선 판본의 terminal hosted 수용 — 2026-10-04

`d251df9`의 [전체 backend](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37205032293)는
6분할 2,671개·별도 UID 4개·같은 전체 목록/마지막 집계와 모든 DB/비밀번호 정리를
통과했다. 같은 판본의 웹·C0·앱 조립·작성 API도 성공했다. 저장/API 소프트웨어의
전체 회귀 수용이며 뒤의 성장 화면 변경·실제 작기/품종·제품 관문은 별도다.
