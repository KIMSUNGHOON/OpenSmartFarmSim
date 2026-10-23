# 새 잎 사용자 API 연결과 남은 요청 예산 보류 — 2026-10-23

**기능 경로는 실제 연결했고 전체 runtime 수용은 미완료다.** 계산 중 동일 POST의30초 초과/504가 남는다.
현재5176의 새 잎 화면은 기존 저장 합성 연구 재생이며 이번 작업의3D 화면 연결은 다음 단계다.
[기계 증거](artifacts/leaf-population-execution-live-20261023.json)에 성공·실패·자원 관측을 함께 보관했다.
판단은 실제 native Codex CLI **gpt-6.1-sol / xhigh**에서 수행했고 두 turn_context 지문·재귀0을 기록했다.

## 연결한 범위

기존5175/5176·원 DB/키/줄기 작업을 보존하면서 새 잎 API만5176의 별도 upstream으로 연결했다.
기존 줄기 URI는 기존 저장소를 계속 사용한다. 같은 UI 주소 뒤에서 기존 저장소를 새 DB로 교체하지 않았다.
새 원점은 별도 소유 합성 DB·현재 권리/검토·키와 **2026-10-22T00:00:00Z의 retrospective farm**이다.
이 농장의 실제 완료 parent job에 새 leaf 입력을 결속했다. 기존 더 이른 farm decision은 바꾸지 않았다.
입력은 기존 자체 합성 fixture이며 실제 지역/품종/시장 자료를 새로 확보한 결과가 아니다.

배포 source는 `4f1f523bf816e629f964e2edb3e55f7e48a01a79`의820개 파일과 모두 byte/hash가 같다.
새 프로필의 정확한 줄기/leaf loop와 표준 보호 route installer를 사용한다.
기존 역할/표 정의를 새 소유 fixture 인스턴스에 설치했으며 제품 schema/역할 정책은 바꾸지 않았다.
로컬 사용자 URL은 HTTP loopback이고 두 backend upstream의 인증서를 Nginx가 검증한다.
새 leaf upstream은 직접 인증서 검증 HTTPS 입력 조회도 통과했다. 공개 인터넷 TLS/G4 수용과 구분한다.

## 실제 확인한 결과

- 실제5176 접수에서 leaf job `399c3c1a-31df-4526-b2f8-d0f9fed7865f`가 자동으로 **완료 attempt1**을 게시했다.
  **12시점/52잎 면적의 모든 원 frame bytes**, parent job/result/root와 최초 계산 시각을 대사했다.
- 응답 지연 뒤 새 job을 만들지 않고 그 작업을 재조회했다. 완료 뒤 같은 POST는 같은 job을 반환했다.
  성공한 복구 묶음의 최장 요청은28.064828초였다.
- 현재 leaf 권리 철회 때 완료 replay는422였고, 원 줄기 조회는200을 유지했다.
  별도 취소 probe는 철회 뒤 cancel200/canceled·결과 미게시였다. 권리 복원 뒤 원 완료 result가 같았다.
  원 program/source/계수 bytes는 바꾸지 않았다.
- 새 leaf API/PG만 cold restart했다. 같은 DB/키·820source, 원 job/result/최초 calculated_at/replay가 같았다.
  재시작 검사의 POST는0, 새/기존 DB의25표 전체 행 SHA도 각각 전후 같았다.
  종료한 새 controller의 자손은0이고 교체한 controller만 의도적으로 실행 상태다.
- 원 줄기 작업 `66b8c06d-7137-42d2-b141-e9d39bc230c4`의 result/replay,
  기존 DB25표 원 행과 parent18파일·2,469감시 항목을 보존했다. 기존 두 화면은 HTTP200이다.

## 미수용: 계산 중 동일 재요청

첫 접수는202였지만, 그 작업이 계산 중일 때 같은 POST를 보낸 요청이 **30.028101초/504**였다.
첫 관측 묶음은 실패로 보존했다. 완료 작업은 새로 생성하거나 계산을 다시 시작하지 않고 복구했다.
실제 job은 이후 정상 완료 attempt1이었으며, 완료 뒤 retry의 성공으로 앞선 실패를 대체하지 않는다.
이 관측만으로 CPU·DB 잠금·원본 검증 중 어느 부분이 원인인지 확정하지 않았다.
현재성 검사를 생략하거나30초 client/proxy 예산을 늘리지 않았다.
따라서 **계산 중 재요청 예산·U1과 전체 runtime/운영 수용은 보류**다.

## 보존·자원과 실행하지 않은 범위

.25초 표본의 보호+소유 합산 peak는494,452,736bytes, 개별 PID peak는99,106,816bytes였다.
각 일반 검사 단계는600초/PID512MiB/합1GiB 안이었다.
cold observer는110.204초/430표본·합459,014,144bytes였으며 원 두 root와 source/감시 항목을 보존했다.
일반 probe 자손은0, 새 controller/PG/API는 사용자 확인을 위해 유지한다. Windows Chrome은 WSL 용량 증거에서 제외했다.
전체 backend 회귀·이번 hosted CI·브라우저/새 UI 검증은 실행하지 않았다.

## 다음 단계

기능/원 값·현재 권리·저장 복원의 증거를 개발 착수 조건으로 삼아 **strict SDK→같은 job의 사실적 잎3D**를 연결한다.
접수 미확정/503·504를 표시하고 같은 pending request/job ID를 보존해야 한다. 임의 완료율이나 static fixture 대체를 사용하지 않는다.
계산 중 동일 retry의30초 문제는 별도 미완료 작업으로 유지하고 실제 동시 관측·수정/재검증 후에만 수용한다.
이는 전체 runtime의 완료나 배포 관문을 낮춘다는 뜻이 아니다. [의존성·작업량](../tasks/plan.md#사용자-leaf-api-기능-연결과-30초-보류--2026-10-23)을 따른다.

실제 Axiany 계수/초기관측·독립 현장 작기0/승인 farm Run0,
한 작기/생산·자원/경제/자율 선정·최종 사실감 R2/첫 셰이더 경고·G0–G4와 전체 완료일 미정을 유지한다.
