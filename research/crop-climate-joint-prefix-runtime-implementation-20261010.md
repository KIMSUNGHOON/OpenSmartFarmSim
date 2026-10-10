# 계산 중 확정 결과의 명시 서버 조립 — P3b 로컬 수용

2026-10-10 KST. reader v2 수정 `5861eb9`, runtime `8e794e4`를 로컬 수용했다.
[원 실행 증거](artifacts/crop-climate-joint-prefix-runtime-reference-20261010.json)는105,364bytes,
SHA-256 `6aa027f1a2fc4ace08f91ba900ee3e8f82b6a5645413f075065e21e752a034bc`다.
짧은 소유 합성 계산의 실제 SCRAM/검증 HTTPS·독립 자동 작업자 범위다. 사용자 화면 배포는 아니다.

## 실제 실패와 수정

P3a의 제어 시험 뒤 자동 작업자와 prefix GET을 연속 실행하자 정상 계산이 두 번 실패했다.
기존 reader가 custody의 배타 잠금을 점유했고, 작업자는 confirm/adopt에서
`joint_execution_busy`로 재시도한 뒤 세 번째 시도에서 failed가 됐다.
두 실패의 source SHA·원 로그·종료/정리 receipt와 두 번째 시험의 실제 예외 경로를 보존했다.
반복 조회 때문에 계산이 실패하는 상태를 사용자 서비스에 활성화하지 않았다.

수정은 reader/test/실제 HTTP test의3파일 자식으로 분리했다.
`joint-crop-climate-prefix-read-v2`는 계산 잠금을 취득하지 않고 기존 nofollow directory·bounded 파일을 연다.
현재 검증된 binding과 signed intent 전체를 대사하고 기존 `_Session`의 서명·계보·현재 권리 검사를 재사용한다.
불변 선택 페이지를 읽고 HEAD/readonly DB snapshot이 전후에 바뀌면503으로 버린다.
안정된 변조/rollback·권리 거부는 기존 hold이며 일시 오류로 숨기지 않는다.
기존 입력/수치/custody/result 형식과 writer/terminal reader는 변경하지 않았다.
이전19개 source 중 reader와 두 대응 test의3파일만 판본을 바꾸고 나머지16개 SHA를 보존했다.

## 명시 설정과 같은 객체

runtime 조립은 기존 API/runtime/operator config와 전용 test의4파일 자식이다.
`ApiRuntimeConfig.crop_climate_joint_prefix`는 정확한 bool·기본False이며 True에는 execution=True가 필요하다.
새 설정 `operator-joint-crop-climate-prefix-api-config-v1`은 execution/prefix 두 top-level bool을 필수로 받는다.
기존 두 joint 설정은 prefix를 비활성으로 유지하고 새 필드를 거부한다. 기존 generic/calculation loader도 새 판본을 거부한다.
보호 파일은 factory/조립 뒤 다시 확인한다.

같은 execution query/jobs/server/result store/farm/principal에서 reader를 만들고 그 인스턴스를 HTTP에 전달한다.
생략/False는 installer를 호출하지 않으며 prefix 경로가 없다. 기존56경로/262스키마는 동일하다.
조립과 조회의 수치·게시·DB 쓰기21계수는0이다. 별도 자동 작업자만 계산한다.

## 통과한 검증

최종 같은7파일 SHA의 **고유185개, skipped0**를 네 순차 guard로 확인했다.

| 범위 | 확인 |
| --- | --- |
| 새 runtime46개 | 명시 bool/폐쇄 판본·보호 파일·default import/API·실제 정상/hold/취소/비활성 |
| reader v2 회귀6개 | 이전 수용/fresh·signed rollback·권리/늦은 철회·잠금 취득0·원 intent/proof/HEAD/commit/page 변조·실제 외부 취소 |
| HTTP/투영/설정133개 | 실제 HTTPS2개·순수 공개 투영42개·기존 설정89개; 원 wire/selector/UTC·늦은 표시권422·owner cancel |

정상/hold 각각 chunk8의 독립 자동 작업자는 pause 없이 첫 번째 시도에서 완료했다.
각 실행의 running accepted summary2회와 원 sample 페이지1행/2행을 읽었다.
각503 여섯 번은 재조회했고 terminal에서는 원 결과 ID/저장 summary bytes로 전환했다.
취소는 실제 작업자가 canceled로 확인했고 결과/게시가 없다. 직접 취소 확인을 대신하지 않았다.
HTTP 계측54응답·최대8.908초이며 전체 응답 제한2MiB 안이다.
현재 자료/계정의 승인과 숫자·UTC 보존을 순수 투영 fixture의 승인으로 대신하지 않았다.

기존 P1의 나머지6개, P3a의 나머지 실제3개/제어105개, P2 실제2개와 전체 backend/CI는 재실행하지 않았다.
웹 SDK/UI/build/브라우저·사용자 prefix 배포는 실행하지 않았다.
WSL 단일/보호 사용자 서버 포함 합산 RSS 최대174,395,392 /904,830,976bytes로512MiB/1GiB 안이다.
원본2,148항목·두 frozen 서버/source/assets·FD4→4·시험 PG/schema/role·소유 프로세스/passfile 정리를 통과했다.
문서 상대 파일 링크1,891개·명시 anchor2개·실제 비밀값5개 미포함을 확인했다.
마지막 관측에서 보호 root4개/동적21프로세스는 생존하고 두 frontend는200·기존 HTML SHA와 동일하다.

## 사용자 확인 범위와 다음 단계

5173은 완료166일 저장 생장/수확 재생이다.5174는 접수한 작업의 상태/checkpoint 자동 조회와 종료 후 저장3D다.
개발·검증용 별도 DB의 작업은 사용자 화면에 자동 노출되지 않는다. 이번 변경도 두 frozen 서버에 배포하지 않았다.
계산 중 성장3D는 [P4 SDK→P5 화면→P6 실제 브라우저/사용자 기동](../tasks/plan.md#joint-prefix-view-20261010)이 남았다.
다음 한 단계는 P4이며 원 selector/UTC·닫힌 응답·취소/크기/오류와 실제 TLS SDK를 확인한다.
남은3.75–7.5집중시간과2026-10-11 KST의 작은 합성 사용자 화면은 조건부 추정이다.
실제 브라우저의 순차 진행/summary/page 조회·자동 작업자·서비스 수명 관측 뒤 다시 산정한다.

native CLI의 실제 model/effort는 `gpt-6.1-sol`/`xhigh`다.
turn context 시각 `2026-10-10T11:00:12.341Z`, LF 포함 SHA
`c9283e30beab6e29be12c2fe0998e6c88abe8396a44061cfa4e0271c9e1b05a6`를 기록했다.
재귀 CLI0·runtime CLI0·native→마지막 검증1,787.576초(약30분), 문서/commit은 별도다.
실제 crop Run/독립 국내 농장 자료0건·G0–G4 미평가·생산/미래 마진/순위 hold와 기반/push 고정을 유지한다.
