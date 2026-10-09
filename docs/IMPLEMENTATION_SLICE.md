# 첫 구현 범위

**2026-10-09 전체 수확 후속:** [정상 전체 저장·등록·복원](../research/crop-harvest-full-writer-completed-20261009.md)은
원96517/별도 root3349 실제0·47,813행 독립 Decimal·인증 backup·fresh 현재 권리/원값·정리로 로컬 수용했다.
[요청 범위 조회/전체 보호 API](../research/crop-harvest-current-read-cost-20261009.md)는 집중238개·실제 DB와
같은 전체 HTTPS7응답으로30초 timeout을 해소했다. 원 서명·시각·원량/권한/정리와30초/2MiB는 유지했다.
[실제 전체 API/대표 WebGL](../research/crop-harvest-full-view-20261009.md)도 원72505/별도 root 종료0·
원6수확/10생장 시점/5사건·권한/늦은 정상 응답 정리·자원/소유 정리로 수용했다.
[조기 연결 종료 보완](../research/crop-harvest-early-disconnect-20261009.md)은149개·실제 같은 DB/TLS의500→422·조회0,
정상 원 wire/현재 권한·원 종료/정리로 수용했다.
[전체 수확 사용자 전환](../research/crop-harvest-full-user-preview-20261009.md)은 실제5173/8445에서 원 수확3행과
같은 UTC WebGL·독립 root, 기존37119 종료0/PG 정리·새24180 생존/원본·FD·WSL 한도를 통과했다.
전체 질량 부하/수확 replay는 명시된 합성 소프트웨어 범위로 수용한다. 일반 압축 빌드의 WSL 보완은 별도 보류다.
현재 UI는 완료 생장/수확을 읽는다. **계산 진행 상태·새 checkpoint의 실시간 U3와 최종 통합 UI는 미구현**이다.
후속은 기후/물·양분/구매 에너지→사용자 실행/Decimal 경제이며 실제 자료·G0–G4/예측·추천 보류를 유지한다.

**2026-10-09 첫 동적 기후 자식:** [고정 LAI의 별도 수관·공기·수증기 계산](../research/crop-canopy-air-dynamics-implementation-20261009.md)은
새56/기존230=286개·원62863/별도2945 실제0·독립 Decimal/수렴·원본/미리보기/WSL 한도를 통과했다.
[새 결합 계약](../contracts/crop-climate-coupling-v1.md)은 기존 aggregate 열 v1과
121상태/상수 온도합 clock을 재사용하지 않는 경계를 고정한다.
**2026-10-10 가변 용량 자식:** [총 용량 운반·적엽](../research/crop-canopy-energy-transport-implementation-20261010.md)을
새48/기존364=412개·독립195스칼라/원 종료·원본/미리보기/FD·WSL 한도로 수용했다.
합성 용량 재고 경계이며 실제 잎 수분/물성/대사열 채택은 없다.
**2026-10-10 공동 순간 RHS:** [같은 trial의 작물·기후 연결](../research/crop-climate-joint-rhs-implementation-20261010.md)을
새51/기존412=463개·독립1,290스칼라·원 종료/원본/미리보기·자원 한도로 수용했다.
signed Uref/현재 leaf에서 유도한 Tc를 crop/교환/T24/Tsum에 함께 사용한다.
[짧은 공동 적분](../research/crop-climate-joint-integration-implementation-20261010.md)은 새44/기존463=507개·
독립798수치/60수렴 비율·원 종료/보존으로 수용했다. 사건 없는32초의108상태/22장부 범위다.
[원자적 관리](../research/crop-climate-joint-management-implementation-20261010.md)도 새69/기존507=576개·
독립3,728수치/60수렴 비율·원 실패 재현/수정·원 종료/보존으로 수용했다. 순수 사건/명시 시험 구성 범위다.
[자동 구간/사건 실행](../research/crop-climate-joint-boundary-implementation-20261010.md)을 새72/기존576=648개·
독립5,973수치/60수렴 비율·원 종료/보존으로 수용했다. 명시 상수 입력의 짧은 구간/사건 범위다.
[분할 실행/복원](../research/crop-climate-joint-continuation-implementation-20261010.md)을 새138/기존648=786개·
독립5,973수치/60수렴 비율·fresh 복원/원 종료·보존으로 수용했다.
[UTC 결속](../research/crop-climate-joint-time-implementation-20261010.md)도 새130/기존786=916개·독립272시각,
원5,076수치·context/checkpoint/prefix 보존·fresh/재계산0·원 종료/자원으로 로컬 수용했다.
[불변 페이지 저장/fresh 조회](../research/crop-climate-joint-storage-implementation-20261010.md)도 새77/기존916=993개·
원5,076수치/46시각 보존·reader 계산0·실제 HEAD 전후 중단/재개·원 종료/자원으로 로컬 수용했다.
다음은 새 입력 검증 증거→현재 농장/자료 권리·server custody/등록/API→같은 시각3D며 온실 경계 조사는 병행한다.
전체 결합·실시간 U3·실제 자료/생산 관문은 미완료다.

**2026-10-09 사용자 확인 화면과 최종 UI:** 기존 App의 실제 API/저장 결과 동시 기동을
먼저 제공하고, [U0–U5 통합 순서·잠정 일정](../tasks/plan.md#최종-제품-ui-통합--2026-10-09-사용자-요청)과
[각 단계 수용 기준](../tasks/todo.md#최종-제품-ui-통합-2026-10-09)을 추가했다.
첫 다음 UI 구현은 현재 계정의 저장 생장·수확 목록/선택(U1)이다. 지역/입력(U2) 준비와
독립 자료 확보를 병행할 수 있으며 전체 수확→기후/자원→경제의 계산 우선순위를 유지한다.
내부 동시 기동, 개별 화면, 최종 통합 UI와 실제 예측/추천·공개 운영의 수용은 각각 기록한다.
[U1 metadata 서버 자식](../research/crop-result-catalog-metadata-implementation-20261009.md)은
현재 권리·원 서명 metadata의 생장/수확 목록까지 로컬 수용했다.
[보호 API/등록 비용 보완](../research/crop-result-catalog-api-implementation-20261009.md)도
집중296개·실제 SCRAM/HTTPS14응답/생장21건·수확1건·최대20건6.483초·원 종료/정리로 로컬 수용했다.
[등록 작물 조회](../research/crop-result-farm-selection-implementation-20261009.md)도 집중348개/실제HTTPS22응답으로 로컬 수용했다.
[두 SDK의 현재 웹1,011개/타입/빌드](../research/web-crop-farm-selection-client-implementation-20261009.md)는
원66094 종료0/19.046초·원source/미리보기·소유 정리로 로컬 수용해 이전 빌드 자원 보류를 해소했다.
[목록 선택→기존 재생 후보의 hosted 회귀](../research/crop-ui-web-hosted-regression-20261009.md)는
동일 웹 소스에서 타입/웹1,028개·일반 빌드/audit·Chromium140개(skip0)를 통과했다.
목록 후보 코드는 현재 기동 빌드에 포함됐으나 기본 수동 조회를 사용한다. 원3상태 디자인 대조·실제 공동 DB 목록 선택·WSL 자원 수용은 남았다.
U1과 같은 실행의 상태/완료 결과를 잇는 실시간 U3는 미완료다.

**2026-10-04 개정:** 기존 열·경제 내부 경로의 계약을 보존하고 다음 구현은 §7의
작물 생장·저장·성장 3D로 진행한다. 첫 작성 시점의 구현 현황은 아래에 남겨두며,
현재 운영 완료 범위와 CI는 [고정 기록](../research/crop-priority-and-runtime-freeze-20261004.md)을 따른다.

**당시 실행 상태 — 2026-10-09 17:46 KST:** [완료 전체 생장 부모의 실제 API·3D/사용자 기동](../research/crop-full-parent-api-view-preview-20261009.md)을 로컬 수용하고 `http://localhost:5173/`을 전환했다.
원7678 실제 도구0/119.766초·같은 실제 SCRAM/보호 HTTPS/제품 App·WebGL에서
고유5시점의50 C/N·LAI/기관값과5관리 사건의 원 UTC·값, 현재 권리/계정 거부·복원,
조회 RHS/행 생성/게시/증명0·FD/원본2,146항목·검증 PG/소유 정리를 확인했다.
지정 single-process Chromium의 단일/관측 합 RSS418,369,536/1,000,091,648bytes로512MiB/1GiB 안이다.
원59276 도구0의 기동 뒤 frontend/보호 summary200·원 bytes 일치로47,809저장 시점/5사건/1,816,704완료 걸음을 확인했다.
[전체 부모의 모든 행/121상태 대사·정상 게시/보존](../research/crop-harvest-full-parent-restored-20261009.md)은 선행 수용을 유지한다.
[조회 사실 묶음](../research/crop-cycle-calculation-query-facts-20261009.md)은 main f79ef64, 시점 이동은532c494로 통합했고 미리보기는 별도 고정 source를 사용한다.
window40개/타입과 압축을 끈 제품 빌드가 통과했다. 일반 압축 빌드의 WSL 메모리 실패는 남기며 운영 용량 수용은 별도다.
현재 화면은 **완료 전체 합성 생장 결과의 조회/수치3D 재생**이다. 수확 미등록·실시간 U3 미완료이며 원3시점 예제는 정상 종료했다.
다음은 전체 수확의 남은 읽기 비용 경계 확정→정상 writer/registry·독립 Decimal 대사/보존→
수확 API/3D→기후/물·양분/구매 에너지→사용자 실행/Decimal 경제다.
원 Backend37892105708은0/1/2/4 성공·3/5 실패·집계 failure로 종료했다. 두 CI 자식과 U1/U3·실제 품종/독립 자료·G0–G4/생산/미래 마진/추천 hold는 유지한다.
아래 시각이 붙은 기록은 당시 관측이며 현재 실행 상태의 증거로 사용하지 않는다.

**당시 진행 관측 — 2026-10-09 10:02 KST:** [새 전체 부모 실행](../research/artifacts/crop-harvest-parent-full-started-reference-20261009.json)을09:12 KST 시작했다.
동일 원 모델/입력의 새166일 계산 판본이며10:02 KST 같은 프로세스의 확정 checkpoint는243,447걸음/commit61이다. 완료/수용은 아니다.
원9시간 상한18:12 KST·이전 전체7시간15분 근거의16:12–18:12 종료 추정은 조건부다.
모든 원 행/121상태 대사→정상 게시/인증 보존→원 DB 정리 후 fresh 복원·원 종료/자원 감사 뒤 전체 부모를 평가한다.
수확 writer/API/3D와 기후/자원/경제·실제 자료 관문은 후속이다.

**최신 수용 — 2026-10-09 10:02 KST:** [새 부모의 작은 수확 저장·보존](../research/crop-harvest-storage-preservation-small-implementation-20261009.md)을
원52100 종료0·집중10개/실제 DB1개·DB 정지 후 fresh 현재 조회로 로컬 수용했다.
원5행/UTC·Decimal 독립 대사·서명/최초 시각·현재 권리/계정·조회 재계산0과 원 입력/artifact/FD·소유 정리를 확인했다.
전체249.050초/900초·raw330,541bytes·동시 전체 계산 포함 RSS 합701.11MiB다. 작은 저장 자식만 완료했다.
전체 부모는10:02 KST 같은 프로세스에서243,447걸음/commit61로 진행 중이며 원18:12 마감/수용 보류를 유지한다.
다음은 전체 부모 최종 감사→전체 수확 writer/registry→실제 API/대표3D→기후/자원/Decimal 경제다.
실제 품종/농장 Run/국내 독립 자료0건·G0–G4/생산/미래 마진/추천 hold와 운영 기반 고정을 유지한다.

**선행 수용 — 2026-10-09 09:10 KST:** [정상 producer와 인증 보존의 작은 구성](../research/crop-harvest-parent-production-small-implementation-20261009.md)을
원17264 종료0·집중11개/실제 DB1개·원 DB 정리 후 현재 checkout의 fresh 복원으로 로컬 수용했다.
고정 `dc7b852`의 원392 source guard를 유지하고 작은120걸음/3시점/3사건·121상태/수지를 fresh 대사한 뒤 정상 게시·인증 보존했다.
전체101.710초/600초·raw308,638bytes·단일/소유 RSS130.61/355.31MiB·1,400 source·소유 정리를 확인했다. 작은 구성만 완료다.
다음은 같은 원 모델/입력의 새 전체166일 계산·모든 원값/현재 query 복원→새 source/profile의 전체 수확 writer/등록→실제 API/대표3D다.
전체는 준비부터9시간 상한·이전7시간15분 근거로7–9시간 잠정이며 실제 종료/정리 전에는 수용하지 않는다.
그 뒤 기후/물·양분/구매 에너지→사용자 실행/Decimal 경제다. 실제 품종/농장 Run/국내 독립 자료0건·G0–G4/생산/마진/추천 hold를 유지한다.

**선행 수용 — 2026-10-09 09:00 KST:** [작은 부모 DB·인증 자료 보존](../research/crop-harvest-parent-backup-implementation-20261009.md)을
원90143 종료0·집중11개/실제 DB1개·원 DB 정리 후 fresh Python 복원으로 로컬 수용했다.
원120걸음/3시점·서명/원량/UTC와 현재 권리·계정/변조 거부, 조회 RHS0·1,480 source·소유 정리를 확인했다.
전체81.287초·raw backup307,294bytes·단일/소유 RSS129.76/388.52MiB다. 이 보존 자식만 완료했다.
기존 전체166일의 DB/config/무작위 서명 key 삭제로 원 인증 복원은 불가하다. 후속에는 같은 모델/입력의 새 전체 계산 판본이 필요하다.
다음은 작은 정상 producer+보존 구성→새 전체 계산/원값 대사·현재 query 복원→새 source/profile 판본의 전체 수확 writer/등록
→실제 API/대표3D→기후/물·양분/구매 에너지→사용자 실행/Decimal 경제다.
종전 첫 복원2–4시간 추정은 철회한다. 이전 전체7시간15분을 근거로 준비 검증 후7–9시간 실행·대사를 잠정 잡고 후속 완료일은 실측 뒤 정한다.
실제 품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4/생산/미래 마진/추천 hold와 운영 기반 고정을 유지한다.

**선행 수용 — 2026-10-09 02:48 KST:** [전체 수확 수량·용량 대사](../research/crop-harvest-full-capacity-implementation-20261009.md)를
원78826 종료0·집중38개·전체 명령85.238초·1,474 source/원본/FD identity·소유 정리로 로컬 수용했다.
원47,809시점/5사건에서47,813행을 RHS0으로 만들고 Decimal 독립 수량/반올림 수지와 단위·목적·미배정을 대사했다.
748page/307,675,603bytes·root/HEAD/atomic 예약 상한311,878,099bytes≤512MiB,
알려진 root95,883bytes·단일/소유 RSS106.55/125.51MiB다. 용량 자식만 완료했다.
실제 전체 writer/DB/API/대표3D와 replay 부모는 미완료다. 다음은 정리된 DB/인증 자료의 실제 전체 부모 복원
→같은 raw profile의 전체 writer/등록·fresh 현재권리→API/대표3D→기후·물/양분·구매 에너지→사용자 실행/Decimal 경제다.
첫 복원은 보존 자료/검증 경로 재사용 조건의2–4집중시간 잠정이며 전체 실행 예산은 실제 복원 뒤 측정한다.
실제 품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4/생산/미래 마진/추천 hold는 유지한다.

**선행 수용 — 2026-10-09 02:22 KST:** [같은 실제 DB의 수확·생장3D](../research/crop-harvest-view-native-implementation-20261009.md)를
원69379 종료0·2통과/226.498초·828 source/소유 정리로 로컬 수용했다.
원6행/3시점·50 C/N/LAI·현재 권리/계정·취소/늦은 응답을 실제 SCRAM/보호 HTTPS/빌드 App/WebGL로 대사했다.
metadata/시각/응답 대체0·조회 RHS/행 생성/게시0이며 완료200응답9개의 양쪽 bytes/SHA가 같다.
13요청·최대22.722초/32,659bytes·지정 heap/GC/GPU thread의 소유 RSS 합1,030,803,456bytes≤1GiB다.
작은 native/view 부모만 추가 완료했다. 전체166일 새 질량 부하·replay 부모와 일반 운영 용량 수용은 남아 있다.
다음은 원 전체 결과의 RHS0 질량/배정 용량 대사→실제 전체 부하→기후/물·양분/구매 에너지→사용자 실행/Decimal 경제다.
실제 품종 계수·농장 작물 Run·국내 독립 자료0건, G0–G4/생산/미래 마진/추천 hold는 유지한다.

**선행 수용 — 2026-10-09 01:32 KST:** [수확 표/기존 생장3D 화면](../research/web-crop-harvest-view-screen-implementation-20261009.md)을
새 Chromium10개/기존15개(1+14분할)·웹851개·타입/빌드·원13586/24832/30303 종료0·820 source/정리로 로컬 수용했다.
원 목적/단위/미배정·현재 부분 범위/전체 합계·합성 비교/hold를 유지하며 같은 UTC의 실제 캔버스 C/N도 대사했다.
선택/계정/부모·권리 실패/취소/늦은 응답의 이전 값 제거와 모바일/키보드를 확인했다.
소유 fixture의 metadata/시각을 맞춘 실제 App 검증이며 새 공동 DB/백엔드 HTTPS 증거는0회다.
화면 자식만 완료했다. 실제 native/전체166일 질량 부하·view/replay 부모는 미완료다.
다음은 작은 같은 실제 DB/API/대표 WebGL→전체 작기 질량 부하→기후/물·양분/구매 에너지→사용자 실행/Decimal 경제다.
지정 시험 heap/viewport에서 소유 RSS 합1GiB/단일512MiB와 정리를 확인했으며 일반 운영 용량 수용은 아니다.
실제 계수/품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4/생산/마진 예측·추천 보류는 유지한다.

**선행 수용 — 2026-10-09 00:50 KST:** [저장 생장·수확 범위 결속](../research/web-crop-harvest-growth-binding-implementation-20261009.md)을
집중34개/웹 전체851개(기존817 포함)·타입/빌드·원 도구86385 종료0·777 source/정리로 로컬 수용했다.
같은 농장/부모/원 hash·상태·저장 UTC만 연결하며 대응 시점이 없는 사건은 보간하지 않는다.
현재 범위와 전체 저장 합계·합성/hold를 구분한다. 새 실제 DB/HTTP/화면/WebGL 검증은0회다.
수확 view의 결속 자식만 완료했고 표/3D·실제 통합/전체166일 질량 부하·replay 부모는 미완료다.
다음은 수확 표/기존 생장3D 화면과 선택/취소/권리 실패 제거→실제 DB/API/대표 WebGL이다.
기후/물·양분/구매 에너지→사용자 실행/Decimal 경제·실제 자료/독립 검증은 후속이다.
실제 계수/품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4/생산/마진 예측·추천 보류는 유지한다.

**선행 수용 — 2026-10-09 00:32 KST:** [등록 수확 결과 웹 SDK](../research/web-crop-harvest-client-implementation-20261009.md)를
집중97개/웹 전체817개(기존720 포함)·타입/빌드·원 종료0·458 source/정리로 로컬 수용했다.
실제 HTTPS 원 응답5개 SHA/길이·원6행/UTC/단위/정확 수량·합성/미배정·관측 비교/hold를 보존했다.
공통 Bearer·30초/2MiB transport와 순차 페이지·전체성/취소/혼합 거부를 연결했다.
SDK와 선행 API를 합친 HTTP/SDK 부모만 추가 완료했다. 수확 표/3D·replay 부모는 미완료다.
선행 합성166일 생장 DB/API/대표3D는 유지한다. 새 수확 경로의 전체166일 질량 부하는 별도다.
다음은 같은 UTC의 수확 목적·미배정 표/기존 생장 수치3D→실제 DB/API/대표 WebGL의 작은 검증이다.
그 뒤 기후/물·양분/구매 에너지→Decimal 경제 연결로 진행한다.
실제 계수/품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4/생산/마진 예측·추천 보류는 유지한다.

**2026-10-08 단계별 경계 기록:** [계산 설정 로더](../research/crop-cycle-calculation-operator-loader-20261007.md)의
고유212개 분할·실제 SCRAM/정리로 명시 operator-runtime까지 로컬 수용했다.
[인증 route/OpenAPI](../research/crop-cycle-calculation-route-openapi-20261007.md)도 고유284개 분할·ASGI/원 선언·78 source 보존으로 수용했다.
[runtime/TLS](../research/crop-cycle-calculation-runtime-tls-20261007.md)도 고유337개 분할·실제 SCRAM/26 HTTPS·
전체 본문 최대5.258614초/23,546bytes·원량/UTC/철회·81 source/정리로 작은 API 부모까지 로컬 수용했다.
[새 SDK](../research/web-crop-cycle-calculation-client-20261007.md)도 새178개 포함 웹 전체700개·타입/빌드·
원량/UTC·검증 정보·101 source 보존으로 수용했다.
[현재 범위 선택](../research/web-crop-cycle-calculation-window-20261008.md)도 새19개 포함 웹 전체719개·타입/빌드·
원/새 source·검증 정보/UTC·취소/settlement·104 source 보존으로 수용했다.
[새 같은 UTC 화면](../research/web-crop-cycle-calculation-view-20261008.md)도 새 Chromium15개/기존47개·웹719개·
타입/빌드·원27시점/5사건·113 source/정리로 합성 공개 응답의 화면 연결까지 로컬 수용했다.
새 실제 등록 PG/TLS/WebGL 연결은 [2파일 구현/시작](../research/web-crop-cycle-calculation-native-started-20261008.md) 후
기록 응답의 새/기존 브라우저와 실제 세 사례 준비를 통과했다.
[후속25시간 계산 완료/TLS 준비 실패](../research/web-crop-cycle-calculation-native-tls-hold-20261008.md)의
원인과 정리를 확인해 인증서 발급 시점을 수정했다.
[수정 실행의 기능 검증](../research/web-crop-cycle-calculation-native-observed-20261008.md)은 시험 로그1통과·
34frame·24 HTTPS·별도 정리를 확인했다. 원 명령 종료 기록 누락으로 최종 native/웹 부모는 보류한다.
[작은 등록 누적 비용](../research/crop-cycle-calculation-prefix-cost-observed-20261008.md)은 정상/hold·수정한32회 시험을
분할 확인했다. 3,990걸음·확정9시점/2사건·원량/권리/복원·종료0/정리이며 전체166일 등록 비용 부모는 미수용이다.
[전체166일의 별도 합성 달력 등록](../research/crop-cycle-full166-calendar-registration-20261008.md)은
원750파일/네 stream·값/clock/격자 보존·73개 회귀·실제 SCRAM 농장/경제 달력·현재 권리/기간 거부·RHS0·종료0/정리로 수용했다.
[같은 전체 입력의 초기32회 비용](../research/crop-cycle-full166-prefix-cost-observed-20261008.md)도
3,990걸음·105시점/2사건·원 상태/행·현재 권리·129 source/정리·종료0으로 로컬 수용했다.
[후보 읽기 연결 개선](../research/crop-cycle-candidate-read-scope-implementation-20261008.md)도 고유37개 분할·
연결38→1/원 검증·산술·같은 첫3회 원량/권리/정리로 로컬 수용했다.
[입력 재검사 개선](../research/crop-cycle-calculation-recheck-cost-implementation-20261008.md)도 고유199개 분할·
같은 첫3회99→85검사/30.737→29.551초·체크포인트 전체/원량·늦은 변조/철회·복원/정리로 로컬 수용했다.
[개선 판본32회](../research/crop-cycle-calculation-full-budget-observed-20261008.md)는 같은 checkpoint/원량·권리/복원·
263 source/정리·종료0/358.024초로 관측 자식만 수용했다. 두 개선 전 advance575.494→304.344초다.
과거 delta QC2n/합1,056회로 전체 등록 장시간 실행/wall 예산은 보류다.
[prefix 검증 증명](../research/crop-cycle-calculation-prefix-attestation-implementation-20261008.md)은
재개 입력/HEAD 직전 권한 철회 두 반례를 RED로 확인·복원하고 최종 수정판208개 분할·같은32회 원량/권리·266 source/정리·종료0으로 로컬 수용했다.
delta QC1,056→64회·advance304.344→290.225초·전체339.187초이며 입력 검사839회는 보존했다.
candidate 현재 bytes 검사 뒤 마지막 입력/권한 검사와 atomic HEAD 순서를 검증했다.
[계산 묶음 가능성](../research/crop-cycle-calculation-chunk-feasibility-observed-20261008.md)도 실제1통과/종료0·같은4,096전이/원105출력/2사건·
비계보 checkpoint 전체·2page/954,171bytes·268 source/정리로 수용했다. 제품128전이 제한은 유지했다.
[새 prefix 공개 연결](../research/crop-cycle-calculation-prefix-api-bridge-implementation-20261008.md)도 실제 RED 뒤 수정·
API193개/웹720개/Chromium15개·타입/빌드·새34 JSON/원량/UTC·270 source/종료0/정리로 로컬 수용했다.
[제한된 계산 묶음](../research/crop-cycle-calculation-bounded-chunks-implementation-20261008.md)도 고유177개·
실제4,096전이 저장/3,990걸음/원105출력·2사건·별도 Python 재개·274 source/종료0/정리로 로컬 수용했다.
요청4,096전이/실효128원경계·기존 bytes 한도·명시 서버v3이며 원 수식/격자/현재 권리를 유지한다.
[등록 농장의 두 큰 묶음](../research/crop-cycle-calculation-registered-chunk-cost-observed-20261008.md)도 실제 SCRAM1통과·
8,192전이/7,980걸음·원210출력/4사건·fork 재개·현재 권리/복사 입력 변조 거부·276 source/종료0/정리로 수용했다.
두 advance50.212/47.349초는 초기 구간 관측이다.
[전체 참조 용량](../research/crop-cycle-calculation-full-capacity-observed-20261008.md)도 고유10개·RHS0·456묶음/
전체47,809출력/5사건·예약 포함481,987,541bytes/512MiB·279 source/종료0/정리로 수용했다.
[같은 농장 별도 Python 복원](../research/crop-cycle-calculation-registered-runtime-implementation-20261008.md)도 고유7개·
실제 SCRAM40→80걸음/2출력·복원 RHS0·계산 전 SIGKILL-9/재개·권리/변조·284 source/종료0/정리로 수용했다.
[등록 계산 감독](../research/crop-cycle-calculation-registered-supervisor-control-implementation-20261008.md)도 고유16개·
실제 SCRAM40→60→80걸음/2출력·같은 마감/복원 RHS0·pause/cancel/실제-9·현재 권리·
289 source/종료0/정리로 작은 감독자 부모를 로컬 수용했다.
[완료 결과 별도 DB 게시](../research/crop-cycle-calculation-registered-terminal-publication-implementation-20261008.md)도
고유9개·실제 SCRAM40→120걸음/3출력·fresh 게시/재시도 RHS0/같은 row1·미완료/권한 거부·
294 source/종료0/정리로 작은 연결을 수용했다.
[같은 DB의 실제 App/3D](../research/crop-cycle-calculation-registered-replay-harness-implementation-20261008.md)도
고유2개·실제120걸음/원3시점·3사건·보호 HTTPS8개/최대2.148초·현재 권리/계정 거부·
303 source/원 종료0/정리로 작은 기능 경로를 수용했다.
이전 descendant RSS 합1.584GB 초과 보류 뒤 [작은 자원 경로](../research/crop-cycle-calculation-registered-replay-resource-implementation-20261008.md)를
고유2개·원 종료0/89.680초·원3시점/3사건·392 source/정리로 로컬 수용했다.
실제 빌드/Nginx·지정 viewport/Node heap·명시 CDP GC2회에서 PG/controller 포함 동시 RSS 합
1,048,477,696bytes≤1GiB다. 일반 운영 브라우저/전체 작기의 자원 수용으로 확대하지 않는다.
[전체 실행 구성의 작은 수용](../research/crop-cycle-calculation-full166-same-db-preparation-implementation-20261008.md)도
고유13시험·실제 대사 자식0→게시 자식0→같은 DB/UTC3D·원 종료0/준비부터102.476초·
PG/controller 포함 RSS 합1,050,714,112bytes≤1GiB·397 source/정리로 수용했다.
원166일 참조의 첫64/마지막1시점·전체5사건/121상태 읽기도 RHS0으로 확인했다.
[별도 전체166일 실행](../research/crop-cycle-calculation-full166-same-db-completed-20261008.md)은10월8일11:41→18:56 KST에 원 종료0/1통과로 완료했다.
준비부터26,127.555초·전체47,809행/5사건·121상태/수지 대사→같은 DB 게시→보호 HTTPS10개/대표14시점 WebGL·
권리/계정 거부·398 source/자원 정리를 최종 감사했다. 표본 RSS 합1,070,809,088bytes≤1GiB이며 여유약2.8MiB다.
원9시간 상한/수식/격자를 유지했고 감사 후 source freeze를 해제했다. 전체47,809프레임·실제 형상/품종/관문 수용은 아니다.
[제거 원장](../research/crop-removal-ledger-implementation-20261008.md)과 [명시 합성 질량 환산](../research/crop-removal-mass-implementation-20261008.md)도 로컬 수용했다. 다음은 수확 의미·작기 질량 게시→자원/경제 연결이며 실제 자료·예측/추천 hold는 유지한다.
[CI 시험 호환 수정](../research/calculation-ci-fixture-compatibility-20261008.md)은 고유19개 집중 검증을 통과했으며 hosted 수용은 별도다.
[기존 설정 호환의 hosted 세 Compose/정리](../research/artifacts/application-operator-policy-hosted-reference-20261008.json)는 수용했다.
전체166일 연구 DB/API/대표3D는 위 종료 증거로 수용했다. 생산/경제·자료 관문·hosted 수용은 별도다.

상태: **내부 구현 계약·부분 구현, 2026-09-27.** C0 Compose, 출처/G0 형식·서버 승인 저장 계약·시장 문맥, 합성 열 매개변수·trace 계약과 `candidate` 엔진, 조건부 경제 원장·판매 정산, PostgreSQL 지속 작업·AI 시도 증거 저장 계약이 수용됐다. G0 독립 권리 증거의 실제 연결, CLI 증거 저장 브리지와 의도 멱등 제약은 수용됐다. 열 모델의 D/R 결정시각 분리·서명된 DecisionContext와 게시 소프트웨어 통합, CLI 작업자 후보, 사용자 가정의 공동 시장 시나리오가 구현됐다. 실제 제품 CLI 실행·독립 게시 권한, 영속 Market hold·전체 경로 손익분기, API·3D·G1 종단 간 경로는 아직 수용 전이다. 세부 기준은 [제품 명세](PROJECT_SPEC.md), [아키텍처](ARCHITECTURE.md), [경제 계약](ECONOMICS.md), [시장 자료의 시점](MARKET_INTELLIGENCE.md), [기술 스택](TECH_STACK.md)을 따른다. 실제 준비 상태는 [구현 준비 현황](IMPLEMENTATION_READINESS.md)에 기록한다.

## 1. 목표와 확인할 사용자 경로

사용자가 확인한 국내 좌표 한 점, 과거 기간 하나, 개념적 온실 한 구역의 내부 경로를 끝까지 만든다. 사용자는 `decision_at`, 온실 구역·재배 가정, 날짜가 있는 농장 물량·가격·비용·투자·수금/지급 가정과 수요·공급·거시 조건부 충격을 입력한다. 중단 후 재개할 수 있는 작업은 **실제 런타임 Codex CLI `gpt-6.1-sol`과 `xhigh`**를 자료 조사·수집 계획, 수집 입력·권리·품질 검토, 최종 평가의 세 단계에서 실행한다. 서버가 각 구조화된 판단을 검사한다. 승인된 제공자 연결 도구 또는 직접 만든 것으로 명확히 표시한 합성 시험 자료가 변경 불가한 원천 기록과 스냅샷을 만든다. 수식과 버전을 확정한 열·수증기 모델은 실내 상태, 제어 상태, 모델 난방 열수요와 공급열을 결정적으로 계산한다. 버전이 고정된 시장 시나리오 엔진은 공통 충격과 계약·재고 제약 아래 날짜별 수확 `H`·판매 가능 `P`·판매 인정 `S`, 등급·채널·차감 전 계약가격과 증거가 완전한 경우의 조건부 순송금 단가·변동비·수금/지급 경로를 함께 계산한다. 실제 정산 완료 농가 순수취가는 정산서와 은행 입금 대사 전까지 보류한다. 별도 `Decimal` 계산기는 조건부 농장 운영 결과, 입력으로 정의할 수 있는 세 가지 손익분기 목표, 월별 현금 잔액을 계산한다. API는 완료 후 변경하지 않는 `run_id`를 제공하고, 3D 장면·그래프·표는 같은 `run_id + timestamp`를 읽는다. 평가 결과는 근거 없는 작물 선택을 명시적으로 `hold`하고 누락 증거를 제시한다.

**완료 경로는 두 가지다.** 합성 자료만 쓰는 **G1 계약 추적 시험**은 출처와 합성 여부를 표시한 변경 불가 입력과 실제 CLI 호출로 작업·화면 전체를 시험한다. 소프트웨어 연결과 결정적 재실행만 확인하며 외부 자료의 G0, 현장 정확도의 G2, G3 예측·순위를 입증하지 않는다. 권리를 확인한 **실제 자료 G0 경로**는 승인된 기상청 제품, 실측한 관측소·기간의 일사 `SI` 보유율, 확인된 시각 의미, 해당 용도의 이용권이 필요하다. 권리나 시각 의미가 없으면 `hold`를 기록하고 실제 자료 Run을 게시하지 않는다. 이때도 합성 자료로 계약은 시험할 수 있다. 실제 자료 보류를 합성 자료로 자동 대체하지 않는다.

`MarketContext`는 정확히 `{kind: "available", snapshot_id}` 또는 `{kind: "unavailable", hold_report_id}`다. 보류 사유와 누락 증거는 참조한 Market hold report에 둔다. 그 보고서는 승인된 MarketSnapshot의 증거가 아니다. 첫 G1 내부 시범에서 `unavailable`이면 `origin=user`, `evidence_level=assumed`로 표시한 사용자 가정만 **조건부** 농장 계산에 쓰고 최종 Assessment는 `hold`한다. 후속 단계에서는 접근·이용권, 해당 농장·기간·채널·계약 적용성, 원장·정산 대사를 독립 확인한 비공개 농장 계약·정산·원장을 조건부 또는 해당 농장의 과거 계산에 쓸 수 있다. 이 기록도 공개 시장 전망이나 작물 순위의 근거로 승격하지 않는다. 후속 객체인 `ForecastRun`에는 승인된 `MarketSnapshot`이 필요하다. 결정 당시 시장 근거는 `available_at <= decision_at`을 충족해야 한다. `decision_at` 뒤에 관측한 과거 날씨로 만든 결과에는 **사후 재현**(`ex_post_replay`)을 표시하며 당시의 예측으로 취급하지 않는다.

첫 G1의 시장 조건부 스트레스도 `unavailable`일 때는 사용자가 직접 소유·명시한 `origin=user`, `evidence_level=assumed` 가정만 사용한다. 이 경로는 자료 유래 전망·작물 순위·가짜 MarketSnapshot을 만들지 않는다. `available`이면 권리와 판본이 유효하고 `available_at <= decision_at`인 G0 승인 MarketSnapshot을 요구한다. 수요·공급·거시 충격의 크기와 방향, 가격·물량·비용 전가 경로는 입력의 근거와 적용 범위를 보존한다. 조건부 산술의 재현은 거시 변수의 정밀도나 미래 가격·수확·마진 예측의 검증이 아니다. 그런 주장은 이후 독립 증거와 해당 관문을 기다린다.

**후속 구현 경로는 첫 합성 G1과 별개다.** `market-source-g0`는 실제 제품의 권리·판본·시점·단위·품질·적합성을 확인해 시장 G0 스냅샷 또는 보류 보고서를 만든다. 이 작업은 첫 합성 경로를 막지 않지만 자료 유래 시장 시나리오와 근거 카드, 이후 ForecastRun의 선행 조건이다. `forecast-engine`은 시장 G0 및 필요한 G2/현장 근거 뒤 버전 고정 미래 경로 또는 명시적 보류를 만들고, 독립 농장 기록의 rolling-origin 시험을 거친 `g3a-evidence` 전에는 미래 마진을 게시하지 않는다. `crop-ranking`은 G3a 이후 같은 실행 가능한 조건에서 후보를 대응 비교하거나 보류하며, 독립 `g3b-evidence` 전에는 순위를 게시하지 않는다. `service-economics`는 첫 G1 뒤 농장 손익과 분리된 요청별 서비스 수지·한도·재원 근거를 준비하고, 실제 계정·청구·수요 증거를 포함한 G4 전에 공개 운영을 열지 않는다.

## 2. 초기 설정 작업에서 만들 실행 명령

`repo-bootstrap`의 다섯 파일 `backend/pyproject.toml`, `backend/uv.lock`, `web/package.json`, `web/package-lock.json`, `.gitignore`와 잠금 설치 확인이 완료됐다. `compose-runtime`의 `compose.yaml`, `.env.example`, `backend/Dockerfile`, `web/Dockerfile`, `.dockerignore`도 준비됐다. [C0 Actions 실행](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36303540834)에서 두 Compose 모델, web/API 의존성 이미지 빌드, PostgreSQL 18.6 건강 확인·컨테이너 재생성 뒤 데이터 보존이 통과했다. 앱 역할 전체 기동과 실제 CLI 세 단계, API·브라우저 경로는 후속 작업이다.

다음 명령은 각 후속 소스·시험이 생길 때 해당 작업의 범위를 확인한다. C0 수용은 위 호스팅 실행으로 별도 확인했다.

```sh
(cd backend && uv run pytest)
(cd web && npm ci && npm run typecheck && npm run test && npm run build)
docker compose config -q # compose-runtime: Docker/Compose 호스트에서 비밀값 출력 없이 구성 검증
```

`compose-runtime` C0는 Docker/Compose 호스트에서 정식 Compose 모델 [`docker compose config -q`](https://docs.docker.com/reference/cli/docker/compose/config/)와 web/API 의존성 이미지를 확인하고, PostgreSQL의 `pg_isready` 준비 상태와 컨테이너 재생성 뒤 데이터 보존을 [호스팅 실행](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36303540834)에서 검증해 수용했다. 비밀이 풀린 `docker compose config` 출력을 증거로 남기지 않았다. 현재 로컬 호스트에는 Docker Engine과 소켓이 없어 앱 역할 기동·작업자 복구·실제 CLI 세 단계·UI 경로는 후속 `end-to-end-g1`에서 확인한다.

## 3. 제안하는 프로젝트 구조

```text
backend/app/       FastAPI, 출처·관문 계약, 작업, CLI 작업자, 결정적 계산기
backend/tests/     집중 Python 시험과 데이터베이스 복구 시험
web/src/           좌표·작업 흐름, MapLibre 지도, Three.js 구역, ECharts와 표
web/e2e/           브라우저 경로와 접근 가능한 재생 시험
contracts/         버전 관리 JSON 스키마, 열 모델 계약, OpenAPI 출력
fixtures/          직접 만든 합성 원천·가정 기록과 manifest
ops/               배포·권리·계정·G4 증거
research/          G2/G3 시험 계획과 출처 등록부
scripts/           재현 가능한 G1 수용 실행기
compose.yaml       자체 운영 web/API/작업자/PostgreSQL/볼륨 구성
.env.example       비밀값 없는 환경 변수 이름과 설정 예시
backend/Dockerfile  부트스트랩 파일부터 빌드할 모듈형 백엔드 이미지 정의
web/Dockerfile      부트스트랩 파일부터 빌드할 웹 이미지 정의
.dockerignore       비밀·원본 자료의 빌드 문맥 제외
```

백엔드는 모듈형 Python 코드베이스 하나로 두고 Compose에 web·API·수집·CLI·수치 계산의 별도 서비스/작업자 역할과 PostgreSQL을 정의한다. PostgreSQL은 지속 작업과 메타데이터를, 영속 POSIX 아티팩트 볼륨은 내용 해시로 식별한 변경 불가 원천·정규화 입력·CLI 이벤트·출력 객체를 보관한다. [Compose `depends_on`](https://docs.docker.com/compose/how-tos/startup-order/)만으로 DB 준비를 보장하지 않으므로 `pg_isready` 건강 검사와 `service_healthy` 조건을 사용한다. PostgreSQL 18을 **검증 후 선택한다면** [공식 이미지](https://hub.docker.com/_/postgres)의 데이터 볼륨 위치는 `/var/lib/postgresql`이다. 실제 검사 전에는 버전이나 digest를 정하지 않는다.

`.env.example`에는 비밀값을 넣지 않고 실행 시 [비밀 파일/관리자](https://docs.docker.com/compose/how-tos/use-secrets/)에서 서비스별 최소 권한으로 주입한다. PostgreSQL에는 `POSTGRES_PASSWORD_FILE`을 사용하며 비밀 파일과 제한된 원본 자료는 저장소·빌드 문맥·이미지에서 제외한다. 기반/배포 이미지의 버전과 digest는 실제 빌드·실행을 확인해 고정한다. CLI 작업자에 Docker 소켓을 마운트하지 않는다. 장기 실행 Compose CLI 작업자 정의만으로는 작업마다 별도 비특권 컨테이너·임시 파일시스템·제한된 외부 통신을 입증하지 못하며, 이 격리와 G4 검증은 후속 작업에 남는다. CLI는 권리를 확인한 입력만 받고 제공자 HTTP 접근은 승인된 연결 도구가 맡는다.

## 4. 코드 형태 예시

스냅샷 ID를 지어내지 않고, 근거가 없는 상태를 자료형 계약에 나타낸다.

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, ConfigDict, Field

class AvailableMarket(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["available"]
    snapshot_id: str

class UnavailableMarket(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["unavailable"]
    hold_report_id: str

MarketContext = Annotated[
    Union[AvailableMarket, UnavailableMarket], Field(discriminator="kind")
]
```

모듈 사이에서는 단위와 UTC 시각을 명시하고 계산 전에 입력 버전을 고정한다. 이 예시는 형태만 정의한다. 서버가 소유권·권리·당시 판본·관문 증거를 따로 검사한다. 보류 사유와 누락 증거는 `hold_report_id`가 가리키는 보고서에 기록한다. `ForecastRun`의 `snapshot_id` 자리에 `hold_report_id`를 넣지 않는다.

## 5. 시험 방법과 수용 기준

1. **출처 기록/G0:** 합성 자료에는 `synthetic`, 작성자, 생성 방법, SHA-256, 단위, 시각 의미, 권리를 기록한다. 실제 기상청 기록에는 정확한 제품 ID, 관측소, 원 요청, 권리, 제공자 QC 유무, 변환 버전도 연결한다. `SI`의 적산 구간이 불명확하거나 값이 음수·야간에 부적절하거나 필수 자료·권리가 없으면 이유를 명시해 보류한다. `SI` 보유율 측정과 권리 확인 전에는 시범 관측소·기간을 정하지 않는다.
2. **지속 작업/CLI:** 중복 제출은 같은 작업으로 처리한다. 임대 만료·작업자 재시작·취소·429/5xx·스키마 오류·계정 부재·권리 거절에서 감사 기록과 올바른 상태가 남는다. 세 단계 각각에 실제 CLI 버전·모델·추론 강도, 입출력 해시, 출처 참조, JSONL 이벤트, 검사 결과, 사용량, 시도 ID를 기록한다. 재시도에는 새 시도 ID를 만들고 실제 검증 출력이 있을 때만 새 AI decision을 만들며, 게시된 판단과 Run은 바꾸지 않는다.
3. **물리 G1 추적 시험:** 코드 작성 **전에** 방정식·매개변수·제어·초기 상태·적분 계약을 확정한다. 모든 계수의 출처를 연구·실측·명시적 가정 중 하나로 밝힌다. 열·수증기 수지 잔차, 단위, UTC/KST, 구간 일사 변환, 결측, 야간 일사, 설비 용량, 안정적 적분, 고정 입력 재실행을 시험한다. 수치 허용 오차와 QC 기준은 이 문서에서 지어내지 않고, 확정한 모델·출처 근거로 시험 전에 등록한다. 열량 `kWh_th`를 구매 전력·연료·요금으로 표시하지 않는다.
4. **경제·시장 시나리오 G1 추적 시험:** 직접 작성한 날짜별 원장은 첫 합성 사례의 **당일 출하와 검수**만 다룬다. 운송 중이거나 검수 대기 중인 재고는 후속 계약이 필요하다. 첫 G1에서 시장이 `unavailable`이면 경제 입력과 수요·공급·거시 스트레스는 명시적 사용자 가정(`origin=user`, `evidence_level=assumed`)만 쓴다. 후속 단계의 `quoted`/`measured` 기록은 앞서 정한 권리·적용성·원장 검사를 통과한 범위에서만 쓴다. 공통 충격, 계약·재고 제약, 결정 시각·판본·`available_at`·as-of·권리·출처를 검사한다. `H → P → S`, 등급·채널·차감 전 가격·조건부 순송금 단가·변동비의 공동 변화, 반품·폐기·기말 재고, 판매 인정분만의 매출, 생산원가 한 번 반영, 발생일과 현금일, 반올림, 수금/지급·현금 대사, 세 손익분기 목표를 시험한다. 각 목표의 시험 kg 또는 KRW/kg마다 날짜별 시나리오 경로 전체의 재계산과 변수·범위·해 없음을 확인한다. 중요한 비용이 빠지면 0이 아니라 미확인으로 둔다.
5. **API/화면:** OpenAPI 스키마는 잘못된 참조를 거부하고 작업, 출처·시장 보류, Run 시계열·manifest, 조건부 경제 결과, 평가를 제공한다. 키보드 사용자는 시각을 골라 장면·그래프·HTML 표에서 같은 값과 단위를 확인할 수 있다. WebGL이 작동하지 않아도 표·문장 경로를 제공한다. 월별 조건부 금액을 보간해 시간별 실측값처럼 보여 주지 않는다.
6. **전체 경로:** 합성 자료 요청이 지속 작업과 실제 CLI 세 단계를 거쳐 좌표에서 최종 `hold`까지 진행한다. 재현 가능한 열·경제 기록과 일치하는 화면 값을 확인한다. 실제 기상청 경로는 별도로 G0 증거를 통과하거나 근거를 기록하고 보류한다. 별도 증거 없이 시험 결과를 G2/G3/G4로 표시하지 않는다.

## 6. 범위, 기능 목록과 구현 순서

기존 열 내부 경로에는 작물 생장·수확 예측, 구매 에너지·요금 예측, 미래 마진, 작물 순위, 식물 생장 애니메이션이 없다. 다음 작물 계산·성장 재생의 개발 범위는 §7에서 추가하며 기존 Run의 검증 범위를 소급해서 넓히지 않는다. 사용자 입력 물량·비용으로 만든 조건부 산술은 예측이 아니다. 이 문서는 온실 계수·센서 허용 오차·경제 정확도 비율·관측소를 가정하지 않는다. 첫 열·수증기 수지의 계약과 합성 후보 엔진은 검토됐다. 승인 trace와 G1 Run은 서버 입력 연결·독립 재계산·새 해제 증거 판본 및 두 시간 최종 해시 원자 게시 전까지 보류한다.

다음 영문 소문자 ID는 [작업 목록](../tasks/todo.md)의 작업 이름이기도 하다.

| 기능 ID | 구현 결과 |
| --- | --- |
| `repo-bootstrap` | **완료:** Python/web 설정·잠금 파일과 웹 검사·시험·빌드 스크립트, `.gitignore`; 오프라인 잠금·설치·import 확인 |
| `compose-runtime` | **완료:** 다섯 파일의 빌드 문맥·이미지 정의, 별도 서비스 역할, DB 준비·영속성 및 비밀 분리의 C0 호스팅 시험 수용 |
| `provenance-g0` | 변경 불가한 출처·권리·품질·관문 기록 계약 |
| `thermal-synthetic-parameters` | 1차 근거의 포화압 법칙과 버전 고정 합성 시설·초기·제어·수치 기준, manifest v2 |
| `thermal-contract` | 버전을 고정한 열·수증기 모델 계약 확정 |
| `fixture-policy` | 직접 작성한 합성 G1 추적 입력과 manifest |
| `durable-jobs` | PostgreSQL 임대·중복 처리·복구·게시 상태 |
| `decision-evidence-store` | CLI 시도별 불변 종료·출력/검사·권리별 감사 아티팩트; 실제 검증 출력에만 AI 결정 ID |
| `g0-authority-store` | **완료:** 독립 검토 resolver를 요구하는 서버 소유 출처·권리·정책 및 불변 G0 판정 저장 계약; 실제 제공자 G0는 보류 |
| `cli-worker` | 제한된 실제 CLI 단계·스키마·보류·감사 |
| `market-context` | 결정 당시 시장 자료의 가용/불가 구분과 ForecastRun 분리 |
| `thermal-engine` | 결정적 단일 구역 합성 열·수증기 후보 trace |
| `thermal-g1-publisher` | 서버 입력·권리/QC·독립 재계산 및 승인 trace 원자 게시 |
| `cli-worker-store-bridge` | CLI 단계별 임대·검증된 보류 보고서·실행 사건 저장 계약 |
| `economic-ledger` | `Decimal` 조건부 원장과 날짜별 현금 |
| `sales-settlement` | 판매별 공제·수금과 미수금/미지급금 대사, 증거가 완전한 조건부 순송금 단가 |
| `market-scenario` | 수요·공급·거시 공동 충격, 시점·권리·재고·계약 제약을 따르는 조건부 날짜별 경로 |
| `economic-break-even` | 전체 날짜별 시나리오 경로를 다시 계산하는 서로 다른 손익분기 목표 세 가지 |
| `api-flow` | 버전 관리된 HTTP 제출·조회 경로 |
| `web-shell` | 좌표·입력·작업·보류 화면 |
| `web-replay` | 동기화된 3D·그래프·표 재생 |
| `end-to-end-g1` | 실제 CLI를 쓰는 합성 자료 계약 추적 시험 수용 |
| `kma-g0` | 권리를 따로 확인하는 실제 ASOS 경로 |
| `market-source-g0` | 실제 승인 시장 제품의 어댑터·정규화·시점/권리/품질 검사와 G0 MarketSnapshot 또는 보류; 첫 합성 G1과 병행 |
| `g2-evidence` | 독립 온실 실측 계획과 증거 |
| `forecast-engine` | G0 시장·G2/현장 근거 뒤 버전 고정 ForecastRun 또는 보류; 엔진만으로 미래 예측 주장 불가 |
| `g3a-evidence` | 독립 작물·경제 미래 검증 |
| `crop-ranking` | 같은 결정·시설·면적·달력·목표와 공통 충격의 후보 비교 또는 보류; G3b 전 순위 비공개 |
| `g3b-evidence` | 후보 간 대응 비교와 순위 검증 |
| `service-economics` | 농장 경제와 분리한 실제 요청별 서비스 원가·매출·용량·재원 대사; G4 선행 |
| `g4-operations` | 운영 계정·격리·권리·실측 서비스 수지·배포 증거 |

구현 순서와 외부 증거 의존성은 [구현 순서](../tasks/plan.md)에 있다. 코드 작업 체크는 해당 작업의 수용 증거만 뜻하며 다른 주장 관문의 통과를 뜻하지 않는다.


## 7. 다음 구현 슬라이스: 단일 작물의 계산과 성장 재생

대상은 [조사 등록부](../research/crop-tomato-source-register-20261004.json)의
Axiany/Maxifort 한 해외 작기 개발 참조다. 대한민국 온실의 최종 대상 경계는 유지한다.
모델 기준 후보와 권리/정정/검증 가능성은 [조사 결과](../research/crop-tomato-model-baseline-20261004.md),
첫 순수 계산 모듈은 [crop-growth-research-v1](../contracts/crop-growth-research-v1.md)에 둔다.
유량 kernel은 [로컬 86개/참조 60수치](../research/crop-growth-rates-implementation.md)로 수용했다.
[작은 수관 적용 정책](../contracts/crop-photosynthesis-domain-v1.md)은 기존 유량과 합쳐
로컬 118개/0.18초로 수용했다.
[시간 적분](../research/crop-growth-integration-implementation.md)까지 합쳐 로컬 146개/0.53초와
독립 165수치·수렴/수지/사건을 수용했다.
[불변 합성 연구 저장](../research/crop-result-storage-implementation.md)까지 로컬 집중
172개/434.49초·실제 SCRAM/별도 프로세스/변조/철회/정리로 수용했다.
[저장 조회 API](../research/api-crop-replay-implementation.md)도 집중 316개/194.11초,
실제 HTTPS 10개·본문 최대 5.580219초·현재 권리/변조/정리로 수용했다.
[같은 계산 결과의 성장 연구 3D](../research/web-crop-replay-implementation.md)도 웹 209개·
집중 Chromium 10개·실제 SCRAM→HTTPS→도형/표/그래프 대사 1개로 로컬 수용했다.
5분/6시점 합성 연구 범위이며 실제 참조 입력 채택/권리 연결은 남아 있다.
[채널/시각/면적·초기조건/관리 입력 감사](../research/crop-forcing-audit.md)도 완료했다.
실제 forcing/작기 재현은 보류이며 [과실 발달식/구획 계약](../research/crop-fruit-cohorts-baseline.md)도
수용했다. [원식이 명확한 순간 이동](../research/crop-fruit-transport-implementation.md)도
새 92개/기존 포함 238개와 독립 3,090수치로 로컬 수용했다. 필수 프로필 포장은
[실제 hosted context/읽기 전용 loader·정리](../research/crop-fruit-transport-image-inputs-implementation.md)로 수용했다.
[명시적 착과/진입 질량 배분 정책](../research/crop-fruit-allocation-policy.md)은 독립 대수/수치로
수용했다. [순수 제품 배분](../research/crop-fruit-allocation-implementation.md)도 새 77개/기존 포함
315개·독립 600개 유입/4개 hold로 로컬 수용했다.
[문헌식 수요·구획 순간 결합](../research/crop-fruit-cohort-rates-implementation.md)도 새 86개/기존 포함
401개·독립 8,592수치로 로컬 수용했다.
[전체 기관의 순간 결합](../research/crop-plant-cohort-rates-implementation.md)도 444개 집중·684수치로 수용했다.
[짧은 시간 적분/사건](../research/crop-plant-cohort-integration-implementation.md)도 488개·1,309수치/해석해 250개로 수용했다.
[새 저장 선행 artifact](../research/crop-coupled-artifact-implementation.md)도 530개·
512출력/별도 Python·재적분 없는 읽기로 수용했다.
[farm/program 결합 DB 저장](../research/crop-coupled-result-storage-implementation.md)도
실제 SCRAM·564개·같은 bytes/현재 권리·변조/철회/원자성·정리로 로컬 수용했다.
[페이지 조회 API](../research/api-crop-coupled-replay-implementation.md)도 고유 207개 분할 검증·
실제 HTTPS 19개·최대 11.508339초/649,718 bytes·현재 권리/재시작/정리로 로컬 수용했다.
[같은 저장 ID/UTC의 50구획 연구 3D](../research/web-crop-coupled-replay-implementation.md)도
단위 129개·Chromium 19개·실제 SCRAM/HTTPS/WebGL 1개로 로컬 수용했다.
실제 완료 6시점/과거 hold 1시점/빈 hold·900개 C/N mesh·권리/정리를 확인했다.
[초기/명시적 유입 정책](../research/crop-fruit-startup-policy.md)은 원천 8개·독립 9개 보존/5개 hold로 수용했다.
[빈 tail 요청/실현 순수 adapter](../research/crop-fruit-startup-rates-implementation.md)도
56개 새/544개 집중으로 로컬 수용했다. [새 기관 순간 결합](../research/crop-plant-startup-rates-implementation.md)도
78개 새/622개 집중·독립 22사례로 수용했다.
[새 짧은 적분/manifest](../research/crop-startup-integration-implementation.md)도
56개 새/678개 집중·독립 6프로그램/23시점·24시간/512출력과 오차 기록으로 수용했다.
[새 불변 artifact/reader](../research/crop-startup-artifact-implementation.md)도
79개 새/799개 집중·기존 6프로그램 결과와 동일·별도 Python/재적분 없는 512출력 읽기로 수용했다.
[v3 표/명시 role·설정](../research/crop-startup-storage-schema-implementation.md)도 새20개/184개 고유
분할·실제 SCRAM/불변/정리로 로컬 수용했다.
[새 저장 v3 custody](../research/crop-startup-result-storage-implementation.md)도 새18개/집중119개·
실제 SCRAM/6프로그램/별도 Python·commit 전후 철회/정리로 로컬 수용했다.
[페이지 조회 API](../research/api-crop-startup-replay-implementation.md)도 새47개/고유252개 분할·
실제 HTTPS/SCRAM19응답·최대14.248425초/700,084 bytes·정리로 로컬 수용했다.
[응답/순차 페이지 결합](../research/web-crop-startup-pages-implementation.md)도 새77개/웹 전체376개·
typecheck/build·기록 TLS 원값 대사로 로컬 수용했다.
[같은 UTC 성장 3D/실제 브라우저](../research/web-crop-startup-replay-implementation.md)도
웹383개·Chromium31개·실제 SCRAM/TLS/WebGL1개·고유12시점/1,500 C/N mesh·정리로 로컬 수용했다.
v3 로그 비교 도형은 원값/영을 보존하며 기존 v2 선형 대체를 유지한다.
`crop-cycle-execution-contract`의 [원 격자/표현 대사](../research/crop-cycle-execution-contract.md)도
원 solver6프로그램/630걸음·30분할 grouping·2,783float64/정확한 clock 반례·후속 검증표로 로컬 수용했다.
[실제 순수 continuation](../research/crop-cycle-continuation-implementation.md)도157개·30실제 분할과
별도 Python6개/726float64·원 상태/누적/clock·사건/hold 대사로 로컬 수용했다.
[불변 분할 원 입력 reader](../research/crop-cycle-input-stream-implementation.md)도64개·48,000자작 합성 구간/
48,003경계·독립 clock/grid·별도 Python 복원·30.23MiB/정리로 로컬 수용했다. 실제 RHS는 실행하지 않았다.
[긴 입력/실제 RHS 연결](../research/crop-cycle-stream-execution-implementation.md)도144개 집중·
25시간/11,400실제 걸음·별도 Python7개/847float64·canonical 사건/hash·원 상태/수지/hold로 로컬 수용했다.
[긴 결과의 불변 파일/reader](../research/crop-cycle-artifact-implementation.md)도58개 고유 분할 검증·
25시간/11,400실제 걸음·755,868bytes·별도 Python7개/847float64·실제 강제 종료2개/복구·정리로 로컬 수용했다.
읽기0.388759초/RHS0회이며 원6프로그램의 canonical 원량/UTC·수지/hold를 보존한다.
[cycle 불변 DB 참조 schema](../research/crop-cycle-storage-schema-implementation.md)도74개 고유 분할·
실제 SCRAM/기본 네 role 권한0·정상 JSON128KiB·불변/변조/rollback·기존 v3 보존/정리로 로컬 수용했다.
직접 작성 metadata 행은 실제 파일/현재 권리/HMAC 검증 결과가 아니며 긴 결과의 농장/웹 재생은 후속이다.
[별도5파일 명시 role/config](../research/crop-cycle-storage-roles-implementation.md)도 새21개/고유236개 분할·
기본 false/선택 authority SELECT·INSERT·일곱 drift·누락/false 호환·실제 네 SCRAM/v3 보존·정리로 로컬 수용했다.
현재 권리 저장은 [농장/input root 결합](../contracts/crop-cycle-farm-binding-v1.md) →
[실제 서버 계산/서명된 progress](../contracts/crop-cycle-server-custody-v1.md) → DB 게시로 분해한다.
첫 [농장/root 결합](../research/crop-cycle-farm-binding-implementation.md)은 고유54개 분할·실제 SCRAM/
현재 권리·중간 입력 변경·별도 Python/정리로10월5일 로컬 수용했다.
[실제 서버 계산/서명 저장](../research/crop-cycle-server-custody-implementation.md)도 고유46개 분할·
실제 SCRAM/현재 권리·강제 종료4개·별도 Python 복원/정리로10월5일 로컬 수용했다.
25시간/11,400실제 걸음·27시점/5사건·서명 저장829,769bytes를 확인했고 마지막 reader 정리 수정 전 참조 판본을 고정한다.
현재 [DB 저장](../research/crop-cycle-db-custody-implementation.md)은 고유76개 분할
(순수61·실제 DB15개)과 원49개 보존/정리로10월6일 KST 로컬 수용했다.
합성 등록 농장25시간/11,400걸음·원27시점/5사건·7페이지와 재시작/fork·변조를 대사했다.
요약의 원 manifest 누락을 실제 정상/hold 실패2개로 재현·수정했고 기존 요약 중 권리 철회도 재확인했다.
수정 전 긴 참조와 최종 판본의 분할 근거를 구분한다. 저장 부모까지 로컬 수용했고 다음 [조회 API 후보](../contracts/api-crop-cycle-pages-v1.md)는
요약/수치 페이지와 한 현재 권리 읽기 context·실제30초/2MiB를 검증한다. 그다음 client → 같은 UTC3D →
작기 부하 → 생과 환산을 [todo](../tasks/todo.md)의 작은 자식 순서로 진행한다.
새 모델의 실제 재시작을 grouping/serialization 시험으로 대체하지 않는다.
이 화면은 실제 품종/전체 작기 생산 검증이 아니며 pixel fidelity도 별도다.
자동 착과/빈 초기 작기·실제 품종과 전체 작기 처리의 수용은 남아 있다.
`590fadc`의 [coupled 조회/3D·순수 startup adapter CI](../research/artifacts/crop-coupled-replay-startup-rates-ci-20261005.json)는
전체5개·백엔드3,157개/별도UID4개·여섯 동일 목록/정리·집계를 통과했다.
후속 `d105daa`의 [CI5개/백엔드3,370개·별도UID4개](../research/artifacts/crop-plant-startup-math-ci-20261005.json)도
여섯 동일 목록/정리·집계로 기관 시작 RHS/적분/artifact까지 수용했다.
새 저장까지의 `92cade3`도 [CI5개/백엔드3,408개·별도UID4개](../research/artifacts/crop-startup-storage-ci-20261005.json)를
여섯 동일 목록/정리·집계로 수용했다. API/client/3D까지의 `1555610`도
[CI5개/백엔드3,456개·별도UID4개](../research/artifacts/crop-startup-replay-ci-20261005.json),
여섯 동일 목록/정리·집계로 수용했다. 후속 `fe41e22`도
[CI5개/백엔드3,709개·별도UID4개](../research/artifacts/crop-cycle-stream-ci-20261005.json),
여섯 동일 목록/정리·집계로 continuation/reader/긴 RHS까지 수용했다. 이어 `ff6eb3d`의
[CI5개/백엔드3,862개·UID4개](../research/artifacts/crop-cycle-artifact-schema-roles-ci-20261005.json)도
여섯 동일 목록/정리·집계로 cycle artifact/schema/roles까지 수용했다. 후속 `0f2925f`의
[CI5개/백엔드3,962개·UID4개](../research/artifacts/crop-cycle-farm-server-ci-20261005.json)도
여섯 동일 목록/정리·집계와 작성 첫 시도7job로 농장 결합/서버 실행까지 수용했다. DB 후보는 그 SHA 밖이다.
`d15cf92`의 [시간 적분/artifact·v2 저장 전체 CI](../research/artifacts/crop-coupled-storage-ci-20261005.json)도
3,070개·별도 UID 4개·같은 목록/여섯 DB·password 정리/집계를 통과했다.
후속 `4bb6e53`의 [CI5개/Backend4,038개·UID4개](../research/artifacts/crop-cycle-db-custody-ci-20261006.json)도
여섯 동일 목록·DB/비밀 정리·집계로 DB 저장까지 수용했다.
[공개 투영](../research/crop-cycle-api-projection-implementation.md)은 고유43개 분할·실제25시간 원량/UTC·
출력0/hold·RHS0회로 로컬 수용했다.
후속 `2c0f0e6`의 [CI5개/Backend4,081개·UID4개](../research/artifacts/crop-cycle-api-projection-ci-20261006.json)도
여섯 동일 목록/정리·집계와 작성 첫 시도7job로 공개 투영까지 수용했다.
[인증 route](../research/crop-cycle-api-route-implementation.md)도 고유146개 분할·최종41개·원량·한 문맥/
후검사·기존 OpenAPI 보존으로 로컬 수용했다.
실제 비용에 따른 [원천 읽기 범위 수정](../research/crop-cycle-market-read-scope-implementation.md)은
고유56개 분할·같은21 짧은 TLS 최대12.764535초/권리·변조·재시작/정리로 로컬 수용했다.
[실제 runtime/API](../research/api-crop-cycle-runtime-implementation.md)는 고유52개 분할 증거와
원25시간의 전체 HTTPS11응답·27시점/5사건·재시작·RHS0회·정리로 로컬 수용했다.
긴 응답 최대15.839875초/64,785bytes이며 기존30초/2MiB를 유지했다.
runtime/API 부모와 [client](../research/web-crop-cycle-pages-implementation.md)는 로컬 수용했다.
client 새120개·집중296개·웹 전체503개/타입·빌드·원23 공개 JSON/helper 보존을 확인했다.
[범위 helper](../research/web-crop-cycle-window-implementation.md)도 새19개·웹 전체522개/타입·빌드·
직렬 취소·원량 보존으로 로컬 수용했다.
[같은 UTC 화면 기능](../research/web-crop-cycle-view-implementation.md)도 기록 응답의Chromium16개·
기존3개·웹522개/타입·빌드·원27시점/5사건·원량/mesh 대사로 로컬 수용했다.
[새 실제 PG/TLS/WebGL](../research/web-crop-cycle-native-implementation.md)도1통과/2044.35초·
원25시간/11,400걸음·27시점/5사건·21 HTTPS 최대20.484300초/64,791bytes·RHS0·
현재 권리/계정 거부·자원/DB/서버 정리로 로컬 수용했다. 별도 CPU4배 형식20범위도 대사해
3D/result-pages 부모를 로컬 수용했다. 실제 저사양기기·pixel fidelity·품종은 별도다.
[종료된 d61 CI](../research/crop-cycle-route-runtime-ci-hold-20261006.md)는 backend 한 분할/웹 감사 실패이며
후속 `7a855a7`의 [CI5개](../research/crop-cycle-route-runtime-ci-success-20261006.md)는 Backend4,145개/UID4개·
동일 목록/정리·집계와 웹522개/Chromium98개·타입/빌드/audit0으로 성공했다.
profile/full runner/입력 대사 실험은 이 hosted SHA 밖이다. 다음 [작기 부하](../contracts/crop-cycle-burden-v1.md)는
비용 측정 → 실제166일 RHS → 전체 저장 조회/중단 복원으로 진행한다.
[profile](../research/crop-cycle-burden-profile-implementation.md)은 고유15개 분할·실제 SCRAM/worker·
자작5시간/원61출력·166일 input plan1,816,704걸음/RHS0·정리로 로컬 수용했다.
이어 [runner/작은 재개 전략](../research/crop-cycle-full-rhs-small-strategy-implementation.md)은 집중17개·
실제 자작5시간61출력/2사건·별도 Python 재개·terminal RHS0/정리로 로컬 수용했다.
다음은 실제166일 RHS/안전한 재개이며6시간은 고정된 실험 예산이고 완료 날짜가 아니다.
전체 공개 조회에는 관측된 원 입력 재검증 비용을 검증/권리 보존으로 개선해야 한다.
전체 날짜는 해당 수정과 실제 종료·조회 예산 수용 뒤 추정한다.
[서버 입력 검사 영수증](../research/crop-cycle-input-evidence-implementation-20261006.md)은33개 집중 시험·
원 발행31.34초/별도 Python 재조회0.176초·현재 원 bytes/context·RHS0/FD 정리로 로컬 수용했다.
원53 source를 바꾸지 않아 전체 RHS와 병행했다. 결과 조회 타입·과거 재생 연결과
현재 farm/Scope/등록/권리·실제 전체 API/3D는 별도다. 영수증만으로 replay-restore/관문을 체크하지 않는다.
[별도 입력 조회 문맥](../research/crop-cycle-input-read-context-implementation-20261006.md)은15개 집중 시험·
원47,811경계/같은 context/clock·재시작·RHS0/FD 정리로 로컬 수용했다.
원 계산과 조회 판본을 분리했고 v1 engine의 새 타입 거부를 확인했다. 결과/현재 farm/권리/API 연결은 다음이다.
[확정 과거 결과 비용](../research/crop-cycle-result-prefix-read-cost-observation-20261006.md)은
원8,175commit/26,831출력의 수지 검증73.71초·같은 참조16,354blob 대사1.03초를 확인했다.
[결과 영수증 primitive](../research/crop-cycle-result-evidence-implementation-20261006.md)의3 core파일은
새41개/관련 고유89개·원 작은 terminal QC·새5시간1,800걸음/61출력/3사건·별도 Python/FD 정리로 로컬 수용했다.
원 QC 발행0.136초/별도 재조회0.013초는 작은 사례의 실측이며 전체166일 성능은 별도다.
[별도 결과 조회 타입](../research/crop-cycle-result-read-context-implementation-20261007.md)은 새36개/관련 고유125개·
새5시간의 원61출력/3사건 전체·별도 Python/FD 정리로 로컬 수용했다. 원값/UTC·현재 bytes/파일 보안·
cache 한도·반환 전 재대사를 확인했다. 다음은 [현재 조회 계약](../contracts/crop-cycle-current-query-v1.md)의
농장/DB/원 서명 결속3 core파일 → API/runtime 명시적 연결·실제 TLS →
실제 전체 저장/같은 UTC3D를 작은 후속으로 나눈다. 조회 개발은 작은 terminal 사례로 독립 진행한다.
첫 수용은 원 등록/result row·전체 부모 custody 서명의 현재 권리/증명 전후 결속과 실제 작은 등록 농장의
SCRAM·철회/변조/재시작·정리다. 다음 API/runtime 연결의 TLS30초/2MiB·투영 후 철회까지
확인해야 현재 조회 부모를 수용한다. 순수 참조 결과를 server trace로 바꾸지 않는다.
전체166일 종료 전에는 전체 작기/복원·부하 부모를 수용하지 않으며 참조 결과를 농장 계산 이력으로 바꾸지 않는다.
현재 [농장/DB 조회 결속](../research/crop-cycle-query-authority-implementation-20261007.md)의 실제 SCRAM8개/631.33초와
[API/runtime 연결](../research/crop-cycle-query-runtime-implementation-20261007.md)의 실제 SCRAM/TLS1개/243.58초를 로컬 수용했다.
원120걸음·3시점/3관리 사건·22 HTTPS·재시작·투영 후 철회·trace/역할 거부·정리를 확인했다.
최대6.306509초/21,514bytes·분할 고유198통과/9건너뜀이며 코드 판본별 증거를 보존했다.
현재 조회 부모의 작은 소프트웨어 범위까지 수용했다. 전체166일/복원·부하·새3D와 관문은 별도다.
[계산 경로의 원 입력 직접 관측](../research/crop-cycle-farm-input-cost-observation-20261007.md)은
현재 조회 개선과 별개인 `_input` 반복 비용을 확인했다. [공식 계산 문맥 계약](../contracts/crop-cycle-calculation-context-v1.md)의
4개 이내 core파일 → 새 판본 artifact → 현재 농장·권리/custody로 [작업 목록](../tasks/todo.md)을 나눈다.
기존 artifact의 원 계산 타입 의존성은 [현재 코드 감사](../research/crop-cycle-calculation-context-inspection-20261007.md)에서 확인했다.
[첫 계산 문맥 수용](../research/crop-cycle-calculation-context-implementation-20261007.md)은 새57개/기존33개·
90통과/76.37초·원 checkpoint/121상태·clock/counter·별도 Python4개와 변조/FD/cache를 확인했다.
큰 입력 factory0.386465초/RHS0·작은120걸음603RHS의 활성 RSS를 구분해 측정했고 원55 source를 보존했다.
[새 artifact writer/reader](../research/crop-cycle-calculation-artifact-implementation-20261007.md)도
새68개/선행90개·158통과·실제25시간/11,400걸음·27시점/5사건·별도 Python7개·
HEAD 전후 즉시 종료2개/복원·조회 RHS0·정리로 로컬 수용했다.
[새 현재 농장 권한 결속](../research/crop-cycle-calculation-farm-authority-implementation-20261007.md)은 실제 SCRAM 고유12개를
분할 수용했다. 등록/provenance·현재 read/write 권리·입력/형/설정 변경 거부와 세 실행의 정리를 확인했다.
이 권한 단계의 RHS/새 작물 row/Run은0이다.
후속 [새 서버 계산/서명](../research/crop-cycle-calculation-server-custody-implementation-20261007.md)은 순수50개·실제 SCRAM12개,
고유62개 분할·실제 중단4곳/fresh Python·현재 권리/원 이력 보존과 등록 농장7→120걸음 재개로 로컬 수용했다.
다음은 DB 원자 게시이며 새 DB row/Run0·farm 연결 부모와 전체166일/DB/API/3D·관문 보류를 유지한다.
[새 표/권한 자식](../research/crop-cycle-calculation-result-schema-implementation-20261007.md)은
현재4 source 전후 대사·전체68개/22.68초·실제 SCRAM·원 행 공존·default deny/명시 권한·정리로 로컬 수용했다.
SQL 형식 fixture와 signed 등록 계산 결과를 구분하며 다음은 새 store의 원자 게시/현재 조회다.
후속 [새 store 게시/조회 수용](../research/crop-cycle-calculation-result-publication-implementation-20261007.md)은
동일 제품 module의 순수81개·실제 SCRAM 고유15개, 고유96개 분할·실제7→120재개/원량·
현재 권리/원자 게시·원 signed 이력 공존/변조·정리로 작은 DB와 농장 연결 부모도 완료했다.
get7.898755초와 다른 실행39.668745초는 내부 관측이며 HTTP30초 수용이 아니다.
전체 등록 prefix 비용·새 proof/현재 조회·공개 판본/operator-config/API runtime 연결·전체166일/3D는 후속이다.
그 [누락된 조회 의존성](../contracts/crop-cycle-calculation-query-v1.md)을 evidence → reader → current query →
API/runtime → client/동일 UTC3D와 독립 prefix 비용 측정으로 작업화했다.
후속 [새 evidence](../research/crop-cycle-calculation-result-evidence-implementation-20261007.md)는
새79개/선행74개·고유153개 분할·자체5시간 정상/hold·별도 Python2개/parser/context/QC/RHS0·
원55 source/FD/PID 정리로 작은 자식을 수용했다. 후속 [reader4 core파일](../contracts/crop-cycle-calculation-result-read-context-v1.md)도
[새49개/선행115개·집중164개](../research/crop-cycle-calculation-result-read-context-implementation-20261007.md)·
원5시간 정상/hold·별도 Python2개/parser/context/QC/RHS0·원량/UTC·byte 경계/변조·FD/cache/PID로 수용했다.
후속 [현재 farm/DB query](../research/crop-cycle-calculation-current-query-implementation-20261007.md)는 실제 SCRAM12개/1,079.43초·
정상/관리 사건/수치 hold·원량/UTC·권리/변조·fork·63 source/FD/DB/비밀/PG 정리로 수용했다.
후속 [순수 공개 투영](../research/crop-cycle-calculation-api-projection-implementation-20261007.md)도 새63개/구형42개·
고유105개 분할·실제25시간/7페이지·원량/UTC·세 hold·RHS0·import/FD·67 source 보존으로 수용했다.
[명시 runtime factory](../research/crop-cycle-calculation-runtime-factory-20261007.md)도 새19개/기존136개·고유155개 분할,
실제 SCRAM 같은 jobs/farm·재구성/9거부·계산/게시0·행/입력/FD/import·73 source/정리로 수용했다.
다음은 [별도 operator loader](../contracts/crop-cycle-calculation-operator-loader-v1.md) → 실제 TLS다.
새 API와 전체 등록166일/같은 UTC3D는 아직 미수용이다.
원 input proof·validation9+8/부모 서명을 보존했고 query3–6시간 잠정은 위 실적으로 대체한다.
전체166일 새 증명/등록/API/3D와 관문/전체 날짜는 별도다.
새 module만 쓰는 순수 개발은 원55 source SHA·현재 입력/spec을 보존해 병행한다.
동결 소스 변경은 실제 실행 종료·증거 보존 뒤이며,
첫 수용은 원 물리값/UTC·121상태/checkpoint·수지/hold·변조 거부와 별도 프로세스 복원이다.

다음 실험의 [지속 저장 감독자](../research/crop-cycle-full-rhs-durable-implementation-20261007.md)는
실제5개/22.67초·child SIGKILL(-9)/같은 checkpoint 재개·연속760걸음/21시점/2사건·121상태 대사로 로컬 수용했다.
원 spec SHA/마감·과거 결과 변조/동시 실행 거부·FD/child/lock 정리를 확인했다.
이 작은 감독자 수용 뒤 새 판본/지속 저장의166일을 시작하며 전체 RHS/복원·부하는 종료 증거 뒤 수용한다.
[새 실제 시작 관측](../research/artifacts/crop-cycle-full-rhs-durable-started-reference-20261007.json)은
첫123걸음/620RHS·정상 종료 뒤 같은 spec 재개·8,104걸음 진행을 기록했다. 전체 종료/수지는 계속 미수용이다.

후속 [새166일 전체 RHS 완료](../research/crop-cycle-full-rhs-durable-completed-20261007.md)는10월7일
종료0·1,816,704걸음·47,809시점/5사건·원 전체 reader 수지/행 SHA·조회 RHS0,
원123걸음 체크포인트 전체/121상태·seed/clock/cursor·55 source/입력/결과 전수 대사·정리로 로컬 수용했다.
준비 포함20,518.836401초로 원6시간 안이다. full-rhs 자식만 완료이며
전체 등록 DB/API/동일 UTC3D·복원/부하 부모는 다음 실제 경로 수용을 기다린다.

10월7일 [재개 관측](../research/crop-cycle-full-rhs-missing-state-20261007.md)에서 원81574 handle·실험/terminal
보존 경로가 없어 최종 상태는 확인 불가다. 보호할 실행의 부재를 확인했고 원 결과/부모는 계속 보류한다.
작은 terminal 조회 개발을 이어가며 전체 수용은 원 증거 복구 또는 별도 판본/지속 저장의 새 실험 증거를 요구한다.
보존 CI 시험 수정은 `4bf9af3`으로 정상 적용해 현재18개/24.30초를 통과했다
([통합 증거](../research/artifacts/crop-cycle-full-rhs-test-isolation-integration-20261007.json)). 새 hosted 수용은 별도다.
`e70a7f2`의 기존 assessment HTTPS 30초 시간 초과와
[로컬 재현/요약 크기 수정](../research/backend-ci-summary-and-timeout-20261005.md)을 별도 기록했다.
로컬 통과로 실패한 hosted 판본을 수용하지 않는다.
실제47,809시점과 기관 단독 v1의20,000 배열/100만 step, 현재 기관·과실/startup의
128 forcing/128 event·512 output·10,000 step·1일 한도의 차이는 `crop-cycle-capacity`에서
연속 상태·사건·저장/출력 시간과 부하/재현을 계약하는 필수 후속이다.
[필수 프로필/고지 이미지](../research/crop-rate-image-inputs-implementation.md)도 실제 hosted
build/실행/정리를 통과했다. `d251df9`의 전체 backend 2,671개·별도 UID 4개와
CI 5개도 통과했다. `d76410f`의 웹/C0/실제 앱 CI는 통과했다.
새 작성 브라우저의 저장/HTTPS/도형 대사도 통과했다.
새 전체 backend 집계와 실제 품종 입력 QC는 별도다.

| 순서·기능 ID | 착수에 필요한 것 | 사용자 산출물과 수용 기준 |
| --- | --- | --- |
| 1 `crop-model-baseline` | 1차 모델·자료·품종 근거 조사 | 후보 비교, 한 품종/작기 개발 경계, 계수/단위/권리 등록부와 보류 목록. 등록만으로 G0 승인 아님 |
| 2 `crop-growth-rates` | 필요한 문헌식/코드·매개변수의 버전/차원/권리 검토, 명시적 합성 forcing | 광 동화·분배·호흡·기관 변화율 표. 독립 참조값, 야간/잎 면적 0, 탄소 수지, 부적합 입력 거부 |
| 2a `crop-photosynthesis-domain` | 원식/작은 수관의 특이점 확인 | 온도·LAI·CO₂의 원식 지원 영역과 초기조건 hold·독립 검증. 원식의 임의 clip/기본값 없음 |
| 3 `crop-growth-integration` | rate kernel과 원식 적용 정책의 수용 | **로컬 소프트웨어 수용:** 잎 면적/기관 상태 시계열·manifest. 초기조건/UTC/관리 사건, 양수성·수지·수렴·재실행 확인. 실제 개발 참조 재현은 forcing QC 뒤 |
| 3a `crop-cycle-capacity` | 적분 수용·실제 archive의 파일/시점 감사 | 개발: 기관 단독v1의20,000 배열/100만 step·16/64MiB와 기관·과실/startup의128 forcing/128 event·512 output·10,000 step·1일을 구분한 연속 상태/수지·저장/출력·부하/재현 계약. 실제 한 작기 실행은 forcing/초기조건 채택 뒤 |
| 4 `crop-result-storage`, `api-crop-replay` | 적분 수용, 기존 불변 저장/현재 권리·계정 제공자 | 저장 결과 ID·입출력 해시·보류·시계열 조회. 다른 농장/테넌트/모델 혼합·변조·철회 거부, 재시작 동일 조회 |
| 5 `web-crop-replay` | 저장/API의 같은 상태 조회 | 같은 ID + timestamp의 잎 면적/기관량을 표·그래프·3D에서 확인. 모식 형태 표기, 키·착과수·숙기는 계산하지 않으면 표시하지 않음. WebGL 대체·키보드/시간 이동 시험 |
| 6 `crop-fruit-transport`·`crop-fruit-allocation-rates` → `crop-fruit-cohorts` → `crop-harvest-conversion` | 개발: 고정 발달식/단위·순간 이동 수용, 원 배분의 보존/W1/초기/gate 정책과 명시적 관리 사건. 실제 작기 적용: 해당 품종/관리·초기조건 QC, 생과 환산: 품종별 건물/생과중/품질 근거 | 개수/탄소 이동·착과/배분/적분→수확 사건·생과 kg·등급과 제거/기관 수지. 평활 탄소 제거나 일반 과실중을 생과 수확으로 대체하지 않음 |
| 7 `crop-climate-coupling`, `crop-water-nutrient`, `crop-energy-purchases` | 생장/생산 모델의 필요한 상태·계수/입력, 계량·변환 근거 | 수관/증산, 배지·급배액/재순환·성분, 열/구매 에너지의 각각 수지와 적용 범위. 기존 작물 효과 중복 차감 금지 |
| 7의 순수 자식 `crop-canopy-exchange` | 고정 원식/단위·권리·명시 합성 forcing; 전체 수확/국내 자료와 독립 개발 | [로컬 수용](../research/crop-canopy-exchange-implementation-20261009.md): 순간 E/H/LE·국소 부호·독립 참조/230시험. 동적 상태/기후 결합·구매 자원·경제 미수용 |
| 7a `crop-execution-link` | 해당 모델/입출력 계약과 같은 농장/작물/배치 연결. 실제 실행에는 해당 forcing/초기조건 G0/G1 | 사용자 접수→작업자→불변 결과 선택/3D·취소/재시작/현재 권리. 기존 작업/worker 재사용 |
| 8 `crop-economic-link` | 생산 배치·자원 결과와 같은 기간의 판매/정산/비용 근거 | H/P/S·등급/재고·원가와 기존 Decimal 손익/현금의 결합·재실행/대사. 모델 수확의 출처 등급 유지, 미래 마진은 검증 전 hold |

`crop-input-audit`와 `crop-independent-data-access`는 2~5 개발과 병행한다.
공개 archive의 존재/CC0만으로 채널 단위·시각·면적·결측 QC를 통과한 것이 아니다.
실제 자료를 사용한 계산/화면을 열려면 해당 G0와 계산/재현 G1의 증거가 필요하다.
순수 모듈·합성 내부 시험은 국내 농장 계약·G2·시장 G0·전체 Compose 완료를 기다리지 않는다.
새 외부 데이터 adapter나 운영 변경은 이 목록의 핵심 경로가 구체적으로 요구할 때 추가한다.

독립 국내 자료 획득과 측정/검증 분할 준비는 모델 착수와 병행하지만,
G2의 최종 비교에는 검증 대상 버전의 계산/재현 증거가 필요하다. 국내 미래 수확은
해당 G2·G3a, 미래 가격·마진은 추가 시장/경제 검증, 후보 추천은 G3b, 공개 서비스는
G4를 요구한다. 연구 계산·3D 소프트웨어 수용은 전체 `end-to-end-g1`·실제 제품 CLI·
독립 해제 또는 현장/미래 검증을 대신하지 않는다.
