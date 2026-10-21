# 정확 열적 나이의 절간 길이 point 수용 — 2026-10-22 KST

[저장 길이3D](morphology-stored-replay-20261022.md) 다음으로
[명시 exact-age point 계약](../contracts/crop-internode-length-point-v1.md)을 구현했다.
기존 canonical F(a) 수식 함수를 분리/공유하고, 닫힌 synthetic 곡선과 정확 나이에서 길이를 계산한다.
시각/기온·기관 이력을 보충하거나 반올림한 출현 UTC를 만들지 않는다.
v1 clock/state의 소수 초 출현 보류는 그대로이며 새 유리수 출현 상태 결속은 다음 자식이다.
[원 증거](artifacts/crop-internode-length-point-20261022.json)에 실제 native CLI 문맥·소스/검사 지문을 기록했다.
재귀 CLI는 없었다.

부재 RED 뒤 새36/기존315=351검사가4.58초에 통과했다.
기존 독립 Decimal800 길이16점에 새 분수/상·하 tail5점을 더해 최대 상대차1.361E-14를 확인했다.
2^56±1/3의 차이를 나이의 float 변환 전에 보존하는 두 반례와 exp(−800)의 underflow를
큰 M에서 복구하는 점을 포함한다. 단위/기원·age basis/축약 분수·문자열 길이·부울/nonfinite·
지수 overflow/normal 미만 길이를 거부하며0으로 채우지 않는다. 입력 불변과 반복 결과/지문도 확인했다.

수정 전 source SHA의 모듈을 별도로 불러 기존8사례의 초기화/전진16개 **전체 결과 bytes와 input SHA**가 같음을 대사했다.
독립 fixture를 별도 파일로 재생성해 원 bytes와 대사했다.
이미 공개한 원 root b720…ec56와 저장12프레임도 새 프로세스에서 원 공개 JSON bytes와 같았다.
그 재조회는 생장8모듈 import0/DB0이었다. 현재 화면/원 저장 artifact를 새 코드의 출력으로 바꿔 기록하지 않았다.
검증 보조 스크립트의 첫 괄호 SyntaxError는 실행 전 실패로 보존하고 수정 후 별도 단계에서 수용했다.

집중 검사의 .25초21표본에서 PID최대124,559,360/합909,021,184bytes·wall5.157602초,
별도 대사의3표본에서 합839,983,104bytes·wall0.523880초를 관측했다.
두 단계 모두 원6root 생존·자원 보류 없음·소유 자식0이다. 전체 backend/브라우저 재실행·새 배포는 하지 않았다.
실제 Axiany 초기 기관/계수·독립 농장 자료는0이며 G0–G4를 해제하지 않는다.
다음은 정확 유리수 출현 시각/열적 나이를 가진 기관 상태→목록→저장/같은 UTC3D를 작은 자식으로 나누는 것이다.
