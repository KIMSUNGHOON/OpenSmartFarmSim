# 저장 면적·기후와 실제 잎 3D 연결 — 2026-10-24

상태: **합성 저장 재생의 소프트웨어·사용자 Chrome 수용**.
[화면](http://localhost:5176/growing-geometry-replay.html), [계약](../contracts/growing-geometry-3d-v1.md),
[기계 증거](artifacts/growing-geometry-3d-20261024.json), [306면적 장부](artifacts/growing-geometry-3d-surfaces-20261024.csv).
[desktop](artifacts/growing-geometry-3d-desktop-20261024.png) / [mobile](artifacts/growing-geometry-3d-mobile-20261024.png).
이전 [export/SDK](growing-geometry-web-replay-20261024.md) 다음 단계이며 전체 goal 완료가 아니다.

## 사용자가 확인하는 범위

여섯 자체 합성32초 사례의17개 저장 시점을 재생한다. 동일한 원 leaf ID/면적/열적 나이와
LAI·실내/수관 온도·정확 원점+분수 초를 실제 Three.js WebGL2 잎 표면·표·그래프로 보여 준다.
이미 저장한 시점을 이동하며 새로운 중간 생장을 계산하거나 변화량을 확대하지 않는다.
URL의 scenario/artifact/frame으로 메뉴 이동·뒤로 가기·새로고침 후 같은 선택을 복구한다.

기존 직접 제작한 토마토 소엽/잎맥·PBR 재질·조명을 재사용했다.
`authored-three-leaf-scaffold-v1`의 줄기1.6m·세 부착 위치/방향과 각7소엽 형태는 제작 자산이다.
원 면적만 실제 표면 삼각형의 크기를 결정한다. 모델에 없는 키·과실·수확을 만들지 않고
기존24시간 줄기 모델이나 가짜 MorphologyFrame과 합치지 않는다.
실제 품종·작기/생산 예측과 최종 사실감 R2는 수용하지 않았다.

## 통과한 검증과 남은 경고

- 새 geometry/URL **34**, 관련 strict SDK **41**, 합계 고유 **75단위 검사**, 전체 web 타입과 minified multi-page build가 통과했다.
- 실제 Windows Chrome 기반 Playwright **12검사**가34.596초에 통과했다. 여섯 사례의102시점/306실제 표면과 원 값·정확 시각/표/그래프, URL·메뉴/reload·키보드·재생/정지, 모바일, 변조 후 stale 장면 제거/재시도·늦은 이전 요청 취소, 실제 WebGL context loss/불가 때 같은 표 유지가 포함된다.
- 별도로 사용자 전용 Chrome의 실제5176에서 **102시점/306표면**과 원 데이터276GET/3,149,941bytes를 대사했다. 최대 상대 면적 차는 **9.547918011776346e-15**로 기준5e-12 이하다. 모든 응답은 원 bytes/SHA와 같고 POST0, 해당 실행의 console error/warning0이다.
- 실제 창 숨김 때 `document.hidden`과 재생 정지를 함께 관측했다.1.1초 뒤와 복귀 뒤 같은 시점이다. 정지 후 유휴 draw 증가0, 모바일 overflow0/실제 투영 잎 경계±0.98 안을 확인했다.

이전 반복 실행의 검사 수는 합산하지 않는다. cold browser 첫 warm-day에는 기존 Three.js/ANGLE shader precision warning1이 남았다.
다른 다섯 사례와 최종 사용자 Chrome에서는 경고0이었다. 경고를 숨기거나 최종 사실감/전체 환경 품질 통과로 해석하지 않는다.
기존 chunk500kB 초과 빌드 경고도 유지한다. 새 모델 수치/전체 backend·전체 UI 회귀/hosted 전체 CI는 이번 검사 범위가 아니다.

처음 모바일 기준은 DOM overflow만 검사해 WebGL 잎 잘림을 놓쳤다. 실제 vertex 투영 검사에서1.478>0.98의 RED를 확인했고,
가로↔세로 전환 때 기본 카메라를 다시 맞춰 최종12검사와 실제 Chrome을 통과했다. 면적은 바꾸지 않았다.
첫 native 검사는 실패 뒤 열린 CDP 클라이언트 때문에260초 timeout으로 끝났다. 종료/단계 기록을 보완한 다음에는
배경 전환 확인이 실패했다. 설치된 Playwright `coreBundle.js`와 타입 설명을 대조해 기본 focus emulation이 실제 hidden 관측을 방해함을 확인했다.
`connectOverCDP(...,{noDefaults:true})`로 원 동작을 관측하자 숨김/복귀 모두 통과했다. 제품의 재생 로직 변경은 없었다.

## 자원·배포·디자인

최종 타입/75검사는6.424초·최대PID486,588,416bytes/합산892,051,456bytes,
최종 build는1.470초·441,769,984/819,871,744bytes,
최종 browser guard는39.599초·81,375,232/428,646,400bytes,
최종 native guard는14.137초·81,469,440/409,354,240bytes였다.
512MiB/PID·1GiB 소유+보호 합산·0.25초 표본/600초/로그4MiB를 바꾸지 않았다.
최종 각 phase의 원 파일/소스·보호4root와 FD4→4/소유 잔류0을 확인했다. Windows Chrome/Node는 위 WSL 합계 밖이며 전체 host 운영 용량 수용은 아니다.

전체 타입의 앞선 두 실행은 자식 exit0이어도 외부 RSS512MiB를 넘어 미수용했다.
설치된 TypeScript7 launcher가 Node를 native Go compiler로 교체하므로 Node heap 옵션은 해당 메모리를 제한하지 못했다.
프로세스에만 `GOMEMLIMIT=384MiB GOGC=50 GOMAXPROCS=2`를 적용해 같은 전체 타입을 통과했다.
이는 Go runtime의 soft memory 설정이며 외부 hard RSS 관측을 대신하지 않는다. [Go 공식 GC 설명](https://go.dev/doc/gc-guide#Memory_limit).

기존 gateway 정적 배포의724파일 metadata를 보존했다. 새 entry/데이터/버전별 asset을 추가한 뒤
최종 v2 asset151개를 먼저 검증하고 이 작업의 새 HTML release pointer만 원자적으로 갱신했다.
이때 기존 다른1,151파일과276원 데이터가 유지됐다. served HTML SHA는
`90da221bda7abfd4d8af25a054da803189097eb7771a3b64bed0095ce62ca626`이다.
기존 HTML 덮어쓰기0·API/DB/키/서비스 재시작0이며 새 서비스를 추가하지 않았다.

12ui는 기존 승인 LayerDoc SHA `a6a0f14e13ff9e34cae3a1b8adfc0dbf0aa6c72cbc07887bd04e4ba63b213498`와
실제 desktop 캡처의 capture/convert/plan을 끝냈다. 가격 상한0·구매0이며 기존 CSS/자체 호스팅 글꼴을 유지했다.
image mode의 unanchored 비교로 DOM coverage0이므로 픽셀 정렬/R2 수용은 아니다.
식물/차트의 raster 교체·원 데이터/조작 축소 제안은 사용자의 실제3D/저장값 요구와 충돌해 채택하지 않았다.
초기 repo 인자/CLI dry-run 후처리 실패도 증거에 보존했다.

현재 native Codex CLI `gpt-6.1-sol`/`xhigh`, turn_context2026-10-24T08:36:34.949Z,
원 LF 포함 SHA `2c309fc06edb8735ca99f16c06d4ceec9628511abd9ddc5910e5703944e8309a`·재귀 CLI0으로 판단했다.

## 다음 한 단계

다음은 **독립 면적의 명시 잎 제거 사건**이다. 우선 같은 정확 시각의 point 경계에서
원 a/A/D0·현재 leaf inventory와 전체 leaf C의 분포·제거할 CH2O/용량/현열을 명시하고 독립 수지로 확인한다.
기존 SLA 일치 제거식을 자동 적용하지 않는다. 같은 잎의 연속 유출과 사건 차감을 두 번 적용하지 않는다.
삭제되지 않은 원 상태/온도·시각은 보존하고, 누락/단위/중복·기초 state SHA 불일치·과다 차감을 거부한다.
그 뒤 사건→다음 연속 구간과 분할 재개를 별도 수용하며 빈 수관/출현 질량·공급 제한을 확장한다.

point 계약/기존 입력 대조30–60분, 최소 구현/독립 수지·거부 검사60–120분, fresh/검토·기록30–60분으로
**2–4집중시간**을 낮은 신뢰로 추정한다. 다음 구간/재개·저장3D·전체 작기·실제 자료 획득은 포함하지 않는다.
국내 원 측정/미사용 독립 작기0·첫 국내 품종 미확정, farm/current rights custody·실제 CLI G1 종단 간,
자원/생산·Decimal 경제·거시/수급·자율 후보 비교와 G0–G4/R2는 남아 있다.
자료 획득은 개발과 병행하며 전체 제품 완료일은 외부 자료/검증 일정이 없어 미정이다.
