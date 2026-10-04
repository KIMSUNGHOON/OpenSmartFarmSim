# 50구획 저장 결과의 웹 페이지 조립 수용

2026-10-05 KST. [계약](../contracts/web-crop-coupled-pages-v1.md),
[실제 영수증/코드 해시](artifacts/web-crop-coupled-pages-reference-20261005.json).
현재 CLI turn(2026-10-04T22:05:49.804Z)에서 gpt-6.1-sol / xhigh를 확인하고
구현·설계했으며 재귀 CLI는 실행하지 않았다. 새 UI/장면이나 현장 자료 수용은 아니다.

## 변경과 검증

새 `coupledCropReplay.ts`와 집중 시험, 기존 `api.ts`의 선택 메서드/AbortSignal을 연결했다.
기존 메모리 Bearer·동일 origin/no-store/redirect 거부·30초 전체 요청 제한을 유지한다.
새 읽기는 2 MiB이며 닫힌 50개 N/C·단위·프로필/코드/solver·불변 해시·연구 범위를 검사한다.
마이크로초 BigInt로 UTC를 비교해 정수 초와 .000001Z hold를 구분한다.
마지막 확인 상태는 별도 진단이며 정상 sample에 추가하지 않는다.

512 sample의 최대 8개 페이지를 순차 읽고 ID/farm/저장 UTC·전체 manifest/hold·총수와
offset/next_offset·순서·시작/끝을 대사한다. 조립 완료 전에는 결과를 반환하지 않는다.
첫 event 페이지만 보존하고 나머지 sample 읽기는 event_offset=total로 반복 사건 payload를
피한다. 추가 사건 읽기는 sample_offset=total이며 기존 sample을 변경하지 않는다.
원 수치/단위를 보존하고 생장식·수지·미래 상태를 계산하지 않는다.

선행/실행 중/페이지 사이 취소·뒤늦은 성공 응답은 결과를 만들지 않는다.
취소된 뒤 받은 body도 cancel하고 Abort listener/타이머를 제거한다.
50배열·scope/모델/단위·달력/순서·혼합/누락/중복, 과거/빈 hold,
2 MiB+1/UTF-8 거부·권리 철회·30초와 listener 정리를 검증했다.

실제 RED는 새 모듈 부재의 Vitest exit 1이었다. 첫 133개 통과 뒤 늦은 body 취소와
UTF-8/두 번째 페이지 철회 반례를 보완해 **최종 135 passed/0 failed**를 확인했다.
새 페이지 시험 73개, 기존 request 26개·작물 v1 36개다. 단일 worker로 실행했다.

```bash
cd web
nice -n 10 npm test -- --maxWorkers=1 src/coupledCropReplay.test.ts src/api.test.ts src/cropReplay.test.ts
npm run typecheck
nice -n 10 npm run build
```

이전 실제 SCRAM/TLS 검증의 공개 합성 응답 13개를 새 decoder에 대사하는 별도 시험
**1개**도 통과했다. 원 8페이지/512 sample·각 50개 N/C·단위/UTC/manifest를 그대로
보존했다. 새 조립 방식에는 이후 페이지의 반복 사건을 이미 기록된 빈 마지막 사건
페이지로 교체하는 adapter를 사용했다. 원 sample/공통 metadata는 변경하지 않았다.
이는 기록된 bytes 재생이며 새 실제 HTTPS 요청이나 브라우저 시험이 아니다.
임시 시험은 실행 뒤 제거했고 원문·credentials·원 프로그램은 공개하지 않았다.

타입 검사와 Vite build도 통과했다. 기존 lazy ECharts installSVGRenderer 518.53 kB의
500 kB 경고는 남아 있으며 숨기거나 chunk 정책을 변경하지 않았다.
한 Vitest worker를 순차 사용했고 DB·브라우저·Docker나 새 패키지를 시작/설치하지 않았다.

## 다음 경계

다음은 `web-crop-coupled-geometry`의 잎 면적·50개 C/N 별도 공통 scale 도형이다.
그 뒤 기존 화면의 선택/표/그래프·취소와 과거 hold를 연결하고 12ui-design의 기존
디자인 정합 및 실제 저장→TLS→브라우저 대사를 검증한다.
이번에는 스킬을 읽어 준비했고 새 디자인 생성/화면 또는 브라우저 수용은 수행하지 않았다.
부모 `web-crop-coupled-replay`는 체크하지 않는다. G0–G4와 국내 자료 0건·실제 forcing/
Run 0개·전체 작기/startup·생과·자원/경제 보류는 그대로다.
