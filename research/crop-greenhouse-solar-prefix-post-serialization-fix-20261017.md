# 일사 확정 페이지의 직렬화 후 재검사 보완 — 2026-10-17

[기계 증거](artifacts/crop-greenhouse-solar-prefix-post-serialization-fix-20261017.json).

공개 투영 준비 중, 원 구간 조회 후 선택한 sample 파일을 실제로 바꿔도 `_after_projection`이 통과하는 경우를 재현했다. 기존 후검사는 현재 권리·DB 묶음·signed HEAD 계보를 확인했으며, 같은 HEAD의 선택 페이지를 다시 읽지 않았다. 원본 응답은 기존 검증 값이지만 현재 파일 변조 차단 조건이 부족했다.

선택한 원 signed snapshot/page를 다시 로드하고 원 selection/binding/manifest/time/summary/page와 대사하도록 보완했다. 현재 권리·owner witness·정상 append/heartbeat 검사는 유지하며 계산·복원·확정·SQL 변경을 추가하지 않는다.

실제 SCRAM 시험87746에서 DID NOT RAISE로 RED(종료1), 수정 뒤35940에서1검사 GREEN(종료0)이다. 변조 차단·원 파일 복원 뒤 정상 후검사·수치/SQL 변경0을 확인했다.5root/동적 자식·원본2,148/두 서비스·FD4→4·소유 프로세스/PG/임시 PG/passfile0·512MiB/PID/합1GiB를 보존했다. 성공 관측 합1,017,700,352bytes다. 시험은 합성 입력이며 실제 농장 Run0/G0–G4 미평가/승인 False다.

공개 응답 형식·직렬화 race/현재 권리·독립 fresh·보호 HTTP/runtime·같은 UTC3D와 사용자 수용은 다음 작업이다. 전체 CI/DOM/WebGL는 재실행하지 않았고 goal은 active다.
