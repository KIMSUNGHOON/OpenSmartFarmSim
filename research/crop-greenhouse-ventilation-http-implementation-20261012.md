# 환기 작물 결과의 보호 HTTP — 2026-10-12

상태: **로컬 수용**. [계약](../contracts/api-crop-greenhouse-ventilation-route-v1.md)과 [기계 영수증](artifacts/crop-greenhouse-ventilation-http-reference-20261012.json).

## 변경과 사용자 범위

`GET /v1/crop-greenhouse-ventilation-research-results/{result_id}`를 기존 인증·농장 graph에 추가했다.
새 signed 결과의 요약·생장 시점·관리 사건을 현재 권리 아래 원 bytes로 반환한다.
기본 runtime은 비활성이다. 별도 명시 조립 전 인증된 새 경로는503이며, 잘못된 query/store/farm/principal 조립은 시작 전에 거부한다.
GET 본문·잘못된/중복 query·범위는422, 권한401/403, 없는 결과404, 증거 보류422, 미구성/예상 밖 오류503이다.
응답은 no-store·2MiB 이하이고 현재 query/projection 판본·코드 해시를 헤더에 둔다.

새 public DTO 이름에 Ventilation 접두사를 붙여 기존 OpenAPI 이름 충돌을 피했다.
기존56경로와262스키마의 내용은 모두 동일하다. 새 경로/51스키마만 추가했다.
같은 불변 입력의 기존/새 projection을 함께 읽는 별도 검사에서 요약·생장·사건 bytes가 정확히 일치했다.
이름 변경으로 수치 방정식·입력·저장 결과/서명을 재발급하지 않았다.

## 검증

| 범위 | 원 도구 handle | 검사 | 종료 | 전체 guard 시간 |
| --- | ---: | ---: | ---: | ---: |
|동일 불변 입력의 namespace 전후 응답|94610|1|0|2.440초|
|실제 SCRAM/ASGI의 현재 권리·계정·연결/취소|4520|5|0|289.388초|
|실제 SCRAM/검증 TLS의 새·기존 정상/보류|30985|4|0|308.130초|
|새/기존 ASGI·OpenAPI·원 수치 형식|85085|222|0|30.895초|

고유232개다. 실제 TLS4개와 실제 DB/ASGI 경계5개를 구분하며, 모든 검사가 TLS에서 실행됐다는 주장은 하지 않는다.
원108상태·25연속/6사건 장부·10수지·환기 진단·마이크로초 UTC는 선행 형식 검사와 실제 DB 응답 대사로 확인했다.
정상/보류 각각 요약·생장·사건이 동일 query의 원 bytes와 일치하며30초/2MiB 안이다.
조회9수치 entrypoint 호출과 DB 추가 행은0이다.
직렬화 중 입력 이용권·검토 승인·농장 원천 철회9조합, 계정 만료3응답을 차단했다.
잘못된 요청/본문·인증·조기 disconnect는 query 전에 거부한다. 없는 결과/타 tenant도 거부한다.
취소·송신 실패 뒤 현재 principal/조회 worker를 정리하고 같은 결과를 다시 읽으며 원 FD를 유지했다.

## 보존과 실패 기록

모든 최종 guard는 원 도구 terminal을 수집했다. FD4→4, 소유 non-zombie/PG/passfile/임시 PG 잔여0이다.
원본2,148·기존 계산248파일·frozen source1,911/자산171·prior UI171/현재172자산·source194·현재 권리/안내와4보호 root를 유지했다.
공유5파일의 전후 SHA를 별도 기록했다: API의 명시 인자/route 설치, 새 DTO/test namespace, 기존 OpenAPI inventory/query fixture, 생성 snapshot이다.
기존 계산 baseline251 중3파일은 위 명시 변경이고 나머지248은 동일하다.
HTTP 검증4묶음의 최대 단일 RSS198,569,984bytes/보호 포함 합957,722,624bytes로512MiB/1GiB 안이다. 두 사용자 주소는200이며 새 모델 배포/서버 재시작은0이다.

첫 inventory 검사에는 새 ID/필수 농장 query가 빠졌고, DTO 검사 한 곳은 옛 Point 이름을 사용했다. 시험 fixture를 수정했다.
실패 출력/성공 capture를 전부 표시하던 private harness는4MiB 로그 제한으로 종료됐다. 실패만 표시하도록 바꿨으며 마지막 동일222검사는 정상 종료했다. 실패 원 handle은 영수증에 남겼다.
독립 생성 fixture끼리의 응답 SHA 비교는 같지 않아 수용 증거로 사용하지 않았다. 해당 진행 문구를 즉시 정정하고 동일 불변 입력의 전후 동등성 검사로 확인했다.

## 다음 단계와 보류

[진행 화면](http://localhost:5174/#crop-execution)은 API 검증 완료/다음 자동 계산·3D와 남은3–6집중시간을 표시한다.
원71514 실제 브라우저/guard0에서 인증 없이 이 내용을 확인했다. 390px overflow0·API쓰기0·pageerror0이며 조회 HTTP200/no-store·main/published bytes가 동일하다. 브라우저 포함 최대 단일246,263,808/합977,776,640bytes도 한도 안이다. 3D 장면 자체를 새로 검증한 것은 아니다.
다음 한 단계는 **명시 runtime 조립**이다. [현재 loader](../backend/app/crop_climate_joint_operator_config.py)는 새 flag True를 거부하고, [runtime](../backend/app/api_runtime.py)에는 새 query/store factory가 없음을 코드에서 확인했다.
수용: 별도 명시 판본/기본 비활성·같은 jobs/farms/principal·고유한 기존 키/현재 권리·실제 SCRAM/TLS의 동일 정상/보류 응답·잘못된/섞인 설정 거부·기존 loader/경로/두 UI 보존.
이어 새 작업 판본/자동 worker·확정 진행/저장 결과→typed web/같은 UTC3D→실제 사용자 브라우저 적용을 진행한다. 기존 작업표·서명 저장·self-hosted stack을 재사용한다.
작업자/typed web/같은 UTC3D2–4시간, 사용자 검증·적용1–2시간의 합3–6은 잠정 집중 작업량이다. 전체 제품 완료 날짜는 아니다.

현재 native Codex CLI `gpt-6.1-sol / xhigh`의 실제 turn context/원 행 SHA를 기록했다. 재귀 CLI0이다.
전체 CI/remote·새 명시 runtime/worker/사용자3D·전체 작기 성능은 미실행이다.
실제 농장 Run·독립 국내 자료0, G0–G4 not_assessed, 실제 품종 생산·구매 자원·미래 마진/작물 순위는 보류한다.
실제 자료 확보와 G2/G3 검증은 계산 개발과 독립된 의존성으로 유지한다.
