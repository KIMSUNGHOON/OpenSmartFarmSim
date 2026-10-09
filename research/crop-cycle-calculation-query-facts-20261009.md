# 현재 계산 조회의 사실 묶음 수용 — 2026-10-09

[작은 계약](../contracts/crop-cycle-calculation-query-facts-v1.md)에 따라 summary/context/identity의
세 사본을 한 번의 기존 전체 검증으로 묶었다. 기존 개별 getter/page·현재 farm/권리/서명 전후 검사는 유지한다.
파일 metadata나 권한 cache는 추가하지 않았다. 실제 native Codex CLI `gpt-6.1-sol`/`xhigh`에서
판단·invocation 문맥/출력 hash를 기록했고 재귀 CLI0이다.

[원 종료·비용·자원·hash](artifacts/crop-cycle-calculation-query-facts-reference-20261009.json)를 보존했다.
코드는 격리 branch `perf/calculation-query-facts-20261009`의 `fedd8e72ed37701f20ccec8ca92df18353a10b75`다.
**main 런타임 소스 통합·현재 미리보기 배포는 아직 없다.** 기존 미리보기는 main 파일의 hash를 검사하므로
그 소스를 보존하는 기동 전환 전까지 격리 판본을 사용한다. 원 모델/증명/서명/입력/artifact는 바꾸지 않았다.

## 실제 검증

- 원94236 실제 종료1: facts 메서드가 없는 RED1개를 확인했다.
- 새8개/기존 read context49개는 원5950 도구0·57통과/100.82초다.
  정상/수치 hold·원 속성과 모든 값 동일·사본 독립성·전체 검증1회·입력/HEAD/page/authority·반환 직전 변조 거부를 확인했다.
- 기존 실제 SCRAM/current query12개는 원82227 도구0·12통과/470.67초다.
  현재 scope/tenant/권리·DB 서명/열·custody trace/입력/늦은 철회·fork·관리 사건/수치 hold를 포함한다.
  schema/role/passfile0·소유 PG 종료/임시 정리까지 통과했다. 고유 시험은69개다.
- 앞선 원26405는12개 fixture setup 오류/실제 pg_ctl 종료1로 실패했고 PG 관측0이다.
  socket 디렉터리 경로131bytes를 확인해 소유 TMPDIR만 짧게 바꿨다. 제품/시험 소스를 바꾸지 않고 이후 통과했다.
  원 서버 로그는 임시 정리로 남지 않았으므로 길이 제한을 원 오류의 직접 로그로 증명한 것은 아니다.
- 복원한 실제 전체 부모에서 원61642 도구0/65.767초: 동일5요청·원 record/최초 시각·대표129sample/5event의
  원 페이지 bytes/hash·수치/UTC·권리/scope/다른 tenant 거부와 복원을 확인했다.
  기존 전체 행 대사를 대표 페이지 대사로 대체하지 않는다. 조회 RHS/행 생성/게시/proof0·FD4→4다.
- 별도 원14795 도구0/11.995초에서 실제 summary 검증 횟수도 확인했다.
  두 소스의 기존 `_current`/page 및 다른 기존 메서드 AST는 같다. current query `open`만 사실 읽기를 바꿨다.

## 같은 전체 부모·요청의 비용

| 요청 | 이전초 | 수정초 |
| --- | ---: | ---: |
| summary | 7.384 | 6.369 |
| 첫64sample | 8.383 | 7.497 |
| 다음64sample | 8.311 | 7.537 |
| 마지막1sample | 7.926 | 6.918 |
| 5event | 8.070 | 7.092 |
| 합계 | 40.074 | 35.413 |

이 다섯 관측의 합은11.63% 감소했고 각 요청은9.31–13.74% 감소했다. 일반 지연 보장은 아니다.
실제 cProfile의 result snapshot은 summary8→6/sample64의9→7,
input verify16→12/18→14다. 현재 farm registration4→4·DB 연결345→345·현재 전후 검사2→2는 보존했다.
연결 반복과 남은 전체 snapshot 비용은 아직 남아 있으며 전체 writer의 실행 예산을 확정하지 않았다.

source/원 입력/artifact/backup·기존 preview dist/identity와 소유 정리를 확인했다.
0.05초 관측에서 native 단일130,433,024bytes/합571,584,512bytes,
동시 summary profile이 두 시험·PG·미리보기 tree를 포함한 합689,782,784bytes다.
512MiB/1GiB 이하이며 WSL 전체나 일반 운영 용량의 수용은 아니다. 관측 PID는 종료 권한을 만들지 않는다.

## 다음 사용자 산출물과 남은 범위

완료한 전체 생장 부모를 **기존 보호 API와 성장3D에서 확인하는 작은 경로**를 다음으로 분리한다.
새 수확이 없으면 미등록 상태를 표시하고 기존 다른 수확 결과를 붙이지 않는다.
실제 같은 DB/서명 부모·대표 첫/마지막/관리 사건 UTC와 3D C/N/LAI·원량,
현재 권리·계정·읽기 계산0·실제 HTTPS bytes/시간·WSL/소유 정리가 수용 기준이다.
기존 `localhost:5173`은 이 수용/기동 전환 전까지 별도 작은 저장 예제를 유지한다.

전체 수확 writer/registry·독립 Decimal 모든 저장 행·수확 인증 보존/fresh reader/API3D는 계속 미수용이다.
현재 연결을 위한 보호 API/대표 frame 조립·검증·기동 전환은 기존 빌드/factory 재사용 조건의1–3집중시간 잠정이다.
조립/자원 거부가 있으면 실측 뒤 갱신한다. 전체 수확·UI U1/U3·기후/자원/경제 완료일은 아니다.

Backend37892105708의 분할3은10실패/1,073통과로 종료했다.
모두 소유 process helper의 `Linux pidfd support is required` 진입 실패다.
같은 uv Python3.12.13의 두 Python pidfd 함수 부재를 로컬 확인했고,
libc의 두 함수로 **자기 process의 실제 pidfd open/signal0/FD5→5**는 통과했다.
이것은 호환 수정의 근거이며 helper 수정/보호 tree 시험/hosted 전체 수용은 아직 없다.
숫자 PID signal fallback이나 시험 생략으로 바꾸지 않는다.
분할5/113695105991은1실패/907통과로 종료했다. 기존 수확 operator/fresh Python 시험의
`authenticated_endpoint_sha256` 대사 실패이며 구형 역할 정리 교착과 같은 원인으로 취급하지 않는다.
원 실제 endpoint 문맥과 예상값을 좁힌 뒤 필요한 작은 수정으로 이어간다. 분할4는17:08 KST 실제 실행 중이다.

실제 농장 작물 Run/국내 독립 자료0건·G0–G4 `not_assessed`, 실제 생산/미래 마진/추천 hold를 유지한다.
