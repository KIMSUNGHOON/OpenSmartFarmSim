# 등록 작물 선택 SDK와 목록 SDK 빌드 수용 — 2026-10-09

상태: `web-crop-result-farm-selection-client`와 `web-crop-result-catalog-client` **두 SDK 자식만 로컬 수용**.
[등록 선택 계약](../contracts/web-crop-farm-selection-client-v1.md),
[목록 계약](../contracts/web-crop-result-catalog-client-v1.md),
[현재 source·원 종료·자원 영수증](artifacts/web-crop-farm-selection-client-reference-20261009.json)을 따른다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`를 확인했으며 재귀 CLI0이다.

등록 선택 SDK는 farm3필드로 현재 등록 작물 ID·원 이름/품종·UTC 기간을 읽는다.
최대32/고유·오름차순, 닫힌 요청/응답과 원 사용자 가정·미검증 상태를 검사한다.
Unicode 이름은 서버와 같은 문자 수1–200·주변 공백/C0 제어 문자 규칙을 유지한다.
UTC 소수6자리를 보존해 밀리초보다 작은 양수 기간도 구분한다.
한 번의 기존 Bearer GET/30초/64KiB와 취소·대기 중 요청 변경·참조 분리를 적용했다.
새 프레임워크/DB/계수·자동 계산이나 캐시는 추가하지 않았다.

## 실제 증거와 통과한 검사

- [새 fixture](../web/e2e/crop-farm-selection-recorded-responses.json)는 선행 실제 SCRAM/HTTPS
  원10756 종료0의 성공 원문2개를 그대로 보존한다. 원1작물/604bytes와 두 SHA를 대사했다.
  현재 권리 철회 뒤 복원한 응답도 원 metadata와 같다. SDK 시험의 fetcher는 소프트웨어 시험이다.
- 기존 목록 원42058 종료0의 실제 원문7개도 현재 source에서 다시 대사했다.
  원20+1/동률·수확1건은 선행 서버 범위이며 이번에 새 DB 계산/게시를 하지 않았다.
- 원66094 **종료0**, 전체19.046초/상한600초다. 웹25파일 **1,011 passed**에는 기존949개와
  새 등록 선택62개가 포함됐다. 전체 시험16.494초·타입0.614초·빌드1.935초, 각 자식 종료0이다.
  원 응답 보존·Unicode/UTC·빈/32·오류/취소·늦은 응답·기존 소비자를 확인했다.
- 현재 두 SDK의 핵심 파일 hash를 결속했다. 기존 목록 구현/fixture/transport는 같고,
  API factory에는 새 선택 SDK import/조립 두 줄만 추가됐다.
  source1,533개·기존 web/dist와 원 계산/미리보기 네 프로세스 identity가 유지됐고 남은 자식은0이다.

## 이전 빌드 보류 해소와 범위

목록 SDK의 [이전 실패 영수증](artifacts/web-crop-result-catalog-client-reference-20261009.json)은 보존한다.
디자인 CLI가 종료한 뒤 원 계산/미리보기의 현재 RSS 약525MB를 확인하고, 빌드 Node heap을128→96MiB로 낮췄다.
단일 CPU/Rayon1/arena2·nice19와 기존 단일512MiB/동시1GiB 제한을 유지했다.
0.1초/187표본의 동시 RSS 합1,005,539,328bytes·단일455,315,456bytes에서 실제 빌드를 마쳤다.
이는 관측한 실행 묶음의 RSS이며 WSL 전체 메모리 또는 일반 운영 용량 수용은 아니다.
빌드는 별도 private 디렉터리에 두었으며 사용자 미리보기에는 배포하지 않았다.

**저장 결과 선택 화면·실제 DB/브라우저/재시작·상위 U1과 실시간 U3는 미완료다.**
현재 UI는 별도 저장3시점 재생이며166일 계산을 자동 표시하지 않는다.
실제 품종/농장 작물 Run/국내 독립 자료0건과 G0–G4·생산/미래 마진/추천 보류를 유지한다.
다음은 승인된12ui 원본/HTML을 사용한 농장→등록 작물→저장 결과 선택과 기존3D/수확 연결이다.
