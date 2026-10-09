# 소유 프로세스 pidfd 호환 수정 — 2026-10-09

19:30 KST, core2847588. [core3 계약](../contracts/owned-research-pidfd-compatibility-v1.md)과
[원 실행·배포본·해시·자원 증거](artifacts/owned-research-pidfd-compatibility-reference-20261009.json).
native Codex CLI `gpt-6.1-sol`/`xhigh`, 재귀 CLI0이다.

## 변경과 검증

원 Backend37892105708 분할3의10실패는 uv Python3.12.13에 두 Python pidfd 함수가 없는 경우다.
기존3.12.3에는 둘 다 있다. Python 함수가 없으면 실제 libc의 두 pidfd 심벌을 지연 로드한다.
표준 ctypes만 사용하며 원 identity/보호 tree·신호 직전 재검사·finally fd close를 유지한다.
숫자 PID 신호로 fallback하거나 실패를 무시하지 않는다. 근거와 ABI/문서 차이는 계약에 기록했다.

- 원87572 종료1: 정확한 uv3.12.13의 기존10실패를 재현했다.
- 최종 원85784/61087 종료0: uv3.12.13/기존3.12.3에서 각각 **30개(기존10/새20)**가 통과했다.
  중간 원15329/35374의27개 통과는 별도 보존한다. 최종 원 실행은1.164/1.391초다.
- 실제 일반/스레드 child·고아/보호 descendant·부모 종료, stale/변경 identity·실패/거부·fd close,
  강제 libc 실제 pidfd/signal0/CLOEXEC와 보호 tree 생존을 대사했다.
  ESRCH/EPERM/ENOSYS 반환을 주입한 실제 소유 fd의 닫힘·대상 생존/재시도0도 확인했다.
- 두 배포본의 별도 실제 자기 pidfd/signal0·CLOEXEC는 모두 FD4→4다.
  현재 glibc2.39에서 uv는 libc 경로, 기존 Python은 원 경로를 선택했다.
- Python 우선·한쪽/양쪽 함수 부재, libc 심벌/로드 부재·errno 하위 오류형·NULL info/flags0·
  import 무부작용을 확인했다. AST 대사는 소유/보호 알고리즘과 신호 호출 두 곳 외 본문이 같음을 확인했다.
- 별도 root 감사 원0e0ad4 종료0·소유 자식/임시 정리·frontend200,
  source1,618개/원 입력·key/권리·기존 미리보기·진행 중 전체 writer의 고정 source를 보존했다.
  현재 main helper SHA는0337a287…이며 실행 중 고정 helper의 기존5839d2ab…는 바꾸지 않았다.
- 0.25초20표본의 단일/관측 합 RSS137,854,976/599,834,624bytes로512MiB/1GiB 안이다.
  지정 controller/소유 자식·보호 미리보기/전체 writer/PG 범위이며 WSL 전체·운영 용량 수용은 아니다.

## 후속

확인된 두 CI 결함의 로컬 수정이 준비됐다. 같은 수정판의 hosted 분할3/5·전체 CI는 아직 미수용이다.
기존 CI가 모두 terminal인 것을 확인했으며, 로컬 수용 문서/코드 고정 뒤 수정판을 push해 회귀를 평가한다.
새 감독자는 수정된 main helper의 해시를 사용하거나 명시 고정 helper를 선택해야 한다.
종료된 구형 private controller의 main helper 고정 SHA를 무단 변경해 재사용하지 않는다.

정상 전체 수확 writer는 계속 실행 중이다. 등록/독립 Decimal/인증 보존/fresh·최종 정리 뒤
같은 결과의 보호 API/대표3D를 진행한다. U3·실제 품종/농장 Run/독립 자료·G0–G4/생산/미래 마진/추천은 보류다.
