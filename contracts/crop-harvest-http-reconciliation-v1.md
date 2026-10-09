# 수확 저장 결과와 HTTP 응답 대사 — v1

2026-10-09. 선행 [전체 writer 계약](crop-harvest-full-writer-v1.md).
native Codex CLI `gpt-6.1-sol`/`xhigh`, 재귀 CLI0.
core3는 이 계약, `research/crop-harvest-http-reconciliation.py`,
`backend/tests/test_crop_harvest_http_reconciliation.py`다.

## 이번 자식

전체 writer가 진행 중인 동안 다음 보호 API 검증의 **응답 대사**를 준비한다.
검증기는 표준 라이브러리만 가져오며 DB·네트워크·파일을 열거나 계산/게시하지 않는다.
호출자는 원 보존 helper의 `checked`를 통과한 manifest와 실제 부모 farm,
고정 query/projection 코드 해시를 전달해야 한다. 검증기 자체는 서명·권리·관문 권위가 아니다.
보존 manifest의 절대 dependency 경로와 backend 모듈을 같은 고정 source에서 로드한다.
구형 manifest의 해시나 경로를 새 코드에 맞춰 변경하지 않는다.

## 대사 경계

정상 API의 summary, 첫 `min(64,total)`행, 마지막1행만 순차 요청한다.
HTTP 클라이언트가 받은 원 bytes와 독립 ASGI 관측기의 완료 상태/bytes/SHA를 비교한다.
원 signed payload의 결과/부모/farm/source/프로필·artifact·행 chain과 최초 UTC를 대사한다.
공개 summary 전체와 원 순서의 page 행은 보존 manifest의 canonical SHA와 같아야 한다.
공개·합성·관문 상태와 query/projection 응답 헤더도 고정 판본과 같아야 한다.

각 성공 응답은 기존 **30초·2MiB** 이하다. 한도·비정상 응답·불완전 전송·다른 bytes·
잘못된 시각/단위/수량/순서/offset·중복 JSON 필드는 고정 대사 실패로 끝낸다.
실패 원문/토큰/DSN/서명 패킷은 공개 보고서에 싣지 않는다. 한도를 늘려 통과시키지 않는다.

## 수용과 후속

집중 시험은 현재 정상 writer의 새 소유 합성6행/summary와 보호 ASGI 경로를 사용한다.
소유 codec의 새 패킷은 실제 DB 서명/등록 증거가 아니다. 과거 SCRAM 영수증은 변경하지 않는다.
원 수량·UTC/순서를 수정한 응답, 서버와 클라이언트 bytes 불일치, 비용 초과를 거부해야 한다.
이는 새 TLS/DB·전체47,813행 API/대표3D·UI U3 수용이 아니다.

전체 writer의 원 종료/독립 대사/인증 backup/fresh·별도 감사 뒤에 같은 원 manifest를
정상 `ApiRuntime`/실제 SCRAM·보호 HTTPS에서 측정한다. 현재 tenant/scope/권리 거부·복원,
읽기 RHS/생성/게시0·FD/원본/소유 PG/512MiB·1GiB 검사는 그 다음 실행의 필수 증거다.
실제 전체 요청이30초를 넘으면 관측된 병목만 별도 작은 수정으로 다룬다.
대표 같은 UTC3D, 사용자 미리보기 전환과 실행 진행 갱신 U3는 각각 후속이다.
