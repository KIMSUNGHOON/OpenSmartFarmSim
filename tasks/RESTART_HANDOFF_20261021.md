# 시스템 재시작을 위한 작업 중단 — 2026-10-21 KST

사용자 요청으로 새 계산·CI 실행을 중단하고 goal 일시정지를 요청했다.
[중단 시점 증거](../research/artifacts/restart-checkpoint-20261021.json)를 따른다.

## 저장된 진행

- `65dff26`: CO₂ 확정 구간 공개 응답 고유110 수용. 실제 CI39544290911/core7,
  CI39545348424/fences10, CI39546601275/regression93은 모두 success다.
  [원 증거](../research/api-crop-greenhouse-co2-prefix-20261021.md)를 보존했다.
- `9b69418`: 보호 접수·진행·취소3경로의 제어/회귀375 수용. 기존65경로/477스키마를
  보존해 기본 문서는68/483이다. [원 증거](../research/api-crop-greenhouse-co2-execution-http-20261021.md)를 따른다.
- 이후 WIP: 명시 prefix3경로와 create_app의 같은 실행 graph 결속을 구현했다.
  missing-module RED→첫 GREEN152통과/fixture 조립4실패→수정 GREEN156통과를 보존했다.
  첫 실패는 forwarding 단위 시험이 다른 기존 결과 installer까지 불완전하게 구성한 것으로,
  단위 fixture의 기존 installer 대역만 보완했다. 실제 전체 graph 검증은 native 단계에 남는다.
  관련425검사/20.916533687초·단일204,627,968/합868,106,240bytes·FD4→4/정리0을 확인했다.
- 실제 SCRAM/검증 TLS 시험14개를 수집만 했다. 원 Solar12 의미와 CO₂ basis/늦은 program2를
  준비했다. 실제 실행/수용은 하지 않았으며 prefix/HTTP 부모와 사용자 적용은 미완료다.

## 미완성 부분과 다음 작업

1. `research/co2_result_projection_hosted.py`의 실행 HTTP core6/fences8 확장은 **WIP**다.
   workflow 선택/조건과 curated artifact allowlist는 아직 추가하지 않았다.
   actor/append의 의도된 시험 SQL을 조회 DB 불변과 구분하도록 postcheck를 검토해야 한다.
   현재 모든 receipt에 query_DB_unchanged를 요구하는 새 조건은 actor/append와 맞지 않는다.
   기존 co2-http 예상215→218 변경은 아직 최종 수집으로 확인하지 않은 초안이다.
2. native14 수집 후 receipt 필드가 추가됐다. workflow/controller를 마무리한 최종 source를
   다시 수집하고 지문·6/8 배치를 고정한다. 원600초/512MiB PID/합1GiB와 원 사례를 유지한다.
3. 실제 SCRAM/TLS core→terminal 확인 후 fences를 순차 실행하고 원 응답/UTC·권리/프로그램/페이지·
   identity/취소·의도된 actor SQL/조회31계측0·소유 정리를 대사한다. 통과 전 부모 체크를 해제하지 않는다.
4. 이후 명시 runtime/독립 worker→typed web/같은 UTC3D→사용자 적용 순서다.

## 재시작 후 확인

- 현재 소유 계산/guard 프로세스는 없고 위3 CI는 terminal success다. 추가 CI는 제출하지 않았다.
- 기존 미리보기5173/5174와 보호5root는 중단 준비 때 유지했다. OS/WSL 재시작 시 프로세스는
  종료되므로 새 PID/시작시각·포트/DB를 확인하고 기존 구성으로 복구한다. 이전 PID를 종료 대상으로 쓰지 않는다.
- 불변 원자료2148항목·동결 source2173파일·DB/키/권리·private 상태를 보존했다.
  재시작 뒤 자료를 새 fixture로 대체하거나 키/서명을 새로 만들지 않는다.
- private 실행 정보/guard 로그/다운로드는 기존 ~/.local/state/OpenSmartFarmSim 아래에 남는다.
  접속 정보는 [기존 안내](../web/README.md#joint-execution-user-preview)와 private handoff를 확인한다.
- 기존 인증 만료는2026-10-22 06:37 KST다. 재개 시 현재 시간을 확인해 만료된 토큰을 사용하지 않는다.
- 사용자가 재개를 요청하면 정확한 Codex CLI gpt-6.1-sol/xhigh 세션에서 이어 간다. CLI를 재귀 실행하지 않는다.

전체 작기/물·양분/구매 에너지·Decimal 경제·최종 UI/실제 CLI 종단 간·독립 농장0건/관문과
전체 goal 완료일 미정은 유지한다. 이번 기록은 중단 checkpoint이며 새 배포·전체 수용 기록이 아니다.
