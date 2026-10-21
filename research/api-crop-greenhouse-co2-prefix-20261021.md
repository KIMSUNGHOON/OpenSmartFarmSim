# CO₂ 확정 구간 공개 응답 — 순수 구현/검증

[계약](../contracts/api-crop-greenhouse-co2-prefix-v1.md) · [87검사/원 증거](artifacts/api-crop-greenhouse-co2-prefix-pure-20261021.json).

## 현재 수용 범위

닫힌 `joint-co2-solar-prefix-replay-v1`을 구현하고 **순수83 + private program witness4 =87개**를 통과했다.
none/closed의 null, accepted의 원 선택자/최초 확정 UTC/attempt·농장/입력/manifest/time grid·summary/page를
검사한다. 기존 CO₂109상태·44연속/6사건 장부·17수지/PAR/NIR·원 quantity/단위/UTC를 보존한다.
유한 binary64/50기관 배열·literal False/provenance·원 CO₂ identity/QC/정규화 판본·2MiB 실제 직렬화 경계와
비공개 입력/계수/권리 원문·서명/개인 경로 차단을 확인했다. 원 source program은 명시 입력이며 순수 투영은 DB/권리 승인이 아니다.

기존 Solar75의 identity13 중 CO₂에 없는 Solar 전용4개를 CO₂ 전용2개로 바꿔 identity11을 시험한다.
공개83은75−2+CO₂ source/basis·수지10개이며 private source4는 별도다. 초기 실패/이전87은 합산하지 않는다.

## 프로그램 결속과 actual 소프트웨어 변형

원 reader는 선택 context.program의 canonical immutable bytes를 owner/tenant/job/응답 hash에 묶인 private witness에
저장한다. `_source_program`은 owner/응답·canonical bytes/manifest hash를 검사하고 새 dict를 반환한다.
원 raw wire에는 프로그램을 추가하지 않았다. 직렬화 후 원 선택 context/page의 program bytes도 다시 대사한다.
이 reader 변경의 실제 DB/독립 회귀는 아직 미수행이다. 원 조회31은 변경 전 source의 수용 기록으로 보존한다.

공개 행의 wet/dry는 검증한 원 프로그램의 forcing_step_index로 결정한다. 기존10프로그램은 각 프로그램 안에서
한 basis만 사용하므로, 기존 weather-multiple의 forcing4에서 basis만 dry로 명시한32초 소프트웨어 변형을
실제 원 커널로 다시 계산했다. 수치 계수는 그대로며 원 표준 사례/파일은 수정하지 않았다.
0:wet/4:dry/8:wet/16:wet의 sample/event 기준과 원 sample 수치·단위/UTC를 보존했다.
이 새 변형은 독립 물리/작물 검증이 아니다. 누락/다른 프로그램·hash/index/basis/단위·CO₂/탄소 수지 누락도 거부한다.

초기 RED는 모듈 부재/소스 witness 부재4실패/수집1오류였다. 첫 GREEN은84통과/3실패였고,
none/closed의 명시 None와 전환 사례의 실제 재계산으로 보완했다. v2와 최종 source 증거의87을 각각 보존하며 합산하지 않는다.

## 자원·남은 수용

최종7.287013304초·단일 PID154,763,264/합769,794,048bytes·FD4→4로 원600초/512MiB/1GiB 안이다.
원2148항목·필수5root/두 서비스 source/assets와 소유 process/PG/임시/passfile0을 확인했다.
순수 조회31계측/CLI/SQL쓰기0이며 fixture 작성·실제32초 계산은 측정 전 수행했다.
새 HTTP/runtime/OpenAPI·숫자/저장/기존 CLI worker·UI 코드는 바꾸지 않았다.

**공개 응답 부모는 미완료다.** 다음은 실제 SCRAM의 현재 세 view·ready/normal/hold/cancel·64+1,
늦은 source/권리/페이지·witness, 독립 actor/producer/reader와 영향받은 원 reader 회귀다.
원 Solar DB15/fresh1의 의미를 유지하고 CO₂ basis 전환/프로그램 변조도 실제로 확인한다.
구체적 전체 사례/배치는 해당 시험을 수집한 뒤 고정한다. 이후 보호 실행 API/runtime → 같은 UTC3D → WSL/사용자 적용이다.
실제 농장 Run0/G0–G4 not_assessed·새 CO₂ 미배포·전체 작기/자원/경제·최종 UI/실제 CLI 종단 간/독립 검증과 전체 완료일은 남는다.
