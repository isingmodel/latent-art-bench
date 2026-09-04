# 생성모델은 실제 화가의 회화 특징분포를 재현하는가?

Painter Feature Generation v1 연구계획·자료수집·현재결과 통합보고서

- 정본 protocol ID: `painter-feature-generation-v1/2.1` (2026-09-04 발행, 14절).
  본문 1~12절은 2.0 기준으로 작성된 기록이며, 2.0 텍스트는 `PROTOCOL.md`에 동결 보존된다.
- 관찰 기준일: 2026-09-02 (13·14절은 2026-09-04 보완)
- 대상 화가: Claude Monet, Alfred Sisley, Camille Pissarro, Paul Cézanne
- 현재 단계: 고정 seed, broad 발견 census, broad media R2 후속검증, AIC route 완료;
  나머지 R0 및 이미지 취득은 `NO-GO`. Protocol 2.1 발행으로 결정 완료(14절)
- 생성–실제 비교결과: 없음
- 검토 주체: 본문에서 "중립 독립 검토"로 부르는 모든 검토는 유지관리자 1인이 실행한 LLM
  검토 서브에이전트의 산출물이다(13.1절)

## 1. 핵심 결론

이 연구의 질문은 “생성 이미지를 보고 화가를 분류할 수 있는가?”가 아니다. 정확한 질문은
다음과 같다.

> 하나의 정확히 동결된 생성모델에서, 같은 야외 장소 내용과 같은 seed 구조를 사용했을
> 때, 화가 이름을 넣은 생성 이미지의 색채·공간/방향·디지털 질감 특징분포가 그 화가의
> 권위기록상 진작으로 확인된 실작품 디지털 재현본의 특징분포를 재현하는가?

이 질문을 위해 Protocol 2.0은 다음 원칙을 고정했다.

1. 화가 분류 정확도 대신 생성–실제 **분포거리**를 직접 비교한다.
2. 네 화가가 공통으로 충분히 보유한 야외 장소 장면만 비교한다.
3. 파일 수가 아니라 물리 작품 수를 센다. 같은 작품의 crop·mirror·re-encode는 새 작품이
   아니다.
4. 색채, 공간/방향, 디지털 질감의 세 family가 모두 사전 검증을 통과해야 한다.
5. 생성물이 주제에서 벗어나도 유리한 셀로 옮기거나 버리지 않는다.
6. 특정 실작품의 복제는 “화가 특징 재현”의 성공으로 세지 않는다.
7. 데이터가 부족하면 표본 기준을 낮추지 않고 연구를 중단하거나 새 protocol을 만든다.

이번 작업에서 실제로 완료한 것은 고정된 Wikidata/Commons seed의 현재 메타데이터
전수추적과, material 필드 누락을 허용하는 별도의 broad no-`P186` 발견 census다. 고정 seed의
165개 요청이 모두 성공했고 3,367개 item–file 행을 현재 상태로 확인했다.
그중 2,029행, 1,967개 distinct Wikidata item ID, 2,028개 distinct Commons filename이
메타데이터 후보 관문을 통과했다. broad census는 4개 화가별 질의를 모두 완결하여 3,722행,
3,543개 distinct item ID, 3,718개 distinct filename을 발견했다. 이어진 broad-media R2는
이 전체 frame의 182개 entity/media batch를 모두 완결했고, 3,722행 중 2,029행(1,967 distinct
item ID)을 현재 메타데이터 관문 후보로 판정했다. named source route 중 첫 기관 경로인 AIC도
완결했다. R1은 string `classification_id`에서 fail-closed로 종료했고, 새 census ID의 R2가 4개
요청을 모두 성공해 153행을 게시했으며 그중 57행이 authority와 media screen을 함께 통과했다.
그러나 어느 수치도 아직 물리 작품 수가 아니다. 권위기관
작품기록 대조, 작품 동일성 통합, 실제 이미지 바이트 취득, 완전한 화면 확인, 맹검 장면
코딩이 남아 있으므로 active-study 입장 작품은 0점이다.

## 2. 이전 설계의 핵심 오류와 수정

### 2.1 폐기한 접근

이전 계획은 화가별 360점의 동일 quota, 24개 prompt 선택, 고차원 content entropy
weighting, 내부/외부 표본의 과도한 분할에 의존했다. 다음 이유로 폐기했다.

- 좁은 장면에서 네 화가의 실제 자료량이 같다는 근거가 없었다.
- 수집 가능한 만큼만 채운 동일 quota는 화가별 source 차이를 숨길 수 있다.
- 생성 결과나 active label을 본 뒤 prompt/가중치를 선택할 여지가 컸다.
- 복잡한 가중치가 실질적인 공통 지지집합 부족을 감췄다.
- “많은 파일”과 “많은 물리 작품”을 혼동했다.

### 2.2 Protocol 2.0의 대체안

- 실제로 남는 unequal finite population을 그대로 사용한다.
- 네 화가 모두 confirmation 작품 20점 이상을 갖는 broad scene group을 전부 유지하며,
  최소 세 장면이 없으면 중단한다.
- 각 유지 장면에 동일 질량 `1/G`, 장면 안 각 작품에 `1/(G n_as)`를 준다.
- historical pixel/feature-exposed 작품은 development-only다.
- 새 작품은 painter × scene × workflow 안에서 고정 hash rank로 development 20%,
  qualification 20%, confirmation 60%에 한 번만 배정한다.
- 모든 화가×장면×workflow에 새 development 10점, qualification 10점, confirmation 20점의
  최소 지지를 요구한다.

## 3. 문헌 검토에서 가져온 방법적 교훈

문헌 패키지는 205개 bibliography entry와 144개 구조화 evidence-matrix row를 포함한다.
문헌 수 자체가 타당성을 보증하지 않으므로, 아래처럼 실제 설계 결정에 연결되는 결과만
사용했다.

### 3.1 Kim 연구

Kim 계열 연구는 대규모 회화 자료에서 multi-scale color organization과 고차원 A/C
표현이 시대·화가 label과 관련된 신호를 갖는다는 근거를 제공했다. 최신 A/C 분석은
72,447점, 2,354명 화가의 16,384차원 표현을 사용한다. 그러나 A는 색·구도·내용이 섞이고,
C는 고차원 local texture 통계이므로 “생성물이 실작품 분포와 동등하다”는 검증법 자체는
아니다.

따라서 본 연구는 Kim A/C를 진단용으로만 남기고, 해석 가능한 31개 좌표의 세 primary
family를 사용한다. 이는 Kim의 다중척도 통찰은 수용하되, label 분류 성능을 화가 특징
재현으로 오인하지 않기 위한 결정이다.

### 3.2 생성 이미지 평가 문헌

FID/KID, precision–recall, CLIP, CSD, ALADIN, ArtFID 계열은 fidelity, diversity, semantic
alignment, style signal을 서로 다르게 측정한다. 단일 점수는 다음 문제를 동시에 해결하지
못한다.

- 평균은 비슷하지만 분산과 mode가 다른 경우
- 한 특정 작품을 복제해 거리가 작아진 경우
- 화가보다 촬영기관·색관리·crop을 학습한 경우
- 주제가 달라서 생긴 특징 차이를 style 차이로 읽는 경우

따라서 learned metric은 보조 진단이며, primary decision은 prespecified image-statistic
family별 energy distance, coordinate shift, 장면별 적합성, wrong-painter specificity,
artist-free control improvement를 결합한다.

### 3.3 디지털 재현본과 source confounding

동일 회화도 촬영, 스캔, white balance, ICC profile, crop, 압축에 따라 측정값이 변한다.
그러므로 본 연구가 측정하는 것은 캔버스의 물리적 붓질이 아니라 **규정된 digital
surrogate pipeline에서의 영상 특징**이다. 화가마다 한 기관만 사용하면 painter와 source를
분리할 수 없으므로 화가별 두 개 이상 authority/capture workflow와 연결된 source graph가
필수다.

## 4. 목표 모집단과 자료 단위

### 4.1 포함 대상

권위기관 기록에서 다음이 모두 확인돼야 한다.

- Monet, Sisley, Pissarro, Cézanne 중 한 명의 exact attribution
- object type이 painting
- paint medium이 oil, support가 canvas
- stable object/accession ID
- unresolved attribution/medium conflict 없음
- item-level public domain, CC0, CC BY 또는 CC BY-SA 근거
- 완전한 작품 화면, watermark·과도한 frame·material crop 없음
- JPEG/PNG/TIFF/WebP 완전 decode와 native short side ≥1,024

### 4.2 세 가지 서로 다른 수량

| 단위 | 뜻 | 이번 결과 |
|---|---|---:|
| metadata row | 하나의 item–file 연결 | 3,367 |
| distinct item ID | Wikidata 식별자 | 3,190 |
| admitted physical work | 모든 권위·권리·기술·내용 관문을 통과한 한 회화 | 0 |

위 표의 첫 두 수량은 material-constrained 고정 seed다. 새 broad no-`P186` census의 대응
수량은 각각 3,722행과 3,543 item ID이며, distinct filename은 3,718개다. 두 frame은 서로
더하지 않고 물리 작품 수준에서 대조·통합한다.

`metadata row`나 `filename`을 “수집한 그림”이라고 부르지 않는다. 서로 다른 item ID가 같은
물리 작품을 가리킬 수 있고, 같은 작품에 여러 파일이 있을 수 있다.

### 4.3 source union

전체 R0은 다음 고정 union을 terminal condition까지 추적해야 한다.

1. `P186`을 요구하지 않는 exact-creator Wikidata/Commons painting+image census
2. Europeana exact creator
3. AIC, NGA, Cleveland, Yale, Getty, Minneapolis, Paris Musées API/export
4. POP/Joconde
5. 이번 material-constrained fixed seed

이번 수집은 1번 발견 census와 5번의 현재 상태를 완결했다. 1번의 authority/rights 후속
검증 및 2–4번 source route가 남았으므로 전체 R0은 아직 닫히지 않았다.

## 5. 자료수집 protocol과 실제 실행

### 5.1 고정 seed

사전 보존된 SPARQL 결과에는 다음이 있었다.

- item–file rows: 3,367
- distinct Wikidata items: 3,190
- distinct Commons filenames: 3,364
- painter 조건: 네 painter exact creator
- discovery 조건: painting, P18 image, oil, canvas

이 seed는 `P186` missingness 때문에 전체 작품 frame이 아니다. 현재 attrition을 측정하고
향후 authority/identity reconciliation 후보를 만드는 용도다.

### 5.2 요청 계획

- Wikidata `wbgetentities`: 40 item씩 80 GET
- Commons `imageinfo`: 40 filename씩 85 GET
- 총 165개 exact request intent
- 최소 요청 간격 0.75초
- timeout 60초, 최대 5회 시도
- 429/500/502/503/504와 명시된 API error만 제한적 retry
- redirect, title normalization, member 누락, continuation, schema drift는 fail-closed
- 30초를 넘는 `Retry-After`, 불완전 attempt, 알 수 없는 network outcome은 새 census 필요

모든 시작/종료 event는 앞 event SHA-256을 포함한다. 응답은 content-addressed storage에
보존하고 candidate manifest는 image를 다운로드하거나 연구에 입장시키지 않는다.

### 5.3 첫 실행과 실패 처리

첫 census `pfg-v1-fixed-seed-media-audit-20260902`는 다음과 같이 종료됐다.

- Wikidata 4개 batch 성공
- 5번째 batch HTTP 200
- Q10346982의 `fr` label이 실제로는 영어 fallback이며 provider가
  `language=en, for-language=fr`로 반환
- frozen parser가 이를 malformed label로 잘못 거부
- outcome: `terminal_stage_schema_failure`

실패를 삭제하거나 성공 4개에 나머지를 이어붙이지 않았다. 11-event ledger, 다섯 raw
response, freeze, review, authorization을 그대로 보존했다. parser는 정상 term이면
`language == map key`, fallback이면 `for-language == map key`만 허용하도록 수정했고, 정상
fallback과 잘못된 target을 모두 시험했다.

### 5.4 완전 재실행

새 census `pfg-v1-fixed-seed-media-audit-r2-20260902`는 첫 실행 기록과 terminal raw response
hash까지 새 freeze에 묶었다. 중립적 독립 품질검증은 metadata-only 범위에 차단 이슈가
없다고 승인했다.

| 실행 항목 | 결과 |
|---|---:|
| planned GET | 165 |
| successful GET | 165 |
| first-attempt success | 165 |
| Wikidata batches | 80/80 |
| Commons batches | 85/85 |
| hash-chained events | 331 |
| raw responses | 165 |
| local raw-response volume | 약 51 MiB |
| provider observation window | 07:01:57–07:08:20 UTC |
| downloaded painting image | 0 |

## 6. 고정 seed 수집 결과

### 6.1 단일 관문별 결과

분모는 항상 3,367 item–file row다.

| 확인 항목 | 통과 행 | 비율 |
|---|---:|---:|
| entity resolved | 3,367 | 100.0% |
| Commons media resolved | 3,367 | 100.0% |
| complete delivery receipt | 3,367 | 100.0% |
| supported image MIME | 3,366 | 100.0%에 근접 |
| open-rights marker candidate | 3,295 | 97.9% |
| reported short side ≥1,024 | 2,098 | 62.3% |
| 모든 metadata discovery gate 동시 통과 | 2,029 | 60.3% |

통합 관문은 exact creator, painting, oil+canvas, 현재 exact P18 filename link, open-rights
marker, ≥1,024 short side, supported MIME, complete delivery receipt의 conjunction이다.

### 6.2 화가별 통합 관문

| 화가 | 전체 item–file 행 | 통과 행 | 통과 distinct item ID |
|---|---:|---:|---:|
| Monet | 1,192 | 725 | 699 |
| Sisley | 772 | 303 | 287 |
| Pissarro | 710 | 458 | 451 |
| Cézanne | 693 | 543 | 530 |
| 합계 | 3,367 | 2,029 | 1,967 |

통과한 distinct filename은 2,028개다. 2,029행과 2,028 filename의 차이, 2,029행과 1,967
item ID의 차이는 파일·item·작품을 같은 단위로 세면 안 된다는 사실을 보여준다.

### 6.3 통과 후보의 기술·권리 표지

- short side ≥2,048: 1,249행
- JPEG: 1,986행
- TIFF: 27행
- PNG: 12행
- WebP: 4행
- Public domain 표지: 1,886행
- 나머지: CC BY/CC BY-SA의 여러 version
- authority URL candidate가 있는 행: 1,864
- collection QID가 있는 행: 1,718
- inventory number가 있는 행: 1,580

이 표지는 다음 단계의 조사 우선순위를 제공하지만 권위검증을 대신하지 않는다. Commons의
Public domain 표지나 download URL만으로 exact attribution, medium/support, accession,
complete-view, capture ancestry가 확정되지 않는다.

### 6.4 현재 0인 항목

| 항목 | 수치 |
|---|---:|
| authority-verified physical works | 0 |
| identity-reconciled physical works | 0 |
| active-study downloaded images | 0 |
| masked eligibility derivatives | 0 |
| blind-coded outdoor-place works | 0 |
| development/qualification/confirmation role assignments | 0 |
| sealed confirmation works | 0 |
| feature vectors | 0 |
| generation requests/outputs | 0 |
| generated-versus-real decisions | 0 |

따라서 “2,029점의 좋은 그림을 수집했다”는 서술은 틀리다. 정확한 문장은 “고정 seed의
2,029 item–file metadata rows가 다음 authority/identity/acquisition 검토 대상으로 남았다”다.
AIC route의 57 후보(6.8)도 같은 의미의 별도 denominator이며, 두 수치는 같은 물리 작품을
서술할 수 있으므로 합산하지 않는다.

### 6.5 Broad no-`P186` 발견 census 실행과 결과

고정 seed의 `P186` 조건은 material statement가 없는 작품을 구조적으로 누락한다. 이를
해결하기 위해 다음 네 질의를 화가별로 한 번씩 고정했다.

```sparql
SELECT DISTINCT ?item ?image WHERE {
  ?item wdt:P170 wd:{creator_qid};
        wdt:P31 wd:Q3305213;
        wdt:P18 ?image.
}
ORDER BY STR(?item) STR(?image)
```

이 단계는 정확한 creator, painting instance, 현재 P18만 요구하며 oil/canvas, 권리,
권위기관 귀속, 작품 동일성은 추론하지 않는다. 첫 census R1은 Monet 1,317행을 받은 뒤
Sisley 요청이 HTTP 502 `text/html`로 끝나 전체 census를 terminal incomplete로 닫았다.
Monet 행을 재사용하지 않았고 candidate manifest와 receipt도 만들지 않았다.

R2는 새 census ID와 완전히 분리된 경로를 사용하고 요청 간격만 2초에서 5초로 늘렸다.
R1 config·freeze·review·authorization·5-event ledger·one-shot lock·두 raw response·부재해야
하는 candidate/receipt를 새 retry freeze에 해시로 연결했다. 독립 품질검토 중 두 종류의
검증–실행 경계 결함이 발견돼 승인 전에 수정됐다.

1. 검토된 설정 경로가 실행 직전에 다른 파일을 가리키는 경우를 차단했다.
2. 같은 경로의 파일 바이트가 검토 뒤 바뀌는 경우를 차단했다.
3. 설정, request intents, 결합 승인서, 재시도 승인서는 각각 한 번 읽은 동일 바이트에서
   해시 확인과 파싱을 함께 수행하고, 실행기는 그 메모리 snapshot만 사용한다.
4. 두 회귀검사 모두 network call 0, workspace/event 생성 0을 요구한다.

최종 retry freeze는 21개 입력을 정확히 닫았고, 집중검사 41개와 전체 offline 검사 586개가
통과했다. 독립 검토가 차단사항 없음으로 승인한 뒤 R2를 실행했다.

| 화가 | item–image 행 | distinct item | distinct filename |
|---|---:|---:|---:|
| Monet | 1,317 | 1,257 | 1,314 |
| Sisley | 879 | 812 | 879 |
| Pissarro | 791 | 766 | 790 |
| Cézanne | 735 | 708 | 735 |
| 합계 | 3,722 | 3,543 | 3,718 |

- 네 요청 모두 첫 시도 HTTP 200 및 parser-complete였다.
- hash-chain event는 genesis 1개와 요청별 시작/종료 8개, 총 9개다.
- raw response 4개, 합계 1,163,447 bytes를 content-addressed storage에 보존했다.
- candidate manifest SHA-256은
  `23092232815dd96ab75ad0c8025469ea74f250c5b847b91f080996f11ba83e4e`다.
- image download와 active-study admission은 모두 0이다.

따라서 현재 “발견 후보 규모”는 충분히 커졌지만 “사용 가능한 실작품 코퍼스”는 아직 0이다.
다음 수량은 authority record의 exact attribution·oil-on-canvas·accession, Commons/official
asset의 item-level reuse, native geometry, 완전화면 여부, physical-work/capture 중복을 모두
적용한 뒤에만 산출한다.

### 6.6 Broad media 후속검증 R1: 승인, 실행, terminal 결과

3,722개 broad 행의 현재 Wikidata entity와 Commons media metadata를 전수 후속조회하기 위해
3,543 item을 89개 batch, 3,718 filename을 93개 batch로 나눠 총 182개 GET 의도를
동결했다. 이 단계는 metadata-only이며 image download, visual coding, corpus admission,
feature extraction, generation을 모두 금지했다.

초기 중립 검토는 실제 표본의 대소문자 동률 정렬, CAS 재읽기, 미확정 transport 재시도,
두 결과 파일의 순차 공개, 실행 import 동결 누락, 외부 seal 경로, lock/genesis 순서,
cutoff와 resume, retry class·상한·간격, malformed response 종결성 문제를 발견했다. 각 문제는
네트워크 실행 전에 수정하고 adversarial 회귀검사를 추가했다. 최종 동결본은 18개 입력과
6개 사전 부재 조건을 묶었고, 중립 독립 검토가 `APPROVE`했다.

- 최종 freeze SHA-256: `8291af6d285b45248c79269dbe33e0f72523966f9a4ff8f694696a0141d4cbe0`
- request-intent SHA-256: `12a70934f2d359bf2fefa65df4d284e426e809ef6b06f37fecfc9b88d8120ae8`
- authorization gate에서 재구성한 요청 수: 182 = Wikidata 89 + Commons 93

승인 후 첫 Wikidata batch를 실행했으나 provider가 HTTP 200과 `Retry-After: 5`를 반환했다.
원응답 본문을 다시 검사한 결과 이는 성공 본문이 아니라 top-level plural `errors` 배열에
`code: "maxlag"`를 담은 MediaWiki 오류 envelope였다. R1 parser는 singular `error`만
인식했으므로 이 실제 표현을 parser-complete success나 retryable maxlag로 분류하지 못했고,
동결 규칙대로 `terminal_retry_after_new_census_required`로 종결했다. 따라서 정확히 한 번의
network call 뒤 census가 닫혔다.

| 실행 항목 | 결과 |
|---|---:|
| 계획 요청 | 182 |
| 실제 시작 요청 | 1 |
| terminal 요청 | 1 |
| hash-chain events | 3 |
| 보존 raw responses | 1 |
| candidate manifest | 없음 |
| execution receipt | 없음 |
| image download / admission | 0 / 0 |

event ledger SHA-256은 `95ed1e87f520b4b8f79882485f8146269ccb416c8d5bbddf31f34c51387d6d3c`이고
terminal event SHA-256은 `2fd4d12b89ddd221b71a81f2a0aafaac493ca0c7c42fce5d198570a03406b062`다.
이 결과는 데이터 부족의 증거가 아니라 “R1이 provider의 plural MediaWiki error 표현을
수용하지 못했다”는 실행 증거다. 같은 census를 재시도하거나 그 응답을 새 census의 성공으로
이어붙이지 않는다.

### 6.7 Broad media 후속검증 R2: 새 동결, 중립 검토, 완결 결과

R2는 R1의 결과를 고쳐 쓰지 않고 새 census ID
`pfg-v1-broad-media-followup-r2-20260902`와 분리된 경로를 사용했다. 변경한 의미 규칙은
관찰된 실패 원인에만 한정했다. top-level `errors`가 비어 있지 않은 mapping 배열이고 모든
entry의 `code`가 비어 있지 않은 문자열이며 unique code가 정확히 하나일 때만 그 코드를
정규화한다. 그 코드가 기존 동결 retryable 목록에 있을 때만 재시도한다. singular와 plural이
동시에 있거나, blank/non-string code, malformed entry, 서로 다른 code가 섞인 경우에는 모두
terminal이다. 기존 HTTP/API/transport retry class, 횟수, 시간 상한, 성공 조건은 바꾸지 않았다.

R2 동결은 다음을 결속했다.

- 28개 입력과 6개 사전 부재 출력;
- R1 config, freeze, review, authorization, 182개 intent, 3-event terminal ledger;
- R1의 content-addressed 원응답, one-shot lock, candidate/receipt 부재;
- R2의 독립적으로 재구성 가능한 182개 intent(89 Wikidata + 93 Commons);
- R1과 겹치지 않는 event, publication, lock, response CAS 경로;
- metadata-only 범위와 2026-09-06 execution-start cutoff.

중립 독립 품질검토는 28/28 입력 hash, aggregate hash, 여섯 부재조건, R1 계보, deterministic
intent 재구성, plural-error strictness, retry/resume ceiling, atomic publication을 확인하고 차단
사항 없이 승인했다. 승인 직전 검증에서 exact R1 응답을 재생하면 `maxlag` retryable로
분류하고 5초 대기 뒤 성공하는 것도 확인했다. 검토는 연구결론의 호의성이나 비관성을
판단하지 않고 실행계약의 내부 타당성만 확인했다.

실제 R2 실행 결과는 다음과 같다.

| 실행 항목 | 결과 |
|---|---:|
| 계획/성공 요청 | 182 / 182 |
| Wikidata / Commons batch | 89 / 93 |
| first-R2-attempt success | 182 |
| retryable/terminal 응답 | 0 / 0 |
| hash-chain events | 365 = genesis 1 + started 182 + finished 182 |
| content-addressed raw responses | 182 |
| raw response bytes | 55,899,277 |
| candidate rows | 3,722 |
| distinct item / filename | 3,543 / 3,718 |
| metadata-gate rows | 2,029 |
| metadata-gate distinct item | 1,967 |
| image download / active admission | 0 / 0 |

화가별 현재 메타데이터 가용성은 다음과 같다. `metadata-gate`는 exact creator/painting/current
P18에 더해 open media marker, supported MIME, reported geometry 등 발견 단계 조건을 묶은
것이며 authority verification은 아니다.

| 화가 | 전체 행 | metadata-gate 행 | gate distinct item | open-media 후보 | short-side 후보 | authority URL 후보 | collection QID 행 | inventory 행 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Monet | 1,317 | 725 | 699 | 1,281 | 790 | 1,162 | 1,111 | 960 |
| Sisley | 879 | 303 | 287 | 864 | 354 | 852 | 440 | 378 |
| Pissarro | 791 | 458 | 451 | 775 | 513 | 695 | 593 | 521 |
| Cézanne | 735 | 543 | 530 | 727 | 575 | 733 | 640 | 577 |

manifest의 모든 3,722행은 `authoritative_holding_record_not_yet_verified`, `not_reconciled`,
`not_downloaded`, `not_coded`, `active_study_admission=false`다. 즉 R2는 후보 풀의 current
entity/media 상태를 완결했지만, 권위기관 귀속·oil-on-canvas·물리작품 동일성·법적 재사용·
완전화면·실제 decode를 확정하지 않았다. 특히 2,029라는 수치는 “사용 가능한 회화 2,029점”이
아니라 다음 단계에서 실패 가능성이 남은 metadata screen 수치다.

중요 SHA-256은 freeze `0a3d6f2a4bf40858018bb0f1ce902a0c830dd1f415f3b0f223e77940ccdf24cb`,
authorization `e7a451ffbd3a63dcfe8c34d5242a1bb34f44be6991a0a962b1176e78c6b9e4c4`,
event ledger `7aabae62e6f01e8b295be1a60d0e65efcb348e456c93e977c9609ff6898d1700`,
candidate manifest `3e14bf91eb0836ec09ae3d25fe9ffba7f618939208c4b944b0b0a5c228bc9ff7`,
execution receipt `c2a08cc8199d3f50bdd04da0cc50efb466fa453afde041d3635eb7f261252445`다.

### 6.8 AIC source route: R1 terminal 실패와 R2 완결

AIC(Art Institute of Chicago)는 Protocol 2.0 source registry의 named route다. 첫 census
`pfg-v1-aic-metadata-20260902`는 중립 검토와 승인을 거쳐 2026-09-02에 실행했다. 계약은 화가별
exact `artist_ids` term query 4건, `page=1&limit=100`, 인증 없음, redirect 금지, 응답
`info.version=1.15` 고정, within-census retry 없음이다.

첫 요청은 HTTP 200과 정상 pagination을 반환했지만 terminal로 끝났다. AIC는
`classification_id`를 `TM-66` 같은 nonblank string 식별자로 반환하는데, 동결된 parser는 이를
optional integer로 요구했기 때문이다. 결과는 `terminal_delivery_or_schema_failure`이고 error는
`AIC row has a malformed optional integer`다. R1은 3-event hash chain, one-shot lock,
129,424바이트 원응답 1건만 남겼고 candidate manifest와 execution receipt는 발행하지 않았다.
이는 provider 장애가 아니라 우리 parser의 자료형 가정 오류이며, 관찰된 실패 원인에만 한정한
수정으로 재실행할 수 있는 순수 기술적 실패다.

R2 `pfg-v1-aic-metadata-r2-20260902`는 R1을 고쳐 쓰지 않고 새 census ID와 분리된 manifest,
publication, workspace, CAS 경로를 사용했다. 유일한 의미 변경은
`classification_id`가 optional nonblank string 식별자라는 것이다. endpoint, query, requested
fields, pagination, 정렬, 중복 규칙, screening, rights 기록, rate limit, retry, 실패 규칙,
publication 규칙은 모두 동일하다. 동결은 25개 입력, 6개 사전 부재 출력, 그리고 R1의 config,
freeze, review, authorization, intent, terminal ledger, lock, 원응답 CAS, manifest/receipt 부재를
허용된 config delta와 함께 결속했다.

중립 독립 품질검토는 다음을 확인하고 차단 사항 없이 승인했다.

- 25/25 입력 hash와 aggregate `dee7b9ab…`, 재구성한 required path set 일치;
- 6개 사전 부재 조건과 R1과의 경로 분리;
- 5개 PYTHONHASHSEED에서 동일하게 재구성되는 4개 intent(digest `bfb268c7…`);
- R1 계보: 3-event chain, terminal event `1e41d54b…`, 정확한 terminal error, 두 파일뿐인
  workspace inventory, 부재한 R1 manifest/receipt;
- exact R1 응답 재생: R1 parser는 여전히 기록된 error로 실패하고, R2 parser는 동일 body를
  46행으로 파싱하며 그중 33행이 두 screen을 통과하고, `classification_id` `TM-66`은 문자열로
  보존되며 46개 provider LQIP는 raw CAS에만 남는다;
- 실제 커밋된 seal로 수행한 production-gate mock: 4/4 요청, 2.0초 최소 간격, atomic
  publication, receipt-bound manifest/terminal event, 9-event chain, content-address 검증,
  image download 0, admission 0, 두 번째 실행은 fail-closed.

실제 R2 실행 결과는 다음과 같다.

| 실행 항목 | 결과 |
|---|---:|
| 계획/성공 요청 | 4 / 4 |
| first-R2-attempt success | 4 |
| retryable/terminal 응답 | 0 / 0 |
| hash-chain events | 9 = genesis 1 + started 4 + finished 4 |
| content-addressed raw responses | 4 |
| raw response bytes | 308,569 |
| candidate rows | 153 |
| distinct AIC artwork ID | 153 |
| authority-record 후보 | 57 |
| authority + media screen 후보 | 57 |
| distinct accession(통과분) | 57 |
| image download / active admission | 0 / 0 |

화가별 screening 결과는 다음과 같다. `paired ID/title`은 target agent ID와 정규화된 이름이
`artist_ids`/`artist_titles`의 짝으로 나타나는지, 나머지는 각 단일 관문이다.

| 화가 | 전체 행 | paired ID/title | painting 분류 | oil+canvas | accession | public-domain | image_id | short side ≥1,024 | 최종 후보 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Monet | 46 | 46 | 33 | 33 | 46 | 46 | 46 | 46 | 33 |
| Sisley | 8 | 8 | 6 | 6 | 8 | 8 | 8 | 8 | 6 |
| Pissarro | 65 | 65 | 10 | 9 | 65 | 65 | 65 | 65 | 9 |
| Cézanne | 34 | 34 | 9 | 9 | 34 | 33 | 34 | 34 | 9 |
| 합계 | 153 | 153 | 58 | 57 | 153 | 152 | 153 | 153 | 57 |

Pissarro와 Cézanne의 전체 행 수가 큰 것은 AIC 소장의 판화·소묘 비중이 크기 때문이며,
painting 분류와 oil-on-canvas 관문에서 대부분 탈락한다. 즉 행 수는 회화 수가 아니다.
통과분 57행의 reported short side는 최소 1,817, 중앙값 5,021, 최대 14,221이다. 이는 provider가
보고한 thumbnail geometry일 뿐 실제 asset delivery나 decode를 확인한 값이 아니다.

manifest의 153행은 모두 `aic_holding_record_candidate_not_role_or_identity_reconciled`,
`not_reconciled`, `not_requested`, `not_blind_coded`, `active_study_admission=false`다. 57이라는
수치는 “AIC에서 사용 가능한 회화 57점”이 아니라 AIC holding record 기준 metadata screen 수치이며,
role/attribution qualifier, 물리작품 동일성, 실제 image 권리와 전달, Wikidata/Commons census와의
중복 제거가 모두 남아 있다. AIC row와 broad census row는 같은 물리 작품을 서술할 수 있으므로
독립적인 수로 더하지 않는다.

중요 SHA-256은 freeze `3d5d7d228905f4028b73dfeb6090509d90af56a85e3b852d3d06125c8e36c7c8`,
review `278688fdbf8066398a2109b5f4c577d3d5816be03794682d80e66bea9260b905`,
authorization `0857fc19442272f7f5aaf9a8852544d8b31b0dee0f06e056279e5d4dbb436bbc`,
event ledger `3040d2d2f4e9e4fb43538350e2d2619d8e967f0b4ea76fa8bdb1e1cc699a89b7`,
candidate manifest `a31b57239b75e8730f9c173594b7fe6b3a0052f6da84ff9439b394f78271b410`,
execution receipt `723d52f2366dd89fc5cf2aaaf22de0d347409f24f009b5d57c5e24e8879d78d5`다.

## 7. 실제 이미지 취득 및 corpus closure 계획

### 7.1 전체 R0 완결

먼저 no-`P186` Wikidata/Commons와 모든 named source를 terminal condition까지 수집한다.
한 source에서 목표 수가 나왔다고 중단하지 않고, 부족한 화가만 다른 source로 top-up하지
않는다. 모든 row에 terminal disposition을 부여한 후 union을 만든다.

### 7.2 physical-work/capture graph

각 candidate를 다음 key로 연결한다.

- authority institution + accession
- canonical authority object URL/ID
- title/date/dimensions의 불확실성 포함 비교
- Commons/기관 asset ID
- raw file SHA-256와 perceptual duplicate signal
- capture/master ancestry

mirror, crop, thumbnail, re-encode는 같은 physical work/capture family로 접는다. 별도 촬영이
provenance로 확인된 경우만 independent capture다.

### 7.3 R1 이미지 취득

별도 reviewed R1 freeze가 authority record, item-level rights receipt, exact delivery URL,
expected MIME/geometry, output path, retry/redirect rule을 묶은 뒤에만 image를 받는다.
취득 후 raw bytes, normalized array, ICC/color-space status, decode, dimensions, complete-view,
frame/watermark, raw/normalized hash를 기록한다. full-resolution bytes는 ignored workspace에
두고 repository에는 compact manifest와 hash만 commit한다.

### 7.4 맹검 내용 코딩

long side ≤512 derivative만 두 coder에게 제공하며 painter, title, institution, accession,
filename, source를 숨긴다. 각 작품을 `eligible`, `ineligible`, `ambiguous`로 코딩하고 eligible
작품은 다음 네 장면 중 하나로 분류한다.

- `water_organized`
- `built_place_organized`
- `route_organized`
- `open_or_wooded_land`

각 painter에서 eligibility agreement ≥0.90, nominal Krippendorff alpha ≥0.80, scene agreement
≥0.85 및 alpha ≥0.80이 필요하다. reliability 실패는 adjudication으로 덮지 않는다.

## 8. 회화 특징 측정법

### 8.1 공통 normalization

실제와 생성 이미지에 byte-identical pipeline을 적용한다.

1. pinned decoder로 truncation 없이 decode
2. embedded ICC를 perceptual intent로 sRGB 변환; profile 없음은 sRGB 가정+flag
3. crop/mask 없이 complete borderless view 사용
4. aspect ratio 유지, upsample 없이 short side 1,024로 Lanczos downsample
5. gamma sRGB와 linear-light를 규정식으로 계산
6. linear luminance `Y=0.2126R+0.7152G+0.0722B`, D65 CIELAB 계산
7. raw, normalized array, software lock, feature vector hash 보존

histogram equalization, white balance, saturation correction, square warp, learned enhancement는
금지한다.

### 8.2 Family A: 색채 조직 11좌표

- CIELAB `L*` median, IQR: 2
- chroma `C*` median, IQR: 2
- `C* ≥ 5` pixel fraction: 1
- 24-bin hue concentration, normalized entropy: 2
- 1%, 4%, 16% image scale lag의 median CIEDE2000: 3
- 세 lag의 log distance–log scale slope: 1

단순 평균색이 아니라 palette spread와 공간적 색 상호작용을 측정한다.

### 8.3 Family B: 공간·방향 조직 8좌표

- radial Fourier power slope와 RMS residual: 2
- Fourier spectral anisotropy: 1
- Scharr orientation entropy와 horizontal–vertical balance: 2
- Scharr magnitude median, IQR: 2
- quadrant PHOG self-similarity의 Jensen–Shannon divergence: 1

이는 scale, edge, composition organization이며 semantic understanding을 주장하지 않는다.

### 8.4 Family C: 다중척도 디지털 질감 12좌표

- 4-level stationary `db2` wavelet log energy: 4
- wavelet scale slope와 curvature: 2
- uniform rotation-invariant LBP entropy at `(8,1),(16,2),(32,4)`: 3
- 1%, 4%, 16% scale local coefficient-of-variation median: 3

이를 “digital texture organization”이라고 부르며 physical brushstroke라고 부르지 않는다.

### 8.5 method qualification

모든 31좌표는 deterministic fixture tolerance, one-pixel translation, 1% uniform crop,
downsample/upscale perturbation, same-work independent-capture disturbance, leave-one-workflow
검사를 통과해야 한다. 공통 development mixture의 median/IQR로만 scaling하며 painter별
scaling과 문제가 생긴 좌표의 사후 삭제는 금지한다. 한 family라도 실패하면 생성 단계로
진행하지 않는다.

## 9. 생성 및 비교 설계

### 9.1 prompt frame

네 장면마다 4개, 총 16개 artist-free prompt를 Protocol에 byte-exact하게 정의했다. named
condition은 같은 문장에 painter name만 규정 위치에 삽입한다. artist-free control 1개와
네 painter condition은 같은 template와 paired seed를 공유한다. model/render는 정확한
checkpoint와 1536×1024 설정으로 G0에서 동결한다.

### 9.2 primary distance

각 family에서 공통 scaling된 실제 분포 `P_a`와 painter-name 생성분포 `Q_a`의 energy
distance를 계산한다.

`D(P,Q) = 2 E||X-Y|| - E||X-X'|| - E||Y-Y'||`

실제 confirmation population은 전수 유한합으로, 생성 기대값은 등록 seed block으로
추정한다. template를 prompt superpopulation으로 bootstrap하지 않는다.

### 9.3 equivalence margin과 specificity

margin은 결과를 본 뒤 정하지 않는다. new-development split-half 2,000회에서 같은-painter
replicate distance의 최대 `W_F`를 구하고, independent-capture tolerance bound `B_F`와 함께
`epsilon_F=max(W_F,2B_F)`로 정한다. untouched qualification에서 이 margin이
wrong-painter separation보다 작아야 family가 qualify한다.

### 9.4 positive painter-reproduction label의 conjunction

한 painter가 positive label을 받으려면 세 family 모두에서 다음이 필요하다.

- target painter distance upper bound ≤ frozen margin
- 모든 wrong-painter보다 target이 명확히 가까움
- artist-free control보다 painter-name condition이 개선됨
- 모든 coordinate median shift ≤ 0.25 common-scaled unit
- 모든 retained scene이 별도로 margin 안에 있음
- leave-one-work/workflow에서 결과가 margin의 10% 이상 흔들리지 않음
- technically analyzable output grid 100% 완결
- searched real corpus의 confirmed copy 0

한두 좋은 family나 cherry-picked output은 결론을 만들 수 없다.

## 10. 표본 충분성 및 중단 기준

다음은 목표 quota가 아니라 연구 진행 최소관문이다.

- 네 화가 공통 retained scene ≥3
- 각 retained painter×scene confirmation physical works ≥20
- 각 painter confirmation equal-scene Kish ESS ≥100
- 각 retained painter×scene×workflow에서 new development ≥10, qualification ≥10,
  confirmation ≥20
- 화가별 authority/capture workflow ≥2, graph connected
- 한 workflow의 equal-scene weight ≤0.80
- independent-capture auxiliary works ≥60, 화가별 ≥12
- 실제 cell size를 사용한 whole-decision simulation에서 favourable full-pass ≥80%, 각 adverse
  alternative rejection ≥95%, unsupported painter-family claim ≤5%

현재는 admitted physical work가 0이므로 이 관문을 하나도 통과했다고 말할 수 없다.

## 11. 재현성 파일 지도

| 목적 | 경로 |
|---|---|
| 유일한 정본 계획 | `studies/painter_feature_generation_v1/PROTOCOL.md` |
| R2 수집 설정 | `configs/painter_feature_generation_v1/federated_metadata_census_r2.json` |
| exact request intents | `data/manifests/painter_feature_generation_v1/federated_seed_metadata_request_intents_r2.jsonl` |
| freeze/review/authorization | `data/manifests/painter_feature_generation_v1/federated_seed_metadata_{freeze,review,authorization}_r2.json` |
| hash-chained events | `data/manifests/painter_feature_generation_v1/federated_seed_metadata_request_events_r2.jsonl` |
| candidate manifest | `data/manifests/painter_feature_generation_v1/federated_seed_metadata_candidates_r2.jsonl` |
| execution receipt | `data/manifests/painter_feature_generation_v1/federated_seed_metadata_execution_receipt_r2.json` |
| broad R2 설정 | `configs/painter_feature_generation_v1/broad_wikidata_discovery_r2.json` |
| broad retry freeze/review/authorization | `data/manifests/painter_feature_generation_v1/broad_wikidata_retry_{freeze,review,authorization}_r2.json` |
| broad hash-chained events | `data/manifests/painter_feature_generation_v1/broad_wikidata_request_events_r2.jsonl` |
| broad candidate manifest | `data/manifests/painter_feature_generation_v1/broad_wikidata_candidates_r2.jsonl` |
| broad execution receipt | `data/manifests/painter_feature_generation_v1/broad_wikidata_execution_receipt_r2.json` |
| broad media R1 freeze/review/authorization | `data/manifests/painter_feature_generation_v1/broad_media_followup_{freeze,review,authorization}.json` |
| broad media R1 exact intents | `data/manifests/painter_feature_generation_v1/broad_media_followup_request_intents.jsonl` |
| broad media R1 terminal events | `data/manifests/painter_feature_generation_v1/broad_media_followup_request_events.jsonl` |
| broad media R2 설정 | `configs/painter_feature_generation_v1/broad_media_followup_r2.json` |
| broad media R2 freeze/review/authorization | `data/manifests/painter_feature_generation_v1/broad_media_followup_{freeze,review,authorization}_r2.json` |
| broad media R2 exact intents/events | `data/manifests/painter_feature_generation_v1/broad_media_followup_request_{intents,events}_r2.jsonl` |
| broad media R2 candidate manifest | `data/manifests/painter_feature_generation_v1/broad_media_followup_publication_r2/candidates.jsonl` |
| broad media R2 execution receipt | `data/manifests/painter_feature_generation_v1/broad_media_followup_publication_r2/execution_receipt.json` |
| compact readiness summary | `reports/painter_feature_generation_v1/evidence/data_readiness_audit.json` |
| literature synthesis | `literature_reviews/SYNTHESIS.md` |
| literature evidence matrix | `literature_reviews/EVIDENCE_MATRIX.csv` |

고정 seed R2의 중요 hash는 다음과 같다.

- R2 freeze: `6d52424091d6cfdfd0050b3ad60848cb030356c11b44694a99d3b0dd1aa33768`
- R2 authorization: `b30f9e4ce7e3821f2944abe5cb1061240dd161698d7ae08b1bf82a4260f16139`
- event ledger: `23905d37b2be4bcec9c8f9be0ec373fe4e2a07a96563ebc644ff183a38943640`
- candidate manifest: `bde48246d121d175be2e8e9b2023be32347cd8f2e33d5df16780d0b20c7e2e33`
- execution receipt: `59c90e698a6609bcce7e4d2a010510db5439f9bf740f279bd7e9ac47fcd7de2a`

Broad no-`P186` R2의 중요 hash는 다음과 같다.

- retry freeze: `d004b89b087e9fd63089cbcacb40722e7b844f2337f32e7a5a9b2548442c2a10`
- retry authorization: `756122c4068b15164dcfc8db81b4e62cb5a7069a2d08cc5299e68e14ceabb5a6`
- combined authorization: `e1b4e11a992ac22efaa448290e74845d1524f22201be79615d493cd3032e8314`
- event ledger: `9bd925534c7b77deb578ef8ce26d9b9f263f6c33f7b3afc3daaa8458a6e6fd66`
- candidate manifest: `23092232815dd96ab75ad0c8025469ea74f250c5b847b91f080996f11ba83e4e`
- execution receipt: `91fe3db46b3316f6cc53d31e49070ab62984a3b6ec0e387ad6880e3ccc4c6b6b`

Broad media R2의 중요 hash는 다음과 같다.

- freeze: `0a3d6f2a4bf40858018bb0f1ce902a0c830dd1f415f3b0f223e77940ccdf24cb`
- neutral review: `ae708bfc68b1c4347d74fe084f052ad7de4703bf75af6f6c1886ef5167c61851`
- authorization: `e7a451ffbd3a63dcfe8c34d5242a1bb34f44be6991a0a962b1176e78c6b9e4c4`
- exact intents: `2e0efd4518ac39025a0327571693d4c66d6b9b54080a8304e4230481ce35bdf0`
- event ledger: `7aabae62e6f01e8b295be1a60d0e65efcb348e456c93e977c9609ff6898d1700`
- candidate manifest: `3e14bf91eb0836ec09ae3d25fe9ffba7f618939208c4b944b0b0a5c228bc9ff7`
- execution receipt: `c2a08cc8199d3f50bdd04da0cc50efb466fa453afde041d3635eb7f261252445`

## 12. 최종 판정과 다음 작업

### 완료된 것

- 연구질문을 generated-versus-real painter feature distribution으로 바로잡음
- 205-entry bibliography와 144-row evidence matrix를 설계결정에 연결
- 31좌표, 세 필수 family, normalization, qualification, energy-distance decision 확정
- actual unequal corpus, equal-scene target, role split, source/capture gate 확정
- fixed-seed 3,190 item / 3,364 filename의 현재 메타데이터 follow-up 완결
- 실패 census를 보존하고 원인을 수정한 새 census의 165/165 성공
- 2,029 metadata-qualified row의 추적 가능한 candidate manifest 작성
- broad no-`P186` R1의 terminal HTTP 502를 all-or-none 규칙대로 보존
- 독립 품질검토에서 검증–실행 경계 결함 두 건을 수정하고 재검토 승인
- broad no-`P186` R2 4/4 성공 및 3,722행·3,543 item·3,718 filename 발견
- broad media R1의 plural `errors:[maxlag]` HTTP 200 표현을 terminal 증거로 보존하고,
  성공 응답이었다는 기존 해석을 원응답에 맞게 정정
- broad media R2를 새 census/경로로 동결하고 중립 검토 승인 후 182/182 요청 완결
- 182개 CAS 응답, 365-event ledger, 3,722-row non-admission manifest를 원자적으로 게시하고
  2,029 metadata-gate 행을 확인

### 완료되지 않은 것

- 나머지 named-source R0 terminal union과 broad 후보의 authority/rights 검증
- authority record verification와 physical-work/capture reconciliation
- active image byte 취득과 complete-view/decode/ICC 검사
- blind eligibility/scene coding과 role assignment
- feature implementation qualification 및 simulation
- generation과 confirmation

따라서 현재 연구결론은 다음 한 문장이다.

> 고정 seed, broad no-`P186`, broad media 후속검증은 재현 가능하게 완료됐고 3,722행 중
> 2,029행이 메타데이터 관문을 통과했지만, 권위검증·물리작품 통합·이미지 취득이 0이므로
> 생성–실제 비교를 위한 충분한 고품질 회화 자료가 확보됐다고 판단할 단계는 아니다.

다음 작업은 수치가 좋은 후보만 골라 즉시 다운로드하는 것이 아니다. 먼저 전체 R0을
terminal union으로 닫고 물리 작품과 capture를 통합한 뒤, 별도 R1 freeze에서 권위·권리·
identity·기술 gate를 묶어 lawful image acquisition을 실행해야 한다. 그 결과가 위
표본관문을 충족하지 못하면 연구질문을 몰래 바꾸지 않고 `NO-GO`로 보고한다.

## 13. 2026-09-04 보완: 검토 주체, 증거 검증, R0 산출물, 사전 스크리닝

### 13.1 검토 주체 공개

이 보고서와 `data/manifests/painter_feature_generation_v1/*review*.json`이 "중립 독립
품질검토"라고 부르는 모든 검토는 유지관리자 1인이 실행한 LLM 검토 서브에이전트의
산출물이다. review 파일의 `independent_reviewer` 값은 예를 들어
`Mencius (independent neutral quality review subagent)`다. 이 검토는 freeze 작성자와
절차적으로 분리되어 있고 실제 결함을 발견·수정하게 했지만, 기관적으로 독립적인
검토는 아니다. 이후 모든 보고서는 이 사실을 명시한다.

Protocol 2.0 §8.2가 요구하는 역할(취득 관리자, 맹검 코더 2명, 조정자, M0 분석자, 생성
운영자)은 겸임이 금지된다. 현재 저장소의 인력은 유지관리자 1인이다. R1 취득과 R2
코딩은 코딩·조정에 필요한 최소 3인이 추가로 지정되기 전에는 시작할 수 없다.

### 13.2 증거 검증 방식 변경

기존에는 freeze가 묶은 파일을 작업 트리 기준으로 대조했고, 고정 seed R1 freeze의
두 파일(`federated_census.py`와 그 test)은 R2 수리 때문에 영구 불일치로 남아 있었다.
2026-09-04부터 검증은 commit 기준이다. `latent-art-bench verify-evidence`는 각 freeze를
그것을 기록한 git commit으로 해석하고, 묶인 입력을 그 commit의 바이트로 대조하며,
추적되지 않는 research workspace 바이트는 작업 트리에서 대조하고, 모든 event ledger의
hash chain과 모든 execution receipt의 ledger·manifest·CAS 응답을 확인한다. hash는 갱신하지
않는다. 위 두 파일의 수리 전 바이트는 어떤 commit에도 없으므로 재검증이 불가능하며,
`evidence_acknowledgements.json`에 원인과 잔존 증거를 기록했다. 검증 결과는 freeze 9건,
ledger 8건(이벤트 736개), receipt 4건(CAS 응답 355개)이 모두 통과하고 acknowledged 입력
2건만 남는다.

### 13.3 추가된 R0 산출물

| 산출물 | 경로 | 상태 |
|---|---|---|
| §11.1 prompt library | `data/manifests/painter_feature_generation_v1/prompt_library.json` | PROTOCOL.md 표에서 렌더링한 exact UTF-8 JSON; artist-free 16 + named 64 문자열; 검토·seal 전 |
| §8 노출 denylist | `data/manifests/painter_feature_generation_v1/exposure_denylist.jsonl` + receipt | pinned git blob 8개에서 재구성; pixel 노출 물리작품 122점(AIC 40, NGA 45, Met 27, CMA 10)은 development 전용; pilot 3 metadata-only 선택 39점은 제한 없음; 화가 미해결 5점; M0 freeze 전 |

denylist는 AIC R2 screened 후보와 이미 겹친다. Monet 33점 중 17점, Sisley 6점 전부,
Pissarro 9점 중 6점, Cézanne 9점 중 5점이 pilot에서 pixel 노출된 작품이므로 development
역할만 가능하다.

### 13.4 장면 지지도 사전 스크리닝과 결정 요청

`reports/painter_feature_generation_v1/SCENE_SUPPORT_PRESCREEN_KO.md`는 §8.1의 20/20/60 배정과
§9의 하한을 그대로 계산한 뒤 완료된 R0 manifest의 제목-토큰 상한과 비교한다. 결과는 다음과
같다.

- 유지 장면이 3개면 화가×장면 셀당 신규 적격작 57점(화가당 183점), 4개면 50점(화가당
  212점)이 필요하다. 역사적 노출작은 이 하한에 기여하지 않는다.
- 야외 추정이면서 소장 QID가 있는 item의 상한에서, 네 화가 모두 셀당 57점을 넘는 장면은
  없다. 최약 셀은 Monet `route_organized` 12점, Sisley `open_or_wooded_land` 28점이다.
- §9의 결정론적 유지 규칙을 이 상한에 적용하면 세 장면이 남지 않으므로 연구는 R2 후
  중단된다. 실제 수치는 권위검증·중복제거·완전화면·맹검 코딩 후 더 낮아질 뿐이다.

이 스크리닝은 어떤 작품도 입장·배제하지 않는다. 결정은 14절에 기록했다.

## 14. Protocol 2.1 발행 (2026-09-04)

### 14.1 결정

유지관리자는 코더와 조정자 없이 연구를 진행하기로 결정했고, 그 결정을 픽셀·활성 label·
feature·생성물이 하나도 없는 시점에 Protocol 2.1로 발행했다. 정본은
`studies/painter_feature_generation_v1/PROTOCOL_2.1.md`이며, 2.0 텍스트는 완료된 census
freeze 9건이 묶은 증거이므로 `PROTOCOL.md`에 그대로 남긴다. 2.1의 0절이 모든 변경을 열거한다.

### 14.2 변경 요약

| 항목 | 2.0 | 2.1 |
|---|---|---|
| 내용 적격성 | 512px 마스킹 파생본을 코더 2명이 맹검 코딩, 제3 코더 조정 | 동결 lexicon(`content_lexicon.json`)을 권위·발견 메타데이터에 적용; 사람 코딩 없음 |
| 장면 층화 | 4개 장면군, 화가 전원 ≥20 confirmation인 군만 유지, 3개 미만이면 중단 | 없음. 야외 장소 단일 도메인, 작품 균등 가중 |
| 프롬프트 census | 유지 장면군만 사용, `T = 4G` | 16개 전부 항상 사용, `T = 16`; 장면 유형은 생성 측 진단 label |
| 역할 배정 | painter × scene × workflow 내 hash 순위 | painter × workflow 내 hash 순위, 도메인 문자열 `pfg-v1/2.1-role` |
| 화가당 하한 | 셀당 dev 10 / qual 10 / conf 20, equal-scene ESS ≥100 | dev 10 / qual 10 / conf 100 (균등 가중이므로 ESS = N), 보조 패널 12 |
| 생성물 판정 | 코더의 장면 adherence ≥0.90 구속 게이트 | 동결 자동 분류기의 adherence는 진단만; 완결성 100%와 confirmed copy 0은 유지 |
| 복제 판정 | 마스킹 검토자 2명 + 제3자 | 두 임계값 결정론 규칙, 사람 검토 없음 |
| 역할 분리 | 취득 관리자·코더·조정자·분석자·운영자 겸임 금지 | 1인 운영자가 순차 수행 가능하되 기술적 봉인과 접근 ledger 필수; 은밀 접근 배제 불가를 한계로 공개 |
| 완전화면 | 사람 확인 | 제공자 asset 지정 + 자동 테두리/워터마크 규칙 |

### 14.3 2.1 하한 대비 현재 상한

`SCENE_SUPPORT_PRESCREEN_KO.md`를 2.1 기준으로 다시 계산했다. 화가당 신규 적격작 하한은 179점
(confirmation 100 ÷ 0.6 = 167, 보조 12)이다. lexicon 판정 eligible이면서 소장 QID가 있는 item의
상한은 Monet 529, Sisley 193, Pissarro 256, Cézanne 200이다. 네 화가 모두 상한에서는 하한을
넘지만 Sisley의 여유는 14점뿐이다. 권위검증·중복제거·완전화면·사적 소장 제외 후 실제 수치는
더 낮아지므로 R2 종료 시 `NO-GO` 가능성은 남아 있다.

### 14.4 다음 작업

1. prompt library, content lexicon, exposure denylist의 중립 검토(LLM 서브에이전트임을
   `reviewer_kind`로 명시)와 freeze.
2. 남은 named route(Cleveland부터)를 공유 census engine으로 freeze·실행. Europeana와
   Paris Musées는 credential이 없으면 `not_executed_missing_authorized_credential`로 기록.
3. union의 physical-work reconciliation 후 R1 취득 freeze.
4. R2 lexicon 판정과 역할 배정, 봉인 store manifest 커밋, 이후 M0.
