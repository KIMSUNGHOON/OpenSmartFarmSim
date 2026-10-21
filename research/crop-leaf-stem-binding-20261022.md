# 잎 목록과 원 저장 줄기의 부착·출현 결속 — 2026-10-22

상태: [생산 경계 계약](../contracts/crop-leaf-stem-binding-v1.md)의 **합성 결속 수용**.
새13/관련150(pytest13+population43+출현38+초기22+전용시계34)이 통과했다.
원 줄기 root/result·UTC와 leaf/부착 ID·출현 정확 초·나이/면적을 대사했다.
없는/미래 줄기·줄기보다 이른 잎·다른 원점/시각·분수 현재 시각의 반올림·잘못된 root/index와 복사본 변조를 거부했다.

실제 기존 줄기14blob/12시점에 자체 명시 새 잎3건을 적용했다.
잎 수는3,3,3,4,4,4,4,5,5,5,6,6이었다. 이는 직접 선언한 probe이며 leaf-per-node 생물 규칙이 아니다.
독립 Fraction/Decimal100의52개 면적/정확 나이와 합계12개를 대사했고 최대 상대차2.0918286405209873e-16이었다.
원14blob의 inode/UID/GID/mode/link/size·mtime/ctime/SHA를 유지했다.
이 새 population/binding의 불변 결과와 새3D는 아직 게시하지 않았다.

시험 안에서 원12개 stem DTO가 기존 public bytes와 같았고 원 ID/분수 출현과 입력 불변을 확인했다.
구간 성장/새 생성·실제 JobStore.connect/psycopg·subprocess run/Popen·blob put/쓰기 open을 차단한 상태에서 결속했다.
이 함수는 population 정규화의 면적 anchor 식 대조를 포함하므로 무계산 GET reader는 아니다.
조회 경계는 다음 별도 reader에서 생장 import/식 평가 없이 구현해야 한다.

첫 GREEN은 시험의 JobStore._conn 계측 대상이 실제 메서드가 아니어서1실패/11통과했다.
실제 connect로 수정하고13검사 및 관련150을 통과했다. 같은 잘못된 계측을 쓰던 이전 leaf fresh helper도 고쳤다.
그 뒤 별도 프로세스로 기존 leaf12시점/40blob을 재확인했다:
생장 모듈 import0, 실제 JobStore.connect·psycopg.connect·subprocess run/Popen·artifact put/content write/write open7계측0,
40blob의 metadata/bytes 전후 같음이다. 이전 psycopg 차단 결과는 유지되며 잘못된 메서드 계측을 보완한 기록이다.

| 단계 | wall/samples(.25s) | WSL 합계 peak bytes |
| --- | --- | --- |
| 관련150 |3.971초/15|1,043,603,456|
| 실제 원14blob 결속 |.600초/2|970,145,792|
| 수정 fresh/원40blob |.346초/1|970,735,616|

단일PID peak124,948,480bytes, 원7root/원2,148항목·source/동결 화면·FD4→4와 소유 process0을 확인했다.
전체 backend/web 회귀·공통 용량·새 population3D는 미실행이다.
새 패키지/DB/API/외부 자료0이며 기존 불변 reader·population을 재사용했다.
원 root 신뢰·farm/current rights·서명/관문 승인을 발급하지 않는다.

다음은 별도 새 population program·모델/코드/초기/출현/상태·binding chain을 불변 저장하고
무계산 reader/fresh→export/SDK→같은 UTC의 새 잎 수/면적3D를 수용하는 것이다.
실제 Axiany 계수/초기관측·자동 출현/분류/관리·독립 농장 자료0,
한 작기/탄소·자원/경제·자율 선정/G0–G4와 전체 완료일 미정은 유지한다.
정확 native `gpt-6.1-sol / xhigh`·재귀 CLI0 및 [검증 지문](artifacts/crop-leaf-stem-binding-20261022.json)을 기록했다.
