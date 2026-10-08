# 전체 등록 작기의 같은 DB 실행 구성 — 준비 v1

2026-10-08 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI 0회.
[원 전체 실행 계약](crop-cycle-calculation-full-registered-run-v1.md)과
[작은 자원 수용](../research/crop-cycle-calculation-registered-replay-resource-implementation-20261008.md)의 후속이다.

## 이번 구현

소유 실행의 준비 시작 전에 원 시작·단조 시계·boot ID·절대 마감·source/도구 hash와
512MiB primary/1GiB pipeline·두 저장 공간 2GiB 여유를 기록한다. 작은 시험은600초,
전체는32,400초다. 등록/키·runtime 설정/원 참조를 계산 전에 불변 실행 기록으로 결속한다.
기존 계산 감독의 내부 마감은 원 준비 마감보다 이른 남은 정수 초로 제한한다.
외부 감독은 원 준비 마감으로 등록·계산·비교·게시·API/3D·정리를 모두 감시한다.
단계 진입/종료에서도 같은 준비 기록을 검사하며 재개로 전체 예산을 초기화하지 않는다.

같은 소유 PG/DB/farm을 유지해 다음을 순서대로 수행한다.

1. 실제 fresh Python 계산 감독의 원 종료·완료 계획/현재 권리·checkpoint를 확인한다.
2. 별도 Python 비교 자식이 원 전체 참조와 새 저장 결과를 samples64/events8 이하로 읽는다.
   행·UTC(+273일 명시 이동)·전체 checkpoint의 상태/clock/counter/누적 수지를 대사한다.
   계보6필드만 제외한다. 페이지의 total/start/next/실제 행 수·현재 증명/원 hash도 검사한다.
   전체 행은 누적하지 않고 hash와 첫64시점/최대8사건만 남긴다. 실제 브라우저에는 첫14시점만 전달한다.
   비교 자식은 브라우저 전에 종료한다.
3. 대사 성공 뒤에만 기존 별도 Python 게시를 수행하고 같은 DB의 보호 API/실제 App/대표 WebGL을 읽는다.
4. 실제 원 종료·로그/hash·원 입력/source 보존·FD/DB/schema/role/비밀/PG/브라우저/임시 경로 정리를 감사한다.

비교/게시 자식은 실제 argv/PID/start/boot/원 종료/로그를 보존하고 마감에 SIGINT→10초→SIGTERM→10초→SIGKILL을 사용한다.
계산되지 않은 용량 cursor, 전체 행의 list 누적, 조회 중 RHS, 관측 유실의 재계산 대체는 허용하지 않는다.
선행 빌드/Nginx/브라우저 지정 설정을 재사용하며 모델 수식·8초 RK4/300초 출력·제품 한도를 유지한다.

## 이번 수용과 다음 실행

먼저 작은 관리 사건 프로그램으로 같은 실행 구성의 전체 경로와 원량·거부·마감·자원/정리를 검증한다.
별도 경계 시험은64행 뒤 변조·빠진/중복/잘못된 페이지·clock 이동·checkpoint 불일치·마감/source 변조 거부를 확인한다.
이 수용은 **전체166일 실행 완료가 아니다**. 전체 실행은 별도 착수/원 영수증으로 판단한다.
전체 입력/원 참조는 기존 고정 root·47,809시점/5사건·1,816,704걸음과121상태를 사용한다.
대표3D 수용은 전체47,809프레임 검사나 실제 토마토 형상의 수용이 아니다.

생과/자원/경제 연결과 실제 CLI/독립 G1은 후속이다. 실제 품종 입력·국내 독립 자료·실측 농장 작물 Run0,
G0–G4 `not_assessed`, 예측·추천 hold와 hosted Backend/push hold를 유지한다.
