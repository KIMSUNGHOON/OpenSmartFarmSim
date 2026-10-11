# 환기 공동 계산의 불변 페이지 저장 — 2026-10-11

**최종 보존 확인 뒤 로컬 수용.** [계약](../contracts/crop-greenhouse-ventilation-storage-v1.md)과
[기계 증거](artifacts/crop-greenhouse-ventilation-artifact-reference-20261011.json)를 기록한다.
새 UTC 판본의108상태·25연속 장부·6사건 장부·10수지를 원 수치/UTC 그대로 저장한다.

## 구현과 검증

기존 파일 helper와 페이지/원자 HEAD 정책을 재사용한 새 typed 저장 판본이다.
구 모델/초기 RHS schema와 혼합하지 않으며 현재 농장 권한·서버 custody 승인은 별도다.
독립 reader는 context 구성·RHS·환기·적분·관리·복원을 호출하지 않는다.

| 검사 | 관측 결과 |
| --- | --- |
| 새 저장 |92통과;10program×예산1/7/128=30구성의 원 bytes/수치/UTC 동일 |
| 관련 회귀 |기존 저장77·새 UTC147;고유 합316통과/pytest129.28초 |
| 강제 종료/재개 |HEAD 전/후 실제 child SIGKILL(-9)·writer 위치0/1/3/6의 확정 prefix 보존 |
| fresh |별도 Python reader의 계산/복원0·원 summary/page 동일 |
| hold |interval·첫/끝 관리·global step/event 수지·관리 후 환기 실패의 원 확정 시각 보존 |
| 제한 |129samples/128events 시험;페이지64samples/8events·2MiB·최대4097commit·디렉터리512MiB |
| 변조/판본 |원 digest·7파일 층·source/helper/notice·구/신 판본 상호 거부·symlink/FIFO·누락/상한·늦은 변경 |
| 실행 |원59116 smoke0/2.73231009초·원48786 focused0/129.774424518초 |
| WSL |.25초 표본493·단일155,918,336/보호 포함 합767,864,832bytes;512MiB/1GiB 이내 |
| 보존/정리 |원본2,148·기존236계산 파일·두 frozen source/assets·protected roots4·FD4→4·소유/PG/passfile 잔존0 |

실제 native CLI `gpt-6.1-sol / xhigh`, turn `2026-10-11T14:09:59.836Z`,
context SHA `a347ab24b004fbbd11cf6222ab0f18cbbeb66a9ee71d559f0d61f2917b07aac6`, 재귀 실행0이다.
[원문/권리 판단](crop-greenhouse-boundary-source-review-20261011.md)을 유지한다.
새 농업 계수·실제 농장 자료는 도입하지 않았다. 새 API/worker/웹 배포·전체 CI/remote는 실행하지 않았다.

최종 보존 원39240 child/tool0·0.602382644초:기존236계산·accepted source1,911/자산171·두 HTTP200·runtime/권리/검토·로컬 링크 확인을 통과했다.

## 사용자 화면과 다음 순서

사용자가 UI에서 진척을 확인하지 못한다는 피드백에 따라, 다음 실행은 **기존 사용자 화면의 진입/연결/작업 선택과 상태 표시 점검**이다.
실제 현재 서버/DB에서 상태·마지막 확인 시각·보류 이유가 보이는 경로를 우선하고 실제 관측 결과를 보고한다.
5173의 완료166일 재생과5174의 기존 합성 계산 화면을 새 환기 모델 배포로 설명하지 않는다.
새 환기 모델의 입력/QC·현재 농장/자료 권리·custody→결과 등록/API→worker/같은 UTC3D 연결은 그 뒤 재개한다.

실제 농장 Run/국내 독립 자료0·G0–G4 `not_assessed`·실제 생산/미래 마진/추천 hold다.
독립 자료 확보는 개발과 병행하되 검증 전 예측을 게시하지 않는다.
전체 작기 온실 경계·물/양분·에너지 구매·경제·최종 UI가 남아 전체 제품 완료 날짜는 아직 산정하지 못한다.
