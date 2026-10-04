# Korean translation: style and terms

The Korean translation of the TMLR manuscript was made anew on 2026-10-04 by an AI assistant at the
user's request. When the English sources change, edit the same passage here with these terms, then
run `make tmlr-ko-assets` and `make tmlr-ko-check`.

## Style

- Academic plain style (-다). Keep every caveat and every number; Korean word order over literal
  rendering.
- A term the English defines with `\emph` appears once as `\term{한국어}(English)`.
- Painter names in Korean. Model and configuration names, CLIP, CSD, Wikidata, Wikimedia Commons,
  OpenRouter and H1/H2 stay in English. Prompt texts and the scene descriptions stay in English.
- References: `\ref{x}절`, `부록~\ref{x}`, `부록 표~\ref{x}`, `표~\ref{x}`, `그림~\ref{x}`,
  `식~\ref{x}`. A particle after `\citet` or a number follows the Korean reading of its last
  digit (2024 → 는, 2026 → 은); after a symbol, the English letter name ($D$ → 는/가).
- Numbers: write digits where the English writes digits. Where Korean needs digits for an English
  word (a date's month, 3분의 1, 4분의 1, "0"), list the difference in `EXPECTED` in
  `build_korean.py`. Table captions must keep exactly the English numerals.

## Terms

| English | 한국어 |
| --- | --- |
| proximity, proximity gain; raw proximity | 근접도, 근접도 이득; 근접도 원값 |
| specificity | 특이성 |
| shared change, shared fraction, shared term | 공통 변화, 공통 비율, 공통 항 |
| between-name differences | 이름 간 차이 |
| painter-specific term | 화가 특이 항 |
| faithful imitator; faithful benchmark/value | 충실한 모방자; 충실 기준/기준값 |
| exact-differences generator/benchmark | 정확 차이 생성기/기준 |
| reference collection, panel; development panel | 참조 컬렉션, 참조 패널; 개발 패널 |
| reference mean, centroid, prototype | 참조 평균, 중심, 프로토타입 |
| reference painter spread $H$ | 참조 화가 산포 $H$ |
| reference pattern; along / off the pattern | 참조 패턴; 패턴 방향 / 패턴 밖 (성분) |
| aligned amplitude $\beta$; relative size $Q$; alignment ratio; error $D$ | 정렬 진폭; 상대 크기; 정렬 비; 오차 |
| scene variation; (held-out) rescaling | 장면 간 변동; (홀드아웃) 배율 조정 |
| centered (generated) contrast | 중심화한 (생성) 대비 |
| configuration; clause (generic, named, none) | 구성; 지시문 (일반, 이름, 없음) |
| artist-free / generic baseline; arm | 화가 미지정 / 일반 기준선; 조건 |
| generic outputs; named images | 일반 출력; 이름 지정 이미지 |
| repeat; cross-repeat products; cell | 반복 생성; 반복 간 곱; 칸 |
| repeat noise, noise power; drift | 반복 잡음, 잡음 전력; 드리프트 |
| squared change, squared size | 제곱 변화량, 제곱 크기 |
| scene resample; paired scene; reference resampling | 장면 재표집; 대응 장면; 참조 재표집 |
| Student interval; Bonferroni; unadjusted; percentile | 스튜던트 $t$ 구간; 본페로니 보정; 미보정; 백분위 구간 |
| coverage; resolved; descriptive; prespecified | 포함 확률; 판별; 서술적; 사전 지정 |
| inferential family | (추론) 비교군 |
| pooled target / control; pseudo-scene | 통합 목표 / 대조군; 의사 장면 |
| recognition; macro accuracy; chance | 인식; 매크로 정확도; 우연 수준 |
| readout; representation; encoder | 지표; 표현; 인코더 |
| feature family; color, spatial, texture | 특징군; 색채, 공간, 텍스처 |
| century group; Hudson River School; Impressionists | 세기 집단; 허드슨강 화파; 인상파 화가들 |
| closeness; familiarity; subject matter | 가까움; 친숙도; 소재 |
| genuine paintings; positive control | 실제 회화; 양성 대조군 |
| content class water/built/route/land/mixed | 내용 범주 물/건축/길/땅/혼합 |
| shared offset; translation | 공통 이동; 평행 이동 |
| percentage points | \%포인트 |
| closed service; selection manifest | 폐쇄형 서비스; 선정 목록 |
| protocol, plan, amendment, freeze | 프로토콜, 계획, 수정, 동결 |
