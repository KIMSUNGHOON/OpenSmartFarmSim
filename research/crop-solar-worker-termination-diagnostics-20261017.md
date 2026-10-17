# 독립 일사 작업자의 종료 사유 관찰 — 2026-10-17

[기계 증거](artifacts/crop-solar-worker-termination-diagnostics-20261017.json) ·
[진단 계약](../contracts/crop-solar-worker-progress-diagnostics-v1.md) ·
[선행 현재 참조 reader](farm-pinned-context-reader-implementation-20261017.md).

## 원 정상의 실제 실패

[trace-OFF CI39034668788](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39034668788),
source8423263은 **121.021초·자식1**로 실패했다. worker exit1·최종 성공 단언 실패와 API-15만 확인했다.
잡힌 예외·실제 반환 outcome·완료 단계·정상/DB 정리 proof는 없다. 원360초/RSS 상한 종료는 아니다.
단일133,279,744/합369,881,088bytes·FD7→7·소유 비좀비/임시0이다.
artifact12101344383/2,086bytes·run/head/ZIP digest/안전 경로를 대사했다.
이를 정상 기능·전체 성능 개선·WSL 용량·S3/사용자 배포로 표시하지 않는다.

## 변경과 통과 검증

source65a609b는 명시 진단의 `detail=worker`를 추가한다. 기본은 기존 `phases`다.
작업자 메서드만 관찰해 잡힌 예외 종류/코드 위치, 실제 `_confirm`의 확정 단계와
`run_once` 반환의 허용 상태/attempt/고정 reason code를 기록한다.
농장·시장·모델 phase journal을 생략한다. locals/메시지/원 입력/환경을 내보내지 않는다.
기존64KiB/최근32·동시16·예외16·atomic 기록과 진단의 정상 수용 금지를 유지한다.
관찰 비용을 포함하며 trace-OFF 처리량을 추정하지 않는다.

- 97179:1은 시험 source 문자열 오류라 행동 RED가 아니다. 보완한59782:1은 detail 기능이 없어 신규1실패/기존6통과다.
- 17910:0은 실제 queued/busy 반환·원 checkpoint·비밀값 제외와 기존 bounded/실제 SIGTERM·반환 형태의 **7검사**를 통과했다.
- 36579:1은 backend venv의 yaml 미설치다. 의존성을 설치하지 않고 기존 system Python을 쓴98252:0에서
  YAML·기존 web/native 및 원 정상 steps/env 보존·원 prototype/현재 application 불변을 확인했다.
- 새5root·원2,148항목·frozen 소스/자산·두 화면·512MiB/PID/합1GiB,
  감독FD4→4·소유 비좀비/PG/임시/passfile0을 유지했다. 실패 단계도 증거에 보존했다.

## 다음 한 단계

[CI39035225593](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39035225593),
source65a609b/detail worker가 진행 중이다. application은 실패한8423263과 같고 원 actor 본문/입력/64걸음·
chunk1·조회 주기·현재 검사·시간/RSS 상한을 바꾸지 않았다.
실제 잡힌 예외/outcome과 확정 단계·종료/정리를 대사한 뒤에만 다음 수정을 정한다.
진단은 정상 수용이 아니며, 수정 후 별도 trace-OFF 원 정상 기준이 필요하다.

[독립 보류·취소 후속](../contracts/crop-solar-unpaused-hold-cancel-v1.md)을 정상→보류→취소→실제 계산 중 WebGL의
개별 수용으로 보완했다. 기존 저장 결과 조회를 독립 실행 증거로 대체하지 않는다.
S3/S4·WSL 용량·새 Solar 배포·실제 품종/독립 농장 자료·권리/G0–G4와 전체 완료일은 미완료/미정이며 goal active다.

최신 실패/진단 진행 기록은15407:0에서 두 주소HTTP200·no-store·원 HTML/source·5root/원본·FD/소유 정리를 확인해 게시했다. 브라우저/디자인 재검사는 하지 않았다.
