# 저장 생장·수확 결과의 범위 결속 — 로컬 수용

2026-10-09 00:50 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[검증 영수증](artifacts/web-crop-harvest-growth-binding-reference-20261009.json)에 원 도구86385 종료0·
777개 원 source 보존·최종5 core hash·검증 로그/자원/정리를 결속했다.

## 구현과 확인할 산출물

[계약](../contracts/web-crop-harvest-growth-binding-v1.md)의5 core파일을 구현했다.
[순수 결속 함수](../web/src/harvestGrowthBinding.ts)는 기존 닫힌 DTO 검사를 재사용하며
두 SDK의 기존 summary/page 대사 함수를 공개해 같은 검사를 공유한다.
농장 네 필드와 부모 result·payload/input/artifact/manifest hash·상태가 같을 때만
현재 수확 page와 현재 생장 sample page를 연결한다. manifest hash는 공개 계산의
`context_sha256`와 대사한다. 서버의 hash/HMAC·현재 권리 검사를 대체하지 않는다.

terminal 제거는 원 두 sample 위치/구간 끝을 유지하고 명시 사건은 원 사건 위치를 유지한다.
3D용 frame은 같은 UTC의 저장 sample만 참조한다. 현재 범위에 대응 시점이 없으면
`outside_loaded_samples`이며 근처 시점을 고르거나 상태를 보간하지 않는다.
같은 UTC의 terminal/사건에 같은 저장 frame을 연결해도 제거 직전/직후 상태라는 주장은 하지 않는다.
원 수량/정확 분수·단위/배정/미배정·관측 비교는 보존하고 전체 저장 summary와 부분 page 범위를 구분한다.
추가 HTTP·전체 배열 수집·작물/수확/경제 계산은 없다.

## 통과한 검증

| 대상 | 최종 결과 |
| --- | --- |
| 집중 | **34통과**. 서로 다른 농장/부모/원 hash/상태·잘못된 위치/시각·부분 범위·같은 UTC/미대응 사건·hold·원 입력 불변 |
| 웹 전체 | **851통과**, 기존817개 포함·Vitest 한 worker/파일 순차 |
| 타입/빌드 | 현재 source에서 모두 종료0. 기존 큰 chunk 경고는 유지 |
| source | 기존777개 bytes 불변·5 core snapshot 일치 |
| 원 도구/정리 | session86385 종료0·생존 소유 자식0·새 DB/서버/브라우저0 |

처음 두 hold 시험은 마지막 확정 sample의 필수 phase를 시험 fixture에서 빠뜨려 실패했다.
해당 필드를 보완한 뒤33개가 통과했다. 별도 검토에서 소수 초의 마지막 확정 시각을 문자열로
비교하면 앞선 정수 초 제거를 잘못 거부했다. 새 시험의 실제 RED/종료1 뒤 기존 UTC microsecond
변환을 재사용해34개가 통과했다. 범위/사건 kind 거부 시험도 각각 독립적으로 유효한 DTO에서
결속 함수가 거부하는지 확인한 최종 판본으로 전체 검증했다.

시험은 서로 다른 소유 합성 fixture의 metadata/시각을 맞춘 **형식 검증**이다.
원 농업 수량은 새로 계산하지 않았으며 같은 실제 DB의 공동 실행·새 HTTPS/WebGL 증거가 아니다.
이번 stage의 새 UI/브라우저/실제 HTTP/DB/RHS/제품 CLI·hosted CI/push는0회다.

nice19·Node heap256MiB·600초 원 마감에서 검증18.871초,
0.1초184표본의 단일 프로세스 RSS 최대446,570,496bytes≤512MiB,
controller 포함 동시 RSS 합562,962,432bytes≤1GiB였다.
표본 RSS 합이며 WSL 전체/production 브라우저 용량 수용이 아니다.

## 다음 단계와 외부 의존성

`crop-harvest-growth-binding` 자식만 체크한다. 수확 표/3D·replay 부모는 미완료다.
다음은 현재 API/계정/부모 선택에 결속한 작은 수확 표와 기존 생장 수치3D 화면이다.
수용 기준은 원 목적/미배정/관측 비교/단위·UTC 표시, 부분 범위, 선택/취소/권리 실패 시
기존 값 제거, 같은 UTC만 연결, HTML 대안과 집중 Chromium 검증이다.
그 뒤 같은 실제 DB/API/대표 WebGL·전체166일 질량 부하를 따로 확인한다.
이후 기후/물·양분/구매 에너지→사용자 실행/Decimal 손익 순서로 진행한다.

실제 품종 입력/환산 계수·독립 국내 농장 자료·실측 농장 작물 Run은0건이다.
G0–G4는 `not_assessed`이고 생산/미래 마진/추천은 보류한다.
원격 `2a3e615`의 CI5개는 이번 읽기에서도4성공/Backend 실패였으며 새 검증을 수행하지 않았다.
구형25시간 원 명령 종료 기록 누락 hold도 유지한다.
수확 화면은 다음 단계이며 최종 production 완료일은 실측 자료 접근/권리·독립 검증 일정이
확정되기 전에는 정할 수 없다. 전체 goal은 활성 상태다.
