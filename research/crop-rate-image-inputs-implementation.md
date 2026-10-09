# 작물 유량 프로필·고지 이미지 포함 — 2026-10-04

상태: **필수 입력/제3자 고지 패키징의 실제 이미지 수용**.
고정 운영 기반에 대한 새 조립 기능이 아니라 새 작물 모듈의 실제 파일 의존성을
보완했다. 수용 판본은 `207e20e6a99533bd0419cfa24ba8e3dec8f6d3d0`이다.

## 필요한 변경과 결과

기존 `.dockerignore`는 새 참조 프로필과 GreenLight 고지를 build context에서
제외했다. 프로필 없이 새 모듈을 실행할 수 없고 원 고지를 함께 배포해야 하므로
다음 3파일을 변경했다.

- `.dockerignore`: 참조 프로필 1개와 원 고지 1개를 명시적으로 허용한다.
- `backend/Dockerfile`: 해당 원 고지를 backend 이미지에 복사한다.
- `scripts/check-application-images.py`: 실제 context와 비특권/읽기 전용 이미지에서
  kernel import·정확한 프로필 바이트 로드·고지 해시를 검사한다. 참조 시험 사례와
  관련 없는 고지/fixture·기존 private probe는 제외한다.

이미지 검사 코드·Dockerfile·허용 목록의 해시와 actual workflow/job/step,
원 로그 해시는 [기계 판독 증거](artifacts/crop-rate-image-ci-20261004.json)에 기록했다.
profile/고지의 해시는 원 모듈과 고정 출처의 값이며 제품 데이터 G0를 발급하지 않는다.

## 실제 검증

[Application runtime verification 37194520191](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37194520191)의
`images` job `111413494194`는 2026-10-04 10:10:46~10:17:32 UTC에 완료됐고
모든 단계가 성공했다. **실제 Docker build/context·이미지 실행**에서 아래를 확인했다.

1. context 4회 각각 관련 없는 probe **13개** 제외, 필요한 프로필/고지 포함,
   독립 참조 사례 파일 제외.
2. backend UID/GID 11001/11010·읽기 전용·닫힌 기동, crop module import,
   `ReferenceParameters`의 고정 profile 해시 검사와 고지 해시 일치.
3. 기존 web TLS/프록시와 baseline·collection·authority Compose의 각각 독립 실행,
   같은 완료 결과/보류의 재시작 조회·현재 권한 변경 차단.
4. 첫 image check의 임시 파일/컨테이너/태그 정리와 Compose 세 모드의 정리 모두 성공.

원 로그는 49,840바이트이고 SHA-256은
`dbc06d5873952d2987223d91d5a87426c77286ff49cdfef36f3e23e22e49873c`다.
로그의 전체 민감 가능 출력을 저장소에 복사하지 않고 선택한 검증 이름·정리/해시를
기록했다. 로컬은 Docker Engine이 없으므로 hosted 실제 검사로 수용했다.

## 범위와 남은 hold

이 수용은 작물 유량 코드의 입력/라이선스 패키징이다. 새 전체 backend CI는
아직 terminal 결과를 확인하지 않았다. 결합된 실제 원천 경로·제품 CLI·독립 해제,
전체 G1/국내 G2/미래 G3a/대응 비교 G3b/공개 G4는 남아 있다.
다음 핵심 작업은 [적용 영역 정책](crop-photosynthesis-domain.md) 뒤 시간 적분이다.
