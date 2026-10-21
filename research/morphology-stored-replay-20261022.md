# 저장된 절간 길이와 실제3D 연결 — 2026-10-22 KST

[확인용 화면](http://localhost:5173/morphology-lab/)에서 `저장 결과 재생`을 누르거나 저장 시점을 선택한다.
[첫 시점](artifacts/morphology-stored-first-20261022.png)·[마지막](artifacts/morphology-stored-last-20261022.png)·
[모바일](artifacts/morphology-stored-mobile-20261022.png).
[계약](../contracts/web-morphology-stored-replay-v1.md)과
[원 증거](artifacts/morphology-stored-replay-20261022.json).
이는 자체 합성 하루/12저장 시점의 연구 연결이며 실제 한 작기/품종 예측은 아니다.

## 구현과 표시 범위

기존 [불변 artifact](crop-morphology-research-artifact-20261022.md)를 계산 없이 typed 조회해 내보냈다.
공개 export는 명시 재배포 권리=true를 요구하며 원 입력/root와 DTO bytes/SHA·UTC/원 result SHA를 보존한다.
브라우저 번들에 신뢰 index/root SHA를 고정하고 제한된 단일 요청으로 읽는다. 변조/권리 실패 때 보류한다.
원 길이는 미터 단위의 각 절간 mesh와 마디 위치에 연결하고 표/그래프/3D는 같은 저장 시점을 선택한다.
첫 합성 축 길이0.045332195340647634m/3절간에서 마지막0.13413312724033077m/6절간으로 변한다.
축 길이 합계는 실제 식물 키의 검증값이 아니다. 고정3복엽·반경/표면/직선 축·배지는 제작 가정이다.
잎 수/면적·화방·과실·숙기·생산량·비용/추천을 추가 계산하지 않는다. 마지막 시점에서 재생은 멈춘다.

## 통과한 검증

[source257da09 / CI39634431597](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39634431597)의
타입·집중22(새10/기존12)·빌드·audit0·실제 Chromium7(새4/기존3)을 확인했다.
원 bytes/hash·단위/UTC/ID·기하의 원 절간 길이/정리·고정 잎 수,
첫/끝·키보드/재생/정지·모바일·변조 보류·WebGL 대체가 포함된다.
별도 backend export는 새3/기존 artifact26=29검사를2.50초에 통과했다.
별도 프로세스의 생장 import0/계산·DB0·권리 거부 전 output 없음과 원 바이트를 확인했다.
기존312 모델/저장 검사 기록을 새 전체 backend 실행으로 합산하지 않는다.

실제 Windows 전용 Chrome에서 첫/끝의 원 길이·같은 UTC 표/그래프·ID, 회전 가능한 WebGL,
키보드 선택·자동 재생/일시 정지와 마지막 시점 정지·정착 후1.5초 idle frame 불변을 확인했다.
원 데이터 GET13·POST/API요청0·CDP 동시 데이터 요청 peak1·console 오류/경고0, AX 버튼6을 확인했다.
브라우저는 첫 저장 시점으로 돌아가 열어 두었다. 19.077326초/74표본의 WSL PID최대124,559,360/
합862,470,144bytes·원6root 생존·소유 자식 종료이며 Windows Chrome/Node 메모리는 이 합계 밖이다.
일반 성능/공통 용량 수용으로 사용하지 않는다.

검증된157파일의 실제 HTTP/SHA와 원5173/5174/5175의190/223/137파일·세 entry bytes를 대사했다.
같은 NGINX master의 별도 `/morphology-lab/` 정적 alias만 적용했다. 기존 backend/DB/키·모델·원 경로는 보존했다.
이전 lab 번들도 보존한다. 최종 제품 메뉴/농장 Run 통합의 완료 처리는 하지 않는다.

## 실패와 남은 보류

로컬9 소비 검사는 통과했으나 기하 검사 추가 시 합1,091,117,056bytes로1GiB를 넘어
보호 감독이 소유 검사만 종료했다. 이 실행은 미수용이며 원6root는 살아 있었다. 이후 빌드/브라우저는 hosted에서 수행했다.
첫 CI의 unused import, native의 그림자 deprecation을 수정했다. 지원 설정은
[Three.js 공식 문서](https://threejs.org/docs/pages/global)의 PCFShadowMap과 설치된0.186.1 소스를 대조했다.
한 native idle 관측 불일치의 원인은 확정하지 않았고, 폰트 준비/스크린샷 정착 후 같은1.5초 관측을 통과했다.

headless CI의 GPU ReadPixels 성능 경고4개는 **남은 드라이버 진단**으로 보존했다.
화면 캡처 중에만 발생한다거나 위치 URL이 비었다는 초기 가정은 실패 증거로 폐기했다.
최종 진단은 원 text/location/timing을 보존하고 정확한 해당 메시지만 분류한다. 다른 오류/경고는 실패한다.
앱의 실제 WebGL readPixels 호출은0이었다. 원인/일반 그래픽 성능은 미수용이다.
Windows native 최종 콘솔은 경고0이었다. 전체 웹 회귀·backend 전체/운영 G4를 새로 실행/수용하지 않았다.

12ui draft/안내된 stable resume는 corpus ambiguous로 실패했고 후보 이미지0이다.
기존 외형의 서체·색/조작과 직접 제작한 기하·텍스처를 사용했다. 승인 시안/close나 최종 사실감 수용을 주장하지 않는다.
실제 Axiany 계수/초기 기관·독립 농장/미래 작기 자료는0이며 G0–G4는 미평가다.
다음은 소수 초 기관 출현을 반올림 없이 길이 상태에 결속하는 계산 자식이다.
농장/current rights·서명 게시, 실제 작기/생산·자원·Decimal 경제/자율 선정은 후속이다.
