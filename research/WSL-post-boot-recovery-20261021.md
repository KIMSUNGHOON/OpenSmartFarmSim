# WSL 재시작 후 기존 사용자 화면 복구 — 2026-10-21

[원 검증 증거](artifacts/WSL-post-boot-recovery-20261021.json). Goal active로 재개했다.
http://localhost:5173/ 와 http://localhost:5174/#ventilation-execution 및 보호5root를 복구했다.
현재 실행은 legacy run-v35, joint serve-v31, ventilation serve-v17이다.
기존 모델·DB/입력·HMAC 키·같은 토큰·원2148항목/동결 source2173파일·두 HTML을 보존했다.
TLS 인증서와 인증 기간은 기존 조립의 재기동 경로에서 새로 발급했다.

처음 새 DB 복제의 initdb가 disk sync에서60초를 넘었다. 기존 물리 DB를 보존한 채 사용했고,
그 DB의 비정상 종료 복구도10초 시작/종료 대기를 넘었다. 종료 요청 뒤 살아 있는 같은
postmaster6731의 fsync/자동 복구와 정상 종료를 실제 관측했다. 관측 timeout만으로 재실행하지 않았다.
정상 종료 뒤 기존 물리 DB를 다시 기동했다. 준비된 nginx의 읽기 전용 파일은 원 config를
원자 교체해 복구했고 살아 있는 legacy는 재시작하지 않았다. 공동 DB의 낡은 nested PID 대신
이전 boot의 실제 보호 root와 PID 파일을 대사했다. 실패/수정은 private 기록에 보존했다.

최종 인증 조회는 legacy8본문, joint 실제 HTTPS/SCRAM·원 입력3/저장9시점,
환기 정상/보류8본문이다. 원 값/UTC(관측 시각 제외)·현재 권리·같은 토큰/키를 확인했다.
환기는 실제 UI proxy와 검증 TLS CA/호스트/시각을 대사했고 조회/쓰기 hooks0·FD8→8이다.
각 guard는 원600초/512MiB PID/합1GiB/0.25초를 지켰고 FD4→4·원 자료/5root·소유 정리0을 확인했다.
이전 종료된 프로세스의 PID를 종료 대상으로 재사용하지 않았다.

화면/모델 소스는 그대로여서 새 브라우저/WebGL·전체 CI를 재실행하지 않았다.
기존 합성166일 재생/짧은 환기 모델의 복구이며 새 CO₂·전체 작기/생산/경제·최종 UI·실제 농장/관문은 미완료다.
다음은 별도의 CO₂ 실제 HTTP core6→fences8→runtime/같은 UTC3D다.
