# OpenSmartFarmSim

**2026-10-09 사용자 확인 UI:** 기존 제품 App과 실제 DB/HTTPS 백엔드를 함께 기동했다.
`http://localhost:5173/`에서 [접속·저장 결과 조회 안내](web/README.md#기존-제품-앱의-로컬-동시-기동--2026-10-09)에 따라
**완료된 합성166일의 생장47,809시점·수확47,813행과 같은 시각의 수치3D**를 조회할 수 있다.
원 시점 번호/마지막 시점으로 이동한다. [전체 수확 사용자 서버 전환·실제 검증](research/crop-harvest-full-user-preview-20261009.md)을 수용했다.
최종 통합 UI는 미완료이며 [U0–U5 작업·수용 기준·잠정 일정](tasks/plan.md#최종-제품-ui-통합--2026-10-09-사용자-요청)을 따른다.
재생은 저장된 계산 시간의 이동이다. **계산 진행 상태·새 checkpoint의 실시간 U3는 아직 연결하지 않았다.**

**2026-10-10 기후 계산 후속:** [짧은 작물·기후 공동 적분](research/crop-climate-joint-integration-implementation-20261010.md)을
새44/기존463=507개·독립 Decimal798수치/60수렴 비율·원 종료/보존으로 로컬 수용했다.
현재 잎 면적·저장 열에서 구한 수관 온도로108상태·22장부를 같은 단계에서 갱신한다.
32초 합성 계산이며 새 UI 연결은 없다. 다음은 원자적 관리→온실 경계·새 저장/3D다.
전체 결합/실제 생산 모델·실시간 U3·품종/독립 자료·관문은 미완료다.

**2026-10-09 최신 수용:** [전체 수확 저장·등록·복원](research/crop-harvest-full-writer-completed-20261009.md)을 완료했다.
원96517/별도 root3349 실제0·47,813행 Decimal 독립 대사·인증 backup·fresh 동일 결과/현재 권리·소유 정리를 통과했다.
[요청 범위 조회/전체 보호 API](research/crop-harvest-current-read-cost-20261009.md)는 집중238개·실제 DB·전체 HTTPS7응답을 통과했다.
같은 저장 summary8.823초/첫64행10.939초/끝1행10.780초로 이전30초 timeout을 해소했다.
[전체 API/대표3D](research/crop-harvest-full-view-20261009.md)는 원72505/별도 root 종료0·실제 같은 DB/App에서
수확6행/생장10시점/관리5사건·현재 권한/늦은 정상 응답 정리·WSL 상한을 통과했다.
[조기 연결 종료 보완](research/crop-harvest-early-disconnect-20261009.md)은149개·실제 같은 DB/TLS의500→422·조회0,
정상 원 wire/현재 권한·원 종료/소유 정리를 통과했다.
[사용자 전환](research/crop-harvest-full-user-preview-20261009.md)은 실제5173의 수확3행/같은 UTC WebGL·독립 root와
기존 서비스 종료0·새 서비스 생존/원본·FD·자원 한도를 통과했다. 합성 저장/재생 부모만 수용하며
실시간 U3·최종 UI·실제 자료/관문 수용은 남아 있다.

**당시 2026-10-09 19:00 KST 계산 관측:** [정상 전체 수확 writer](research/crop-harvest-full-writer-running-20261009.md)를
18:52:18 KST 시작해 durable JSON53개를 저장했다. 아직 DB 등록/독립 대사·fresh 수용 전이며 화면은 기존 완료 생장을 읽는다.
producer21:52:18 KST 마감과 후속 fresh900초는 감독 상한이다. 수확 API/3D 검증 뒤 사용자 화면 연결을 평가한다.

**수확 API 연결 준비:** [원 저장 결과와 HTTP 응답의 대사](research/crop-harvest-http-reconciliation-20261009.md)를
새29/기존7=36개·원 종료0으로 확인했다. 현재 소유 합성/보호 ASGI 범위이며 전체 수확 HTTPS/3D·실시간 U3 수용은 아니다.
같이 관측한 과거 코드 판본 거부74개는 [현재 실제 DB 값/과거 거부 검사](research/crop-harvest-api-fixture-current-version-20261009.md)로
로컬 보완했다. 정상 SCRAM/fresh2Python·집중174개/실제 DB1개와 원 종료/정리를 통과했으며 hosted/전체 API 수용은 별도다.

**UI 후보 검증:** 목록 선택의 선행 [동일 웹 소스 hosted 회귀](research/crop-ui-web-hosted-regression-20261009.md)는
웹1,028개·Chromium140개/skip0·타입/일반 빌드/audit가 통과했다. U1의 원3상태 디자인·실제 공동 DB 선택 수용은 남았다.
이번 [전체 생장 연결/시점 이동](research/crop-full-parent-api-view-preview-20261009.md)은 별도 검증이며 기본 수동 조회를 안내한다.

지역을 고르면 기상·시설·작물·시장 자료의 출처를 확인하고, 온실 시나리오를 계산해 3D로 재생하며, **평가한 작물 중 어떤 선택이 목표에 가장 맞는지** 근거와 불확실성을 설명하는 오픈소스 프로젝트입니다. 수확 시점의 수요·공급과 거시 비용 변화도 재배 결정의 조건으로 다룹니다.

**당시 실행 상태 — 2026-10-09 17:46 KST:** [완료 전체 생장 부모의 실제 API·3D/사용자 기동](research/crop-full-parent-api-view-preview-20261009.md)을 로컬 수용하고 `http://localhost:5173/`을 전환했다.
원7678 실제 도구0/119.766초·같은 실제 SCRAM/보호 HTTPS/제품 App·WebGL에서
고유5시점의50 C/N·LAI/기관값과5관리 사건의 원 UTC·값, 현재 권리/계정 거부·복원,
조회 RHS/행 생성/게시/증명0·FD/원본2,146항목·검증 PG/소유 정리를 확인했다.
지정 single-process Chromium의 단일/관측 합 RSS418,369,536/1,000,091,648bytes로512MiB/1GiB 안이다.
원59276 도구0의 기동 뒤 frontend/보호 summary200·원 bytes 일치로47,809저장 시점/5사건/1,816,704완료 걸음을 확인했다.
[전체 부모의 모든 행/121상태 대사·정상 게시/보존](research/crop-harvest-full-parent-restored-20261009.md)은 선행 수용을 유지한다.
[조회 사실 묶음](research/crop-cycle-calculation-query-facts-20261009.md)은 main f79ef64, 시점 이동은532c494로 통합했고 미리보기는 별도 고정 source를 사용한다.
window40개/타입과 압축을 끈 제품 빌드가 통과했다. 일반 압축 빌드의 WSL 메모리 실패는 남기며 운영 용량 수용은 별도다.
현재 화면은 **완료 전체 합성 생장 결과의 조회/수치3D 재생**이다. 수확 미등록·실시간 U3 미완료이며 원3시점 예제는 정상 종료했다.
다음은 전체 수확의 남은 읽기 비용 경계 확정→정상 writer/registry·독립 Decimal 대사/보존→
수확 API/3D→기후/물·양분/구매 에너지→사용자 실행/Decimal 경제다.
원 Backend37892105708은0/1/2/4 성공·3/5 실패·집계 failure로 종료했다. 두 CI 자식과 U1/U3·실제 품종/독립 자료·G0–G4/생산/미래 마진/추천 hold는 유지한다.
아래 시각이 붙은 기록은 당시 관측이며 현재 실행 상태의 증거로 사용하지 않는다.

**당시 진행 관측 — 2026-10-09 10:02 KST:** [새 전체 부모 실행](research/artifacts/crop-harvest-parent-full-started-reference-20261009.json)을09:12 KST 시작했다.
동일 원 모델/입력의 새166일 계산 판본이며10:02 KST 같은 프로세스의 확정 checkpoint는243,447걸음/commit61이다. 완료/수용은 아니다.
원9시간 상한18:12 KST·이전 전체7시간15분 근거의16:12–18:12 종료 추정은 조건부다.
모든 원 행/121상태 대사→정상 게시/인증 보존→원 DB 정리 후 fresh 복원·원 종료/자원 감사 뒤 전체 부모를 평가한다.
수확 writer/API/3D와 기후/자원/경제·실제 자료 관문은 후속이다.

**최신 수용 — 2026-10-09 10:02 KST:** [새 부모의 작은 수확 저장·보존](research/crop-harvest-storage-preservation-small-implementation-20261009.md)을
원52100 종료0·집중10개/실제 DB1개·DB 정지 후 fresh 현재 조회로 로컬 수용했다.
원5행/UTC·Decimal 독립 대사·서명/최초 시각·현재 권리/계정·조회 재계산0과 원 입력/artifact/FD·소유 정리를 확인했다.
전체249.050초/900초·raw330,541bytes·동시 전체 계산 포함 RSS 합701.11MiB다. 작은 저장 자식만 완료했다.
전체 부모는10:02 KST 같은 프로세스에서243,447걸음/commit61로 진행 중이며 원18:12 마감/수용 보류를 유지한다.
다음은 전체 부모 최종 감사→전체 수확 writer/registry→실제 API/대표3D→기후/자원/Decimal 경제다.
실제 품종/농장 Run/국내 독립 자료0건·G0–G4/생산/미래 마진/추천 hold와 운영 기반 고정을 유지한다.

**선행 수용 — 2026-10-09 09:10 KST:** [정상 producer와 인증 보존의 작은 구성](research/crop-harvest-parent-production-small-implementation-20261009.md)을
원17264 종료0·집중11개/실제 DB1개·원 DB 정리 후 현재 checkout의 fresh 복원으로 로컬 수용했다.
고정 `dc7b852`의 원392 source guard를 유지하고 작은120걸음/3시점/3사건·121상태/수지를 fresh 대사한 뒤 정상 게시·인증 보존했다.
전체101.710초/600초·raw308,638bytes·단일/소유 RSS130.61/355.31MiB·1,400 source·소유 정리를 확인했다. 작은 구성만 완료다.
다음은 같은 원 모델/입력의 새 전체166일 계산·모든 원값/현재 query 복원→새 source/profile의 전체 수확 writer/등록→실제 API/대표3D다.
전체는 준비부터9시간 상한·이전7시간15분 근거로7–9시간 잠정이며 실제 종료/정리 전에는 수용하지 않는다.
그 뒤 기후/물·양분/구매 에너지→사용자 실행/Decimal 경제다. 실제 품종/농장 Run/국내 독립 자료0건·G0–G4/생산/마진/추천 hold를 유지한다.

**선행 수용 — 2026-10-09 09:00 KST:** [작은 부모 DB·인증 자료 보존](research/crop-harvest-parent-backup-implementation-20261009.md)을
원90143 종료0·집중11개/실제 DB1개·원 DB 정리 후 fresh Python 복원으로 로컬 수용했다.
원120걸음/3시점·서명/원량/UTC와 현재 권리·계정/변조 거부, 조회 RHS0·1,480 source·소유 정리를 확인했다.
전체81.287초·raw backup307,294bytes·단일/소유 RSS129.76/388.52MiB다. 이 보존 자식만 완료했다.
기존 전체166일의 DB/config/무작위 서명 key 삭제로 원 인증 복원은 불가하다. 후속에는 같은 모델/입력의 새 전체 계산 판본이 필요하다.
다음은 작은 정상 producer+보존 구성→새 전체 계산/원값 대사·현재 query 복원→새 source/profile 판본의 전체 수확 writer/등록
→실제 API/대표3D→기후/물·양분/구매 에너지→사용자 실행/Decimal 경제다.
종전 첫 복원2–4시간 추정은 철회한다. 이전 전체7시간15분을 근거로 준비 검증 후7–9시간 실행·대사를 잠정 잡고 후속 완료일은 실측 뒤 정한다.
실제 품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4/생산/미래 마진/추천 hold와 운영 기반 고정을 유지한다.

**선행 수용 — 2026-10-09 02:48 KST:** [전체 수확 수량·용량 대사](research/crop-harvest-full-capacity-implementation-20261009.md)를
원78826 종료0·집중38개·전체 명령85.238초·1,474 source/원본/FD identity·소유 정리로 로컬 수용했다.
원47,809시점/5사건에서47,813행을 RHS0으로 만들고 Decimal 독립 수량/반올림 수지와 단위·목적·미배정을 대사했다.
748page/307,675,603bytes·root/HEAD/atomic 예약 상한311,878,099bytes≤512MiB,
알려진 root95,883bytes·단일/소유 RSS106.55/125.51MiB다. 용량 자식만 완료했다.
실제 전체 writer/DB/API/대표3D와 replay 부모는 미완료다. 다음은 정리된 DB/인증 자료의 실제 전체 부모 복원
→같은 raw profile의 전체 writer/등록·fresh 현재권리→API/대표3D→기후·물/양분·구매 에너지→사용자 실행/Decimal 경제다.
첫 복원은 보존 자료/검증 경로 재사용 조건의2–4집중시간 잠정이며 전체 실행 예산은 실제 복원 뒤 측정한다.
실제 품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4/생산/미래 마진/추천 hold는 유지한다.

**선행 수용 — 2026-10-09 02:22 KST:** [같은 실제 DB의 수확·생장3D](research/crop-harvest-view-native-implementation-20261009.md)를
원69379 종료0·2통과/226.498초·828 source/소유 정리로 로컬 수용했다.
원6행/3시점·50 C/N/LAI·현재 권리/계정·취소/늦은 응답을 실제 SCRAM/보호 HTTPS/빌드 App/WebGL로 대사했다.
metadata/시각/응답 대체0·조회 RHS/행 생성/게시0이며 완료200응답9개의 양쪽 bytes/SHA가 같다.
13요청·최대22.722초/32,659bytes·지정 heap/GC/GPU thread의 소유 RSS 합1,030,803,456bytes≤1GiB다.
작은 native/view 부모만 추가 완료했다. 전체166일 새 질량 부하·replay 부모와 일반 운영 용량 수용은 남아 있다.
다음은 원 전체 결과의 RHS0 질량/배정 용량 대사→실제 전체 부하→기후/물·양분/구매 에너지→사용자 실행/Decimal 경제다.
실제 품종 계수·농장 작물 Run·국내 독립 자료0건, G0–G4/생산/미래 마진/추천 hold는 유지한다.

**선행 수용 — 2026-10-09 01:32 KST:** [수확 표/기존 생장3D 화면](research/web-crop-harvest-view-screen-implementation-20261009.md)을
새 Chromium10개/기존15개(1+14분할)·웹851개·타입/빌드·원13586/24832/30303 종료0·820 source/정리로 로컬 수용했다.
원 목적/단위/미배정·현재 부분 범위/전체 합계·합성 비교/hold를 유지하며 같은 UTC의 실제 캔버스 C/N도 대사했다.
선택/계정/부모·권리 실패/취소/늦은 응답의 이전 값 제거와 모바일/키보드를 확인했다.
소유 fixture의 metadata/시각을 맞춘 실제 App 검증이며 새 공동 DB/백엔드 HTTPS 증거는0회다.
화면 자식만 완료했다. 실제 native/전체166일 질량 부하·view/replay 부모는 미완료다.
다음은 작은 같은 실제 DB/API/대표 WebGL→전체 작기 질량 부하→기후/물·양분/구매 에너지→사용자 실행/Decimal 경제다.
지정 시험 heap/viewport에서 소유 RSS 합1GiB/단일512MiB와 정리를 확인했으며 일반 운영 용량 수용은 아니다.
실제 계수/품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4/생산/마진 예측·추천 보류는 유지한다.

**선행 수용 — 2026-10-09 00:50 KST:** [저장 생장·수확 범위 결속](research/web-crop-harvest-growth-binding-implementation-20261009.md)을
집중34개/웹 전체851개(기존817 포함)·타입/빌드·원 도구86385 종료0·777 source/정리로 로컬 수용했다.
같은 농장/부모/원 hash·상태·저장 UTC만 연결하며 대응 시점이 없는 사건은 보간하지 않는다.
현재 범위와 전체 저장 합계·합성/hold를 구분한다. 새 실제 DB/HTTP/화면/WebGL 검증은0회다.
수확 view의 결속 자식만 완료했고 표/3D·실제 통합/전체166일 질량 부하·replay 부모는 미완료다.
다음은 수확 표/기존 생장3D 화면과 선택/취소/권리 실패 제거→실제 DB/API/대표 WebGL이다.
기후/물·양분/구매 에너지→사용자 실행/Decimal 경제·실제 자료/독립 검증은 후속이다.
실제 계수/품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4/생산/마진 예측·추천 보류는 유지한다.

**선행 수용 — 2026-10-09 00:32 KST:** [등록 수확 결과 웹 SDK](research/web-crop-harvest-client-implementation-20261009.md)를
집중97개/웹 전체817개(기존720 포함)·타입/빌드·원 종료0·458 source/정리로 로컬 수용했다.
실제 HTTPS 원 응답5개 SHA/길이·원6행/UTC/단위/정확 수량·합성/미배정·관측 비교/hold를 보존했다.
공통 Bearer·30초/2MiB transport와 순차 페이지·전체성/취소/혼합 거부를 연결했다.
SDK와 선행 API를 합친 HTTP/SDK 부모만 추가 완료했다. 수확 표/3D·replay 부모는 미완료다.
선행 합성166일 생장 DB/API/대표3D는 유지한다. 새 수확 경로의 전체166일 질량 부하는 별도다.
다음은 같은 UTC의 수확 목적·미배정 표/기존 생장 수치3D→실제 DB/API/대표 WebGL의 작은 검증이다.
그 뒤 기후/물·양분/구매 에너지→Decimal 경제 연결로 진행한다.
실제 계수/품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4/생산/마진 예측·추천 보류는 유지한다.

**단계별 검증 기록(수용 당시 범위):** 합성 생장 계산→실제 DB/HTTPS→같은 UTC3D의25시간 경로는 로컬 수용했고,
[새 검증 조회의 화면](research/web-crop-cycle-calculation-view-20261008.md)도 Chromium 새15개/기존47개·웹719개·
타입/빌드·원27시점/5사건으로 로컬 수용했습니다. [새 화면 캡처](research/artifacts/calculation-cycle-desktop.png)는
소유 시험용 HTTP 응답의 실제 App입니다. [새 실제 DB/HTTPS/WebGL 기능 검증](research/web-crop-cycle-calculation-native-observed-20261008.md)은
시험 로그1통과/27분45초·원27시점/5사건·34frame·24 HTTPS와 별도 정리를 확인했습니다.
[실제 새 화면](research/artifacts/calculation-cycle-native-desktop.png)도 보존했습니다. 원 명령 종료 코드 기록이 유실돼
최종 native 수용은 보류하며 같은 계산은 재시작하지 않았습니다.
[작은 등록 누적 비용](research/crop-cycle-calculation-prefix-cost-observed-20261008.md)은 정상/hold와 수정한32회 시험을
분할 확인했습니다. 3,990걸음·확정9시점/2사건·원값/권리/복원·종료0/정리를 확인했습니다.
[전체166일의 별도 합성 달력 등록](research/crop-cycle-full166-calendar-registration-20261008.md)도
원750파일/전체 값·격자 보존·73개 회귀·실제 SCRAM 농장/경제 달력·현재 권리/기간 거부·RHS0·종료0/정리로 수용했습니다.
[전체 입력의 초기32회 비용](research/crop-cycle-full166-prefix-cost-observed-20261008.md)도
3,990걸음·105시점/2사건·원 상태/행·현재 권리·129 source/정리·종료0으로 로컬 수용했습니다.
[후보 읽기 연결 개선](research/crop-cycle-candidate-read-scope-implementation-20261008.md)도 고유37개 분할·
연결38→1/검사·원량 보존·같은 첫3회60.421→30.737초·권리/정리로 로컬 수용했습니다.
[입력 재검사 개선](research/crop-cycle-calculation-recheck-cost-implementation-20261008.md)도 고유199개 분할·
같은 첫3회99→85검사/30.737→29.551초·체크포인트 전체/원량·변조/철회·복원/정리로 로컬 수용했습니다.
[개선 판본32회 관측](research/crop-cycle-calculation-full-budget-observed-20261008.md)도 같은 checkpoint/원량·권리/복원·
263 source/정리·종료0/358.024초로 수용했습니다. 두 개선 전과 같은 advance575.494→304.344초입니다.
과거 delta QC2n/합1,056회를 확인해 전체 등록 장시간 실행과 wall 예산을 보류했습니다.
[prefix 검증 증명](research/crop-cycle-calculation-prefix-attestation-implementation-20261008.md)은
재개 입력/HEAD 직전 권한 철회 두 반례를 RED로 확인·복원하고 최종 수정판208개 분할·같은32회 원량/권리·266 source/정리·종료0으로 로컬 수용했습니다.
delta QC1,056→64회·advance304.344→290.225초·전체339.187초이며 입력 검사839회는 보존했습니다.
candidate 현재 bytes 검사 뒤 마지막 입력/권한 검사와 atomic HEAD 순서를 검증했습니다.
[계산 묶음 가능성](research/crop-cycle-calculation-chunk-feasibility-observed-20261008.md)도 실제1통과/종료0·같은4,096전이/원105출력/2사건·
비계보 checkpoint 전체·2page/954,171bytes·268 source/정리로 수용했습니다. 제품128전이 제한은 유지했습니다.
[새 prefix 공개 연결](research/crop-cycle-calculation-prefix-api-bridge-implementation-20261008.md)도 실제 RED 뒤 수정·
API193개/웹720개/Chromium15개·타입/빌드·새34 JSON/원량/UTC·270 source/종료0/정리로 로컬 수용했습니다.
[제한된 계산 묶음](research/crop-cycle-calculation-bounded-chunks-implementation-20261008.md)도 고유177개·
실제4,096전이 저장/3,990걸음/원105출력·2사건·별도 Python 재개·274 source/종료0/정리로 로컬 수용했습니다.
요청4,096전이/실효128원경계·기존 bytes 한도·명시 서버v3이며 원 수식/격자/현재 권리를 유지합니다.
[등록 농장의 두 큰 묶음](research/crop-cycle-calculation-registered-chunk-cost-observed-20261008.md)도 실제 SCRAM1통과·
8,192전이/7,980걸음·원210출력/4사건·fork 재개·현재 권리/복사 입력 변조 거부·276 source/종료0/정리로 수용했습니다.
두 advance50.212/47.349초는 초기 구간 관측입니다.
[전체 참조 용량](research/crop-cycle-calculation-full-capacity-observed-20261008.md)도 고유10개·RHS0·456묶음/
전체47,809출력/5사건·예약 포함481,987,541bytes/512MiB·279 source/종료0/정리로 수용했습니다.
[같은 농장 별도 Python 복원](research/crop-cycle-calculation-registered-runtime-implementation-20261008.md)도 고유7개·
실제 SCRAM40→80걸음/2출력·복원 RHS0·계산 전 SIGKILL-9/재개·권리/변조·284 source/종료0/정리로 수용했습니다.
[등록 계산 감독](research/crop-cycle-calculation-registered-supervisor-control-implementation-20261008.md)도 고유16개·
실제 SCRAM40→60→80걸음/2출력·같은 마감/복원 RHS0·pause/cancel/실제-9·현재 권리·
289 source/종료0/정리로 로컬 수용했습니다.
[완료 결과 별도 DB 게시](research/crop-cycle-calculation-registered-terminal-publication-implementation-20261008.md)도
고유9개·실제 SCRAM40→120걸음/3출력·fresh 게시/재시도 RHS0/같은 row1·미완료/권한 거부·
294 source/종료0/정리로 작은 연결을 수용했습니다.
[같은 DB의 실제 App/3D](research/crop-cycle-calculation-registered-replay-harness-implementation-20261008.md)도
고유2개·실제120걸음/원3시점·3사건·보호 HTTPS8개/최대2.148초·현재 권리/계정 거부·
303 source/원 종료0/정리로 작은 기능 경로를 수용했습니다. [현재 실제 화면](research/artifacts/registered-cycle-desktop.png)이 있습니다.
이전 descendant RSS 합1.584GB 초과 보류 뒤 [작은 자원 경로](research/crop-cycle-calculation-registered-replay-resource-implementation-20261008.md)를
고유2개·원 종료0/89.680초·원3시점/3사건·392 source/정리로 로컬 수용했다.
실제 빌드/Nginx·지정 viewport/Node heap·명시 CDP GC2회에서 PG/controller 포함 동시 RSS 합
1,048,477,696bytes≤1GiB다. 일반 운영 브라우저/전체 작기의 자원 수용으로 확대하지 않는다.
[전체 실행 구성의 작은 수용](research/crop-cycle-calculation-full166-same-db-preparation-implementation-20261008.md)도
고유13시험·실제 대사 자식0→게시 자식0→같은 DB/UTC3D·원 종료0/준비부터102.476초·
PG/controller 포함 RSS 합1,050,714,112bytes≤1GiB·397 source/정리로 수용했다.
원166일 참조의 첫64/마지막1시점·전체5사건/121상태 읽기도 RHS0으로 확인했다.
[별도 전체166일 실행](research/crop-cycle-calculation-full166-same-db-completed-20261008.md)은10월8일11:41→18:56 KST에 원 종료0/1통과로 완료했다.
준비부터26,127.555초·전체47,809행/5사건·121상태/수지 대사→같은 DB 게시→보호 HTTPS10개/대표14시점 WebGL·
권리/계정 거부·398 source/자원 정리를 최종 감사했다. 표본 RSS 합1,070,809,088bytes≤1GiB이며 여유약2.8MiB다.
원9시간 상한/수식/격자를 유지했고 감사 후 source freeze를 해제했다. 전체47,809프레임·실제 형상/품종/관문 수용은 아니다.
[제거 원장](research/crop-removal-ledger-implementation-20261008.md)과 [명시 합성 질량 환산](research/crop-removal-mass-implementation-20261008.md)도 로컬 수용했다. 다음은 수확 의미·작기 질량 게시→자원/경제 연결이며 실제 자료·예측/추천 hold는 유지한다.
`f2dc10f`의 [CI 종료 상태](research/artifacts/full166-calendar-registration-ci-terminal-20261008.json)는
C0/웹/작성 PG/앱 성공, Backend 분할0/4/5 성공·1/2/3/집계 실패입니다.
[Python·원격 PG 시험 수정](research/calculation-ci-fixture-compatibility-20261008.md)은 고유19개 집중 검증을 통과했으며 hosted 수용은 별도입니다.
[기존 세 Compose 경로와 정리](research/artifacts/application-operator-policy-hosted-reference-20261008.json)는 실제 로그로 수용했습니다.
구형 CI는 [C0/웹/작성 PG 성공·앱/Backend 실패로 종료](research/artifacts/crop-cycle-calculation-view-ci-terminal-20261008.json)했고,
관련 설정 생성기/fixture의 로컬 수정·125개 분할 검증과 기존 Compose의 hosted 수용은 완료했습니다. 전체 Backend 수용은 별도입니다.
[새166일 전체 RHS](research/crop-cycle-full-rhs-durable-completed-20261007.md)는 종료0·1,816,704걸음·47,809시점/5사건·
원 전체 수지/행 hash·55 source/체크포인트 복원·자원 정리로 로컬 수용했습니다. 전체 등록 농장 DB/API/3D는 후속입니다.
생과 수확량·물/양분·구매 에너지·작물 결과와 손익의 연결은 남아 있습니다. 실제 품종 입력·국내 독립 검증 자료는
아직0건이므로 생산 예측·추천은 보류입니다. 현재 CI 시험 정리 오류는
[수집 시험](research/application-collection-passfile-cleanup-20261007.md)과
[계획 fixture](research/planning-passfile-cleanup-20261007.md)에서 각각 로컬 수정·검증했고, 수정의 hosted 수용은 별도입니다.
`2daa99f`의 [종료 CI](research/artifacts/crop-cycle-durable-ci-terminal-20261007.json)는 다른4workflow 성공,
Backend4분할 성공·위 정리 오류2분할/집계 실패입니다. 전체 backend 수용으로 표시하지 않습니다.
후속 `4b0d559`의 [종료 상태](research/artifacts/crop-cycle-calculation-server-custody-ci-prepush-20261007.json)는
C0/앱/작성 경로·Backend6분할/집계 성공이며 Web은 Chromium97통과/1실패입니다.
[경제 이력 키보드 시험](research/web-financial-history-keyboard-20261007.md)은 같은 실패를 재현해
대기 조건을 수정했고 로컬7개를 통과했습니다. 수정 판본 hosted 수용은 별도입니다.
[새 계산 문맥](research/crop-cycle-calculation-context-implementation-20261007.md)은90개 집중 시험·
별도 Python4개 복원·원 값/clock/counter·변조/자원 정리로 로컬 수용했습니다.
큰 입력 factory0.386465초는RHS0의 입력 경로 측정입니다.
[새 불변 artifact](research/crop-cycle-calculation-artifact-implementation-20261007.md)도 새68개/선행90개·
158통과와 실제25시간/11,400걸음·27시점/5사건·별도 Python7개·HEAD 전후 즉시 종료2개/복원·
조회 RHS0·원55 source 보존으로 로컬 수용했습니다.
[새 농장 권한 결속](research/crop-cycle-calculation-farm-authority-implementation-20261007.md)은 실제 SCRAM 고유12개를
분할 검증했고 현재 등록/권리·입력 변조 거부와 세 실행의 DB/역할/비밀/PG 정리를 확인했습니다.
이 권한 단계의 생장 계산/새 작물 row/Run은0입니다.
후속 [새 서버 계산/서명](research/crop-cycle-calculation-server-custody-implementation-20261007.md)도 순수50개·실제 SCRAM12개,
고유62개 분할·실제 중단4곳/fresh Python·등록 농장7→120걸음 재개·현재 권리/원 이력 보존으로 로컬 수용했습니다.
이 서버 자식 뒤의 새 DB 원자 게시도 아래 증거로 수용했으며 전체166일 등록 저장/API/3D는 후속입니다.
[새 DB 표/권한](research/crop-cycle-calculation-result-schema-implementation-20261007.md)은 전체68개/22.68초·
실제 SCRAM·원 행 보존·default deny/명시 authority 권한·제약/불변성/rollback·정리로 로컬 수용했습니다.
SQL 형식 시험 metadata를 저장한 단계입니다. 후속 [서명 결과 DB 게시](research/crop-cycle-calculation-result-publication-implementation-20261007.md)는
순수81개·실제 SCRAM 고유15개, 고유96개 분할·원량/실제7→120재개·현재 권리/rollback·원 signed 이력 공존·정리로 수용했습니다.
작은 DB·농장 연결 부모도 완료했습니다. get39.668745초 관측은 HTTP30초 미수용 근거이며,
다음은 전체 등록 비용과 새 proof/현재 조회·공개 판본/API runtime·같은 UTC3D 연결입니다.
[후속 구현 순서/다음 수용 기준](contracts/crop-cycle-calculation-query-v1.md)을 고정했습니다.
[새 계산 결과 검증 증명](research/crop-cycle-calculation-result-evidence-implementation-20261007.md)은
새79개/선행74개·고유153개 분할·자체5시간 정상61시점/3사건·hold60시점/2사건·
별도 Python2개/parser/context/QC/RHS0·원55 source/FD/PID 정리로 로컬 수용했습니다.
[새 조회 타입](research/crop-cycle-calculation-result-read-context-implementation-20261007.md)도 새49개/선행115개·집중164개·
원5시간 정상/hold·별도 Python2개/parser/context/QC/RHS0·원량/UTC·byte 경계/변조·원58 source/FD/cache/PID로 수용했습니다.
[현재 농장/DB 조회](research/crop-cycle-calculation-current-query-implementation-20261007.md)도 실제 SCRAM12개/1,079.43초·
원량/UTC·정상/관리 사건/수치 hold·철회/변조·fork·63 source/FD/DB/비밀/PG 정리로 로컬 수용했습니다.
작은 내부 조회5.01–6.06초는 HTTP/전체166일 성능 수용이 아닙니다.
[새 공개 투영](research/crop-cycle-calculation-api-projection-implementation-20261007.md)도 새63개/구형42개·고유105개 분할·
실제25시간/7페이지·원량/UTC·hold·RHS0·import/FD·67 source 보존으로 로컬 수용했습니다.
[명시 runtime factory](research/crop-cycle-calculation-runtime-factory-20261007.md)도 새19개/기존136개·고유155개 분할,
실제 SCRAM 같은 jobs/farm·재구성/9거부·계산/게시0·원 입력/FD/import·73 source/정리로 로컬 수용했습니다.
별도 설정 loader·실제 API 뒤 동일 UTC3D를 연결합니다. `353bffb` CI는 C0/웹/작성 PG 성공,
앱/Backend 설정 필드 거부로 종료했습니다. [설정 생성 호환 수정](research/application-operator-policy-compatibility-20261007.md)은
고유125개 분할·실제 SCRAM/TLS·원 loader/70 source/정리로 로컬 검증했으며 hosted Compose는 후속입니다.
[별도 운영 설정 loader](research/crop-cycle-calculation-operator-loader-20261007.md)도 새57개/기존155개·고유212개 분할,
실제 SCRAM/TLS 파일·명시 flag/재구성·원 파일/FD·75 source/정리로 로컬 수용했습니다.
[인증 route/OpenAPI](research/crop-cycle-calculation-route-openapi-20261007.md)도 새63개/관련 회귀221개·고유284개 분할,
원량/UTC·한 query/투영 뒤 철회·원48 path/148 schema·78 source 보존으로 로컬 수용했습니다.
[runtime/실제 TLS](research/crop-cycle-calculation-runtime-tls-20261007.md)도 실제3개/runtime19개/회귀315개·고유337개 분할,
26 HTTPS 전체 응답 최대5.258614초/23,546bytes·철회/변조·원량/UTC·FD11→11/81 source·정리로 로컬 수용했습니다.
[새 웹 SDK](research/web-crop-cycle-calculation-client-20261007.md)도 새178개 포함 웹 전체700개·타입/빌드·
34 공개 JSON/원량·UTC·검증 정보 대응·직렬 페이지/취소·원101 source 보존으로 로컬 수용했습니다.
[현재 범위 선택](research/web-crop-cycle-calculation-window-20261008.md)도 새19개 포함 웹 전체719개·타입/빌드·
원/새 source·원량/UTC·검증 정보·취소/settlement·104 source 보존으로 로컬 수용했습니다.
[같은 UTC 화면](research/web-crop-cycle-calculation-view-20261008.md)도 새 Chromium15개/기존47개·웹719개·
타입/빌드·원27시점/5사건·113 source/정리로 합성 응답의 화면 연결까지 로컬 수용했습니다.
다음은 새 실제 PG/TLS/WebGL이며 전체166일 등록 비용/복원과 hosted 수용은 별도입니다.
[전체 원 결과 증명 관측](research/crop-cycle-full-result-evidence-cost-observation-20261007.md)은6.11MB/8MiB·
발행175.7초·별도 Python 검증1.59초·선택 page1.7–2.0초/정리를 확인했습니다. 농장/HTTP/3D 수용은 별도입니다.
`8d111f1`의 [종료 CI](research/artifacts/crop-cycle-calculation-current-query-ci-prepush-20261007.json)는 다른4workflow 성공이며 Backend5분할 성공·분할0/집계 실패입니다. 분할0은
[권한 서버 시험의 복사 파일 정리](research/application-authority-passfile-cleanup-20261007.md) 실패입니다.
같은 순서 실제 DB 재현2통과/1정리 오류 뒤 수정2통과·정리를 확인했고 수정 판본 hosted 수용은 별도입니다.

**다음 구현 (2026-10-06 KST):** [긴 결과 DB 저장](research/crop-cycle-db-custody-implementation.md)을
고유76개 분할 검증(순수61·실제 DB15개)과 정리·원49개 파일 보존으로 로컬 수용했습니다.
합성 등록 농장25시간/11,400걸음·원27시점/5사건·7페이지와 재시작/fork·물리 변조를 대사했고,
원 manifest 누락도 실제 정상/hold 실패2개로 재현·수정했습니다. 단일 전체 backend 검증은 아닙니다.
`4bb6e53`의 [CI5개](research/artifacts/crop-cycle-db-custody-ci-20261006.json)도 Backend4,038개·별도UID4개와
여섯 동일 목록/DB·비밀 정리·집계까지 성공했습니다. [공개 투영](research/crop-cycle-api-projection-implementation.md)도
고유43개 분할·실제25시간의 원값/UTC·조회 RHS0회로 로컬 수용했습니다.
`2c0f0e6`의 [CI5개](research/artifacts/crop-cycle-api-projection-ci-20261006.json)도 Backend4,081개·UID4개,
여섯 동일 목록/정리·집계와 작성 첫 시도7job까지 성공했습니다. 이 SHA는 공개 투영까지 포함합니다.
[인증 route](research/crop-cycle-api-route-implementation.md)도 고유146개 분할·최종41개로 로컬 수용했습니다.
후속 [원천 읽기 연결 수정](research/crop-cycle-market-read-scope-implementation.md)은 고유56개 분할·
실제21 TLS 최대12.764535초로 수용했습니다.
[실제 runtime/API](research/api-crop-cycle-runtime-implementation.md)도 고유52개 분할 증거와
원25시간의 전체 HTTPS11응답·27시점/5사건·재시작·RHS0회·정리로 로컬 수용했습니다.
긴 응답 최대15.839875초/64,785bytes이며 기존30초/2MiB를 유지했습니다.
이후 client/3D·두 CI 수정까지 포함한 `7a855a7`의
[CI5개](research/crop-cycle-route-runtime-ci-success-20261006.md)도 Backend4,145개·UID4개·동일 목록/정리·집계,
웹522개/Chromium98개·타입/빌드·audit0으로 성공했습니다. 후속 profile/full runner/실험은 이 SHA 밖입니다.
[같은 원 시점 client](research/web-crop-cycle-pages-implementation.md)도 새120개·집중296개·
웹 전체503개·타입/빌드와 실제23 공개 JSON 보존으로 로컬 수용했습니다.
[현재 범위 helper](research/web-crop-cycle-window-implementation.md)도 새19개·웹 전체522개·
타입/빌드와 직렬 취소·원량 보존으로 로컬 수용했습니다.
[같은 UTC 화면 기능](research/web-crop-cycle-view-implementation.md)도 새Chromium16개·기존3개·
웹522개/타입·빌드·원27시점/5사건·C/N2,700 mesh와 원49개/선행7개 보존으로 로컬 수용했습니다.
[현재 범위 3D 화면](research/artifacts/cycle-crop-selected-window-preview.png)은 실제 컴포넌트를
소유한 기록 합성 응답/검토용 shell에서 캡처했습니다. 이후 실제 경로의 증거는 아래에 있으며 pixel fidelity는 별도입니다.
[새 실제 PG/TLS/WebGL 연결](research/web-crop-cycle-native-implementation.md)도
1통과/2044.35초·원25시간/11,400걸음·27시점/5사건·31frame·21 HTTPS와 정리로 로컬 수용했습니다.
전체 정상 본문 최대20.484300초/64,791bytes이며 조회 RHS0·실제 요청1개·현재 권리/계정 거부를 확인했습니다.
[실제 데스크톱](research/artifacts/cycle-native-desktop.png)과 [모바일](research/artifacts/cycle-native-mobile.png)을 확인할 수 있습니다.
과거/빈 보류·출력 없는 완료, 자원/DB/서버 정리와 별도 CPU4배 형식 시험20범위를 확인했습니다.
이 소프트웨어 수용은 실제 품종·전체166일·pixel fidelity·현장/미래 검증과 구분합니다.
다음 [작기 부하](contracts/crop-cycle-burden-v1.md)는 비용 측정 → 실제166일 RHS → 저장 조회/복원이며,
그 뒤 생과·자원·경제 순서입니다. [profile](research/crop-cycle-burden-profile-implementation.md)은
순수/shape14개·실제 SCRAM/worker1개·5시간/원61출력·166일 input plan과 정리로 로컬 수용했습니다.
전체 계획은1,816,704걸음이며 RHS0회입니다.
[runner/작은 재개 전략](research/crop-cycle-full-rhs-small-strategy-implementation.md)은 집중17개·
실제 자작5시간61출력/2사건·별도 Python 재개·terminal RHS0/정리로 로컬 수용했습니다.
다음 실제166일의 고정6시간 실험 예산은 완료 날짜가 아닙니다.
[실제166일 시작 관측](research/artifacts/crop-cycle-full-rhs-started-reference-20261006.json)은 첫checkpoint 뒤
같은 spec으로 재개한 실제16,086걸음 진행을 기록했습니다. 이 관측은 전체 완료 증거가 아닙니다.
원 입력 반복 검증 비용의 개선과 실제 전체 실행/조회 수용 뒤 전체 날짜를 갱신합니다.
[서버 입력 검사 영수증](research/crop-cycle-input-evidence-implementation-20261006.md)은 집중33개·
원 발행31.34초/별도 Python 재조회0.176초·현재 원 bytes/context·RHS0/FD 정리로 로컬 수용했습니다.
결과 조회 타입·과거 재생 연결·현재 농장 권리·실제 전체 API/3D 연결은 남아 있습니다.
[조회 전용 문맥](research/crop-cycle-input-read-context-implementation-20261006.md)은 집중15개·
원47,811경계/같은 context·재시작14경계/3page·RHS0/FD 정리로 로컬 수용했습니다.
열기0.380초/전체 경계 대사13.18초이며 원 계산과 조회 판본을 분리했습니다. 결과/농장 권리/API 연결은 다음입니다.
[확정 과거 결과 비용](research/crop-cycle-result-prefix-read-cost-observation-20261006.md)은
실제8,175commit/26,831출력의 원 수지 검증73.71초와 같은 참조 bytes 대사1.03초를 기록했습니다.
전체166일/HTTP 수용은 아닙니다. [결과 검증 영수증](research/crop-cycle-result-evidence-implementation-20261006.md)은
새41개·관련 고유89개와 새5시간1,800걸음/61출력/3사건·별도 Python/FD 정리로 로컬 수용했습니다.
원 QC 발행0.136초/별도 재조회0.013초는 이 작은 사례의 실측이며 전체166일 성능은 별도입니다.
[별도 결과 조회 타입](research/crop-cycle-result-read-context-implementation-20261007.md)은 새36개·관련 고유125개와
새5시간의 원61출력/3사건 전체·별도 Python/FD 정리로 로컬 수용했습니다. 원값/UTC·현재 bytes·변조 거부를 확인했습니다.
다음은 현재 농장/권리·원 server trace/API → 전체 저장/같은 UTC3D 연결입니다.
작은 조회 개발을 수용한 범위이며 실제 전체 proof/부모는 미수용입니다.
remote `8fe7dce`의 [종료 CI](research/crop-cycle-full-rhs-ci-hold-20261006.md)는
다른4workflow 성공·Backend5분할 성공/1실패·집계 실패입니다. 원 RSS 제한을 보존한
별도 시험 수정 `e310e27`은 로컬18개 통과이며 원166일 종료 전 main/hosted에는 반영하지 않았습니다.
`d61bcb3`의 [종료된 CI](research/crop-cycle-route-runtime-ci-hold-20261006.md)는
Backend5분할 성공/1실패·집계 실패, 웹 감사 실패이며 C0/앱/작성 경로는 성공했습니다.
[백엔드 분할2의 기대값 불일치](research/market-candidate-read-authority-assertion-20261006.md)도
재현해 시험만 수정했고 실제 PG5개/정리를 통과했습니다. 후속 `7a855a7`의 hosted 결과는 위 기록에 있습니다.
[단일 잠금 수정](research/source-map-js-audit-fix-20261006.md)은 웹503개/타입·빌드·audit0으로
로컬 수용했고 위 `7a855a7`의 hosted CI에서도 두 수정을 확인했습니다.
현재 실제 품종/작기 입력과 국내 독립 검증 자료는0건이며 생산 예측·추천은 보류입니다.

**재개 확인 (2026-10-07 KST):** [원166일 실험의 세션·임시 보존 상태가 유실](research/crop-cycle-full-rhs-missing-state-20261007.md)되어
최종 완료 여부를 확인할 수 없습니다. 기존 부분 관측을 완료로 바꾸거나 같은 실험을 재시작하지 않았습니다.
결과 증명 관련89개는 현재 환경에서도 통과했고, 새 작업 증거는 재부팅 후에도 유지되는 사설 경로에 보존합니다.
보존된 CI 시험 격리 수정은 `4bf9af3`으로 정상 적용했고 현재18개/24.30초를 통과했습니다
([통합 증거](research/artifacts/crop-cycle-full-rhs-test-isolation-integration-20261007.json)). 새 hosted CI 성공은 별도 확인합니다.
결과 조회 타입은 위36개/125개로 로컬 수용했습니다. 다음은 [현재 조회 계약](contracts/crop-cycle-current-query-v1.md)에 따라 농장/권리·원 DB/custody trace의
3 core파일 결속을 실제 SCRAM에서 확인하고, 이어 API/runtime 연결의 TLS30초/2MiB·투영 후 철회를 검증합니다.
두 자식의 수용 범위는 작은 저장 조회 소프트웨어이며 전체166일/복원·부하는 계속 보류입니다.

현재 [농장/DB 조회 결속](research/crop-cycle-query-authority-implementation-20261007.md)은 실제 SCRAM8개/631.33초로,
후속 [API/runtime 연결](research/crop-cycle-query-runtime-implementation-20261007.md)은 실제 SCRAM/TLS1개/243.58초로 로컬 수용했습니다.
원120걸음·3시점/3관리 사건·22 HTTPS 전체 응답·재시작·투영 후 철회·변조·역할 거부와 자원 정리를 확인했습니다.
최대6.306509초/21,514bytes이며 분할 검증은 고유198통과·9건너뜀입니다. 선행8개와 최종 transport 변경의 판본은 보고서에서 구분합니다.
현재 조회 부모의 작은 소프트웨어 범위까지 수용했고, 다음은 별도 판본/지속 저장의 전체166일 실험 → 저장 조회/중단 복원 → 같은 UTC3D입니다.

[지속 저장 감독자](research/crop-cycle-full-rhs-durable-implementation-20261007.md)는 실제5개/22.67초로 로컬 수용했습니다.
실제 계산 child 강제 종료(-9)·같은123걸음 checkpoint 재개와 연속760걸음의21시점/2사건·121상태 일치를 확인했습니다.
원 spec/마감과 과거 결과 변조·동시 실행을 거부하며, 원 계산식/runner/한도를 보존했습니다.
다음 새166일은 지속 저장의 별도 실험으로 실행하고 전체 종료·수지 검증 뒤에 수용합니다.
기존 `86290c3`의 [hosted CI5개](research/artifacts/crop-cycle-full-rhs-test-isolation-ci-20261007.json)는
백엔드6분할/집계까지 모두 성공으로 종료했습니다. 이 SHA는 선행 조회3커밋과 새 감독자를 포함하지 않습니다.
[새166일 실제 시작 관측](research/artifacts/crop-cycle-full-rhs-durable-started-reference-20261007.json)은
원123걸음/620RHS의 정상 중단 뒤 동일 spec 재개와8,104걸음 진행을 기록했습니다.
지속 저장 경로·nice15/단일 계산 child·실제 PID/시작 시각/lock을 확인했습니다.
고정 마감은10월7일20:07 KST이며 관측 당시 실행 중입니다. 전체 종료·수용이나 완료 날짜의 증거가 아닙니다.

`2daa99f`의 Backend 분할1은751개 본문 통과 뒤 앞선 수집 시험의 복사 비밀번호 잔존으로
종료 정리1오류가 발생했습니다. [소유 시험의 정리 수정](research/application-collection-passfile-cleanup-20261007.md)은
동일 순서 실제 SCRAM2개/75.53초·전체 비밀/DB 정리로 로컬 수용했습니다.
조회 검사·원 수식·pipeline은 보존했으며, 종료된 기존 CI와 수정의 hosted 수용은 별도입니다.

**현재 상태 (2026-10-05): 운영 기반 고정, 계산→저장→성장 연구 3D의 첫 소프트웨어 경로를 로컬 수용했습니다.**
`d19f7c0`의 백엔드·웹·C0·앱 조립·작성 경로 CI 5개가 모두 통과했습니다
([완료 범위와 증거](research/crop-priority-and-runtime-freeze-20261004.md)).
현재 3D는 저장된 열 계산과 합성 생장 연구 결과의 재생입니다. [첫 작물 탄소 유량 kernel](research/crop-growth-rates-implementation.md)은
로컬 집중 86개/0.12초·참조 수치 60개를 통과했습니다.
[작은 수관의 원식 적용 정책](research/crop-photosynthesis-domain.md)까지 합쳐 최종 118개/0.18초를
통과했고 [필수 프로필·고지 이미지](research/crop-rate-image-inputs-implementation.md)도 실제 Docker로 확인했습니다.
[UTC 시계열 적분](research/crop-growth-integration-implementation.md)까지 합쳐 146개/0.53초·
독립 165수치·수렴/수지/사건을 통과했습니다.
그 [불변 합성 연구 저장](research/crop-result-storage-implementation.md)도 실제 SCRAM·
별도 프로세스/변조·철회·정리를 포함한 집중 172개/434.49초로 통과했습니다.
[저장 조회 API](research/api-crop-replay-implementation.md)도 집중 316개/194.11초·
실제 TLS/SCRAM 10개 전체 응답·현재 권리/DB 변조·정리로 통과했습니다.
[계산 기반 성장 연구 3D](research/web-crop-replay-implementation.md)도 웹 단위 209개·
집중 Chromium 10개와 실제 저장→HTTPS→장면 대사 1개로 로컬 수용했습니다.
6개 시점·5분 합성 탄소 계산의 잎 면적/기관량을 재생합니다.
[직접 실행](web/README.md#지금-3d를-직접-보기)과 [화면](research/artifacts/crop-replay-final-desktop.png)을 확인할 수 있습니다.
실제 Axiany 전체 작기·생과 생산량·자원/경제 결합은 남아 있습니다.
[참조 작기의 실제 입력 감사](research/crop-forcing-audit.md)도 완료했습니다.
시간대/면적·수관/초기기관·관리와 원천 형식/QC의 실제 입력 채택은 보류입니다.
[과실 발달식/구획 계약](research/crop-fruit-cohorts-baseline.md)도 원식/21개 계수·상수와
배분식 보존 문제·보류/검증 계획을 고정했습니다.
[50구획 순간 이동](research/crop-fruit-transport-implementation.md)도 새 92개/기존 포함
238개와 독립 3,090수치로 로컬 수용했습니다. 필수 transport 프로필 포장도
[실제 hosted context/읽기 전용 loader·정리](research/crop-fruit-transport-image-inputs-implementation.md)로 수용했습니다.
[명시적 착과/진입 질량의 배분 정책](research/crop-fruit-allocation-policy.md)도 독립 대수/수치로
수용했습니다. [순수 제품 배분](research/crop-fruit-allocation-implementation.md)도 새 77개/기존 포함
315개·0.70초와 독립 600개 유입/4개 hold로 로컬 수용했습니다.
[50구획의 문헌식 수요·순간 결합](research/crop-fruit-cohort-rates-implementation.md)도 새 86개/기존 포함
401개·독립 8,592수치로 로컬 수용했습니다.
[전체 기관의 순간 결합](research/crop-plant-cohort-rates-implementation.md)도 444개 집중 시험·
독립 684수치로 로컬 수용했습니다.
[과실/기관의 짧은 시간 적분·관리 사건](research/crop-plant-cohort-integration-implementation.md)도
488개·독립 1,309수치/해석해 250개로 로컬 수용했습니다. 합성 24시간/512출력은
57.85초·약 41 MiB로 완료했습니다.
[새 저장 선행 artifact](research/crop-coupled-artifact-implementation.md)도 집중 530개·
별도 Python/재적분 없는 읽기로 수용했습니다. 같은 512출력 파일은 3.68 MB,
읽기/검사는 0.3055초였습니다.
[농장 결합 저장 v2](research/crop-coupled-result-storage-implementation.md)도 실제 SCRAM·
564개/850.85초·동일 bytes/별도 Python·현재 권리/변조/철회/원자성·정리로 로컬 수용했습니다.
[새 페이지 조회 API](research/api-crop-coupled-replay-implementation.md)도 고유 207개 분할 검증·
실제 HTTPS 19개·최대 11.508339초/649,718 bytes·현재 권리/재시작/정리로 로컬 수용했습니다.
[같은 저장 ID/UTC의 50구획 표·그래프·연구 3D](research/web-crop-coupled-replay-implementation.md)도
단위 129개·Chromium 19개·실제 SCRAM/HTTPS/WebGL 1개로 로컬 수용했습니다.
이어 [시작 조건/명시적 착과 정책 조사](research/crop-fruit-startup-policy.md)와
[빈 과실 요청/실현 adapter](research/crop-fruit-startup-rates-implementation.md)를
544개 집중 시험으로 로컬 수용했습니다. [새 기관 순간 결합](research/crop-plant-startup-rates-implementation.md)도
78개 새/622개 집중·독립 22사례/4,796수치로 buffer/생장 호흡 동시 대사를 수용했습니다.
[새 짧은 적분/누적 수지](research/crop-startup-integration-implementation.md)도
56개 새/678개 집중·독립 6프로그램/23시점과 실제 24시간/512출력으로 로컬 수용했습니다.
초기 전환/미세 구획의 수치 오차도 기록했습니다.
[새 불변 artifact/reader](research/crop-startup-artifact-implementation.md)도
79개 새/799개 집중·6프로그램의 동일 결과·별도 Python/재적분 없는 읽기로 로컬 수용했습니다.
실제 512출력 파일은 3,519,579 bytes·읽기/검증 0.286초입니다.
[농장 결합 저장 v3의 표/명시 권한·설정](research/crop-startup-storage-schema-implementation.md)도
새20개/184개 고유 분할·실제 SCRAM/불변 trigger·정리로 로컬 수용했습니다.
[현재 농장/입력 권리·서버 계산/HMAC 저장과 재시작 조회](research/crop-startup-result-storage-implementation.md)도
새18개/집중119개·실제 SCRAM/6프로그램/별도 Python·commit 전후 철회/정리로 로컬 수용했습니다.
[같은 저장 ID/UTC의 새 페이지 조회 API](research/api-crop-startup-replay-implementation.md)도
새47개/고유252개 분할·실제 HTTPS/SCRAM19응답·최대14.248425초/700,084 bytes와 정리로 로컬 수용했습니다.
[새 응답 해석/순차 페이지 결합](research/web-crop-startup-pages-implementation.md)도
새77개/웹 전체376개·typecheck/build·기록 TLS 원값 대사로 로컬 수용했습니다.
[같은 UTC 표·그래프·성장 3D와 실제 브라우저 연결](research/web-crop-startup-replay-implementation.md)도
웹383개·Chromium31개·실제 SCRAM/TLS/WebGL1개·12완료 시점/1,500 C/N mesh·정리로 로컬 수용했습니다.
[새 저장 모델의 화면](research/artifacts/startup-crop-desktop.png)을 확인할 수 있습니다.
빈 초기/제거 후 재유입의 원값과 명시적 로그 비교 3D를 연결합니다. 전체 작기 실행 계약은 수용했고
다음은 긴 결과 저장/같은 UTC·작기 부하 → 생과 환산입니다. 실제 품종/생산 예측과 pixel fidelity는 별도입니다.
자동 착과·생식기 이전/실제 초기 품종 계수는 보류입니다.
`e70a7f2`의 [최종 CI](research/artifacts/crop-coupled-api-web-ci-hold-20261005.json)는
기존 assessment HTTPS 30초 시간 초과 1개로 Backend 미수용이며 나머지 네 workflow는 성공했습니다.
동일 테스트의 로컬 최대 22.118초 통과와 요약 크기 수정은 [별도 기록](research/backend-ci-summary-and-timeout-20261005.md)에 있습니다.
후속 `590fadc`는 [CI 5개 모두 성공](research/artifacts/crop-coupled-replay-startup-rates-ci-20261005.json),
백엔드 3,157개·별도 UID 4개·여섯 동일 목록/정리·집계까지 통과했습니다.
후속 `d105daa`도 [CI5개 모두 성공](research/artifacts/crop-plant-startup-math-ci-20261005.json),
백엔드3,370개·별도UID4개·여섯 동일 목록/정리·집계로 새 기관 시작 RHS/적분/artifact까지 수용했습니다.
새 저장까지의 `92cade3`도 [CI5개 모두 성공](research/artifacts/crop-startup-storage-ci-20261005.json),
백엔드3,408개·별도UID4개·여섯 동일 목록/정리·집계로 수용했습니다.
API/client/3D까지의 `1555610`도 [CI5개/백엔드3,456개·별도UID4개](research/artifacts/crop-startup-replay-ci-20261005.json),
여섯 동일 목록/정리·집계까지 수용했습니다. 후속 `fe41e22`도
[CI5개/백엔드3,709개·별도UID4개](research/artifacts/crop-cycle-stream-ci-20261005.json),
여섯 동일 목록/정리·집계로 continuation/reader/긴 RHS까지 수용했습니다. 이어 `ff6eb3d`의
[CI5개/백엔드3,862개·별도UID4개](research/artifacts/crop-cycle-artifact-schema-roles-ci-20261005.json)도
여섯 동일 목록/정리·집계와 작성 경로 첫 시도7job까지 성공해 cycle artifact/schema/roles를 수용했습니다.
농장 결합과 아래 서버 실행은 이 CI SHA 밖이었습니다. 후속 `0f2925f`의
[CI5개/백엔드3,962개·별도UID4개](research/artifacts/crop-cycle-farm-server-ci-20261005.json)도
여섯 동일 목록/DB·비밀 파일 정리·집계와 작성 첫 시도7job를 통과했습니다. DB 후보는 이 SHA 밖입니다.
[기록 합성 데모의 3D·원값](research/artifacts/coupled-crop-replay-recorded-demo-geometry.png)과
[실제 저장 경로의 화면](research/artifacts/coupled-crop-replay-desktop.png)을 확인할 수 있습니다.
기록 데모는 운영 저장 목록이 아니며 실제 완료 6시점의 소프트웨어 검증입니다.
새 동일 UTC 3D 판본은 로컬 수용했고 다음은 전체 작기 실행·생과 환산입니다.
[전체 작기 실행 계약/원 격자 대사](research/crop-cycle-execution-contract.md)도 원 solver6프로그램/630걸음,
30분할·2,783개 float64 round-trip과 chunk/clock 반례로 로컬 수용했습니다. 이어 원 상태/누적량을
실제 RHS로 중단·복원하는 [순수 continuation](research/crop-cycle-continuation-implementation.md)도
157개·30실제 분할/JSON 복원과 별도 Python6개·726float64 대사로 로컬 수용했습니다.
[bounded 원 입력 reader](research/crop-cycle-input-stream-implementation.md)도64개·48,000자작 합성 구간/
48,003경계·독립 clock/grid·별도 Python 복원/정리로 로컬 수용했습니다.
[긴 입력/실제 RHS 연결](research/crop-cycle-stream-execution-implementation.md)도144개 집중·
25시간/11,400실제 걸음·별도 Python7개/847float64·사건 JSON/hash·원 수지/hold·정리로 로컬 수용했습니다.
[cycle 불변 파일/reader](research/crop-cycle-artifact-implementation.md)도58개 고유 분할 검증·
25시간/11,400실제 걸음·755,868bytes·별도 Python7개/847float64·실제 강제 종료2개/복구로
10월5일 로컬 수용했습니다. 읽기0.388759초/RHS0회이며 긴 결과의 웹 연결은 후속입니다.
[cycle 불변 DB 참조 schema](research/crop-cycle-storage-schema-implementation.md)도74개 고유 분할·
실제 SCRAM/네 기본 role 거부·정상 JSON128KiB 경계·불변/변조/rollback·기존 v3/정리로10월5일 로컬 수용했습니다.
[명시 role/config](research/crop-cycle-storage-roles-implementation.md)도 새21개/고유236개 분할 검증·
실제 네 SCRAM/선택 SELECT·INSERT·일곱 권한 drift·기존 v3/기본 false·정리로10월5일 로컬 수용했습니다.
다음 현재 권리 저장은 [농장/input root 결합](contracts/crop-cycle-farm-binding-v1.md) →
[실제 서버 계산/서명된 progress](contracts/crop-cycle-server-custody-v1.md) → DB 게시로 나눕니다.
첫3파일 [농장/root 결합](research/crop-cycle-farm-binding-implementation.md)은 고유54개 분할 검증·
실제 SCRAM/현재 권리·입력 변경/Unicode 수정·별도 Python/정리로10월5일 로컬 수용했습니다.
[실제 서버 계산/서명 저장](research/crop-cycle-server-custody-implementation.md)도 고유46개 분할 검증·
실제 SCRAM/현재 권리·강제 종료4개·별도 Python121float64 복원·정리로10월5일 로컬 수용했습니다.
25시간/11,400실제 걸음의27시점/5사건을 독립 제어 흐름과 대사했고 서명 저장은829,769bytes였습니다.
이 긴 참조는 마지막 invalid reader 정리 수정 전 판본이며 실제 품종/전체 작기 검증은 아닙니다.
[DB custody](research/crop-cycle-db-custody-implementation.md)도76개 고유 분할·실제 SCRAM/
25시간의 원 페이지·manifest 수정·정리로10월6일 KST 로컬 수용했습니다.
기존 DB2–3시간 예상은 이 실적으로 대체합니다. API/client → 같은 UTC3D → 작기 부하로 진행합니다.
짧은 실행 수용을 전체 작기 검증으로 표시하지 않습니다.
자동 착과/초기 작기·실제 품종은 보류합니다.
작기 처리 한도·국내 확보를 병행합니다. 앞선 `d251df9`는 전체 백엔드 2,671개·
별도 UID 4개와 CI 5개를 모두 통과했습니다. `d76410f`의 웹/C0/실제 앱 이미지·Compose CI도
통과했고 작성 경로의 새 저장→HTTPS→3D 시험도 통과했습니다.
`d76410f`의 전체 백엔드도 2,671개·별도 UID 4개와 여섯 동일 목록/정리·집계까지
통과해 [CI 5개 모두 성공](research/artifacts/crop-fruit-predecessor-ci-20261005.json)했습니다.
`78b5d17`의 과실 이동/배분 판본도 [전체 CI 5개](research/artifacts/crop-fruit-transport-allocation-ci-20261005.json)와
백엔드 2,840개·별도 UID 4개·여섯 동일 목록/정리·집계를 통과했습니다.
`784335d`의 순간 구획/기관 결합도 [전체 CI 5개](research/artifacts/crop-fruit-cohort-plant-ci-20261005.json),
백엔드 2,969개·별도 UID 4개·여섯 동일 목록/정리·집계를 통과했습니다.
`d15cf92`의 시간 적분/artifact·v2 저장/기본 policy 판본도 [전체 CI 5개](research/artifacts/crop-coupled-storage-ci-20261005.json),
백엔드 3,070개·별도 UID 4개·여섯 동일 목록/정리·집계까지 통과했습니다.
Application image/runtime 49개·세 Compose 정리도 통과했습니다.
API·웹 페이지/도형의 hosted 수용은 `590fadc`이며 이후 새 시작 모델/저장 판본 수용과 구분합니다.
다음은 **방울토마토 한 품종·한 작기의 생장 계산 → 불변 저장/같은 시점 성장 3D →
생과 생산량·자원·경제 연결**입니다. [수정 순서·잠정 작업량](tasks/plan.md#작물-생산과-성장-3d-우선순위-2026-10-04),
[모델/계수/권리 조사](research/crop-tomato-model-baseline-20261004.md),
[현재 수용과 다음 구획 결합의 기준](tasks/plan.md#현재-수용과-다음-한-단계)을 기록했습니다.
해외 Axiany 한 작기는 개발 참조이며 국내 독립 검증 자료는 아직 0건입니다.
모델 개발과 국내 측정 자료 확보를 병행합니다.

최종 첫 대상은 **대한민국 좌표 한 점·온실 한 구역·방울토마토 한 품종/작기**입니다.
**사업성은 핵심 기능**입니다. 현재 조건부 경제 계산은 입력한 판매량·가격·비용에
대한 마진·손익분기·월별 현금입니다. 생산/자원 모델과 결합할 때 수확·판매·구매
전력/연료를 각각 검증하고 모델값·가정·측정 등급을 유지합니다. 국내 미래 수확과
가격·판매량·마진, 작물 순위는 해당 독립 검증 전까지 판단 보류합니다.


작물 순위에는 **같은 지역·시설·평가 기간·목표에서 여러 후보를 비교한 독립 검증 자료**가 필요합니다. 이를 확보하는 일은 외부 협력에 달려 있으며, 작물별 모델만 따로 검증해 순위를 열지 않습니다. 각 평가에서 입력 실행과 후보의 자료·모델·현장·비교 관문(G0~G3)을 다시 확인합니다. 근거가 부족하면 **판단 보류**와 필요한 자료를 보여줍니다. G4 운영·권리·설치 검증 전 단계는 내부 시범이며 공개 production 서비스가 아닙니다.

## 현재 내부 웹 구현

[손익분기 비동기 검증 화면 후보](contracts/web-break-even-verification-v1.md)는
계산 완료 확인 → 검증 작업 요청 → 별도 검증 상태 → 현재 완료 결과 조회를 연결합니다.
검증 접수 응답을 잃으면 같은 계산 작업으로 재확인하며, 완료 전·취소·불일치에는
금액을 표시하지 않습니다([검증 기록](research/web-break-even-verification-implementation.md)).
최대 256개 취소/재시도/원천 권리 철회, 자동 운영 조립과 독립 CLI/G1/G4는 남아 있습니다.
[접수 성능 보완](research/break-even-admission-performance-implementation.md)은
같은 256개 ASGI 접수를 29.5103초로 확인했고, 집중 47개와 작업자·현재 결과 조회·
두 시험값의 실제 TLS 11개가 통과했습니다. 접수 보완 판본의 호스팅 백엔드 2,306개·
별도 UID 4개, 작성 141회·웹 160/51·C0도 통과했습니다. 실제 최대 HTTPS의
30초 시간 초과 반례는 입력 검사 보완 후 같은 256개 표준 인증 HTTPS 접수
29.6373초·동일 재접수 29.0140초로 로컬 통과했습니다. 같은 256개의 보호된 로컬 전체 경로도
75분 27초에 통과했습니다. 별도 계산·검증과 전체 결과 조회, 동일 접수 재사용·
현재 문맥 변경 후 금액 비표시·정리를 확인했습니다. 최초 접수 여유는 0.3627초로,
동시 처리량이나 production 응답 여유를 확인한 것은 아닙니다.

[경제·손익분기 작업 발견](contracts/deterministic-job-discovery-v1.md)은 고정 계정의
대기 작업을 읽기 전용 페이지로 찾고 기존 작업자가 임대·복구·완료를 처리하게 합니다.
실제 SCRAM을 포함한 집중 47개가 통과했습니다.
[자동 전경 소비](contracts/deterministic-worker-loop-v1.md)도 별도 Python/SCRAM을 포함한
37개 시험으로 경제·손익분기 계산/검증·종료·취소·강제 종료 뒤 회복을 확인했습니다.
[보호된 운영자 구성](contracts/operator-config-v1.md)은 명시적 비밀 파일과 신뢰된
의존성 factory를 기존 API에 전달합니다. 집중 45개로 파일/구성 검사, 실제 SCRAM·
표준 HTTPS/Bearer 기동·접수/조회·기동 후 권한 변경 차단·종료/정리를 확인했습니다.
발견·소비 판본 `c9bc689`의 호스팅 웹 160/51·작성 141회·C0는 통과했습니다.
전체 백엔드는 여섯 파트 성공 뒤 목록 해시 집계 실패로 수용을 보류했습니다.
[시험 목록 안정화](research/backend-inventory-repeatability-implementation.md)는 수집 시 생성한
UUID를 고정하고 새 전체 목록 회귀를 추가해 집중 18개와 여섯 동일 수집을 통과했습니다.
`4867c1f`의 실제 호스팅 백엔드 2,436개·별도 UID 4개와 모든 동일 목록/집계·정리,
작성 141회·웹 160/51·C0도 통과했습니다. 구성·발견·전경 소비의 소프트웨어 회귀를 수용했습니다.
[앱 이미지 수용](research/application-images-implementation.md)은 별도 target의 실제 Docker 빌드,
비특권 UID·읽기 전용·닫힌 기동·표준 TLS/잘못된 상위 DNS 거부와 정리를 확인했습니다.
[API·웹·자동 경제 작업자 Compose 후보](contracts/application-compose-runtime-v1.md)를 추가했고,
실제 서비스의 TLS/SCRAM 접수→자동 완료→현재 결과→동일 재시작·권한 변경 차단과
[정리도 통과했습니다](research/application-compose-runtime-implementation.md). 수집/CLI 운영 연결,
독립 자격증명 소유권·실제 제품 CLI/G1/G4는 후속입니다.
[조사 RPC 반복 소비](research/cli-dispatch-loop-implementation.md)는 실제 소켓 시험36개와
기존 결정적 소비37개, `7225546`의 전체 호스팅 백엔드2,455/별도UID4·작성141·웹160/51·
C0/앱 서비스 회귀를 통과했습니다. [수집 자동 소비](research/collection-consumer-implementation.md)도
실제 SCRAM95개로 자동 완료·취소/복구·부모 증거 훼손/권한 철회·정리를 확인했습니다.
같은 `394ff78`의 전체 hosted 백엔드2,489/별도UID4·작성141·웹160/51·C0/앱과 정리도 통과했습니다.
[수집 Compose 단계](research/collection-compose-runtime-implementation.md)는 실제 TLS/SCRAM 자동 저장·
동일 재시작·부모 증거 철회/권한 변경 차단·UID/자원과 정리를 통과했습니다.
[조사 RPC Compose 단계](research/authority-compose-runtime-implementation.md)는 `b8df8f9`에서
지역 접수→자동 서명/검증 보류·접근 거부·소켓 정리/동일 재시작·권한 변경 후 중단과 정리를 통과했습니다.
새 전체 회귀는 `d19f7c0`에서 통과했습니다. 결합된 소유 원천 경로·실제 모델·독립 해제/G1/G4는 미완료이며, 추가 운영 조립은 작물 핵심 경로의 구체적 필요에 따라 재개합니다.

[원천→농장 참조 제공자](contracts/source-farm-selection-v1.md)는 정확한 완료 조사·수집에서
이미 저장된 원본 스냅샷과 서명 문맥을 검증한다([SCRAM 집중 4개](research/source-farm-selection-implementation.md)).
같은 참조의 [인증 API](contracts/api-source-farm-selection-v1.md)와 표준 HTTPS 조립도
[집중 66개](research/api-source-farm-selection-implementation.md)로 확인했다.
같은 원천 문맥의 [저장 경제 후보 목록/현재 선택](contracts/farm-economic-candidate-selection-v1.md)과
[인증 API](contracts/api-farm-economic-candidate-selection-v1.md)도
[SCRAM 5개](research/farm-economic-candidate-selection-implementation.md)와
[집중 64개·실제 HTTPS 20개 전체 응답](research/api-farm-economic-candidate-selection-implementation.md)으로 확인했다.
조회는 새 입력이나 승인을 발급하지 않는다. [농장 작성 화면 연결 후보](research/source-farm-web-implementation.md)는
저장된 완료 조사·수집과 경제 판본을 선택하고 참조만 읽기 전용으로 옮긴다.
조합 변경·동의 취소·응답 유실·재연결을 집중 Chromium 14개로 확인했으며
실제 HTTPS/SCRAM 신규 등록→검토/Run→3D의 두 경로도 통과했다.
같은 새 Run의 서버 금액·월별 현금·평가 보류·재접속·동일 3D도
[실제 HTTPS/SCRAM 집중 1개](research/source-farm-financial-continuation-implementation.md)로 확인했다.
같은 새 Run 연결의 호스팅 작성 7개 묶음·웹/C0도 통과했다.
[화면 보완](research/source-farm-layout-refinement-implementation.md)은 참조 상세 펼치기,
넓은 화면의 나란한 요약과 키보드 구역 이동을 확인했다.
`93e30a7`의 [최종 UI 소프트웨어 수용](research/source-farm-web-implementation.md#final-software-ui-acceptance-2026-10-01)은
호스팅 웹 154/50개와 작성 브라우저 4개에서 저장 원천 선택→신규 농장 등록→경제/평가·동일 3D를 확인했다.
본문 최대 26.3284초이며 낮은 디자인 일치율은 기록된 한계다. 별도 경제 브라우저 1개 실패와
[후속 권한 감사 지연 보완](research/runtime-role-audit-batching-implementation.md#all-role-query-batching-follow-up-2026-10-01)은
분리하여 검증한다. `7f49f52`에서 작성 7개 묶음 139회·웹/C0가 통과했고 별도 경제 브라우저의
29개 전체 본문 최대는 17.0664초다. 같은 판본의 전체 백엔드 2,253개·UID 4개와 정리가 통과해
권한 감사 보완을 소프트웨어 범위에서 수용했다. 실제 제품 CLI·독립 G1/G4 수용은 남아 있다.

[07 작성 Run 경제·평가](contracts/web-authored-economic-assessment-v1.md)는 저장 Run을 선택해
같은 농장에 고정된 V3 경제 입력으로 계산을 요청하고, 서버 금액·월별 현금·보류 6개·같은 3D Run을 확인한다.
재연결 후 저장 기록을 선택할 수 있으며 미확인 접수는 같은 요청으로 재확인한다
([웹 단위 122개·집중 Chromium 19개·실제 HTTPS/SCRAM 브라우저 1개](research/web-authored-economic-assessment-implementation.md)).
시험용 CLI·서명의 소프트웨어 범위다. 일반 지역 흐름과 실제 제품 CLI·독립 G1/G4는 남아 있다.

[작성 Run의 경제 입력·작업 이력 조회](contracts/authored-financial-selection-v1.md)는
현재 농장에 고정된 경제 입력 V3와 같은 Run의 경제·평가 작업을 서버에서 다시 찾는 웹 선행 기능이다
([집중 시험 59개](research/authored-financial-selection-implementation.md)).
이력 선택 뒤에는 실제 결과를 현재 권리로 다시 조회해야 한다. 위 07 화면이 이 조회와 작성 경제·평가를 연결한다.

[작성 Run의 경제 실행 후보](contracts/authored-economic-execution-v1.md)는 현재 농장 판본과
실제 완료 작성 Run을 별도 경제 입력/영수증 V3에 묶고 기존 금액·월별 현금 조회를 제공한다
([SCRAM·HTTPS/OpenAPI 검증](research/authored-economic-execution-implementation.md)).
작성 Run의 공통 평가 서버 연결도 아래 후보에 추가했다. 웹 부모 선택은 위 07 후보에 연결했고 실제 제품 CLI·독립 G1은 후속이다.

[작성 Run 평가 연결 후보](contracts/authored-calculation-assessment-v1.md)는 실제 완료 작성 열·경제 작업을
평가 입력 V3에 고정하고 별도 CLI 검증기로 기존 보류 6개를 저장·조회한다
([SCRAM·HTTPS 검증](research/authored-calculation-assessment-implementation.md)).
현재 권리·해제·입력 해시와 부모의 문맥을 재검사하며 혼합·변조·늦은 변경을 거부한다.
가짜 CLI와 시험 서명으로 확인한 서버 경로이며 실제 제품 CLI·독립 G1은 남아 있다.

[06 계산 평가 화면](contracts/web-calculation-assessment-v1.md)은 같은 조건의 완료 열·경제 작업을 서버에 접수하고, 저장된 평가 상태·보류 근거를 조회하거나 재연결 후 다시 엽니다([실제 HTTPS/SCRAM·브라우저 증거](research/web-calculation-assessment-implementation.md)). 현재 운영자 작업 식별자 입력 경로이며 일반 지역 흐름의 자동 연결, 작성 농장의 웹 경제·평가 부모 선택과 실제 제품 CLI·독립 G1 수용은 남아 있습니다.

합성 열/계산 기반 성장 3D는 [로컬 데모 실행법](web/README.md#지금-3d를-직접-보기)에 따라 직접 볼 수 있습니다. 성장 화면은 기록된 공개 합성 계산의 재생이며 실제 품종의 생산·사업성 예측은 아닙니다.

[지역 조사→원본 수집→수집 입력 검토 화면 후보](research/web-owned-source-workflow-implementation.md)를 내부 웹에 연결했습니다. 실제 서버 작업 상태와 검토 보류를 단계별로 조회하지만, 합성 자료 작업 완료가 실제 원천 G0 승인이나 Run 게시를 뜻하지는 않습니다.
[저장된 원천 작업 이력 후보](contracts/api-owned-source-history-v1.md)는 재연결 뒤 같은 계정의 조사 기록을 찾고 선택한 조사의 최근 수집·검토 작업과 이전 시도 목록을 복원합니다([소프트웨어 검증](research/owned-source-history-implementation.md)). 현재 원천·문맥을 확인할 수 없는 기록은 이력으로만 보이며 새 접수는 보류합니다.

[첫 웹 화면](web/README.md)은 등록된 합성 좌표·UTC 기간의 조사 요청, 실제 작업 상태와 보류 근거 조회를 구현한 후보입니다. [경제 화면](contracts/web-economic-workspace-v1.md)은 저장 가정 조회·새 숫자 판본 등록, 선택 원장/수급·거시 공동 가정의 계산 요청과 완료 서버 결과를 연결합니다. 새 숫자의 권리 확인·공동 가정 판본 등록·선택과 [월별 현금 조회](research/web-economic-cash-implementation.md)를 연결하는 후보를 추가했습니다. [손익분기 화면 후보](contracts/web-break-even-workspace-v1.md)는 기존 판매·수금과 저장된 시험 판본을 선택하고 계획·완료 결과를 조회하며 응답 유실 시 저장 접수 기록을 확인합니다([검증 기록](research/web-break-even-workspace-implementation.md)). 일반 원장·정산 작성, 지역 선택에서 농장 작성까지의 자동 연결, 자동 시험 가정 생성과 새로고침 후 복구는 남아 있습니다. [첫 웹 검증 기록](research/web-location-shell-implementation.md)에는 실제 HTTPS API·PostgreSQL과 브라우저 연결 시험이 있습니다. 그 시험의 CLI는 직접 작성한 가짜 실행기이며 실제 모델·전체 농장/경제 입력·3D를 포함한 종단 간 G1·공개 운영 수용은 남아 있습니다.

열·경제 입력을 함께 고정하는 [농장 재생 계획 등록 후보](contracts/farm-replay-scenario-v1.md)를 추가했습니다. 등록된 조사 좌표·기간, 열 시나리오와 경제 판본의 해시, 서명 문맥·결정 시각·시장 보류를 검사하고 실제 작업 저장소에 변경 불가 입력을 남깁니다([검증 기록](research/farm-replay-scenario-implementation.md)). 등록은 입력 선택 의도이며 전체 농장 작성·열과 비용의 물리적 결합·공통 평가 연결·3D·전체 G1 수용은 남아 있습니다.

[농장 계획을 사용하는 열 실행 후보](contracts/farm-thermal-execution-v1.md)는 새 입력/영수증 v3로 접수·계산·완료 조회를 연결합니다. 같은 계획 판본과 실제 완료 조사·수집·검토의 연결을 재검사하며, 현재 권한이 없거나 다른 조사 작업이면 보류합니다([소프트웨어 검증](research/farm-thermal-execution-implementation.md)).

[농장 경제 실행 후보](contracts/farm-economic-execution-v1.md)는 같은 계획과 실제 완료 열 작업을 경제 입력/영수증 v2에 연결하고, 금액·월별 현금 조회에서도 현재 연결을 검사합니다([검증 기록](research/farm-economic-execution-implementation.md)). 전체 평가·열과 구매 에너지/비용의 물리적 결합·실제 CLI와 독립 G1/G4 수용은 남아 있습니다. [첫 내부 3D 열 재생 뷰어](contracts/web-thermal-replay-v1.md)를 구현했습니다. 저장된 합성 계산의 온도·습도·모델 열수요/공급열을 같은 시각의 장면·그래프·표로 확인합니다([검증 기록](research/web-thermal-replay-implementation.md)). 실제 서버 Run 연결과 WebGL 장애 시 HTML 대체를 시험하는 내부 후보이며, 작물 생장·수확 예측과 전체 G1/G4 수용은 남아 있습니다. [공통 Assessment 연결 후보](contracts/farm-calculation-assessment-v1.md)도 구현했습니다. 실제 HTTPS 접수·재요청과 가짜 CLI 보류 조회, 혼합 거부·거래 롤백·기존 경로 호환 시험을 확인했습니다([진행 기록](research/farm-calculation-assessment-implementation.md)). 전체 농장 입력 작성의 [첫 제공자](contracts/farm-inputs-v1.md)를 구현했습니다. 명시적 시설·제어값을 실제 열 수식 입력으로 변환하고 재배 면적·달력과 경제 배치/날짜 범위를 검사합니다([검증 기록](research/farm-inputs-implementation.md)). [내부 영속 등록 후보](contracts/farm-authoring-storage-v1.md)는 실제 조사·문맥·경제 후보와 사용자 권리 선언, 작성한 계산 입력을 변경 불가 판본으로 묶습니다([검증 기록](research/farm-authoring-storage-implementation.md)). 작성된 스냅샷의 독립 검토·해제, 실제 작업자 실행, 공개 API와 전체 작성 화면 연결은 다음 단계입니다.

[작성 입력 열 궤적 후보](contracts/farm-thermal-candidate-v1.md)는 저장된 농장 판본에서 120개의 온도·습도·공급열 계산 시점을 재현합니다([검증 기록](research/farm-thermal-candidate-implementation.md)). 이 후보 자체는 승인 Run이나 3D 게시 대상이 아닙니다.
[작성 입력 검토 접수 후보](contracts/farm-authored-review-v1.md)는 이 궤적의 입력·두 결과 해시를 기존 CLI 검토 작업에 묶습니다([검증 기록](research/farm-authored-review-implementation.md)). [완료 검증 후보](contracts/farm-authored-review-completion-v1.md)는 저장된 결정·캡처·서명 실행 증거를 대사합니다([시험 기록](research/farm-authored-review-completion-implementation.md)). [독립 해제 검증 후보](contracts/farm-authored-release-v1.md)는 현재 코드·입력과 별도 검토자의 서명·보고서 원문을 묶고, [영속 저장 후보](contracts/farm-authored-release-store-v1.md)가 패킷을 변경 불가하게 보존·재검사합니다([시험 기록](research/farm-authored-release-store-implementation.md)). 실제 제품 CLI 실행과 독립 해제 발급·G1 수용은 후속입니다.
[작성 입력 Run 준비 후보](contracts/farm-authored-run-preparation-v1.md)는 유효한 저장 해제와 현재 농장 판본을 다시 확인한 뒤 120개 계산 시점의 최종 두 궤적·해시·Run ID를 준비합니다([시험 기록](research/farm-authored-run-preparation-implementation.md)). 이후 작성 작업자가 이 바이트를 게시하고 별도 API·3D 화면이 조회할 수 있습니다. [합성 서비스·브라우저 연결 시험](research/authored-full-software-path-implementation.md)은 미리 등록한 판본 조회부터 브라우저의 신규 검토·계산 작업 접수, 시험용 CLI 검토·서명 해제, 저장 Run의 실제 Chromium 3D 재생까지 확인했습니다. 사용자 농장 작성·수집과 실제 제품 CLI·독립 해제는 아직 한 흐름으로 검증되지 않았습니다.
[작성 Run 저장 후보](contracts/farm-authored-run-store-v1.md)는 별도 불변 테이블에서 작업 완료와 원자 저장·재조회를 검사합니다([시험 기록](research/farm-authored-run-store-implementation.md)). 제품 CLI·독립 검토 발급과 전체 G1 증거는 남아 있습니다.
[작성 simulation 접수 후보](contracts/farm-authored-simulation-v1.md)는 현재 작성 입력·서명 해제·최종 궤적을 다시 확인하고 동일 요청을 변경 불가 작업 하나로 등록합니다([시험 기록](research/farm-authored-simulation-implementation.md)).
[작성 simulation 작업자 후보](contracts/farm-authored-simulation-worker-v1.md)는 임대한 작업의 Run·영수증·완료를 같은 거래에서 게시하고, 취소·만료·오류 때 부분 Run을 되돌립니다([SCRAM 시험](research/farm-authored-simulation-worker-implementation.md)). 현재 시험은 가짜 CLI와 합성 해제를 사용합니다. 실제 제품 CLI·독립 해제/G1은 남아 있습니다.
[작성 농장 웹 작업 후보](research/authored-farm-web-workflow-implementation.md)는 농장 수치와 권리 선언을 직접 입력해 등록하고, 저장된 판본을 조회해 검토·열 계산 작업을 접수하며, 완료된 저장 Run의 3D 화면으로 이동합니다. [저장 판본 목록](research/authored-farm-catalog-implementation.md)에서 같은 계정의 등록 입력을 다시 찾고 선택할 때 현재 권리와 해시를 확인할 수 있습니다. [검토·계산 작업 이력 후보](research/authored-farm-activity-implementation.md)에서 재연결 후 저장된 작업을 선택해 상태와 연결된 Run을 다시 열 수 있습니다. 같은 계정의 [완료 Run 목록](research/authored-run-catalog-implementation.md)도 농장 선택 없이 조회하고, 선택할 때 현재 단건 조회를 거쳐 3D로 이동합니다. 작성 폼은 기존 조사·원본·시장 보류·경제 판본의 식별자를 요구하는 내부 도구이며 이 자료를 자동으로 찾거나 농업 수치를 제안하지 않습니다. 합성 HTTP Chromium 시험과 로컬 PostgreSQL 16.15/SCRAM·HTTPS 전체 소프트웨어 경로가 통과했고 호스팅 백엔드 CI는 확인 중입니다. 실제 제품 CLI·독립 해제와 G1 수용은 남아 있습니다.
[작성 Run 조회 API 후보](contracts/api-authored-thermal-run-v1.md)는 완료 작업과 별도 작성 Run ID를 인증된 요약·120시점 열 응답에 연결합니다([시험 기록](research/api-authored-thermal-run-implementation.md)). [작성 Run 3D 화면 후보](contracts/web-authored-thermal-replay-v1.md)는 브라우저의 실제 3D·그래프·표를 같은 저장 시점에 연결하고 합성 응답으로 확인했습니다([화면 캡처](research/artifacts/authored-thermal-replay-desktop.png), [검증 기록](research/web-authored-thermal-replay-implementation.md)). [표준 HTTPS 작성 Run 조립 후보](contracts/api-runtime-authored-run-v1.md)와 작성 폼→신규 작업→저장 Run→브라우저의 합성 시험도 있습니다. 일반 사용자 원천 입력 흐름, 실제 제품 CLI·독립 해제/G1은 남아 있습니다.
[저장 작성 Run 전체 목록 API 후보](contracts/api-authored-thermal-run-v1.md)는 같은 계정의 완료 Run 식별자를 다시 찾되 현재 표시 가능 여부는 정확한 Run 조회에서 재검사합니다([검증 기록](research/authored-run-catalog-implementation.md)). 내부 웹은 이 목록을 페이지별로 읽고 현재 단건 조회가 실패하면 3D 표시를 보류합니다.
[작성 농장 입력 API 후보](contracts/api-farm-authoring-v1.md)는 기존 불변 입력 등록부에 인증된 등록·재조회 경로를 추가합니다. 합성 자료의 권리와 입력 연결을 현재 시점에 다시 검사하며, 등록 자체는 계산 완료나 작물 추천을 뜻하지 않습니다.
[작성 입력 검토 접수 API 후보](contracts/api-farm-authored-review-v1.md)는 등록된 입력 해시를 다시 확인하고 검토 작업을 대기열에 넣습니다([로컬 검증 기록](research/api-farm-authored-review-implementation.md)). 접수만으로 CLI 검토나 독립 해제가 완료되지는 않습니다.
[작성 Run 접수 API 후보](contracts/api-authored-simulation-admission-v1.md)는 독립 해제 기록이 준비된 판본만 다시 확인해 시뮬레이션 작업을 접수합니다([로컬 검증 기록](research/api-authored-simulation-admission-implementation.md)). 작업자가 완료·게시하기 전에는 3D 조회 결과가 아닙니다.

## 문서 읽는 순서

1. [입문 안내](docs/DOMAIN_PRIMER.md): 농업과 시뮬레이션의 기본 개념
2. [제품 명세](docs/PROJECT_SPEC.md): 사용자 흐름, 추천의 의미, 수용 기준과 단계
3. [자료·연구 기준선](docs/RESEARCH_BASELINE.md): 입력 자료, 출처, 권리, 결측 처리, 모델 근거
4. [아키텍처](docs/ARCHITECTURE.md): 구성 요소, API·작업·실행 기록 계약과 운영 요건
5. [비용·마진 계약](docs/ECONOMICS.md): 가격·원가 증빙, 손익·현금흐름, 손익분기와 검증 경계
6. [시장·거시 명세](docs/MARKET_INTELLIGENCE.md): 수요·공급·출하기 가격과 비용 시나리오, 결정 시점 자료와 전망 검증
7. [기술 스택](docs/TECH_STACK.md): 필수/선택 소프트웨어와 이유, 버전·배포 정책, 외부 의존성
8. [한국어 설계 백서](docs/whitepaper/README.md): 근거·수식·경제 계산과 검증 관문을 통합한 설계 제안
9. [에이전트 작업 지침](AGENTS.md): 개발 판단·증거·검증의 기본 절차
10. [첫 구현 슬라이스](docs/IMPLEMENTATION_SLICE.md): 내부 완주 경로와 시험 가능한 경계
11. [구현 준비 현황](docs/IMPLEMENTATION_READINESS.md): 관측된 도구·자료·권리·외부 증거 상태
12. [구현 순서](tasks/plan.md): 의존성·체크포인트·외부 증거 경로
13. [구현 작업 목록](tasks/todo.md): 작은 작업별 수용 기준과 확인 절차
14. [첫 화면 설계 기준](docs/UI_DESIGN.md): 합성 재생·조건부 경제·보류 표시와 접근성

## 라이선스와 공개 범위

이 저장소에서 새로 작성하는 코드와 문서는 [Apache License 2.0](LICENSE)으로 공개합니다([OSI 승인 목록](https://opensource.org/licenses), [공식 원문](https://www.apache.org/licenses/LICENSE-2.0.txt)). 이 선택은 기상청·FAO·WUR 등의 자료나 외부 라이브러리·3D 자산에 권리를 부여하지 않습니다. 각 자료와 자산은 원래의 이용조건을 따르며, 공개 배포 전에 개별 권리와 출처표시를 확인합니다. 설치 가능한 사용자 서비스는 아직 없습니다. [직접 작성한 합성 입력](fixtures/README.md)은 소프트웨어 계약 시험용으로만 공개하며, 실제 농장 관측·시장 자료나 검증된 예측 결과가 아닙니다.

사용자는 농업 배경지식이 없어도 범위와 한계를 이해할 수 있어야 합니다. **Codex CLI `gpt-6.1-sol` `xhigh`는 개발 중 조사·설계에도, 배포 제품에서 지역 선택 후의 자료 조사·수집 판단과 작물 판단에도 필수**입니다(2026-10-01 변경). [런타임 작업자 계약](docs/ARCHITECTURE.md#필수-codex-cli-런타임-작업자)에 호출·격리·기록·실패 시 보류를 명시했습니다. 기존 DB는 [모델 이전 계약](contracts/cli-model-policy-migration-v1.md)에 따라 과거 실행 기록을 보존하며 변경합니다. 실제 배포 계정의 모델 접근, 인증·계약 조건, 한도·비용은 아직 검증되지 않아 공개 출시 전에 확인해야 합니다. 계산 모델의 고정 입력 재실행과 새 AI 판단은 서로 다른 작업입니다.
