# 현재 C_i/a/A와 개별 장부의 분할 재개 수용 — 2026-10-25 KST

[새 계약](../contracts/crop-leaf-carbon-stock-continuation-v1.md)의 합성 고정 목록 재개를 수용한다.
[구현](../backend/app/crop_leaf_carbon_stock_continuation.py)은 [수용한 짧은 적분](crop-leaf-carbon-stock-dynamics-20261025.md)의
현재107+3n상태/21+3n누적량과 원 D0·코드/profile/격자를 불변 context/checkpoint에 묶는다.
현재 C_i/A를 초기값이나 곡선에 재맞추지 않고, 과거 구간을 계산하지 않는다.
기존 모델/프로필/저장 결과·사용자 화면은 변경하지 않았다. 다음은 불변 저장/같은 상태3D다.

현재 native Codex CLI context는 `2026-10-24T16:46:39.669Z`, model=`gpt-6.1-sol`, effort=`xhigh`,
원 LF SHA-256은 `d45214a3f27969dc848e1a189cd4114c2014acd36fbd52edc9e083d24c189028`다. 재귀 CLI0이다.
부모가 새 short와 기존 companion continuation의 호출·직렬화/장부를 대조했다.
새 모듈은 기존 불변 protocol 패턴을 사용하되 새 타입/version·실제 code fence와 동적 perleaf 유량 단위를 결속한다.
새 농업 계수/원문/측정 자료 채택0, 별도 독립 검토자·자료/관문 승인은 없다.

context는 원 요청/정규 program/seed·초기 영수증/첫 RHS·manifest의 immutable bytes다.
checkpoint는 신뢰한 원 bytes SHA를 요구하며 현재 endpoint를1회 검증한 뒤 걸음당4새 stage를 전진한다.
chunk크기·벽시계/복원 횟수는 payload identity에 넣지 않아 같은 격자의 prefix/최종 bytes를 보존한다.
현재 code/profile/float 환경·schema/단위/시각/상태/파생량·전체/개별 장부가 다르면 보류한다.
이 SHA는 **외부의 신뢰한 원 bytes**를 식별하는 계약이다. SHA를 다시 만든 것만으로 과거/권리/농장 진본을 증명하지 않는다.
후속 서버의 불변 저장/서명 공급자가 신뢰 anchor를 발급해야 하며 Python 내부 필드 조작의 보안 경계가 아니다.

| 실제 검증 | 결과 |
|---|---|
| 신규/관련 | 신규 **138개**를 포함해 **297 passed**.6조건×4step의 모든8composition과 대표32초의 모든15단일 cut, 초기/중간/완료 원 bytes·같은 sample/누적량·최종 bytes를 대사했다. 전체 백엔드 시험은 실행하지 않았다. |
| 보존/거부 | 초기화 helper/원 whole integrator를 막고 현재 C_i/A/D0·원 순서/단위·누적량을 복원했다. malformed/중복/비UTF8/비canonical·wrong digest/구형 version·shape/float/현재 진단/장부·profile/code/환경·예산과 확정 prefix를 검사했다. |
| 경계/실패 | 1/512잎의 raw roundtrip/이어 계산, 서로 다른 perleaf weight의 직렬화 순서,512KiB checkpoint/2MiB context·scalar/time/step 상한을 확인했다. k2/k3/k4/endpoint/balance/seal 실패에서 미확정 상태를 게시하지 않았고 cancel/외부 오류는 정상 hold로 바꾸지 않았다. |
| 별도 프로세스 | 같은6context·초기/중간/완료의 **18checkpoint**가 원 bytes/SHA 그대로였다.2,628현재 state/유량 수량을 보존하고 중간에서8걸음씩 이어 계산한 **48시점**과6최종 checkpoint bytes가 생산 프로세스와 일치했다. 이는 합성32초 사례이며 실제 작기/관측이 아니다. |
| 독립 장부 | 원 raw 상태/유량으로 Decimal120의 전체 C/fruit number·수관/공기/증기/용량/reduced energy·각 나이/개별 C **234장부**를 다시 계산했다. 잔차/반올림 예산 최대0.009821872825203812. 생물학적 정확도가 아니다. |
| 호출/부작용 | fresh의 context 초기6·복원 현재18·재개 현재6/새192=총222stage, 새 scalar advance240회. 복원 중 과거 전진/재초기화·옛 geometry 계산·DB·CLI/network/쓰기 시도0, FD4→4. |
| WSL/자료 | 원 소스/감시4,500항목·현재4root 보존·소유 잔여0. 최대 PID74,690,560bytes/소유+보호 합계452,734,976bytes.512MiB/PID·1GiB 상한 유지, Windows 전체 자원 측정은 아니다. |

[검사](../backend/tests/test_crop_leaf_carbon_stock_continuation.py),
[증거 JSON](artifacts/crop-leaf-carbon-stock-continuation-20261025.json),
[18checkpoint 요약 CSV](artifacts/crop-leaf-carbon-stock-continuation-20261025.csv)에 현재 판본을 고정했다.
첫 RED는 모듈 부재의 exit2였다. 초기126pass 뒤 late component fence가 seal에서 source 예외 타입을 노출하는 문제를
별도 RED로 확인했고 공개 continuation 예외로 결속해 최종138/297을 통과했다.
source field·모든 숫자를 옳은 과거로 인증하는 시험이 아니며 코드 검토/수지·외부 anchor의 경계를 구분한다.

자체 검토에서 단일 C_i 권위·동적 유량 순서와 code/입력/profile/환경 결속, 현재1회 검증/초기화0·원자 prefix를 확인했다.
웹·DB·제품 CLI는 변경하지 않아 관련 build/브라우저·DB/실제 CLI를 다시 실행하지 않았다.
고정 목록/elapsed 격자의 연구 재개이며 공급 제한 면적·조달된 출현·UTC 농장/관리 checkpoint를 승인하지 않는다.
현재 새 제거3D의 무모사 표시 창/R2 보류는 유지한다.

다음은 현재 계산 결과의 불변 저장/무계산 reader→strict SDK/같은 상태3D다.
새 잎의 초기 C/호흡·현열 조달 근거는 이 저장 경로를 막지 않는 병행 연구로 남긴다.
실제 품종/한 작기·생산/자원/Decimal 경제·거시/수급·자율 비교, 국내 독립 측정/미사용 작기0·첫 품종 미확정,
farm/제품 CLI·R2/G0–G4·전체 goal/완료일은 미완료·미정이다.
