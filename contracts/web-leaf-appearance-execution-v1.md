# 정책 기반 잎 실행 SDK — v1

상태: [집중·관련164검사/전체 타입·SDK 번들·실제 현재 API 수용](../research/leaf-appearance-execution-sdk-20261024.md). 선행은 [실행 HTTP](api-crop-leaf-appearance-execution-v1.md)와
[사용자 API 연결](../research/leaf-appearance-execution-live-20261024.md)이다.
[저장 연구 SDK](web-leaf-appearance-sdk-v1.md)와 기존 실행 client/화면은 보존한다.

`createLeafAppearanceExecutionClient(token)`은 preview/submit/status/observe/manifest/frame/replay/cancel을 제공한다.
즉시 취소된 작업은 `canceled / cancel_accepted=true / cancel_requested=false`로 수용한다.
취소 수락이면서 미종결이면 서버의 pending cancellation flag를 요구한다.
인증된 같은 출처의 appearance 경로만 사용하며 닫힌 request/JobStatus·현재 읽기/cancel envelope를 검사한다.
Bearer·no-store/redirect=error/credentials=omit, UTF-8/JSON·응답2MiB와 각 요청30초·caller abort를 유지한다.
다른 family/추가 필드·단위/부착/시각/식별자·완료 전 결과를 거부한다. POST의 자동 재시도는 없다.
503/504 등의 status를 그대로 전달하며 caller의 원 pending request/job ID를 바꾸지 않는다.

완료 replay는 같은 job/result/parent·farm/source/binding/최초 시각과 signed manifest를 대사한다.
수치 root는 정수/문자열/boolean 메타데이터의 canonical SHA를 원 root와 비교한다.
source/preparation/population/stem 참조·model/display 판본·sample_count/UTC와 실제 frame/기관/단위·합계를 확인한다.
고정 fixture의 root/기관 수/정책 값으로 실행 결과를 대체하지 않는다. API에 없는 정책 수치는 반환하지 않는다.
프레임 원 bytes와 원 program/정책·프로필/수치/서명의 검증은 현재 서버 authority/reader가 담당한다.
SDK의 형식·참조 검사는 독립적인 수치/서명 검증이나 과학 관문 승인으로 확대하지 않는다.
Python float JSON을 JavaScript로 재직렬화해 원 프레임 SHA를 계산하지 않는다.

manifest/frame 요청도 같은 완료 summary에 결속한다. frame은 먼저 현재 manifest를 확인하고
그 뒤 원 frame wrapper/result/index·source/parent·단위를 대사하며 양쪽 summary가 달라지면 거부한다.
observe는 현재 status를 먼저 읽고 완료일 때 같은 summary의 replay를 조회한다. 미완료는 result/replay가 null이다.
누락/변조/권리 거부·중단에는 부분 frames나 대체 자료를 반환하지 않는다. 조회가 생장/출현 계산을 하지 않는다.

수용은 부재 RED→focused type/unit·실제 저장 응답/원12시점·47면적·현재 API의 원 값/UTC/부모·조회 POST0,
다른 family/범위/순서/부착/단위/원 참조/transport/abort·기존 client 회귀/WSL/원 자료·4root 보존이다.
새 UI·같은 job3D/메뉴/reload/재연결·현재 철회 제거와 실제 Chrome은 후속이다.
실제 품종/독립 자료·생산/경제/추천·G0–G4 수용을 선언하지 않는다.
