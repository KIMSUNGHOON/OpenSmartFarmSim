# 저장 수확 전체 행 검사의 반복 조회 축소 — 2026-10-09

18:12 KST. [core4 계약](../contracts/crop-harvest-row-verification-v1.md)의 작은 구현을
`e2eeb8c`에서 로컬 수용했다. [원 명령·출력·소스/자원 영수증](artifacts/crop-harvest-row-verification-reference-20261009.json)을 보존했다.
실제 native Codex CLI `gpt-6.1-sol`/`xhigh` 문맥과 판단을 기록했고 재귀 CLI0이다.

## 변경과 검증

registry의 전체 행 검사에 `verify_all_rows()`를 사용한다. 한 작업의 기존 전후 guard로 현재
부모/권리/identity·디렉터리/HEAD/root를 검사하며, 모든 저장 page의 실제 bytes/hash/count와
원 순서의 canonical 행 SHA·전체 count를 대사한다. 질량·배정이나 RHS를 다시 계산하지 않는다.
공개 `page()`/`summary()`·writer·최종 권리/INSERT/rollback 등의10개 메서드 AST는 기존과 같다.

- 원74739 도구0: **집중70개**, 새16개/기존54개, pytest6.59초·wrapper7.086초.
  실제1/3page 시험에서 기존 순회와 원 행 SHA가 같고 검사 본체의 부모 조회는 각각2→2/6→2회다.
  첫/중간/마지막 blob 변조, 잘못된 count/행 순서, 마지막 page 뒤 권리/계정·HEAD/root/디렉터리 변경과 FD close를 확인했다.
- 원48655 도구0: **실제 SCRAM 등록1개**, pytest136.32초·wrapper145.156초.
  원6행/서명·동일 재시도/최초 시각, INSERT 뒤 계산 권리만 철회한 rollback과7종 거부를 확인했다.
  기존 작은 부모의 DB/input/custody·FD13→13, 조회/등록 중 RHS·새 crop proof0을 보존했다.
  schema/role/passfile0·소유 PG 종료와 data/pidfile 부재를 확인했다.
- 새/기존 집중과 실제 등록을 합친 **고유71개**다. 최종 두 검사에 사용한 core4의 hash가 같다.
  소스1,602개와 실행 중 전체 생장 미리보기의 고정 source/dist·원 controller/service/PG identity를 보존했다.
  frontend200을 확인했고 시험 소유 임시 디렉터리는 별도 확인 뒤 정리했다. 비공개 원 로그/영수증은 유지한다.
- 최종 native의0.05초1,921표본에서 단일125,083,648bytes/관측 합497,868,800bytes로512MiB/1GiB 안이다.
  범위는 controller/소유 자식·정확한 기존 미리보기/PG·이번 실제 PG tree다. WSL 전체나 운영 용량 보증은 아니다.

처음 누락 메서드의 RED 원56190 종료1/2실패와, 중간69개/작은 native 수용을 보존했다.
검토 중 bytes로 분할한 blob은 작아도 논리적64행 응답이2MiB를 넘는 반례를 발견했다.
원33925 종료1/1실패·69통과로 확인한 뒤 envelope 포함 기존 제한을 복구했고 최종70개가 통과했다.
이를 단순 blob 한도 통과로 새로 허용하지 않는다.

## 비용의 의미와 다음 단계

전체748page에 기존 순회 구조를 적용하면 검사 본체의 부모 조회는1,496회이며 새 구조는2회다.
이 숫자는 작은 시험의 호출 구조를 전체에 적용한 계산이다. **전체 registry 실행 시간의 실측은 아니다.**
원 수확 writer가 생장748page를 읽는 비용은 그대로 남아 있다. 전체 수확을 생성·등록하거나
전체47,813저장 행의 독립 Decimal 대사·인증 보존/fresh reader·API/3D를 완료하지 않았다.

다음 작은 단계는 보존된 전체 부모와 새 source/profile에서 정상 writer의 처음 두 page를 실제로
생성해 원 수량/UTC·현재 권리·부분 비용을 대사하고, 통제된 중단에서 HEAD/DB 미게시와 정리를 확인하는 것이다.
그 실측과 이번 검사 비용 구조를 합쳐 전체 writer/registry의 wall 예산을 정한다.
전체 RHS를 재실행하거나 기존 작은900초 예산만 늘려 시작하지 않는다.

현재 `localhost:5173`은 완료된 합성166일 생장47,809시점의 실제 API/수치3D다.
18:16 KST 원88052 도구0의 보호 HTTPS summary도200/9,628bytes·6.929초였으며
원 수용 응답 SHA와 같았다. 인증서 검증·no-store·47,809시점/5사건/1,816,704완료 걸음을 확인했다.
계산 진행률·새 checkpoint 자동 갱신(U3)과 전체 수확은 미연결이다.
실제 품종/독립 국내 농장 자료0건·G0–G4 `not_assessed`, 생산/미래 마진/추천 보류를 유지한다.
