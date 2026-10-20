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

## 다음 수용

다음은 이 app source의 **계측 OFF 정상20개 실제 HTTPS**다. 원4.47MB packet/20개 생성,
30초/64KiB·현재 거부/복원·원 row/DB 불변·조회 계산/쓰기0·자원/정리의 완료 증거가 필요하다.
원 실패 source를 재실행하지 않는다. 결과를 받기 전에는20개/U1·WSL·사용자 적용을 수용하지 않는다.
전체 backend/web CI·브라우저와 새 UI/Solar 배포를 이번163개로 수용하지 않는다.
생산/자원/경제·실제 CLI 종단 간/독립 자료/G0–G4·전체 완료일은 미완료/미정·goal active다.
