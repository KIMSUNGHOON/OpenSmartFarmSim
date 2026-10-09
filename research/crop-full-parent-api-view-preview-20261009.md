# 완료 전체 생장 결과의 실제 API·3D와 사용자 기동 — 2026-10-09

**17:46 KST:** `http://localhost:5173/`을 완료된 합성166일 생장 부모의 현재 조회로 전환했다.
현재 HTTPS API는 `https://127.0.0.1:8443`이다. 기존 작은3시점 미리보기는 원83196 실제 종료0으로
정상 정리했고, 검증한 별도 source/복원 DB를 읽기 전용으로 기동했다. 전체 RHS를 재실행하지 않았다.
사용법은 [웹 안내](../web/README.md#기존-제품-앱의-로컬-동시-기동--2026-10-09)에 있다.

[작은 계약](../contracts/crop-full-parent-api-view-preview-v1.md)의5개 core파일만 바꿨다.
원 저장 시점 번호로 작은 범위를 읽고 마지막 원 시점으로 이동한다. 기존 현재 query/취소/권리 검사와
원 UTC·C/N·LAI를 사용하며 저장 시점 사이를 보간하지 않는다. 선택한 수확이 없는 상태를 명시한다.
source `8c1227f`와 동일한 코드가 main `532c494`에 있고, 선행 조회 사실 묶음은 `f79ef64`로 통합했다.
실행 중 미리보기는 별도 고정 source를 사용하므로 main 후속 작업이 그 판본을 덮어쓰지 않는다.

## 검증과 실제 범위

[원 도구·hash·응답·자원 기록](artifacts/crop-full-parent-api-view-preview-reference-20261009.json)을 보존했다.
실제 native Codex CLI `gpt-6.1-sol`/`xhigh`의 turn 문맥과 판단 출력을 기록했고 재귀 CLI0이다.

- window 집중40개(새2/기존38)와 타입 검사는 통과했다. 원26255의 후속 압축 빌드는 RSS 한도로 중단돼
  그 전체 wrapper는 종료1이다. 이 로그를 전체 명령 종료0으로 표시하지 않는다.
- 미리보기 제품 빌드는 원1078 실제 도구0, Vite production mode/`--minify=false`다.
  같은 소스의 일반 압축 빌드는 단일512MiB를 넘겨 중단했다. 일반 압축 빌드/운영 용량 수용은 별도 보류다.
- 원7678 실제 도구0/119.766초와 별도 root 감사: 원 backup·서명 결과/최초 저장 시각을 복원한
  같은 실제 SCRAM DB에서 API·제품 App·실제 WebGL을 대사했다.
- 고유 원 index **0/6/23904/23910/47808**의50 C/N·LAI·기관값/UTC·표·그래프·mesh와
  관리 사건5개의 제거/직전/직후 C/N·원 UTC를 확인했다. 모든47,809frame의 브라우저 시험은 아니다.
  전체 행/121상태 대사는 [선행 부모 수용](crop-harvest-full-parent-restored-20261009.md)에 남아 있다.
- HTTPS14응답/브라우저11응답 중 완료200응답9개의 양쪽 길이/SHA가 같다.
  최대6.625초/65,064bytes·현재 권리 철회422/복원·scope 거부403·다른 tenant의 비공개404를 확인했다.
  응답/metadata/UTC 대체0·동시 읽기 최대1·조회 RHS/행 생성/게시/증명 발급0이다.
- DB 행 수, 원 입력/artifact/backup2,146항목과 FD identity를 보존했다.
  임시 검증 PG/소유 data·HTTPS thread·nginx·브라우저/child를 정리했고 잔여 소유 process0이다.
- 지정 Chromium **single-process/in-process-GPU·renderer32MiB/Node64MiB·CDP GC250ms**에서
  관측 단일418,369,536bytes/합1,000,091,648bytes로512MiB/1GiB 안이었다.
  합계는 기존 미리보기와 두 실제 PG tree를 포함한다. WSL 전체나 일반 브라우저/운영 용량의 보증은 아니다.

앞선 grant 기간/다른 tenant 상태 예상·시험 script 중복 선언·진단 table selector 오류와
다중 process 브라우저의 두 RSS 실패를 원 종료1로 남겼다. 실제 API의404 거부를403으로 바꾸거나
수치·권리 검사를 생략하지 않았다. 자원 상한은 늘리지 않았다. 비공개 로그의 credential 일치0도 확인했다.

## 사용자가 확인하는 화면

[중간 원 시점의 실제 화면](artifacts/full-parent-growth-middle.png),
[마지막 시점 desktop](artifacts/full-parent-growth-desktop.png),
[마지막 시점 mobile](artifacts/full-parent-growth-mobile.png)을 보존했다.
이는 LAI·50과실 구획의 **수치 모식도**다. 실제 작물 외형·키·숙기·생과 수확을 복원한 장면이 아니다.

기동 전환 뒤 원59276 실제 도구0으로 frontend200/원 빌드 index 일치·보호 summary200을 확인했다.
summary9,628bytes/SHA가 검증 때와 같고47,809시점/5사건/1,816,704완료 걸음이다.
user preview의 원37119는 의도적으로 실행 중이며 WSL 종료/계정 만료 뒤에는 재기동해야 한다.

**실시간 U3는 미완료다.** 이 부모 계산은 완료됐고 재생은 저장된 계산 시간을 이동한다.
계산 중 진행률·새 checkpoint를 자동 갱신하지 않는다. 전체 수확은 미등록이며 다른 부모의 작은 수확을 연결하지 않는다.
목록 선택 코드는 빌드에 포함되지만 U1의 원 디자인/실제 선택 경로 수용은 남아 기본 수동 조회를 안내한다.

## 다음 작업과 외부 의존성

다음은 현재 권리/원 파일 검증을 유지한 전체 수확 읽기 비용 경계 확정 → 정상 전체 수확 writer/registry·
독립 Decimal 대사/인증 보존 → 수확 API·3D → 기후/물·양분/구매 에너지 → 사용자 실행/Decimal 경제다.
단순히 작은900초 예산을 늘려 전체 writer를 시작하지 않는다. 완료된 전체 RHS도 다시 계산하지 않는다.

이번 전체 생장 화면 연결은 완료됐으며 U1/U3/전체 제품 완료일은 아니다.
실제 품종·국내 독립 농장 자료0건, G0–G4 `not_assessed`·생산/미래 마진/추천 hold는 유지한다.
원 Backend37892105708은 분할0/1/2/4 성공·3/5 실패·집계 failure로 모두 종료했다.
pidfd 호환과 수확 endpoint 결속 실패의 작은 수정을 별도 작업으로 유지한다.
