# 작물·기후 원 입력 검증 증거 — 2026-10-10

## 수용 범위와 산출물

core **9a89a908ca1060856e110c1ae8af94ca4d1b28a6**의
[검증 모듈](../backend/app/crop_climate_joint_input_evidence.py), [82개 검사](../backend/tests/test_crop_climate_joint_input_evidence.py),
[계약](../contracts/crop-climate-joint-input-evidence-v1.md)을 로컬 수용했다.
[검증 묶음](artifacts/crop-climate-joint-input-evidence-reference-20261010.json)에 원 종료·현재 원본/검토·별도 Python·자원을 기록했다.
새108상태 공동 모델의 합성 입력 수학/QC 검사 증거다. 이전121상태의 authority/context를 새 모델 승인으로 재사용하지 않는다.

신뢰한 caller가 제공한 원 source SHA·원 context/UTC binding과0700 directory의 원본6파일을 받는다.
4개 고정 reference profile·원 notice·초기 상태/초기 RHS·시간 origin·schema/QC/정규화/코드/수치 환경과
명시 검토자·결정·증거 ID를 별도 domain의 HMAC에 결속한다. 키는 증거에 포함하지 않는다.
기존 bounded secure-file/metadata/strict-JSON 함수만 재사용했다. 새 DB/권한 서비스/큐를 추가하지 않았다.

발급은 원 입력에서 초기 context를 새로 한 번 준비해 기존 원 context/binding에 정확히 대사한다.
**발급 초기 RHS1회**, 진행 적분/관리 사건0회다. 현재 조회는 서명·expected SHA·현재 원 파일/검토/코드를 검사하며
초기 context를 다시 만들거나 계산을 실행하지 않는다. 현재 검토 resolver는 caller가 제공하는 신뢰 경계다.
이번 시험 resolver는 소유 합성 기록이며 제품의 현재 농장/자료 권리 저장소 조립은 다음 단계다.

## 실제 검증과 발견한 오류

| 단계 | 원 세션/완료 도구 | 실제 결과 |
| --- | --- | --- |
| 첫 집중 검사 | 67439 / `a50075` | 종료1·71통과/2실패·pytest4.38초/감독4.911초 |
| 수정·확장 후 집중 검사 | 80995 / `9f1fad` | 종료0·82통과·pytest5.06초/감독5.675초 |
| 별도 root 대사 | 20815 / `c46807` | 종료0·감독2.611초/body1.535초 |

첫 검사에서는 두 번째 검토 callback이 원본 bytes를 바꾸는 반례2개가 실제 실패했다.
검토 확인 뒤 원본을 최종 재검사하도록 순서를 수정했다. 발급/조회 모두 반환 직전 변경을 거부한다.
실패 당시 원 source SHA `331c17641d3632a5ddd71d1464ab88d7d2d682c05471a4c4318ab4d6a5564b66`과 로그를 보존했다.
최종82개에는 원 반례와 최대 schedule·잘못된 원 schema/단위/시간·현재 Python 환경·초기 RHS 실패를 포함한다.

원9개 수용 프로그램의 context/UTC binding SHA를 [기존 시간 증거](artifacts/crop-climate-joint-time-reference-20261010.json)와
정확히 대사했다. 원9×108=972개 초기 상태·원 program/초기 RHS/manifest·4프로필/notice/UTC와 검토 ID를 보존했다.
추가128사건/512출력 schedule까지10개를 발급해 각각 초기 RHS1회, 별도 준비 RHS1회를 확인했다.
이것은 초기 입력/QC 검증이며 최대 schedule의 생장 실행/전체 작기 예측 수용은 아니다.

독립 fresh PID1914997은 원 모델 Context/Binding 객체 없이10개 현재 원본과 서명 증거를 검증해 실제 종료0이었다.
context 생성·start/restore/advance·RHS/step/event·UTC binding 생성이 **모두0회**다.
같은 fresh 서버에서 각 검토를 철회해10개 모두 hold를 확인했다.
서명·키/issuer/key ID·버전/범위/관문/QC/정규화·다른 seed/시각/프로필/환경/expected SHA,
검토 변경/철회/누락/오류, 현재 파일 변조/누락/추가/writable/symlink/ancestor symlink/hardlink/FIFO/초과를 거부했다.
반환 record의 복사본 변경이 원 증거를 바꾸지 않으며 실패에서도 FD 누수가 없다.

선행29개 core파일·9개 구성 코드·16개 oracle 입력 SHA는 기존 수용 파일과 같다.
기존993개 수치/저장 검사를 이번에 다시 돌리지 않았다. 새82개의 결과에 기존 통과 수를 더해 새 실행으로 표시하지 않는다.
원166일 RHS/writer/API/WebGL과 이미 수용한 Decimal/시간 oracle도 재실행하지 않았다.

## 용량·보존·CLI·CI

최대 실제 원 source201,751bytes·서명 증거263,531bytes로1MiB/2MiB 상한 안이다.
source6파일은0400·euid 소유/단일 link의 regular file이고 경로 전체를 nofollow로 열며 전후 metadata를 검사한다.
각 단계 source1,729·원본2,148항목·기존 preview source/assets와3개 실제 PID를 보존했다.
감독/별도 root FD4→4, 소유 non-zombie 잔류0, 기존 frontend200이다.
0.25초 관측 최대 단일 RSS147,255,296bytes·소유+보호 합456,556,544bytes로512MiB/1GiB 안이다.

설계/구현/검토는 현재 native Codex CLI **gpt-6.1-sol / xhigh**,2026-10-09T18:24:31.625Z에서 수행했다.
원 turn_context JSONL 줄(LF 포함) SHA는 `5f31dda7b00b4bae20ec4e102b9f008256801d4dcfe73e0d6247815c0fc1bfc0`다.
재귀 CLI0회이며 이 세션의 출력은 위 core/계약과 원 검증 묶음이다. 제품 runtime CLI 새 호출이나 관문 승인 증거는 아니다.
03:33 KST 관측 exact703e49c Backend37962183498은0–4 success·5 in_progress였다.
현재 core의 hosted 수용은 아직 없으며 원 CI를 취소하거나 새 push로 대체하지 않았다.

## 사용자 화면·다음 단계·외부 의존성

`localhost:5173`은 기존 완료 합성166일 생장/수확의 실제 DB/API·같은 UTC3D를 유지한다.
이번 새 입력 증거는 그 UI에 아직 연결되지 않았으며 계산 진행률/새 checkpoint 자동 반영 U3도 미구현이다.
다음은 **현재 농장/자료 권리 결속→서버 custody/등록→현재 권리 API→같은 UTC3D→사용자 실행/U3**다.
기후 원식·온실 forcing과 독립 농장 자료 확보는 이 개발과 병행한다.

다음 `crop-climate-joint-farm-binding`은 현재 등록 tenant/농장 판본·crop/batch/zone/재배 기간과
새 context/UTC/input evidence를 결속하고, 현재 원 source 계산·표시권 및 검토 철회를 전후 확인한다.
기존 FarmAuthoringService/권리 resolver를 사용하되 새108상태를 이전 CalculationContext로 위장하지 않는다.
실제 등록 DB·다른 계정/기간/원본/모델 혼합·철회·fresh/FD/원 종료/자원을 검증한다.

잠정 작업 분해는 기존140줄 결속/현재 resolver와 새 계약 검토0.5–1시간, 구현1–2시간,
실제 등록 DB/fresh·권리/혼합 반례1–2시간, 증거/기록0.5–1시간의 **3–6집중시간**이다.
현재 입력 증거의 실제 집중 검증5.675초·root2.611초를 확보했지만 DB/권리 연결 시간은 아직 실측 전이다.
계속 작업·새 외부 자료를 요구하지 않는 합성 경로 조건으로10월10일 검토를 목표로 하며 전체 UI/제품 완료일은 아니다.
실제 품종 입력/농장 Run/국내 독립 자료0건, G0–G4·생산/미래 마진/추천 hold를 유지한다.
