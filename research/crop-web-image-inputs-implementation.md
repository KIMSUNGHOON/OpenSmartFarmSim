# 성장 화면 이미지 입력 보완 — 2026-10-04

상태: **로컬 입력 재현·보완 통과, 실제 hosted 이미지 재검사 대기**.
필요한 핵심 기능은 `web-crop-replay`다. 기반 추가의 근거는
`0f3ce74`의 [실제 앱 이미지 실패](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37209918683)다.
동일 판본의 웹 CI와 C0는 성공했지만 앱 이미지는 `npm run build`에서 실패했다.
기존 `d251df9` CI 5개 성공과 성장 화면의 로컬 수용 범위는 유지한다.

기존 Codex CLI 세션의 `gpt-6.1-sol / xhigh`에서 진단·수정했다. 재귀 호출은 없다.
Docker COPY와 허용 목록을 임시 파일 트리로 재현해 RED를 확인했다.
e2e/단위 검사/Vite 설정의 4개 import가 Docker가 복사하지 않는 `web/demo/crop-reference`
파일을 요구했다. `.dockerignore`는 새 디자인 자산 9개도 제외했다.
로컬 전체 소스 build는 이 포장 입력 누락을 검출하지 못했다.

## 최소 변경과 검증

고정 공개 시험 응답을 기존에 복사하는 `web/e2e/crop-fixture.ts`로 이동하고
import 5개만 바꿨다. fixture bytes는 `0f3ce74`의 기존 파일과 같다.
Dockerfile의 target·COPY 범위와 일반 production entry는 바꾸지 않았다.
자산 9개는 정확한 파일명으로만 허용했다. 기존 이미지 검사에 자산/fixture 해시,
개발 데모 디렉터리 제외, 추가 private/미선언 asset 제외 probe 4개와
최종 정적 JS의 데모 토큰 비포함 검사를 연결했다.

[수정 증거](artifacts/crop-web-image-inputs-reference-20261004.json)는 실제 실패 로그 hash,
로컬 RED→GREEN, 현재 파일 hash와 원 fixture bytes의 동일성을 남긴다.
Docker COPY를 재현한 GREEN build는 1.28초에 통과했다. 개발 demo 폴더를 포함하지
않고도 typecheck/build가 성공하고 production JS의 고정 응답/데모 토큰이 없다.
이동 후 웹 단위 **209 passed**와 이미지 검사 Python 구문 검사를 통과했다.
이 로컬 검사에서는 Docker Engine을 시작하지 않았다.

실제 hosted 수용은 기존 앱 이미지 CI에서 실제 export context의 17개 제외 probe,
9개 자산/fixture hash·두 앱 image build·비특권/읽기 전용·표준 TLS/잘못된 DNS 거부·
정리가 통과한 뒤 기록한다. 로컬 파일 트리 모사를 실제 Docker 증거로 제시하지 않는다.
계산 엔진/생장 값·데모 응답·G0–G4는 바꾸지 않았다.

앞선 [성장 화면 증거](artifacts/web-crop-replay-reference-20261004.json)의 code hash는
`0f3ce74`에 남긴 당시 경로/bytes다. 해당 JSON은 수정하지 않는다. 이 후속 판본에서
경로와 import가 바뀐 파일은 새 기록의 hash로 대사한다.
