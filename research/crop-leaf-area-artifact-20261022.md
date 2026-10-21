# 원 줄기·명시 잎 면적의 불변 저장/원 조회 — 2026-10-22

상태: [저장 계약](../contracts/crop-leaf-area-artifact-v1.md)의 **자체 합성 저장/공개 export 수용**.
현재5176의 farm/job API와 새 잎3D는 아직 갱신하지 않았다.

18집중 pytest(기본15+export3)와 별도 fresh exec를 통과했다.
실제 producer는 원 줄기14blob을 새 디렉터리에 그대로 보관하고, 같은 원 기온/12 UTC에서 잎 목록을 실제 계산했다.
36개 면적을 독립 Decimal 원식과 대사했고, 원12개 줄기 DTO는 기존 public bytes와 같았다.
실제 source/권리·부착 ID/시각·단위·raw/state chain·투영 변조와 중도 code-pin 변경을 거부했다.
leaf 또는 stem 한쪽만 재배포 권한이 없어도 export를 거부했다.

실제 보관본 root는 `7ebcd02d902f03343e61e2151a93107d021404eed74071fa3e9bbe417743a8a5`,
24code 지문·40blob/12시점이다. 기존 stem14blob을 변경하지 않았다.
자체 소유 input/root·stem input/root·12 frame/index의17개 public 파일만 export했다.
index SHA는 `c6f0ba4d5b85483a78c5d94d2e40389b8fd45787cb795b5dba2a0c8d2a379621`다.
합성 추적 면적 합계는 첫 `0.0009700372917537751`, 끝 `0.0054279032106053435 m2`다.
이는 선언된3잎의 수학 probe이며 실제 품종의 생장/면적·잎 수 예측이 아니다.

별도 새 프로세스에서 원12 frame bytes를 대사했다.
생장 모듈 import0, JobStore connection/psycopg·subprocess run/Popen·artifact put/content write/write-open7계측 모두0,
40blob의 inode/UID/GID/mode/link/size·mtime/ctime/SHA 전후 같음을 확인했다.
이 fresh 검증은 추가 Python을 pytest와 동시에 띄우지 않도록 별도 guarded phase로 수행했다.
같은 내용의 pytest fresh 항목1개는 로컬에서 deselect했으며19개 pytest 전체가 통과했다고 세지 않는다.

주요 WSL 관측(.25초):

| 단계 | wall/samples | 합계 peak bytes |
| --- | --- | --- |
| 기본15 pytest | 6.300초/24 | 1,021,677,568 |
| export3 pytest | 3.462초/13 | 1,038,061,568 |
| 실제 생산/export | 1.120초/4 | 1,009,860,608 |
| fresh 최종/쓰기 차단 | .635초/2 | 993,562,624 |

원7root·source/원2,148항목·동결 화면/FD4→4와 소유 정리0을 확인했다.
첫 GREEN의 원 입력 trailing LF가 기존 canonical JSON 계약에 거부된9개 실패를 보존했다.
생성기를 canonical bytes로 수정하고 같은 권리 선언 시각을 유지한 뒤 위 검증을 통과했다.
fresh 첫 수용 뒤 파일 쓰기7계측/메타데이터 경계를 추가한 최종 검증을 기록했다.
전체 backend/web 회귀·공통 용량·새3D/현재 권리 farm API는 이 수용에 포함하지 않는다.

다섯 축 검토: 기존 blob 운송·원 stem reader를 재사용하고 계산 producer와 무계산 reader를 분리했다.
새 표/role/패키지·외부 자료/코드/CLI 실행은0이다. 모델 source 변경은 완료 root 전 hold하며,
reader는 원 저장 숫자를 투영하고 원 stem/leaf 결과·입력 지문을 확인한다. root 신뢰가 계산 증명/관문 승인은 아니다.

다음은 typed frontend → 저장면적을 제작 단면 leaflet 삼각형 면적에 대응 → 실제 WebGL/표·그래프/재생이다.
길이/폭·소엽 수·각도·petiole/rachis·표면과 부착 위치는 display policy의 제작 가정이다.
실제 측정 면적 정의/품종 형상의 검증은 없으며 새로운 잎/관리·탄소/자원/경제와 G0–G4는 후속이다.
실제 Axiany 초기관측/계수·독립 농장자료0을 유지한다.

native `gpt-6.1-sol / xhigh`·재귀 CLI0, source/원 증거 지문·관측은
[공개 증거](artifacts/crop-leaf-area-artifact-20261022.json)에 기록했다.
