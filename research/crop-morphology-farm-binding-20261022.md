# 형태 입력의 현재 농장/권리 결속 수용 — 2026-10-22

[계약](../contracts/crop-morphology-farm-binding-v1.md)의 소프트웨어 자식을 수용했다.
[기계 증거](artifacts/crop-morphology-farm-binding-20261022.json)는 실제 원 입력·새 exec/DB·자원/실패 지문을 기록한다.
기존 FarmAuthoringService·SCRAM authority/현재 scopes를 사용하며 **농장/품종·수치/G0–G4 승인은 아니다.**

## 무엇을 연결했는가

원 v2 입력6,719bytes와 기존 실제 source 선언을 같은 등록 decision에 결속했다.
판단은 `2026-10-21T18:49:47.384461Z`, 모델 구간은10월1일00UTC–2일00UTC다.
이 사례는 현재 자료를 사용하는 **합성 retrospective replay**다. 과거 당시 이미 알았던 자료나 미래 예측 검증으로 표시하지 않았다.
기존 원 program/source/evidence bytes·가용 시각을 바꾸지 않고 synthetic 경제/농장 fixture의 판단 문맥을 같은 시각으로 구성했다.

등록 job/hash·crop/batch/zone/면적·원 source binding과 현재 자료 사용/표시 권리를 대사했다.
한 tracked shoot와 원점/초기 상태/forcing·schedule·원9모델/19코드·SourceRecord/검토를 보존한다.
면적/식물 수·생산량으로 확대하지 않는다. 등록 품종 적용은 `unvalidated_for_registered_crop`이며
source 검토의 `numerical_initial_state_validation=False`와 관문 미평가를 유지한다.

## 통과한 검증

- 부재 RED 뒤 순수28검사: 닫힌 요청/원 입력·서명/같은 decision·원 UTC/단위, 1마이크로초 가용/점유 경계 거부.
- 최종 관련 회귀 **623검사/14.20초**와 별도 실제 SCRAM3그룹을 통과했다. 서로 다른 검사 합계626개다.
  전체 backend/web 회귀·새 API/UI는 이번에 실행하지 않았다.
- 실제 등록/prepare/read/write와 새 Python exec는 **41,256bytes의 동일 binding**을 반환했다.
  관측 prepare0.726403초/current0.721733초는 이 사례의 값이며 서비스/최대 용량 약속이 아니다.
  입력 검증·현재 권리를 각각 전후 확인했다. 새 exec는 seed/pytest/전체 HTTP app을 import하지 않았다.
- 현재9 read scope·read/write 분리·foreign tenant/다른 crop/revision/등록 hash와 자료 권리/검토 철회를 거부했다.
  늦은 권리·review·scope·선언 변조/기존 farm source 철회도 거부하고 복구 뒤 원 binding을 대사했다.
- 실제 임시 DB의 불변 trigger·digest 제약을 확인했다. 임시 관리자만 rehash 변조를 주입했고 현재 조회가 거부했다.
  예상 밖 DELETE grant도 거부하며 원 행/권한 복구 뒤 같은 bytes를 확인했다. 사용자 DB에는 주입하지 않았다.
- 정상/fresh의 생장/CLI26진입점0, jobs/events88/88 불변·새 crop-result/Run0이다.
  임시 schema/role·PG/temp/passfile0과 FD4→4를 확인했다.

## 자원·검토·남은 작업

두 native 실행은 같은3,140 source 지문과 원2,148항목·동결 source/assets·6root를 보존했다.
정상17.728037초/65표본·합1,015,373,824bytes, 거부34.110287초/125표본·합987,340,800bytes다.
PID 최대124,948,480bytes, .25초 표본/512MiB·합1GiB/600초/로그4MiB를 유지했다.
최종 회귀는14.692199초/58표본·합925,908,992bytes/소유 자식0이다.

첫 native 시도는 fixture의 canonical helper import 누락으로 설정 중 실패했다. 3.383502초에 정리했고
원 자료/6root를 보존했다. 수정 후 두 실제 배치가 통과했다. 원 실패를 삭제하거나 수용으로 세지 않았다.
새 exec는 생산 모듈만 읽도록 분리해 WSL의 seed/pytest 동시 메모리를 줄였다.

현재 검토/등록/권리는 다른 저장소의 관측이며 하나의 원자 snapshot 승인은 아니다.
다음은 실제 수치 producer가 만든 **완료 artifact의 서버 서명과 계산 없는 현재 조회**다.
이후 결과 등록/보호 API·제품 UI로 진행한다. 실제 Axiany 초기 기관/계수·잎 식/독립 자료0,
전체 작기/자원·경제·자율 선정은 별도 미완료이며 현재 사용자 미리보기는 변경하지 않았다.
앞의1–3집중시간은 이 실제 수용 기록으로 대체한다. 후속 날짜는 다음 계약/검증 비용과 자료 상태로 갱신한다.

검토는 native Codex CLI `gpt-6.1-sol / xhigh`, context18:31:18.690Z의
LF SHA `b3c3ff5325fb029473061d116799c0f1468b096986e70ad8118f6979b5607ff9`에서 수행했다. 재귀 CLI0이다.
