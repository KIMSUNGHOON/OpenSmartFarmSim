# 형태 연구 artifact 파일 운송 수용 — 2026-10-22 KST

[명시 기관 목록 계산](crop-shoot-internode-inventory-20261022.md)의 후속으로
[파일 운송 계약](../contracts/crop-morphology-artifact-io-v1.md)을 구현했다.
새 저장 플랫폼 대신 기존 JobStore의 private 디렉터리/동기화·no-clobber 파일 보관과 ContentAccess를
재사용했다. DB·농장/테넌트 권한 체계는 이 파일 계층의 수용 대상이 아니다.
부모 native gpt-6.1-sol/xhigh 실제 문맥과 소스/시험 지문은
[원 증거](artifacts/crop-morphology-artifact-io-20261022.json)에 있다. 재귀 CLI는 없었다.

부재 RED 뒤 새14/기존272=286검사가2.09초에 통과했다.
원 bytes/같은 digest의 동일 파일 재보관·별도 Python 프로세스 읽기,
동시 writer 거부/reader 허용·DB 연결0, symlink 부모/파일·hardlink·디렉터리 교체,
파일 권한/bytes/크기 변경·명시 상한과 반복 실패 FD 증가0을 확인했다.
키·DSN·농장 raw 자료를 새로 읽거나 저장하지 않았다.

.25초11표본의 PID최대124,559,360/합864,141,312bytes·2.579960초,
원6root생존·자원 보류 없음·소유 자식0이다. 전체 backend/브라우저·새 모델 배포는 실행하지 않았다.
다음은 합성 producer의 입력/모델·단계/불변 root와 계산 없는 typed reader다.
그 뒤 같은 UTC의3D 연구 연결이며 제품의 현재 농장/원천 권리·등록/서명 경로는 별도다.

병행한 [Axiany 측정 자료 조사](axiany-morphology-independent-data-20261022.md)는
주별 집계의 이용 경로와 개별 초기 기관/계수·독립 작기의 미확보를 구분했다.
부모가 실제 자식 context/model/effort/hash를 대조했다. 실제 품종 계수/자료 채택·G0–G4 해제는0이다.
