# 자동 잎 출현 결과의 공개 export — 2026-10-24 KST

[계약](../contracts/crop-leaf-appearance-export-v1.md)의 export를 소프트웨어 연구 범위에서 수용했다.
[검사·실제 두 fresh/자원 증거](artifacts/crop-leaf-appearance-export-20261024.json).
[공개20파일](../web/public/leaf-appearance-replay/index.json)은 저장소 자료이며 새 SDK/사용자3D에는 아직 연결하지 않았다.

## 산출물과 검증

- [exporter](export-leaf-appearance-replay.py)는 source/원 stem의 재배포 권리가 모두 True일 때 별도 새 폴더에만 쓴다.
  원 canonical 근거7파일과 새12 DTO를 보존하고, 원 manifest/권리·실제 출력19파일의 길이/hash를 다시 검사한다.
  index는 임시 파일 fsync→rename으로 마지막에 게시한다. 새 수식·계수·자료 채택/관문을 추가하지 않았다.
- 신규13/조회·이전 export90/입력 준비·producer80=고유183검사 통과.
  기존 출력 덮어쓰기·source 내부 출력, 양쪽 실제 권리 거부와 늦은 철회·입력/출력 변조·쓰기/rename 실패를 확인했다.
  실패 때 완료 index0이고 원43파일/이전17공개파일은 보존된다. 부분 출력은 완료 묶음이 아니다.
- 실제 원 root `77c3ffcab5f02b0dab132530a3f4c278db07dd18a258633bb4b148c18f5e423a`에서
  두 별도 프로세스가 같은20파일 bytes/index SHA를 만들었다.
  index SHA는 `86b2146daa37ecc68b0be086a80bc3212a03f6cc6a18a17e4d44049d8ba1a928`이다.
  전체126,865bytes이며 원7파일 bytes와12 DTO/47면적·원 ID/UTC가 이전 실제 reader 검증과 같다.
  이미 독립 Decimal100으로 대사한47개 원 값의 보존이며 새 농업 수치 검증을 추가했다는 뜻은 아니다.
- fresh는 허용7개 crop read/IO 외 수치 모듈 import를 차단했다. DB/외부 명령·소유 출력 외 쓰기0·FD 보존이다.
  원43/기존17파일 metadata도 보존했다. 검증 뒤 별도 web/public/leaf-appearance-replay에 같은20파일을 복사하고
  모든 SHA/길이와12 DTO 원 bytes를 다시 대사했다. 현재 UI/runtime·DB/키는 변경하지 않았다.

## 실패와 한도

스크립트 부재 RED1을 확인한 뒤 최초 GREEN13이 통과했다. 별도 제품 오류/재시도는 없었다.
최종 신규/조회 회귀/producer 회귀/실제 fresh 단계는 각각12.405/22.375/44.841/2.454초였다.
최대 WSL 합산 RSS는478,117,888bytes이며 PID512MiB/합산1GiB·600초·0.25초 표본/4MiB 로그 안이다.
원2,481항목/현재 소스·보호3root를 보존했고 모든 소유 잔여0·FD4→4였다.
전체 backend/new hosted CI/새 SDK·실제 browser/사용자 적용은 실행하지 않았다.

판단은 실제 현재 CLI `gpt-6.1-sol`/`xhigh`의2026-10-23 15:30:30.936Z turn_context를 확인한 상태에서 수행했다.
원 LF 포함 SHA는 위 증거에 보존하며 recursive CLI 호출은0이다.

## 다음 한 단계와 외부 의존성

다음은 **새20파일/root/index SHA의 strict SDK**다. 기존 read/단위·정확 시각 IO와 원 stem decoder를 재사용한다.
source/준비/생성·내부 root/원 stem·양쪽 권리와 새 DTO를 닫힌 형식/해시로 검사하고,
정책 기반3→5잎의 원 수치/UTC만 전달한다. 기존3→6잎 예제의 고정 선언/표식을 재사용하지 않는다.
변조/누락/중단 때 대체 값을 만들지 않고 재생 데이터를 제거한다. 기존 client/17파일과 화면을 보존한다.
계약/메타데이터0.25–0.5h + decoder0.5–1h + fixture/거부 검사·기록0.25–0.5h = **1–2집중시간**의 낮은 신뢰 추정이다.

그 뒤 기존 geometry/재생 화면에 연결하고 새 entry·12시점/47면적·UTC/표/그래프·모바일/유휴·권리/오류·실제 Chrome을 대사한다.
이 UI/기동 검증의1–2.5집중시간 초안은 해당 계약 분해 뒤 갱신한다. 위 시간은 전체 제품 완료일이 아니다.
실제 품종/독립 국내 작기0과 farm/current 권리·서명/worker 적용, 관리/생산/자원/Decimal 경제·거시/수급·자율 비교,
R2/첫 cold 경고가 남는다. G0–G4/예측·미래 마진·추천은 미평가/보류이며 전체 날짜는 자료 확보 일정이 없어 미정이다.
