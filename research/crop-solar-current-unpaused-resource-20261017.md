# 현재 reader 이후 독립 동시 실행 관측 — 2026-10-17

[기계 증거](artifacts/crop-solar-current-unpaused-resource-20261017.json) ·
[호스팅 저장3D 수용](crop-solar-current-webgl-verification-20261017.md) ·
[기존 runtime 수용 계약](../contracts/crop-greenhouse-solar-execution-runtime-v1.md).

6004735의 현재 조회 연결306→186/동시2→1과 실제 SDK/호스팅 저장3D 수용을 근거로
현재 source에서 기존 정상64걸음 prototype을 한 번 실행했다. 기존 API/worker 생성 원문과
중단 장벽 없는 worker·원 입력/청크/조회 주기를 유지했다. 부모에 PID/identity/hash 관찰만 더했다.
제품 코드나 계수·권리·검증·자원 한도를 바꾸지 않았다.

30.502초에 합 RSS1,075,159,040bytes로 중단됐다. 단일 최고137,015,296bytes이며
normal 완료 proof는 없다. 중단 뒤 부모의 worker 상태 단언은 이 종료에 따른 것이며
별도 수치 모델 결함으로 분류하지 않는다. **정상 동시 실행/S3는 미수용**이다.

같은 최고 합 표본의 소유 주체를 관찰 identity와 대사했다.

| 주체 | RSS bytes |
| --- | ---: |
| configured API |116,858,880|
| 독립 worker |83,562,496|
| 시험 대기 부모 Python |22,401,024|
| 자원 감독 |28,385,280|

이 표본의 차이가 이후 실행에 필요한 여유량이나 최고 사용량의 상한은 아니다.
현재 원5root/동적 자식·원2,148항목/기존 source·자산/두 UI를 보존했다.
FD4→4·소유 비좀비/PG/임시 PG/passfile0으로 종료했다. 숨은 재시도는 없다.

다음 작은 변경은 [시험 대기 부모 교체](../contracts/crop-solar-unpaused-probe-parent-v1.md)다.
API/worker 프로그램을 고정한 뒤 부모의 불필요한 Python 대기 보유를 줄이는 시험 실행기 변경만
허용한다. 기존 SDK의 대기 부모 exec 분리 경험과 이번22.4MB 관측이 근거이며 성공을 보장하지 않는다.
supervisor/worker dispatcher·수식·검증기를 재설계하거나 기존 서비스를 종료하지 않는다.

호스팅 정상/hold 저장3D 기능은 수용 상태를 유지한다. 로컬 브라우저 동시 용량·S2b/부모·
독립 정상/hold/취소·실행 중3D/사용자 적용과 제품 관문/외부 자료는 별도 미완료다.
새 근거 없이 같은 조건을 반복하지 않으며 전체 완료일·남은 집중시간은 미정이다.
실제 농장 Run0/G0–G4 미평가/승인False·전체 goal active다.

진행 feed를 `2026-10-17T10:52:25.036312Z`로 게시했다. parser28개·실제 두 UI의
200/no-store·동일 원문·기존 HTML/환기2,173파일·원5root/원본/FD4→4·소유 정리를 확인했다.
