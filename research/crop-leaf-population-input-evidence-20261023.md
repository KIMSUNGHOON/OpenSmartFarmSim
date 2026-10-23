# 출현 잎 입력의 출처와 현재 검토 — 2026-10-23

상태: [입력 증거 계약](../contracts/crop-leaf-population-input-evidence-v1.md)의 합성 소프트웨어 수용.
[원 저장 잎3D](leaf-population-stored-replay-20261023.md) 뒤의 첫 농장 통합 자식이다.

## 구현·검증

`LeafPopulationInputEvidenceAuthority`는 원 leaf program/source·기존 SourceRecord/현재 검토와
같은 decision UTC의 parent stem 입력 증거를 검증하고 새 domain의 HMAC 영수증으로 결속한다.
원 초기/출현 단위43개·시간/QC/권리와 parent program/source/evidence 지문을 보존한다.
metadata는 복사본이며 재배포 False를 보존한다. 원 stem artifact root는 **미검증 식별자**로 명시한다.
수치 초기 상태·실제 품종/자료·농장 승인과 권리/G0–G4 승인을 이 영수증으로 만들지 않는다.

집중 **52검사**가 통과했다. 정상/비공개 재배포, 재해시한 출처·단위/권리·시각·parent 불일치,
현재/늦은 양쪽 검토 철회, 서명과 재서명한 의미 변조·코드/모델/경로 drift·원 byte 상한을 포함한다.
처음 RED는 모듈 부재2건이었다. 첫 GREEN의 중복 ID fixture 경로 오류1건을 고쳐51건을 통과했다.
게시 전 검토에서 마지막 parent 검토 중 leaf가 철회되는 반례를 RED로 재현했다.
parent 검증 뒤 leaf를 최종 확인하도록 고친 소스의52건을 수용했다. 이전 통과와 합산하지 않는다.

그 최종 소스의 별도 새 Python 프로세스에서 실제 원 fixture SHA
`4f3f9a441a0598fe44ea8c76f9ba9529c8d6661f9e25331319fb4a3f54bda4e0`와 parent SHA
`0c6ebe7ddbff19b64a6348c6ea003a2c78340006a81028977cbc35a7bbef1eb3`를 대사했다.
발급/검증·철회 거부 중 생장 import 시도0, DB/프로세스·artifact/쓰기 진입9개 모두0,
FD4→4와 원40blob의 inode/소유·권한/링크·size/mtime/ctime/SHA 보존을 확인했다.
서로 다른 resolver의 원자 snapshot을 증명하지 않으며 후속 게시기는 현재 검사를 다시 해야 한다.

최종 pytest2.642초/9samples·합계 peak272,031,744bytes,
fresh1.120초/3samples·250,728,448bytes였다. .25초·PID512MiB/합계1GiB 안이며
기존5175/5176의2root·원2,148항목/모델28source/배포 파일을 보존했다. 소유 child 잔여0이다.
전체 backend 회귀/hosted CI·농장 DB/worker/API 수용은 이번 검사 범위에 없다.
현재 사용자의5176 backend는 기존 동결 판본이고 새 입력 증거 모듈은 미배포다.

[기계 판독 증거](artifacts/crop-leaf-population-input-evidence-20261023.json)에 최종31코드/시험 지문,
RED/수정/최종 phase와 native gpt-6.1-sol/xhigh·재귀 CLI0을 보관했다.

## 다음 한 단계

등록 농장/작물·기간과 **실제 완료된 parent stem job/서명 결과**를 현재 검증한다.
새 leaf의 root 참조가 그 원 numerical root·입력 증거와 같은지, 현재 사용/표시 권리와
tenant/farm/기간·양쪽 source가 같은지 실제 SCRAM DB에서 확인해야 한다.
다른 결과·미완료/취소·현재/늦은 철회 거부와 새 Run/결과 쓰기0·원 행/파일/FD·소유 정리를 수용 기준으로 삼는다.
이후 leaf의 서명/자동 worker→같은 job의 API/제품3D가 뒤따른다.

다음 farm 자식은 계약/현재 결속2–3h, 실제 SCRAM/반례1–2h,
늦은 변경/보존1–2h, 검토/기록0.5–1h의 **4.5–8집중시간**으로 잠정 분해했다.
기존 parent 서비스와 원 완료 결과를 재사용할 수 있다는 가정이며 실제 DB 확인 후 갱신한다.
위 첫 입력 자식의 기존2.5–5h 추정은 이 실제 수용 기록으로 대체한다.
실제 Axiany/초기 관측·독립 농장 작기0, 생산·자원/경제·자율 작물 선정과 전체 날짜 미정을 유지한다.


**후속 수용:** [현재 farm/완료 parent 결속35/fresh](crop-leaf-population-farm-binding-20261023.md)를 수용했다.
위 farm 추정은 실제 수용으로 대체하며 다음은 leaf 수치 결과의 서명·현재 무계산 조회다. 사용자 미배포를 유지한다.
