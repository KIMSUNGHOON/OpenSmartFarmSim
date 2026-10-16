# 일사 계산의 확정 구간 원 조회 v1 — 구현 예정

2026-10-17. [현재 진행 조회](crop-greenhouse-solar-execution-query-v1.md),
[실행 핵심](crop-greenhouse-solar-execution-core-v1.md),
[서명 이력](crop-greenhouse-solar-server-custody-v1.md),
[불변 페이지](crop-greenhouse-solar-storage-v1.md)가 선행한다.
이 문서는 다음 단계의 수용 경계이며 구현 완료나 사용자 게시 증거가 아니다.

## 다음 한 단계

별도 `SolarExecutionPrefixQuery`의 내부 `joint-solar-prefix-read-v1` 응답을 구현한다.
범위는 `synthetic_joint_solar_confirmed_prefix_only`다. 같은 Solar jobs/admission/checkpoint/custody/result 조립만 허용한다.
현재 권리로 DB가 확인한 사건의 최초 기록 UTC/attempt와 원 signed HEAD를 선택한다.
선택자는 publication_sequence/head_sha256/proof_sha256의 닫힌 집합이며 bool·불명확한 숫자·추가 필드를 거부한다.
summary는 최신 확인 사건, samples/events는 명시 선택자에 결속한다.
서버 내부 witness로 후검사하며 외부 payload로 witness를 재구성하지 않는다.

원108상태·41연속/6사건 장부·15수지·PAR/NIR·관리 전후 진단·provenance·literal 승인 False와 UTC를 보존한다.
sample/event 페이지는 기존64/8개·2MiB 한도를 유지하며 원 offset/total/끝 빈 배열을 검사한다.
서명했어도 DB에서 미확정인 HEAD는 공개 구간으로 채택하지 않는다.
정상 append/heartbeat 중에도 선택 사건·이전 latest·관측 HEAD와 현재 signed ancestry를 대사한 경우만 같은 원 페이지를 반환한다.
취소/종료/attempt/token/input 변경은 재조회로 처리하고, rollback/fork/삭제·변조·권리 철회는 차단한다.
none/closed에는 수치나 미래 프레임이 없다. 내부 응답은 공개 API의 원 입력/권리/경로 표시 허가가 아니다.

## 수용 기준

1. 실제 SCRAM의 미시작/ready/running·정상/수치 hold·취소에서 선택/원량/UTC/최초 시각·빈/끝·범위 오류를 확인한다.
2. 실제 독립 append/heartbeat·private HEAD와 DB 확인의 전진 후에도 이전 선택자의 원 sample/event가 같아야 한다.
3. 현재/직렬화 뒤 권리·선택/이력/서명/페이지·provenance/승인·job 변경을 검사하고 계산/복원/checkpoint 확정/SQL 변경0을 확인한다.
4. 같은 DB/키/파일을 별도 fresh 프로세스에서 읽어 원 바이트·시각을 대사한다.
   기존5root/동적 자식·원본2,148항목·두 서비스/키/역할·512MiB/PID/합1GiB·FD/소유 정리를 유지한다.

다음은 별도 닫힌 공개 투영/후검사→접수/진행/취소·prefix 보호 HTTP/명시 runtime→typed 웹/같은 UTC3D→사용자 적용·재접속/재시작이다.
각 자식의 수용 전에는 부모를 완료하지 않는다. 합성32초 범위이며 실제 작기/독립 자료/G0–G4·예측/추천·전체 완료 날짜는 별도다.
