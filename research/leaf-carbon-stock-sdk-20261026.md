# 저장된 잎별 탄소·나이·면적의 웹 SDK — 2026-10-26 KST

[SDK 계약](../contracts/leaf-carbon-stock-sdk-v1.md)을 합성 연구 범위에서 수용한다.
[SDK](../web/src/leafCarbonStockReplay.ts)는 원6개 공개 packet의 bytes/지문·코드/profile/notice·권리·시간/상태 구조를 확인하고
현재 C_i/a/A와 기후/50과실 cohort·동적 누적량/장부를 분리된 복사본으로 반환한다.
새 생장 계산·보간이나 탄소→면적/키/생과 추론은 없다. 사용자 화면·기존 모델/프로필·저장 경로는 변경하지 않았다.
다음은 같은 leaf ID/현재 A의 실제 삼각형과 같은 시점 C_i·표/그래프 연결이다.

실제 검증은 2026-10-24 17:45–17:58 UTC(10월25일 KST)에 수행했고 10월26일 현재 파일/원 지문을 재확인했다.
구현 당시 native context=`2026-10-24T17:41:50.640Z`, gpt-6.1-sol/xhigh,
원 LF SHA=`40722356f39574c29e4952523b43d83915322cd8613b1fd5e233f01c474a7b6d`다.
현재 수용 검토의 native context=`2026-10-25T22:24:12.672Z`, 같은 모델/effort,
원 LF SHA=`71cfd60b0ed9a022e40fe36599baff1f21299046f16b0d627717473d3c073f8f`다. 재귀 CLI0이다.
새 외부 자료·농업 계수/측정·패키지를 채택하지 않았으며 독립 농업 검토나 관문 승인이 아니다.

| 검증 | 실제 결과 |
|---|---|
| SDK/회귀 | [신규99검사](../web/src/leafCarbonStockReplay.test.ts), 기존 면적41/제거109를 포함해 **249 passed**.6조건/102시점의 원 DTO/CP·상태/유량을 보존하고 모든46종 wire file·source/단위/ID/권리/시각·취소/상한의 변조를 거부했다. 전체 웹 unit suite는 실행하지 않았다. |
| 실제 경계 | 백엔드의 원 계산/저장/export를 거친1개·512개 잎과 dt=1/3의 결과를 test-only packet52파일로 보존하고 SDK decoder에서 원 상태/장부·정확 분수 시각을 대사했다. 임의 합성된 mesh 상태를 예상값으로 쓰지 않았다. |
| 재현/원본 | [고정 공개 선언](../fixtures/crop-leaf-carbon-stock-web-declaration-v1.json)과 [generator](generate-leaf-carbon-stock-replay-fixtures.py)로6packet/276파일을 재생성했다. 기존 export/채택한 새 namespace와 원 bytes가 같았고 code/profile/원 정규화 곡선 지문을 등록했다. 원 private False168blob은 유지했다. |
| 타입/빌드 | 전체 웹 `tsc --noEmit`와 **독립 SDK Vite 빌드**를 수용했다. SDK39,614bytes, SHA=`bd7e7d518e36c5e346ae94a9559001fa28a89fd4f8b4e5c388fe5cecffb109b2`다. 독립 SDK 빌드는 주앱 전체 빌드의 통과가 아니다. |
| 실제 HTTP | 임시 loopback HTTP 서버/별도 Node 프로세스의 실제276응답·고유276파일이 원 bytes와 같았다.102시점/**19,278수량**·원 CP/DTO가 일치했고 권리/notice·원 file metadata와 FD를 보존했다. 관측 wrapper는 실제 응답을 같은 bytes로 SDK에 전달했다. 서버를 종료했으며 사용자용 상시 서비스가 아니다. |
| 최종 통과 자원 | 최종 통과 단계의 최대 PID506,191,872bytes/소유+보호885,235,712bytes. 당시 보호4root/감시4,500항목/원 source·FD4→4를 보존했다. Windows 전체 측정은 아니다. 실패 단계의 초과는 아래 별도로 기록한다. |

[증거 JSON](artifacts/leaf-carbon-stock-sdk-20261026.json)과
[공개/경계328파일 지문 CSV](artifacts/leaf-carbon-stock-sdk-files-20261026.csv)에 실제 판본을 고정한다.
공개 파일276개와 test-only 파일52개이며 기존 화면/배포 디렉터리에는 복사하지 않았다.
원 input/request/program/seed/context의 닫힌 구조·원 코드/profile/환경·정확 격자와 초기 영수증/곡선,
107+3n vector·21+3n 유량 및 각 leaf carbon 수지/허용량을 자체 검토했다.
loader가 고정 wire 지문을 검사하며 decoder 단독은 새로운 root나 권리를 인증하지 않는다.

첫249검사 중7개는 등록한 곡선 지문이 원 선언의 정수 표현을 사용해 실패했다.
원 정규화 DTO의 지문을 사용하도록 수정하고 재생성·249검사·타입/독립 빌드·HTTP를 통과했다.
첫 타입 명령은 이전 검증의 Go 메모리/병렬 제어 누락으로 상한을 넘었다.
기존 GOMEMLIMIT=384MiB/GOGC=50/GOMAXPROCS=2를 복구한 뒤 전체 타입 검사는 통과했으나,
이어진 기존 주앱의 기본 Vite 전체 번들 생성은 최대 PID798,302,208bytes/합계1,177,403,392bytes로 다시 중단됐다.
두 단계 모두 실패로 남기며 마지막 잔여 프로세스도 재확인했다. 상한을 완화하거나 전체 빌드 통과로 바꾸지 않았다.
현재 주앱 진입점에 새 SDK를 연결하지 않았으므로 전체 타입·독립 SDK 빌드·HTTP까지를 이 SDK의 수용 범위로 명시했다.
**주앱 전체 번들 생성은 보류**이며 후속 사용자 통합/배포가 해당 빌드에 의존하면 먼저 해결해야 한다.

10월26일 재개 시 이전 API/worker3root는 종료됐고5175 외형 root만 기존 identity로 살아 있었다.
이전 유효기간 `2026-10-24T21:17:48.213594Z`는 경과했으며 갱신하지 않았다. 당시 검증의4root 보존을 현재4개 실행으로 표시하지 않는다.
새3D의 공개 합성 미리보기와 기존 farm/API 복구·인증은 별도 작업이다.
실제 브라우저/3D·사용자 적용은 이번에 실행하지 않았다. 기존 제거3D의 모사 없는 표시 창/R2 보류도 남는다.
첫 실제 품종 미확정·국내 독립 측정/미사용 작기0, 실제 한 작기/생산/자원·Decimal 경제·거시/수급·자율 비교,
farm/제품 CLI·R2/G0–G4·전체 목표/완료일은 미완료·미정이다.
