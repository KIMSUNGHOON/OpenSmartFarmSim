# 기관 reader와 계산 작기 CODE 경계 — 2026-10-20

[기계 증거](artifacts/organ-reader-code-boundary-20261020.json).
현재 native Codex CLI `gpt-6.1-sol` / `xhigh` 문맥에서 판정했다. 재귀 CLI/하위 agent 호출은0이다.

기존 계산 작기 record는 `runtime_roles_code_sha256`를 CODE에 고정하며, 보존 reader와
현재 backend의 역할 모듈 해시가 다르다는 실제 기록이 있다. 이 사실을 기관 v1까지
공통 비호환 근거로 확대하지 않는다.

기관 v1의 `crop_result_store.py`, `crop_growth_integration.py`, `crop_growth_rates.py`는
현재 source와 보존 사용자 source에서 원 bytes/SHA256이 각각 같다.
기관 `CropResultStore._checked`는 저장 코드·프로필·통합/유량 코드·원 program/결과 해시와
HMAC, 현재 농장 등록·display 권리를 검사한다. 계산 작기의 CODE 객체를 사용하지 않는다.

이는 **코드 결속 경계의 정적 증거**다. 역사적 기관 row의 현재 농장/권리 조립이나 실제 저장소
읽기 호환성까지 입증하지 않는다. 옛 역할 해시 허용 목록, 검증 생략, 원 packet/서명 변경은 추가하지 않았다.
새 정상 synthetic producer를 사용하는 실제 API/DB/현재 App 통합 시험을 선행 개발할 수 있고,
그 성공을 역사적 row 채택으로 보고하지 않는다.

현재 보호5root의 실제 identity/live와 RSS를 별도 관측했다. 기존
[동시 API/PG/브라우저의 RSS hold](catalog-owned-api-lifecycle-20261020.md)는 유지한다.
건강한 기존 서비스에 시험용 중지/재시작/GC를 하지 않았다. hosted 검사는 원512MiB/PID·합1GiB/
600초·.25초 기준으로 별도 감독하며, WSL 보호 forest를 포함한 동시 용량이나 사용자 적용의 수용이 아니다.

다음 실제 통합의 기준은 [기관 native 계약](../contracts/crop-organ-native-acceptance-v1.md)이다.
실제 농장0·G0–G4/전체 U1 미평가·전체 완료일 미정과 active goal을 유지한다.
