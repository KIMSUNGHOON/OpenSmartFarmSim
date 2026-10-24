# 개별 잎 탄소·나이·면적의 불변 저장/무계산 조회 — 2026-10-25 KST

[저장 계약](../contracts/crop-leaf-carbon-stock-artifact-v1.md)의 합성 고정 목록 경로를 수용했다.
[producer](../backend/app/crop_leaf_carbon_stock_artifact_producer.py)는 원 C_i/a/A·기후/과실 상태와
개별 누적량을 원 checkpoint bytes로 저장하고 완료 root를 마지막에 게시한다.
[reader](../backend/app/crop_leaf_carbon_stock_artifact_reader.py)는 생장/재개 모듈을 불러오지 않고 이를 읽는다.
기존 모델/프로필/저장 경로·사용자 화면은 바꾸지 않았으며 기존 POSIX 저장소를 재사용했다.

현재 native Codex CLI context는 `2026-10-24T17:24:22.588Z`, model=`gpt-6.1-sol`, effort=`xhigh`다.
원 LF SHA-256은 `0d3b6e377042eff35397f26fdf6e41d74791861b0173895c151988920a858938`, 재귀 CLI0이다.
이 판단은 기존 면적 companion 저장 경로와 새 state/layout/동적 유량 계약의 코드 대조다.
새 농업 계수·외부 원문/측정 자료 채택0이며 별도 독립 농업 검토나 G0–G4 승인이 아니다.

| 검증 | 실제 결과 |
|---|---|
| 집중/회귀 | [신규102검사](../backend/tests/test_crop_leaf_carbon_stock_artifact.py)와 기존 companion 저장89검사, **191 passed**. 최종 판본에서 plant/cohort/climate 투영도 원 vector와 대사했다. 전체 백엔드 시험은 실행하지 않았다. |
| 저장 결속 | 원 input/request/program/context/seed·초기 면적 영수증/profile4종/notice, 각 raw checkpoint의 원 SHA와 순서/prefix·정확 분수 초를 보존했다. 반복/다른 디렉터리의 같은 root와 fraction dt를 확인했다. |
| 새 C_i 계약 | aggregate leaf의 입력/상태 중복을 거부한다. 원107+3n state와21+3n 누적량·개별 C_i/a/A를 복사하며 모든 plant/cohort/climate offset을 대사했다. 1/512잎·동적 유량 순서/단위·원 scalar/512KiB CP·2MiB context 경계를 확인했다. |
| 거부/실패 | schema/단위/ID/권리/상한·재지문 변조와 현재/늦은 파일 정책/코드, 원본 corruption·partial write/domain hold에서 완료 root 반환0을 확인했다. caller copy와 FD를 보존했다. |
| 독립 프로세스 | 별도 producer/reader의6조건×17시점=**102시점**에서 원 checkpoint bytes·DTO/hash가 같았고 **19,278수량**을 대사했다. 원 plant4/cohort100/climate3의 DTO 투영도 매번 원 vector와 대사했다. 합성 elapsed32초이며 실제 작기·관측이 아니다. |
| 조회 부작용 | import finder와 audit hook·DB/CLI 차단으로 생장/초기화/재개 import·호출, DB/CLI/network/쓰기 시도 **0**, FD 보존과 원 file metadata/bytes 보존을 확인했다. |
| 권리/자료 | 새 private6store의 **168blob/1,828,518bytes**, redistribute=False를 보존했다. raw bundle/store는 저장소에 커밋하거나 공개하지 않았다. 자체 합성 source 선언과 원 reference/notice를 보존하며 실제 farm 권리/서명 진본의 검증은 아니다. |
| WSL | 감시4,500항목/보호4root·원 source 보존·소유 잔여0, FD4→4. 최대 PID141,185,024bytes/소유+보호530,309,120bytes.512MiB/PID·1GiB 합계 상한을 유지했다. Windows 전체 측정은 아니다. |

[증거 JSON](artifacts/crop-leaf-carbon-stock-artifact-20261025.json)과
[102시점 해시 CSV](artifacts/crop-leaf-carbon-stock-artifact-20261025.csv)는 raw 데이터 대신 소프트웨어 검증·해시만 기록한다.
부모가 source pin·새 code/context/layout/동적 유량·state offset·root-last/반환 전 fence와 무계산 경계를 자체 검토했다.
조회는 신뢰한 root의 원 데이터를 복사하며 새로운 root의 해시 재작성만으로 과거/방정식/권리를 인증하지 않는다.
현재 파일 정책은 검사하나 실제 farm/테넌트 권리·서명 custody는 상위 경로의 후속이다.
저장소 구현은 변경하지 않았고 새 서비스/패키지·DB·제품 CLI를 추가하거나 실행하지 않았다.
웹/사용자 화면을 바꾸지 않아 타입/build/브라우저 검사는 다시 실행하지 않았다.

다음은 원 bytes의 strict export→SDK→같은 시점의 사실적 잎 mesh/표/그래프다.
private False를 공개로 바꾸지 않으며 필요하면 별도 자체 합성 공개 선언/새 불변 root로 분리한다.
저장 A를 실제 잎 면적에 연결하고 C_i에서 면적/키/생과를 추론하거나 임의 애니메이션을 만들지 않는다.
새 출현 C/호흡·현열 조달 연구와 독립 농장 자료 확보는 병행하며 저장/3D의 선행 조건으로 추가하지 않는다.
현재 제거3D의 모사 없는 표시 창/R2 보류는 그대로다.
첫 실제 품종 미확정·국내 독립 측정/미사용 작기0, 실제 한 작기/생산/자원·Decimal 경제·거시/수급/자율 비교,
farm/제품 CLI·R2/G0–G4·전체 목표와 완료 날짜는 미완료·미정이다.
