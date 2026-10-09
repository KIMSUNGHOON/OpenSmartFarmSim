# 전체 166일 합성 부모의 게시·보존·현재 복원 수용 — 2026-10-09

## 수용한 범위

`crop-harvest-full-parent-restore`와 해당 중단 복구를 로컬 수용했다.
원 계산95915의 실제 도구 종료0, 후속36916의 실제 도구 종료0과
16:21:40 KST 별도 종료 감사를 확인했다. 원95086의 중단 실패는 보존한다.
[불변 관측과 공개 hash](artifacts/crop-harvest-full-parent-restored-reference-20261009.json)에
원 명령·각 자식 종료·원본/현재/fresh 복원·자원·비공개 영수증 hash를 기록했다.

같은 모델/입력의 새 합성166일 판본이다. 실제 품종 계수나 독립 농장 검증은 없으며
실제 농장 작물 Run/국내 독립 자료0건, G0–G4 `not_assessed`를 유지한다.
제품 runtime CLI나 전체 G1·생산량 예측·마진·작물 추천의 수용으로 확대하지 않는다.

## 실제 통과한 검증

- 원 계산: 1,816,704걸음/456commit, 47,809sample/5event,
  919파일/404,673,556bytes. 원18:12:12 KST 상한 안에서 종료했다.
- 전체 비교: sample748page/event1page의 모든 원 행·UTC와 checkpoint121상태를 대사했다.
  두 행 SHA는 이전 수용 전체166일과 같고, 비교 RHS 호출0·FD4→4다.
- 원 사전 선언/plan/key로 정상 게시하고 DB·인증 자료를 보존했다.
  무작위 서명 key와 proof도 실제 보존 bytes와 대사했으며 서명 우회나 임의 행 삽입은 없다.
- 현재 checkout의 실제 SCRAM 조회는 고정 producer 조회와 같은 원 record/UTC/수치다.
  현재 권리 철회·scope 제거·다른 tenant를 거부한 뒤 원 상태로 복원했다.
- UID/data/binary/PID identity를 확인한 원 소유 PG를 정지하고 그 시험 cluster만 제거했다.
  원 입력/artifact/runtime/key와 인증 backup은 의도적으로 보존했다.
- 원 PG가 없는 상태에서 별도 현재 Python/fresh PG를 만들고 같은 record와 대표 첫64/마지막1시점·5사건을
  다시 조회했다. 원본/현재/fresh 결과가 같고 조회 RHS·게시·proof 발급0, FD4→4다.
  fresh PG도 정지했으며 pidfile/소유 비좀비/잔여 자식0이다.

## 실측 비용과 자원

| 후속 실제 명령 | 종료 | wall초 |
| --- | --- | ---: |
| 전체 비교→정상 게시→인증 backup | 0 | 2,537.614 |
| 현재 source 조회/권리·계정 거부 | 0 | 51.359 |
| 확인한 source PG 정지/cluster 정리 | 0 | 1.166 |
| source 정리 후 fresh 현재 복원 | 0 | 34.564 |

후속 전체는2,626.363초(약43분46초)다. 첫 명령 중 전체 비교는2,302.571초,
정상 게시는39.200초였다. raw backup500,601bytes≤128MiB이며 원404MB artifact는 별도 보존한다.

0.05초44,287표본에서 단일 PID 최대178,319,360bytes≤512MiB,
관측 합588,541,952bytes≤1GiB다. controller/소유 자식/확인한 source PG·보호 미리보기와
실제 fresh PG tree 범위이며 공유 메모리는 중복될 수 있다. WSL 전체나 일반 운영 용량의 수용은 아니다.
현재 source1,584개·고정 source1,400개·preview dist와 보호 미리보기 identity를 보존했다.
원 도구0과 종료 감사 뒤 이 작업의 source 변경 보류를 해제했다.

판단은 실제 native Codex CLI `gpt-6.1-sol`/`xhigh` 세션에서 수행했고
invocation 문맥/출력 hash를 기록했다. CLI 재귀 실행0이다.

## 다음 작은 단계와 사용자 화면

다음은 **복원된 실제 전체 부모의 제한된 조회 비용 측정**이다. summary·첫/다음64·마지막1시점·
5사건을 현재 query로 읽고 원 record/수치·실제 SCRAM·FD/원본 보존·읽기 재계산0·
원 종료/PG 정리·512MiB/1GiB 한도를 확인한다. 계산 RHS나 수확 행은 생성하지 않는다.
전체 writer의748page 반복 조회에 실제 비용 문제가 있는지 먼저 판단하고 실행 예산을 정한다.

이후 정상 전체 수확 writer/registry→독립 Decimal 원 수량 대사·인증 보존/fresh reader
→보호 API/대표3D→기후/물·양분/구매 에너지→사용자 실행/Decimal 경제 순서다.
전체 writer/API/3D와 UI U1/U3는 아직 수용하지 않았다.

`localhost:5173`은 별도 DB의 저장된3시점/5수확행 미리보기다.
이 완료 전체 부모나 계산 중 상태를 자동으로 표시하지 않으며 재생은 저장 UTC의 이동이다.
U3의 같은 실행 상태/확정 checkpoint·최종 갱신 시각과 완료 결과 연결이 필요하다.
새 UI 후보의 [hosted 웹1,028개/브라우저140개](crop-ui-web-hosted-regression-20261009.md)는 통과했으나
원3상태 디자인 대조·실제 공동 DB·WSL 브라우저 자원·배포는 남았다.

전체 부모의 종료는 확정 사실이다. 후속 완료 날짜는 조회/writer/API 비용과 UI 실제 수용을
측정한 뒤 갱신한다. 실제 국내 품종/독립 자료·기후/자원/경제가 미확보라 최종 제품 날짜는 산정하지 않는다.
