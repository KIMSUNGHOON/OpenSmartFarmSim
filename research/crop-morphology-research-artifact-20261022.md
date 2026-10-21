# 합성 형태 결과 불변 저장·계산 없는 조회 — 2026-10-22 KST

[기관 목록 계산](crop-shoot-internode-inventory-20261022.md) 다음으로
[불변 artifact 계약](../contracts/crop-morphology-research-artifact-v1.md)을 구현했다.
명시 자체 합성 입력과 권리 선언, 초기 목록·8개 모델 판본/14개 의존 코드 지문,
각 출력의 입력 state/결과 state hash와 원 UTC를 내용 주소 파일에 보관한다.
모든 시점이 저장된 뒤 마지막 root만 반환하며 중간 실패의 비공개 객체는 완료 결과로 게시하지 않는다.
수용한 동일 Python/플랫폼의 동일 입력/코드는 동일 root와 기존 파일 bytes/inode/mtime을 유지한다. 재호출은 계산을 다시 할 수 있다.
공개 작업 멱등성·중단 producer 자동 재개는 이번 내부 export의 범위가 아니다.

reader는 호출자가 신뢰한 root SHA를 받아 canonical 입력/선택 결과와 단위·UTC·형식/단계 연결을 검사한다.
저장된 기관별 길이와 추적 축 길이 합계를 그대로 제공한다. 생장 식·적분·합계 계산은 하지 않는다.
신뢰 root 자체는 농장/테넌트 승인·현재 원천 권리나 독립 정확도 서명이 아니다.
공개 fixture export에는 redistribute=true가 필요하며 실제 FarmAuthoringService/서명 경로는 별도다.

부재 RED 뒤 새26/기존286=312검사가4.01초에 통과했다.
원 값/단위/UTC·독립 Decimal fixture, 원 hash chain/같은 root·파일 불변을 확인했다.
별도 프로세스에서 생장8모듈 import0, 조회 모델 호출0/DB 연결0을 확인했다.
잘못된 권리·기원/출력 순서/미지원 모델·관문/연결·terminal/원본 hash,
새 hash를 붙인 결과의 잘못된 단위/UTC/관측 기원/추가 생산량 필드를 거부했다.
초기 길이0·소수 초 출현과 두 번째 단계 강제 실패는 정상 root를 만들지 않았다.
[원 증거](artifacts/crop-morphology-research-artifact-20261022.json)에 실제 native CLI 문맥과 소스/로그 지문이 있다.
재귀 CLI는 없었다.

.25초18표본, PID최대124,559,360/합886,595,584bytes·wall4.381081초,
원6root 생존·자원 보류 없음·소유 자식0이다. 전체 backend/브라우저/새3D 배포는 실행하지 않았다.
소스 검토에서 기존 모델·JobStore/ContentAccess 변경과 새 의존성·DB/API/플랫폼 추가는 없다.
다음은 이 자체 합성 저장 프레임을 같은 UTC의 사실적 외형3D에 연결하고 브라우저에서 대사하는 것이다.
실제 Axiany 초기 기관/계수와 독립 농장 관측은0이며 G0–G4/생산 예측·자율 선정은 해제하지 않는다.
