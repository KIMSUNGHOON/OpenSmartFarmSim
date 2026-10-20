# 독립 확인의 파일 읽기·인코딩 소비 검토 — 2026-10-20 KST

[기계 증거](artifacts/solar-confirm-load-consumption-review-20261020.json) · [원 시간 관측](solar-driver-column-mask-evaluation-20261020.md) · [기존 같은 load 후보](solar-same-load-two-read-evaluation-20261020.md).

## 각 읽기가 보증하는 것

[confirm](../backend/app/crop_greenhouse_solar_execution_checkpoint.py)은 다음 순서를 사용한다. 원 `_snapshot`이 parsed data를 버리는 사실만으로 full validation을 제거할 수 없다.

|순서|소비와 보증|
|---|---|
|첫 current/lease/input|현재 물리·경제 입력/권리와 lease/input 바이트를 검사한다.|
|첫 session.progress|full header/context/profile·commit/page/hash/prefix/time 검증과 HEAD/proof·storage usage를 응답에 결속한다.|
|DB history|기존 확인의 provenance·연속 sequence·서로 다른 HEAD·원 attempt/UTC를 검사한다.|
|snapshot의 full load|다시 파일 전체를 검증하고 head/digest/proof를 첫 progress와 대사한다. parsed bundle은 반환 후 버려지지만 검증의 오류는 소비한다.|
|descendant/lease/event|서명된 ancestry·입력을 확인하고 기존 event 재사용 또는 신규 event를 같은 DB transaction에 준비한다.|
|늦은 current/최종 progress|현재 입력/권리를 다시 검사하고 full-load 응답의 exact bytes를 첫 응답과 비교한다.|
|최종 locked lease/input/history|취소/만료·입력·event 변경을 거부하고 최종 record를 반환한다.|

## 실제 반례: HEAD만 확인하면 중간 변경을 놓친다

원 CASE6/input64/chunk1에서 한 단계만 계산하고 기존 확인 event를 만든 뒤, `_snapshot`에만 일시적인 결함을 넣었다. 변경은 늦은 progress 전에 복원했다. 비교용 사설 지름길은 원 `_snapshot`의 full load만 fresh HEAD/selected-proof로 바꿨다. 나머지 원 함수·current/lease/DB 흐름은 유지했다.

|중간 결함|원 snapshot|HEAD 지름길|
|---|---|---|
|commit 원문 변조|hold|같은 기존 checkpoint 수용|
|commit decoder 변경|hold|같은 기존 checkpoint 수용|
|load method 변경|hold|같은 기존 checkpoint 수용|
|HEAD 위치 변조|hold|hold|

최종1검사/8관측에서 각 원 파일/method/codec 복원·기존 확인 재조회·원 UTC/record·DB digest 불변과 계산/CLI0을 확인했다. 따라서 HEAD 지름길은 미채택하며 **가운데 full validation을 유지**한다. 실제 운영 취약점이나 모든 경쟁 조건 수용을 뜻하지 않는다. fixture schema/role0·guard64.593574초·최대 합1,045,557,248bytes였다.

## 인코딩 구성요소: exact bytes를 보존하는 작은 경계

같은 원 app의 별도 소유 저장 artifact46commit에서 source와 그 source를 포함한 time-bound payload46쌍을 수집했다. 기존은 source hash와 payload hash를 각각 인코딩한다. 사설 구성요소는 source의 canonical bytes를 그 한 쌍 안에서만 쓰고, 정확한8개 payload key를 source 전/후의 원 canonical mapping으로 나눠 원 bytes를 조립했다. 파일·자료/권리 결과를 재사용하는 제품 경로는 추가하지 않았다.

각 pass는 원46쌍을6회 사용했고 ABBA 모든 출력의 bytes·source/payload SHA를 대사했다. Unicode/escaping·signed zero/float·scalar3경계도 확인했다.

|경로|실측 초/276쌍|
|---|---:|
|원|0.373902405|
|구성요소|0.205327943|
|구성요소|0.205652722|
|원|0.377523075|

구성요소 평균45.306531%, 짝별45.085150%/45.525788% 감소다. **전체 worker/current/IO·codec/소유권 guard 비용은 포함하지 않았다.** 원64 처리량/전체2% 기준을 수용하지 않는다. 한편 첫 source 인코딩 뒤 콜백이 원 객체를 바꾸는 실제 반례에서는 source SHA는 같아도 기존/조립 payload SHA가 달랐다. 따라서 임의 callback·공유 mutable data로 확대할 수 없으며 native provenance/codec/error·소유권 보증은 다음 단계다. 일반 unguarded 재사용은 승인하지 않는다.

초기 standalone probe는 backend import path가 없어 app import/계측 전에 실패했다. 경로를 명시한 v2만 최종 구성요소1이다. 최종 guard2.140494초·최대 합896,188,416bytes였다. 두 최종 실행 모두 FD4→4·5root/원본2,148/두 frozen source·자산·소유 잔여0·단일144,003,072bytes를 보존했다. 기존82/전체 backend/browser/원64 CI는 재실행하지 않았고 app261/d477b74b…는 그대로다.

## 다음 구현 경계

같은 load 안의 첫/두 번째 commit 읽기 소유권과 인접 source/payload 인코딩 소유권을 명시하는 작은 primitive를 검토한다. 이전 같은-load 후보의 평균1.093551%는 미채택 상태로 유지하며 단독 재실행으로 유리한 timing을 고르지 않는다. 새로운 결합은 검증된 native decoder/encoder·실제 같은 bytes의 재확인·값 비노출/일회 전달·초기/늦은 함수 변경 시 원 경로와 오류·단일 aggregate1MiB 상한·종료 정리를 먼저 증명해야 한다. 현재 권리/HEAD/proof/모든 fresh file 보안·SHA/원 semantic 검증은 유지한다.

그 뒤에만 같은 최종 guard를 포함한 원 worker ABBA 평균2%/양짝 개선을 평가한다. 성능은 더하지 않고 실제 전체 구간에서 한 번 비교한다. 기존 유효 ABBA guard146.971106초는 실행 시간 참고이며 primitive 개발·판단/회귀/원64/외부 자료의 완료 일정이 아니다. 새 DDL/서비스/라이브러리·계산 계수나 actor/input/chunk/poll/retry360/RSS 변경은 없다.

원 정상64→독립 hold→HTTP취소→계산 중WebGL→WSL 적용과 실제 품종/권리 확인 원자료·독립 작기 자료는 남는다. 새 Solar 미배포·실제 농장 Run0·G0–G4 보류·전체 완료일 미정·goal active다. native CLI gpt-6.1-sol/xhigh 실제 문맥/소스/출력/종료 SHA를 묶었고 재귀 CLI/하위 agent0이다.

## 사용자 상태 게시

[게시 영수증](artifacts/solar-confirm-load-status-publication-20261020.json): 두5173/5174는 동일 최신 JSON·HTTP200/no-store이며 원 frozen HTML/환기2,173·5root/원본2,148·FD4→4·소유 잔여0을 보존했다. guard1.368070초·최대 합947,634,176bytes다. UI code/DOM/WebGL·새 모델 배포·원64 CI는 재실행하지 않았다.
