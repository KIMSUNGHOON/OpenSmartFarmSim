# 기관 목록 등록 재구성 범위 수정 — 2026-10-21 KST

[원20개 실패/구간 관측](organ-catalog-hosted-capacity-20261021.md) ·
[하위 비용 증거](artifacts/organ-catalog-nested-cost-20261021.json) ·
[수정/회귀·같은 자료 비용 증거](artifacts/organ-catalog-registration-scope-20261021.json) ·
[계약](../contracts/crop-organ-result-catalog-v1.md#현재-용량-수정-후보).

## 비용 근거와 수정

source0b3086b의 [CI39455715905](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39455715905)는
원20개/입력·SQL·현재 검사·30초/RSS를 유지한 하위 계측이다. 정상 용량 수용은 아니다.
같은 첫 검사에서 timeout 전에 완료한 항목2–19(18개)를 선택했다.
표본 끝은 관측29.891726초, client timeout은 관측30.491453초였다.
중첩 포함 시간은 합산하지 않았고, 자식 제외 시간의 합이 표본 get 포함 시간과 일치하는지도 대사했다.

| 표본 호출 | 횟수 | 포함 wall | 자식 제외 wall |
| --- | --- | --- | --- |
| store.get | 18 | 22.591703초 | 1.197601초 |
| farm.read_registration | 36 | 13.731674초 | 13.731674초 |
| store._checked | 18 | 12.879542초 | 5.735982초 |
| store._current | 36 | 14.620262초 | 0.023207초 |

이는 선택한18개 완료 표본의 관측이며 전체30초 요청의 비용 비율/처리량 증거가 아니다.
전체 계측은 child1/152.728067초·합592,900,096bytes·FD6→6·소유 정리를 확인했다.
WSL ZIP 다운로드도 종료0/2.962930초·합642,281,472bytes·보호5root/원본/소유 정리를 확인했다.
ZIP/추출 파일/실행 source hash·동일 입력과 표본 시각을 독립 대사했다.

각 초기/전/후 항목 검사에 기존 `registration_read_scope`를 열어 등록의 재구성만 그 검사 안에서 재사용한다.
기존 scope는 매 lookup마다 현재 원천/권한/등록을 재확인한다. 각 `store.get`과 그 내부 검증,
프로그램 표시 권리·양쪽 guard와 페이지3회 항목 검사는 그대로다.
상위 호출자의 scope는 빌려 쓰며 예외에서 새 scope만 닫는다.
저장 producer/서명·원 packet·계수/모델·SQL/공개 응답은 변경하지 않았다.
`_binding`/`_registration`/`_rows`/`_item` AST와 원 저장 파일 bytes의 불변을 확인했다.

## 실제 회귀와 비용 비교

실제 SCRAM3행의 RED에서 반환 전/후 재구성이15/23회임을 확인했고,
수정 후5/8회로 GREEN을 통과했다. standalone GREEN1은 이후160회귀에 포함돼 중복 합산하지 않는다.
기관 metadata/API·기존 API·원 scope의 집중160개, 호출자 scope 소유/철회2개와 paired1개로
**같은 app source의 고유163개**를 통과했다. 중간 항목의 program 권리/계정/등록 변경도 거부했고
scope 종료와 원 행 보존을 확인했다. 등록 변경 반례는 실제 저장소 read의 반환값 fault 주입이며 DB 원본 변경은 아니다.

같은 정상 small3행을 baseline/candidate/candidate/baseline 순서로 조회했다.
baseline은 추가 inspection context만 no-op으로 만들어 원 `get`/검사 순서를 수행했다.

| 짝 | baseline | candidate | 감소 |
| --- | --- | --- | --- |
| 1 | 8.755874초 | 5.335928초 | 39.058878% |
| 2 | 8.711907초 | 5.372707초 | 38.329147% |

두 짝 양수·평균 **38.694012%**로 사전 평균5% 기준을 만족해 이 부분 비용을 수용했다.
각18회 program 권리 검사·동일 metadata/원 row·조회 put/integrate/RHS/SQL 쓰기0과 scope 종료를 확인했다.
직접 reader의 small3 비교이며 HTTP/큰 packet/20개 또는 WSL 동시 WebGL 용량으로 확대하지 않는다.

집중160 guard는 종료0/288.445010초·단일175,403,008/합859,389,952bytes,
paired/호출자 guard는 종료0/79.186363초·단일134,631,424/합782,852,096bytes였다.
모두 원5root/원본2,148·두 frozen source/자산·FD4→4·소유 프로세스/PG/임시/자격증명 잔여0을 확인했다.
원512MiB/PID·합1GiB·600초를 유지했다. 실제 농장·과학 관문은 평가하지 않았다.

## 계측 OFF 실제20개 후속

source `e8e70a28552b16b9df032221b27adebb21e68e8d`의
[CI39459278835](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39459278835)은 실패했다.
계측 OFF·원20개/각4,474,409bytes·합89,488,180bytes 생성 준비91.172334초 뒤,
첫 목록이 **30.081630초/TimeoutError**로 원30초를 통과하지 못했다.
현재 거부/복원·완료 목록/원 정렬과 마지막 row/DB counts 불변 대사는 미수행이다.
small3 부분 비용 수용은 유지하지만 실제20개/큰 packet 용량은 미수용이다.

조회 put/integrate/RHS/SQL 쓰기0·HTTPS 서버 종료를 확인했다.
hosted guard는 child1/reason없음·147.885015초·단일327,319,552/합605,040,640bytes,
FD6→6·source8파일 보존·소유 프로세스/임시/자격증명 잔여0이었다.
원 store와 catalogue/farm/scope source를 추가로 pin했고 ZIP/모든 파일/hash를 독립 대사했다.
WSL 다운로드도 종료0/3.224781초·합633,028,608bytes·원본/5root/FD/소유 정리를 확인했다.
부분 개선 진행 상태를 두 주소에 게시해200/동일 bytes/no-store·원 HTML/환기2,173파일을 확인했다.

## 다음 핵심 구현과 남은 수용

기관20개 용량은 미체크로 남긴다. 재개 시 immutable 검증의 중복 처리 경계 등을 먼저 검토하고,
필요한 작은 수정/집중 반례와 같은 자료 비용 비교→계측 OFF 실제20개를 검증한다.
같은 실패 source를 그대로 재실행하거나 개수/상한을 바꿔 수용하지 않는다.

다음 핵심 개발은 `crop-greenhouse-co2-stomatal`의 원문/단위 정책 검토다.
[제품 명세 §5.3](../docs/PROJECT_SPEC.md#53-개발-착수와-결과-게시)의 순수 계산 착수 조건과
기존 계산 의존성에 따라 개발하며, 이 연구의 선행에 기관 목록/UI 용량을 추가하지 않는다.
CO₂ 질량/ppm·압력/온도/부피와 CH₂O↔CO₂ sink의 source/pointer/권리·검증 가능성을 대사하고,
기존 `sRsSlope` 단위 충돌은 별도 판본 정책의 해소 또는 명시 hold를 요구한다.
먼저2개 연구 산출물/등록부로 다음 순수 계산 자식의 의존성과 수용 기준을 고정한다.
기관20개 용량·역사적 reader/다른 판본/디자인·전체 U1/WSL·사용자 적용은 최종 수용 전에 여전히 필요하다.
실패 확정/다음 핵심 개발의 최신 진행 기록도 두 주소의200·동일 bytes/no-store로 게시했다.
최종 게시 guard는 종료0/.343453초·합585,056,256bytes·원 HTML/환기2,173파일·원본/5root/FD/소유 정리를 확인했다.

전체 backend/web CI·브라우저와 새 UI/Solar 배포를 이번163개로 수용하지 않는다.
생산/자원/경제·실제 CLI 종단 간/독립 자료/G0–G4·전체 완료일은 미완료/미정·goal active다.
