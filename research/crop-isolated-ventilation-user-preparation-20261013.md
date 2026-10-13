# 새 환기 모델의 지속 사용자 설정 준비

2026-10-13. [선행 3D 배치](crop-isolated-ventilation-browser-batch-20261013.md) 뒤
[별도 영역·설정 준비 증거](artifacts/crop-isolated-ventilation-user-preparation-20261013.json)를 수용했다.
원26495 실제0·14.397초, 단일 PID105,955,328bytes·합569,368,576bytes·원 root4/FD4→4/원본·두 서비스 보존이다.

## 수용 범위

27표 중26표의 원 행을 대사하고 시장 입력85건은 새 authority로 재접수했다.
실제 SCRAM 로그인4·상호 접근 거부20·DDL/owner 거부8·입력 결속3과 설정 오조립8건 거부를 확인했다.
새 로그인4개의 grant option 없는 CONNECT만 추가됐으며 기존 DB 권한 항목·schema/role/row는 보존했다.
공동 결과 읽기는 새 계정에서 거부한다. 입력 원파일·증거·키·권리는 변경하지 않았다.

명시 옵션 `--prepare-retained-runtime`으로 새 영역/역할과 사설 자격 파일을 유지한다.
API/작업자는 아직 기동하지 않았고 사용자 HTTP 연결도 미적용이다.
기존 transient 실행은 기본값으로 자동 정리한다. 준비 실패 시 사본 자격 파일도 정리한다.
첫 사설 wrapper의 import 경로 실패와 지속 CONNECT 비교 실패를 보존하고 후속 고정 판본에서 통과했다.
실패한 영역/역할과 남은 소유 사본 자격 파일은 정리했다.

## 다음 단계

유지한 설정으로 별도 API/자동 작업자 기동→기존5174의 모델별 HTTPS 연결→
실제 사용자 정상/보류/취소·계산 중/저장3D·재접속/권리·같은 결과 재시작 조회를 확인한다.
기존5173/5174·원 결과와 WSL512MiB/PID·합1GiB를 보존하고 사설 접속 안내를 게시한다.

판단은 실제 CLI gpt-6.1-sol/xhigh 문맥에 기록했고 재귀 CLI 실행0이다.
자동 goal은 usageLimited이며 위임된 수동 진행이다. 전체 CI/push 미실행, 합성 소프트웨어 범위다.
실제 농장 Run0·G0–G4 not_assessed·전체 완료일 미정을 유지한다.
