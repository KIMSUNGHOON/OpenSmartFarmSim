# 저장 결과 선택 UI의 실제 hosted 실패 보완 — 2026-10-09

상태: **컨테이너 타입 오류 재현/수정·집중 검증 통과. 수정판 브라우저·이미지 수용은 대기**.
전체 계산과 기존 사용자 미리보기는 유지하며 새 후보를 배포하지 않았다.
[원 종료·로그·자원 근거](artifacts/crop-ui-hosted-failure-fixes-reference-20261009.json)를 남겼다.

## 실제 실패와 수정

[상세 빌드 기록을 추가한 실행37893003883](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37893003883)은
`45571d7`에서 `selected-crop-replay.spec.ts`31/73의 TS2339로 실패했다.
`Window.__showSelectedCrop` 선언이 Docker에서 제외되는 e2e TSX harness에만 있었다.
선행 [이미지 경계 메모](crop-catalog-image-build-boundary-20261009.md)의 미확정 원인은 이번 로그로 보완한다.
누락 PNG는 별도 포장 결함이며 이 타입 오류의 원인이 아니다.

사설 복사본에서 e2e TSX를 제외해 동일 두 오류를 재현했다.
RED controller 종료0은 예상 자식 종료1을 확인했다는 뜻이며 제품 빌드 성공이 아니다.
공유 Window 선언을 기존 `*.ts` 허용 범위의 `.d.ts`로 옮기고 실제 harness는 이를 사용한다.
TSX/HTML fixture를 제품 이미지에 추가하지 않는다. 같은 제외 조건의 GREEN 타입 검사가 종료0이다.

[Web 실행37892105702](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37892105702)은
타입·단위·일반 빌드·audit 통과 뒤 Chromium132통과/8실패다.
이전 대기30개 중22통과/8실패이며, 목록7개는 정확한 농장 label을 찾지 못했고
선택 전달1개는 부모 hash 불일치인데도 수확 행까지 조회한 뒤 거부했다.

목록 select에 보이는 글과 같은 접근성 이름을 지정했다.
기존 수확/생장 summary의 정확한 farm4·부모·source hash/status 검사를 공통 함수로 옮겨
수확 page 요청 전에 실행한다. page/행/UTC의 기존 검사는 유지한다.
유효 summary 무변경과 기존10종의 독립 유효/상호 불일치 거부를 집중 검증했다.
원 브라우저의 거부 시 요청1개 조건을 유지했으며 timeout·skip으로 실패를 감추지 않았다.

## 로컬 검증과 남은 범위

원69406 종료0/3.393초: 제외 조건 타입·현재 타입 종료0, 생장/수확 binding과 목록/선택/SDK
4파일 **211개 통과**다. source1,580개·기존 배포 dist·보호4 identity·소유/child0을 보존했다.
표본 단일/합 RSS399,736,832/940,683,264bytes, 0.05초46표본이며512MiB/1GiB 이하다.
실제 native CLI `gpt-6.1-sol`/`xhigh` 문맥·출력 hash와 재귀0을 기록했다.

수정판의 실제 Docker export/이미지 빌드, Chromium30개와 원3상태 디자인 improve/렌더 대조,
실제 공동 DB의 목록 선택/재시작 수용은 아직 통과하지 않았다.
전체 계산/미리보기의 같은 동시 자원 조건에서 Chromium을 반복하지 않는다.
이 수정은 U1의 후보 보완이며 UI 배포·상위 U1/U3·실시간 연동·G0–G4 수용은 아니다.
