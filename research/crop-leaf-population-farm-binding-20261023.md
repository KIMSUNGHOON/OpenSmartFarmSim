# 출현 잎과 현재 농장·완료 줄기 결과 — 2026-10-23

상태: [농장 결속 계약](../contracts/crop-leaf-population-farm-binding-v1.md)의 **합성 소프트웨어 수용**.
[입력 증거](crop-leaf-population-input-evidence-20261023.md) 다음의 현재 농장/parent 결과 연결 자식이다.
새 leaf 결과의 서명·자동 worker/API·사용자 화면 적용은 남는다.

## 구현과 시간 범위

`LeafPopulationFarmBinding`은 기존 실제 `MorphologyExecutionQuery`와 같은 농장 authority/JobStore,
stem 입력 authority를 사용한다. parent의 실제 완료/publication·서명/원 root와 leaf 원 입력 증거,
등록 farm/crop/기간·양쪽 자료의 현재 검토/사용·표시 권리를 전후 대사한다.
요청의 경로/임의 callback 또는 unsigned root 대체는 없다. 새 표/역할/leaf Run·결과 row도 만들지 않는다.
binding은 원 parent job/result/root·최초 계산 시각과 leaf 원 bytes/초기/출현·코드/검토를 고정한다.

기존 사용자 parent 작업의 decision은 새 leaf 자료의 가용 시각보다 이르므로 소급 재사용하지 않았다.
별도 합성 농장을 **2026-10-22T00:00:00Z**의 decision으로 등록하고 실제 parent 작업을 완료해 검증했다.
모델 구간은 원10월1–2일의 retrospective replay이며 과거 당시 전망이나 실제 재배 검증이 아니다.
`parent_result_binding_verified=True`는 해당 job·서명·root의 연결 확인이다.
실제 품종 적용/수치 초기조건·권리 또는 G0–G4 승인으로 표시하지 않는다.

## 통과한 검사

- **순수33:** 닫힌 요청/크기·parent UUID/원 SHA·leaf/parent 증거 불일치,
  원 단위/기간·1마이크로초 가용/점유 경계와 per_tracked_shoot 보존.
- **실제 SCRAM2:** 별도 farm 등록→실제 parent 계산/완료→leaf prepare/read/write,
  미완료·취소/다른 result/root·crop/tenant와 현재/늦은 양쪽 검토·권리/범위 변경 거부.
  표시만 허용될 때 read는 가능하지만 parent 계산 권리가 없으면 write는 거부한다.
  시험 DB의 과도한 DELETE 권한과 rehash한 등록 row 변조도 거부하고 원 상태를 복구했다.
- **별도 fresh:** 같은32,605bytes binding·parent result/root/최초 시각,
  두 검토 철회 거부·생장/worker import 시도0·지속 SQL 쓰기0·작업 쓰기6진입0,
  seed/pytest/HTTP app import0·원 signed18파일·FD4→4를 확인했다.

정상 경로 prepare/read/write 각각의 지속 SQL·작업 쓰기도 직접 차단·계측했고 모두0이었다.
관련 생장/CLI 진입도0이다. 정상/변경 거부 각각의 **시험 스키마25표 행 SHA**는 전후 동일하다.
이는 기존 사용자 DB 전체를 이번에 재대사했다는 주장이 아니다. 검사는 별도 소유 DB만 사용했다.
원31코드·기존 입력/저장 파일과5175/5176의2서비스를 보존했다.

첫 RED는 모듈 부재였다. 첫 native 설정에서 tuple 권한 목록의 집합 결합 오류가 났고 수정했다.
이 실패에서도 소유 DB/역할/임시 파일 정리를 확인했다.
개별 정상/변경 거부 뒤 쓰기 계측을 보완한 **최종 같은 소스 native2건**을 다시 통과했다.
이전 시도를 합산하지 않으며 최종 수용은33+2=35건이다.
전체 backend 회귀/hosted CI와 HTTP·제품 UI는 실행하지 않았다.

## 자원과 응답 시간

최종 native2건은267.531초·1,021samples, .25초 간격 설정에서 PID peak113,303,552/
합계416,301,056bytes로512MiB/1GiB 안이었다. subreaper로 daemon PG도 포함했다.
원2root·2,148항목/관련 저장·배포 파일이 보존됐고 소유 child·schema·role 잔여0,
passfile/짧은 임시 디렉터리 정리를 확인했다.

단일 관측의 prepare14.09초/read13.92초/write current13.51초를 기록했다.
평균 처리량·HTTP30초/사용자 U1이나 공통 WSL 용량 수용은 아니다.
향후 API/worker 조립에서 중첩 현재 검증의 실제 비용과 polling 부담을 확인해야 한다.
이번 단계에는 현재 권리 cache/검사 생략을 도입하지 않았다.

[기계 판독 증거](artifacts/crop-leaf-population-farm-binding-20261023.json)에 원 해시·각 phase/실패·
최종 소스와 정확 native gpt-6.1-sol/xhigh·재귀 CLI0을 보관했다.

## 사용자 산출물과 다음 단계

[새 잎3D](http://localhost:5176/leaf-population-replay.html)는 기존 저장 합성12시점의3→6잎 화면이다.
이번 binding 모듈은 그 사용자 runtime에 미배포다. 현재 사용자 화면의 자동 계산에 새 잎이 연결됐다고 표시하지 않는다.

다음은 **leaf 불변 수치 결과의 서명·현재 무계산 조회**다.
수용 기준은 실제 parent 결속 아래1회 계산→원40blob/root/12frame·서명/원 시각 보존,
발급/게시 전후 현재 철회·source/root/서명 변조 거부와 fresh의 생장 import/계산·DB쓰기/파일쓰기0,
원 parent 결과/행·소유 정리다. 이후 명시 worker/기존 작업 표→보호 API→같은 작업의 제품3D를 잇는다.

다음 서명 자식은 계약/원 저장 결속1–2h, producer/reader2–3h,
변조/철회·fresh 검증1–2h, 기록0.5–1h = **4.5–8집중시간**의 낮은 신뢰 작업량이다.
이번 farm 자식의 기존4.5–8h 추정은 이 실제 수용 기록으로 대체한다.
실제 Axiany 계수/초기관측·독립 농장 작기0, 한 작기/생산·자원/경제·자율 선정,
최종 사실감 R2·첫 native GPU 경고와 전체 완료 날짜 미정을 유지한다.
