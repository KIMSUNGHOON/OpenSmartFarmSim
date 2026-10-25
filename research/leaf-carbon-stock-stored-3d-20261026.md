# 같은 저장 탄소·면적 상태의 사실적 잎 3D — 2026-10-26 KST

[별도 공개 합성 미리보기](http://localhost:5177/leaf-carbon-stock-replay.html)를 기동했다.
`저장 결과 재생`은 원6조건/17시점 중 같은 index의 실제 잎 표면·C_i/나이·기후·표/그래프/장부를 선택한다.
자체 합성32초의 저장 계산이며 실제 품종의 한 작기나 생산·사업성 예측이 아니다.
미리보기의 이번 소유 실행은 **2026-10-26 11:48 KST**까지다. 원 저장 파일·선택 URL은 그대로 남는다.

[계약](../contracts/leaf-carbon-stock-stored-3d-v1.md), [페이지](../web/src/LeafCarbonStockReplayPage.tsx),
[renderer](../web/src/growingGeometryPlant.ts)의 새 진입점을 기존 승인 외형/장면에 연결했다.
원 A만 실제 복엽 삼각형 면적을 결정하며 C_i는 같은 시점의 독립 저장 수량이다.
제작 줄기1.6m·3개 부착/소엽 pose·보기 위한 조명은 고정된 제작 외형이다. 예측된 키·새 과실/출현은 만들지 않았다.
512개 잎 SDK 경계 수용을 이 제작3잎 renderer의 범위로 확대하지 않는다.
원 수치 모델/입력·저장 결과/프로필·기존 배포 파일은 유지했고 공유 장면의 기존 두 모드도 회귀했다.

현재 native Codex CLI context=`2026-10-25T22:24:12.672Z`, model=`gpt-6.1-sol`, effort=`xhigh`,
원 LF SHA=`71cfd60b0ed9a022e40fe36599baff1f21299046f16b0d627717473d3c073f8f`다. 재귀 CLI0이다.
새 외부 자료/농업 계수·관측/패키지·사진/3D 자산 채택0이며 독립 농업 검토/관문 승인이 아니다.

| 실제 검증 | 결과 |
|---|---|
| Unit/타입 | [새 renderer20](../web/src/leafCarbonStockPlant.test.ts)/[URL22](../web/src/leafCarbonStockReplayLocation.test.ts)를 포함해 **388 passed**, 전체 웹 타입 통과. 원102frame/306표면·C_i 복사본/처분·C_i 변경에도 A/pose 불변과 기존 renderer/SDK/URL을 확인했다. 전체 웹 unit suite는 실행하지 않았다. |
| 화면 build | 기존 `vite.crop-appearance.config.ts`의 모듈별 화면 빌드를 수용했다. 기존 주앱의 기본 전체 build와는 다른 진입점이다. 500kB chunk 경고1이 남았으며 숨기지 않았다. |
| 실제 Chrome | [신규12](../web/e2e/leaf-carbon-stock-replay.spec.ts)/기존31=**43 passed**. 새102시점의 실제 삼각형306면적·306 C_i/나이·원 장부/허용량·LAI/탄소 그래프와 같은 원 index/정확 시각을 대사했다. 면적 상대차 수용 한계는5e-12다. 메뉴/새로고침·키보드/시나리오·재생/유휴/모바일·원본 실패/늦은 응답·context loss/무WebGL의 표 보존을 확인했다. |
| 경고 | 43검사의 새6정상 조건에서는 콘솔 오류/경고0, 기존 첫 제거 조건에서 셰이더 정밀도 경고1이었다. 이후 새 Chrome 프로필로5177을 확인할 때도 첫 셰이더 X4122 경고1이 있었으나 오류0·면적/탄소 대사와 모바일/재조회는 통과했다. 경고를 억제하지 않았다. |
| 실제 미리보기 | 소유 정적5177에서 Chrome가 마지막32초를 선택·재조회해 같은 CP/3표면/3 C_i·50,490삼각형을 확인했다.1502빌드 파일을 새 소유 정적 root로 제공하며 요청 때 지문을 검사한다. `2026-10-26T02:48:40.375755Z` 만료, 기존 private API/DB/자격증명·이전 기한 갱신0이다. |
| 자원/보존 | 첫2단계의 실제 보호 root는 기존5175의1개, 새 미리보기 확인 때2개였다. 원 감시4,500항목/자료·source 보존, FD4→4·소유 잔여0. 최대 측정 WSL PID518,074,368bytes/합계567,992,320bytes.512MiB/PID·1GiB 상한 유지. Windows Chrome/Node와 전체 호스트 RSS는 이 합계로 측정하지 않았다. |

실제 브라우저는 분리된 Chrome의 headless WebGL2와 원 DOM/삼각형을 검사했다.
**모사 없는 사용자 표시 창/실제 최소화 검증·최종 R2는 아직 보류**다. headless의 document visibility나 이전 창의 통과로 대체하지 않는다.
현재 링크는 실제 미리보기이지만 이 브라우저 검증을 현장 작물/한 작기의 검증으로 확대하지 않는다.
기존 주앱 전체 번들의 WSL 자원 보류와 farm/API의 만료 상태도 남는다. 이번 모듈별 UI build를 전체 build 통과로 표시하지 않는다.

12ui-design의 기존 승인 `source.png`/완료 kit와 desktop/mobile 스크린샷을 직접 비교했다.
기존 색/글꼴/배치/카메라·PBR 외형을 재사용했으며 기능상 C_i 표/장부/그래프를 추가했다.
사용자의 실제 렌더링/계산값 요구에 따라 kit의 식물/차트 raster는 사용하지 않고 실제 WebGL/동적 SVG를 유지했다.
새 유료 디자인 호출·새 자동 improve alignment 실행은 하지 않았으므로 새 자동 정렬 점수의 통과를 주장하지 않는다.
별도 브라우저 도구가 없어 기존 분리된 Chrome/Playwright 경로를 사용했다. 개인 프로필·외부 URL/메시지는 사용하지 않았다.

[증거 JSON](artifacts/leaf-carbon-stock-stored-3d-20261026.json),
[원102시점/306잎 요약 CSV](artifacts/leaf-carbon-stock-stored-3d-20261026.csv)에 현재 판본을 기록한다.
자체 검토에서 실제 geometry/현재 C_i의 분리·원 ID/면적/시각·리소스 해제/유휴·URL 상태/실패 보류와 원 자료 보존을 확인했다.
같은 source의 검사가 통과한 뒤 생장/백엔드·DB/제품 CLI를 다시 실행하지 않았다.
첫 실제 품종 미확정·국내 독립 측정/미사용 작기0, 실제 한 작기/생산/자원·Decimal 경제·거시/수급/자율 비교,
farm/제품 CLI·G0–G4·전체 목표/완료일은 미완료·미정이다. 조달된 새 출현과 실제 자료 확보는 다음 핵심 의존성으로 남는다.
