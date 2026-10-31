# 소유 생산 batch/schema4 입력의 불변 등록·조회 — 2026-10-31

[새 source 저장소](../backend/app/economic_batch_source_store.py)와
[입력/권한 계약](../contracts/economic-batch-source-store-v1.md)을 실제 PostgreSQL에서 검증했다.
실제 작업의 원 입력 bytes·tenant·원문 SHA와 최초 기록을 결속하고 fresh reader에서 조회한다.
**저장 라이브러리/명시 프로필을 구현했으며 제품 HTTP/접수·worker·3D UI에는 아직 연결하지 않았다.**
[기계 증거](artifacts/economic-batch-source-store-20261031.json).

## 변경과 기본 동작

원 MarketSourceStore의 등록·조회·변조/작업 검증을 재사용한다.
model/version/table 선택 지점과 공통 DDL만 분리했고 원7종·schema3·기존 테이블은 기본값 그대로다.
새 `economic-batch-user-source-v1`은 별도 `economic_batch_source_records`에
schema4·생산 batch와 기존 나머지6종을 저장한다. 원 목록에 새 자료를 섞지 않는다.
JobStore 원문/등록 한도는64KiB이며 계산 커널의2MiB와 구분한다.

새 flag `economic_batch_source_storage`는 기본 false이며 market source/calculation 활성화가 필요하다.
명시 프로필에서만 authority SELECT/INSERT를 추가하고 원 권한 감사의 전체 행렬을 유지한다.
원 정책 판본은 그대로이며 새 프로필에만 v9 marker를 낸다.
새 읽기/쓰기 scope를 사용하고 진행 중 읽기/쓰기 권한 철회도 결과 반환/commit을 차단한다.
운영 설정의 생략/false·엄격 boolean을 지원하며 자동 설치·권한/운영 전환은 없다.

## 실제 검증

- 최종 신규 **20검사**: actual SCRAM 등록/원 pin·동일 bytes의 같은/다른 작업 재시도와 최초 시각,
  fresh reader,8종/목록, 원 테이블/숫자 입력 보존, 충돌·다른 tenant/현재/늦은 권한,
  SQL 불변/SELECT·INSERT 한정,2개 동시 요청·caller transaction rollback,
  잘못된 stage·조회 ledger/SQL쓰기0·운영 옵션을 확인했다.
- 실제 서명 시장 hold/decision context와 새로 저장한 숫자·batch/schema4를 연결했다.
  원 메모리의 경제 입력/시나리오/pin을 제거한 뒤 실제 source 조회만으로 v10 계산에 도달했다.
  수확/판매 생성 없이 원 비용/현금을 대사했고 assessment hold/G0–G4 미평가를 유지했다.
  ASCII/한글 계획 ID 두 경우의 실제 입력 UTF-8 SHA와 원 작업 참조도 확인했다.
  이는 소유 테스트 DB의 합성 사용자 가정이며 실제 농장/독립 경제 검증이 아니다.
- 기존 source22 + 경제206 + 정책/운영 설정134 + 신규20 = **고유382검사**를 통과했다.
  source/경제 묶음247은 신규19/기존228을 포함한다. 최종 신규20은 그19와 추가 한글1이며
  별도 실행의 반복 사례를 다시 합산하지 않았다. 정책/운영134는 별도 두 파일 전체다.
- 최초 missing-module RED와 운영 옵션의 유효 false/true를 거부한2fail/5pass RED를 보존한다.
  후자는 새 dataclass flag의 운영 설정 허용 목록을 추가해 수정했다.
  최종 production 코드는 이후의382검사·통합 대사에서 같다.

## DB·자원·자료 보존

PG16.15의 별도 소유 클러스터를 사용했다. bootstrap만 private Unix socket이고
실제 runtime 호출은 host SCRAM·정확 session/current user·효력 권한 감사를 거쳤다.
기존 사용자 서비스 DSN/비밀번호를 읽거나 그 DB에 접속하지 않았다.
권한/운영과 최종 source 묶음은 private controller가 같은 실제 클러스터를 fixture들에 제공했다.
변경한 것은 테스트 클러스터 공급뿐이며 가짜 DB/권한 결과나 skip으로 대체하지 않았다.
shared_buffers16MiB, 한 번에 한 phase, PID512MiB/합계1GiB/600초를 유지했다.

최종 source20은 guard20.083초/PID130,486,272bytes/합계354,963,456bytes,
source/경제247은98.319초/158,371,840/414,597,120,
정책/운영134는54.081초/192,704,512/538,677,248이었다.
각 소유 클러스터를 종료하고 데이터/암호 파일을 정리했으며 소유 자손 잔여0·FD4→4였다.
Windows/전체 host RSS는 새로 측정하지 않았다.

기존711source/1output/private20/phase16·추가2pin, 원 수치 코드·CAS·기존 GUI와
현재238파일의 실제 HTTP bytes/hash/no-store/CSP·PID/boot/ticks·첫 만료를 보존했다.
보존 wrapper의1차/2차는 이전 cold proof와 native proof를 잘못된 새 경로에서 찾아 실패했다.
별도3차 replay 디렉터리에 지문이 같은 이전 증거를 제공해 수정했고 보존 검사는 exit0이었다.
이전4사례 cold proof 재사용은 새 계산 실행이나 신규 검증 수로 합산하지 않았다.
현재 [3D](http://localhost:5184/supply-material-quantities-replay.html)는17:03 KST 첫 만료까지 유지한다.
mutable 통합 파일5개는 새 커밋의 검증된 지문으로 기록한다. 기존 수치 버전/불변 산출물과 구분하며
후속 명시 프로필 확장은 새 코드 커밋·회귀 증거로 남긴다. 과거 Git 판본/증거를 고치지 않는다.
기존 운영 DB/설정·서비스를 새 프로필로 배포하거나 새 브라우저/전체 suite/hosted CI를 실행하지 않았다.

실제 native gpt-6.1-sol/xhigh·CLI0.157.1 turn `2026-10-31T02:52:17.524Z`의 지문/출력을 보존했다.
재귀 CLI·새 agent·실제 농장 자료/매개변수·요금 채택은0이다.

## 다음 단계

다음은 **제품 서버의 source/서명 hold 권한 결속과 계산 접수**다.
이번 통합의 test-only facade를 production 권한 factory로 보고하지 않는다.
실제 EconomicBatchSourceStore/MarketHoldStore/decision-context store의 같은 schema·로그인 정책·
principal·tenant/기간/참조를 구조적으로 결속하고, 등록된 schema4만 접수해야 한다.
중복 요청·충돌/rollback·current/late 권한/원문 변경·원 bytes/최초 시각과 원 schema3 보존이 수용 기준이다.
권한 결속/접수2–4집중시간 초안이며 구체 객체·원 job/input 계약을 확인한 뒤 갱신한다.
그뒤 deterministic worker/불변 결과→원 저장 창의 독립 가정 비용 관계→strict SDK/같은 선택 UI다.
물리 열·수분 counter를 구매량으로 간주하지 않는다.

긴 작기/반복 성장·실제 품종·독립 국내 farm raw0, 실제 설비/계량/구매/청구 권리,
생과중·다회 수확/판매·미래 경제/거시·수급·자율 비교·최종 제품/R2는 남는다.
개발과 자료 확보를 병행하며 원 G0–G4와 독립 검증 없이 예측·추천을 게시하지 않는다.
전체 goal active/incomplete·완료일 미정을 유지한다.
