# 등록 계산 완료의 별도 DB 게시 연결 — v1 개발 계약

2026-10-08 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh` 판단이며 재귀 CLI는0회다.
[등록 감독자](crop-cycle-calculation-registered-supervisor-control-v1.md) 다음,
[전체166일 실행](crop-cycle-calculation-full-registered-run-v1.md)의 게시 연결 자식이다.

새 사설 게시 선언은 계산 전에 발급한다. 원 supervisor spec SHA·고정 입력의 계획 걸음/출력/사건 수·
원 config/DB 참조·현재 source SHA와 별도 무작위 DB 게시 key의 SHA를 고정한다.
DB key는0400 파일에만 보관하고 서버 key와 같으면 서비스 구성 전에 거부한다.
닫힌 schema/판본·실제 현재 파일/mode·원 마감과 이전 명령/종료/결과를 검사한다.
계산·입력·권리 정책·서버v3·제품 API/lease를 변경하지 않는다.

새 Python 게시 프로세스는 마지막 실제 감독 영수증이 종료0/recorded이고 해당 현재 계산이
completed·고정 전체 계획과 같은 경우에만 기존 결정적 DB store를 호출한다.
yielded/hold·결과 부재·마감 경과·설정/키/source 변조는 게시하지 않는다.
게시/재조회/재시도에서 RHS를 금지하고 현재 입력/농장/계정 권리·원 bytes/HMAC를 기존 store가 검사한다.
최종 현재 설정/마감과 게시 row를 다시 확인한 뒤 새 사설 결과 파일을 fsync한다.
중간 실패 뒤 이미 저장된 비공개 row가 있더라도 승인/성공으로 표시하지 않으며 같은 입력 재시도만 허용한다.

수용: 형식/원 SHA/key/mode/마감 반례의 정상 대조·작은 실제 SCRAM의 계산 전 거부→
새 Python 완료 게시/재조회→새 Python 재시도와 동일 result ID/원 payload/DB row1,
원 출력/UTC·현재 입력/계정 철회·RHS0·원 argv/로그/실제 종료·source/FD/DB/비밀/PG 정리.
작은 시험은 원 명령600초 이내이며 전체166일 실행의 대체가 아니다.

실제 전체 실행은 같은 DB/farm/artifact를 전체 원량 대사와 후속 API/동일 UTC3D까지 사용하는
통합 실행 구성을 준비한 뒤 시작한다. 계산과 게시 사이에 임시 fixture DB를 지우거나 재계산으로 대체하지 않는다.
전체 실행/DB/API/3D·생과/자원/경제·실제 제품 CLI/독립 G1은 후속이다.
실제 품종/국내 독립 자료/측정 농장 작물 Run0건·G0–G4 `not_assessed`·예측/추천 hold를 유지한다.
