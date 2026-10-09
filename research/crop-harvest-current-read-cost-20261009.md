# 전체 수확의 요청 범위 조회와 실제 API 비용 수용

2026-10-09. 조회 core `6195dd9`, 판본 호환 도구 core `bfb038b`.
[계약](../contracts/crop-harvest-current-read-cost-v1.md)과
[불변 검증 영수증](artifacts/crop-harvest-current-read-cost-reference-20261009.json)을 함께 읽는다.
영수증 SHA256은 `f46f22a665c98cb2c6529a7406f9d066d9b6640a1c2cdc83c4dc88883e2ec713`다.
범위는 보존된 합성 전체 수확의 보호 API 조회다. 전체 API/대표 WebGL 부모와 실시간 U3는 미수용이다.

## 변경과 검증 경계

한 수확 요청 안에서 원 `CalculationCurrentCycleQuery.open`을 한 번 유지한다.
원 입력·결과 증거와 custody trace의 전체 시작/끝 검사는 원 코드로 수행하고,
내부 harvest guard마다 실제 부모 서명 행·현재 농장 등록·Scope·표시권·정책/해결자/고지 판본을 확인한다.
복사한 metadata는 요청 범위에만 있으며 종료 뒤 callback은 만료된다. 끝 검사가 성공하기 전에 HTTP 본문을 내보내지 않는다.
원 artifact/registry/부모 query decoder와 생장·수확 계산 코드는 바꾸지 않았다.

과거 storage manifest는 절대 경로의 frozen source를 고정한다. 새 도구의 `--original-source-root` 경로는
별도 실제 Python에서 그 원 helper/manifest/의존성과 보존 파일을 먼저 검증한다.
현재 runtime과의 차이는 storage 의존성 중 `crop_harvest_current_query.py` 한 파일만 허용하고,
새 호환 관측을 별도로 기록한다. 원 manifest/서명/최초 UTC를 수정하거나 결과·증명을 다시 발급하지 않았다.
이 Python은 Codex CLI를 재귀 실행하지 않는다. 판단은 실제 CLI `gpt-6.1-sol`/`xhigh`의 사건 SHA와 함께 기록했다.

## 집중 검사와 작은 실제 DB

- 새 요청 범위19개는 내부 현재 권한/행·농장 변경, 독립 복사/만료, 끝 검사 실패,
  늦은 HEAD/page 변경과 호출자 실패 정리를 검사한다. 초기 fixture의 정책 누락 실패는 보완하고 원 로그를 보존했다.
- 기존 실제 SCRAM 검사 원21850 종료0/174.238초에서 정상6행과 표시 전용 읽기,
  계정·농장·범위·HMAC/HEAD/root/page 및 yield 뒤 변경 거부를 확인했다.
  같은 DB의 별도 Python 둘도 각각 종료0이었다. 조회 재계산/등록/증명0, FD14→14,
  보호 파일19개 제거/잔여0과 schema/role/passfile 정리를 통과했다.
- 새 실제 DB 관측의6행 영수증을 별도로 만들었다. 이전 `88055f22`의 query 관측은 과거 판본으로 거부하되
  원 저장 packet은 유효하게 decode되는지 검사한다. 과거 `3e845e6a`도 원 bytes/hash를 보존한다.
  native와 최종 fixture 수정 사이에 제품 조회·계약·새 범위 검사3파일은 동일하다.
- 최종 원24804 종료0은 새 호환 경계10개를 포함한 **238개/27.96초**, 감독29.393초다.
  허용 파일 외 변경·원본 변조·경로 이탈/누락·실제 별도 validator의 실패 기록과 기존 TLS/HTTP/route를 확인했다.
  native와 다른 fixture 변경을 전체 동일 source라고 보고하지 않는다.

## 같은 전체47,813행의 실제 보호 HTTPS

[정상 전체 writer·독립 Decimal 대사·fresh·root 수용](crop-harvest-full-writer-completed-20261009.md)의
같은 인증 backup/원 artifact를 복원했다. 원70467 실제 종료0/48.635초다.
원 frozen manifest의 별도 validator도 실제0/1.298초이며 허용된 reader 외 차이는 없다.

| 요청 | 완료 wire 시간 | body bytes | 결과 |
| --- | ---: | ---: | --- |
| 전체 summary | 8.823초 | 16,519 | 200, 원 summary 일치 |
| 첫64행 | 10.939초 | 486,219 | 200, 원 행/순서 일치 |
| 마지막1행 | 10.780초 | 9,027 | 200, 원 마지막 행 일치 |
| 권한 복원 뒤 summary | 8.915초 | 16,519 | 200, 최초 응답 SHA 일치 |

Scope403·다른 tenant404·현재 표시권422를 포함해7응답 모두 실제 TLS wire와 독립 ASGI의
bytes/SHA/완료를 대사했다. 요청 중복은 없고 최대 동시 읽기1이다. 각 성공 응답은30초/2MiB 안이다.
과거 [30초 timeout/서버34.619초 관측](crop-harvest-api-cost-20261009.md)은 당시 증거로 보존한다.
이번 관측은 그 보류를 해소하는 새 판본이며 과거 성공 기록을 만들지 않는다.

조회 RHS/수확 생성/등록/증명0, 실제 DB counts 불변, 원본2,927항목·FD3→3을 확인했다.
별도 root 도구 종료0/chunk `4aba2b`에서 원본2,148항목·원 의존성/보존 파일·실행 종료를 다시 검사하고,
정지 소유 DB41,968,312bytes와 두 임시 디렉터리를 제거했다. 인증 backup과 사용자 미리보기는 보존했고 root FD4→4다.
단일/관측 프로세스 트리 합 RSS는 전체 API141,455,360/487,325,696bytes,
집중226,222,080/533,909,504bytes, 작은 native134,131,712/605,290,496bytes다.
0.25초 표본의 명시 소유+보호 트리 범위이며 전체 WSL 용량을 뜻하지 않는다.

## 사용자 확인과 다음 단계

`http://localhost:5173/`은 계속 완료 합성 생장47,809시점/5사건을 조회한다.
이 수확 API 검증으로 현재 화면을 교체하거나 자동 갱신하지 않았다.
다음은 같은 전체 DB/보호 API/기존 제품 App의 대표 WebGL 시점에서 수확·생장의 부모/hash/UTC와
원 C/N·LAI·관리 사건을 대사한 뒤 수동 확인 화면 연결을 평가하는 단계다.
검증용 복원/기존 화면 연결·대표 시점/권한·자원/정리를1–3집중시간으로 잠정 분해한다.
브라우저/빌드 자원 실패가 없다는 조건이며 아직 완료 시각을 약속하지 않는다.

U3는 같은 실행의 진행 상태·확정 checkpoint·완료 결과를 자동으로 잇는 별도 작업이다.
기후/물·양분/구매 에너지→사용자 실행/Decimal 경제의 후속 순서는 유지한다.
동일 이전 head `921d0e7`의 hosted Backend는0/4 성공·1/2/3 실패·5 진행 중이었다.
실패 로그에서2/3의 과거 수확 관측 거부74개와1의 소유 프로세스 검사2개를 확인했다.
과거 관측 문제의 로컬 보완과 이번 집중 통과를 hosted 성공으로 대신하지 않는다.
진행 중인 같은 branch CI를 취소하지 않도록 push는 보류했다.
실제 품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4 `not_assessed`, 생산/미래 마진/추천 hold다.
