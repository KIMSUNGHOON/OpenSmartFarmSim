# 기관 목록의 실제 저장소·HTTPS·브라우저 통합

선행은 [기관 서버/API와 SDK 계약](crop-organ-result-catalog-v1.md) 및
[소프트웨어 연결 수용](../research/organ-catalog-web-20261020.md)이다.
기존 WSL 동시 API/PG/브라우저의 RSS hold와 독립인 hosted 소프트웨어 통합 자식이다.
정상 synthetic producer의 새 시험 결과를 쓰며 기존 역사적 row의 호환성이나 실제 농장을 대신하지 않는다.

## 수용 기준

- 같은 CI의 전체 웹 검사를 통과한 minified artifact와 digest/commit을 확인한다.
  실제 SCRAM PostgreSQL, 기존 `ApiRuntime`/Bearer와 검증된 upstream HTTPS를 사용한다.
  정적 frontend는 원 API status/body를 그대로 전달한다. 응답 mock/임의 수치·시각은 사용하지 않는다.
- 농장→등록 작물→`organ_v1` 목록의 원 ID를 선택한다. 원 여섯 시점의 탄소/LAI와
  readout·표·WebGL/UTC를 대사한다. 재접속 뒤 같은 결과 재선택, 현재 권리 철회/복원,
  계정 scope 거부/복구와 numeric hold 결과를 실제 API로 확인한다.
- 1536×1024/390×844·320px, DPR0.5와 키보드 시점 이동을 확인한다.
  ResizeObserver가 실제 새 폭을 반영한 뒤 가로 넘침을 검사한다. 보간/임의 성장 애니메이션은 추가하지 않는다.
- GET만 허용한다. 정상 원 row/payload/hash/서명·DB counts가 보존되고 조회 중 put/integrate/RHS·SQL 쓰기는0이다.
  모든 응답의 서버/브라우저 status를 대사한다. 성공 응답은 원 body SHA256과 SDK의 실제 끝까지 읽기를 확인한다.
  SDK가 `!response.ok`에서 본문을 읽지 않고 거부하는403/422는 브라우저 헤더/현재 화면 제거로 검증한다.
  해당 오류 본문의 bytes/hash는 upstream proxy에서만 관측하며 브라우저 본문 소비로 표시하지 않는다.
  기존30초/metadata64KiB·재생2MiB 한도를 유지한다.
- native child 전체를512MiB/PID·합1GiB/600초·0.25초 표본으로 감독한다.
  실제 종료·FD/소유 프로세스/PG/passfile/임시 정리를 확인하며 credential·개인 자료·원 제한 자료는 공개하지 않는다.

핵심 파일은 `backend/tests/web_crop_organ_catalog_smoke.py`, `web/e2e/real-organ-catalog-smoke.mjs`,
`research/crop_organ_catalog_hosted.py`, 기존 web workflow와 이 계약이다.
호스팅 실제 통합과 WSL 동시 용량/사용자 적용을 따로 기록한다. 원3상태 디자인,
기존 보존 row의 지원 reader/CODE,20건/큰 packet·구획v2/startupv3·기관 family/U1과
실제 자료/G0–G4·생산/자원/경제·전체 제품 완료는 계속 별도다.
