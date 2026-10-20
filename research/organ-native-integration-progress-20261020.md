# 기관 목록의 실제 통합 시험 진행 — 2026-10-20

[시험 계약](../contracts/crop-organ-native-acceptance-v1.md) ·
[기계 증거](artifacts/organ-native-integration-progress-20261020.json).
판단은 현재 native Codex CLI `gpt-6.1-sol` / `xhigh`에서 수행했으며 재귀 CLI/하위 agent 호출은0이다.

## 추가한 시험

기존 직접 기관 조회의 정상 synthetic producer/ApiRuntime을 재사용해 실제 SCRAM PostgreSQL,
Bearer/검증된 upstream HTTPS와 같은 CI의 minified 빌드를 연결했다.
서버 status/body를 그대로 전달하는 정적 frontend와 실제 Chromium으로 농장→작물→기관 목록을 선택한다.
응답 mock이나 원 결과의 재작성은 사용하지 않는다. 정상/숫자 보류 두 시험 row를 정상 producer로 만든 뒤
조회 중 put/integrate/RHS·SQL 쓰기를 금지하고 원 row/선택 DB counts와 브라우저 값을 대사한다.
새 synthetic 시험 row이며 역사적 원 row 채택·실제 농장·G0–G4 또는 사용자 적용이 아니다.

## 첫 실행: 웹 통과, native 미수용

source `c410ba48f1b1904e8189cca145309b157b862687`의
[CI39437814720](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39437814720)는
전체 웹36파일/단위1,886개·Chromium256개·타입/프로덕션 빌드/audit를 통과했다.
native 작업은 실제 종료1이었다. 원153.702566초·단일358,187,008/합697,909,248bytes·
607표본/.25초, FD6→6·소유 프로세스/임시/자격증명 잔여0과 source 보존을 확인했다.
자원/600초 감독에 의한 종료는 아니었다.

실패는 Python의 `browser.communicate(timeout=120)`였다. 이 줄 이전의 두 중간 protocol 메시지는
통과했으나 최종 브라우저 보고서를 받지 못했다. 첫 source에 단계 영수증이 없어 정확히 어느
브라우저 동작/응답 대사/종료에서 기다렸는지는 관측되지 않았다. 파이프 EOF나 제품 결함으로 단정하지 않는다.
최종 원 row/응답/정리 대사를 포함한 실제 통합 수용은 하지 않았다.

원 native artifact ZIP의 GitHub digest를 대사했다. WSL 다운로드 guard는 종료0/3.767559초·
합621,289,472bytes, 원5root·2,148자료·두 frozen source/자산·FD4→4와 소유 정리를 보존했다.
새 시험의 로컬 pytest 수집1개/구문 검사도 통과했으나 이것은 실제 통합 성공이 아니다.

## 보완한 다음 실행

source `88d766ed70383501f3acf7e98c4a75373a4578c0`의
[CI39441263299](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39441263299)를 한 번 접수했다.
현재 결과는 미확인이다. 동일 실행을 추적하며 관측 지연만으로 다시 실행하지 않는다.

브라우저 동작/탐색을30초로 한정하고 단계 영수증과 응답 대사의 종료 조건을 기록한다.
최종 검증 메시지까지 stdin을 유지한 뒤 종료를 기다리도록 protocol을 분리했다.
마지막 구간은105초 메시지/15초 종료로 기존120초 안을 유지한다.
제품 UI/계산 코드는 수정하지 않았고 요청30초·512MiB/PID·합1GiB/600초·.25초 기준을 유지한다.
다음 실행도 전체 웹과 같은 minified 빌드를 사용한다. 통과 전 체크를 해제하지 않는다.

## 남은 범위

기관 v1과 계산 작기의 CODE 결속은 [별도 정적 근거](organ-reader-code-boundary-20261020.md)로 구분했다.
hosted 정상 producer의 실제 통합과 역사적 원 row의 지원 reader/현재 권리 호환성,
WSL5root 동시 용량/사용자 적용·20건/큰 packet·구획v2/startupv3·원3상태 디자인/U1은 각각 남는다.
생산/자원/경제·지역 입력부터 최종 결과의 U2–U5·실제 CLI 종단 간 G1과 독립 농장/시장 관문도 남는다.
전체 goal은 active이며 완료일은 아직 확정하지 않았다.

진행 JSON에 첫 native 실패/보완 CI 진행과 미수용 범위를 게시했다. 실제5173/5174의200·동일 bytes/
no-store, 원 두 HTML과 환기 source2,173파일·5root/원본/정리를 확인했다. 게시 guard는
종료0/0.342912초·합586,317,824bytes였다. UI 코드 활성화나 새 DOM 검증은 하지 않았다.
