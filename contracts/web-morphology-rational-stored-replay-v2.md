# 정확 출현 시각의 저장 형태 3D — v2 연구 화면

상태: [CI38/브라우저11·실제 native 수용](../research/morphology-rational-stored-replay-20261022.md).
[공개 v2 export](../research/crop-rational-morphology-export-20261022.md)가 선행이다.
현재 authored 복엽/표면·장면과 같은 디자인을 재사용하며 새 프레임의 원 길이/기관 ID만 geometry에 연결한다.
새 앱/프레임워크·작물 runtime/API·과실 애니메이션을 만들지 않는다.

별도 진입은 `morphology-rational-replay.html`, 기존 `morphology-replay.html`은 v1 root/12프레임을 유지한다.
현재 사용자 서버의 적용 후 주소는 `/morphology-lab/morphology-rational-replay.html`이다.
두 진입은 shared typed 소비자/페이지를 사용하며 명시 source 판본/경로·index/root SHA를 각각 고정한다.
GET는 index1+frame12를 순차 조회하고 bytes/hash·범위/단위/flags/선택 판본을 대사한다.
불일치/미지원 판본/권리·WebGL 실패는 보류하며 새 계산/대체 결과를 만들지 않는다.

v2 DTO는 원 UTC 시점과 별도의 time_origin_utc·기관별 정확 출현 초를 보존한다.
분수 초는 축약된 비음수 정수 문자열/양의 분모·단위s로 확인하고 현재 원 UTC 경과 초 이내/순서를 검증한다.
BigInt 분수 비교는 형식/QC이며 생장 계산이 아니다. 가짜 emerged_at/반올림 UTC는 만들지 않는다.
3D/표/그래프/재생 상태는 같은 선택 UTC·원 미터 길이/ID·원 축 합계를 사용한다.
출현 표에는 같은 원점과 정확 n/d초를 표시하고 시각 종류를 분명히 한다.
고정3복엽·잎맥/털·표면/반경은 제작 외형이다. 잎/면적/과실·키/생산·수익을 추론하지 않는다.

수용은 v1 소비자/기하 회귀와 v2의 원12프레임/단위·출현 분수·원점·오류 보류/순차 GET,
실제 first/last/키보드/재생·정지·끝 자동 정지/모바일·원 값/UTC/표·graph/WebGL 대사다.
타입/집중 unit/build/audit·Chromium CI 뒤 현재 server 적용/HTTP bytes와 Windows native를 확인한다.
기존 exact driver ReadPixels 진단은 원 text/location을 보존하며 다른 warning/error를 무시하지 않는다.
일반 graphics 성능 hold와 WSL/Windows의 계측 범위를 분리한다.
원190/223/137파일·기존 v1 root/15파일과 원6root/WSL 상한을 보존해야 한다.

이 자식은 자체 합성 하루의 저장 재생이다. 농장 custody/현재 권리·실제 품종/한 작기·자원/경제와
최종 제품 UI·G0–G4의 새 승인은 포함하지 않는다. 부모 체크는 실제 배포/브라우저 증거 뒤에만 한다.
