# 기관 큰 결과 용량 사전 검사의 WSL 자원 보류 — 2026-10-21 KST

[계약](../contracts/crop-organ-catalog-capacity-v1.md) ·
[기계 증거](artifacts/organ-catalog-capacity-preflight-20261021.json).

## 실제 결과

기존 정상 producer의 큰 결과1개 사전 검사를 실행했으나 **WSL 합산 RSS 한도로 미수용**이다.
전체20개 검사는 실행하지 않았다. 정상 producer 완료 영수증/크기 progress와 HTTPS 관측은 없으며,
정확히 어느 내부 문장에서 중단됐는지는 관측하지 않았다. 생성된 결과 개수나 packet 크기를 추측하지 않는다.

guard의 실제 child는−15, 이유 `RSS_limit`, wall17.235083초였다.
최대 단일323,657,728bytes·합1,095,081,984bytes,63표본/.25초였다.
원512MiB/PID·합1,073,741,824bytes·600초를 유지했다.
합산 peak의 최대 단일 프로세스는 소유 PostgreSQL이며 같은 표본의 시험 Python은167,174,144bytes였다.
이 관측만으로 SQL/producer의 구체적인 메모리 원인을 단정하지 않는다.

source2,729개·원본2,148개·두 frozen source/자산·보호5root 보존,
원 frontend200·controller FD4→4와 소유 non-zombie/PG 잔여0을 확인했다.
guard terminal 작성 시 임시 PG 디렉터리1개와 passfile4개를 기록했으며 원 terminal은 유지했다.
controller 종료 뒤 별도 재확인에서는 소유 controller/PG·해당 임시 디렉터리·passfile/TLS private key 잔여0,
보호5root 생존을 확인했다. 삭제 과정을 관측하지 않아 수동 정리 성공으로 바꾸어 쓰지 않는다.

## 일정과 다음 실행

이번 준비·실행·결과 보고의1–3집중시간 추정은 소프트웨어 자식의 판단까지이며
검사 통과나 전체 제품 완료 약속이 아니다. 이 실행으로 WSL 보류를 확인했고 전체 완료일은 여전히 미정이다.
같은 WSL 구성/입력을 재실행하지 않는다. 건강한 사용자 서비스를 중단하거나 원 상한을 늘리지 않는다.
다음은 기존 hosted 소유 실행기에서 같은 정상1결과 사전 검사를 준비해 실제 크기/생성 시간과
원30초 HTTPS를 확인하는 것이다. 그 결과가 원 한도를 만족해야 실제20개를 실행한다.
호스팅 용량이 통과해도 기존5root를 포함한 WSL 동시 용량/사용자 적용은 별도다.

`organ-catalog-20-large-HTTPS-capacity`·기관 family/U1은 미체크다.
검증된 hosted API/DB/저장 WebGL 자식은 유지하되 이번 결과로 확장하지 않는다.
새 목록 UI/Solar 미배포, 생산/자원/경제·U2–U5·실제 CLI 종단 간·독립 자료/관문은 미완료다.
전체 backend/web CI와 브라우저는 이번에 실행하지 않았다. goal은 active다.

일정/보류를 두 로컬 개발 진행 기록에 게시했다. 최초 설명은 기존240자 검증에서 거부돼 미게시였고,
같은 검증 한도 안에서 줄인 기록은 실제5173/5174의200·동일 bytes/no-store를 통과했다.
게시 guard는 종료0/.339822초·합570,445,824bytes·보호5root/원본/FD4→4·소유 잔여0이었다.
원 두 HTML과 환기2,173파일을 보존했다. UI 코드/사용자 기능 배포나 새 DOM 검증은 수행하지 않았다.
사전 검사 파일 구문·증거 source hash/보류 상태·새 문서 링크와 diff 검사를 통과했다.
