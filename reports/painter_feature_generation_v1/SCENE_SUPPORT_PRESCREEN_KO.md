# Painter Feature Generation v1 코퍼스 적정성 사전 스크리닝

- 상태: 비구속 메타데이터 사전 스크리닝. 프로토콜 수치가 아니며, 어떤 작품도 입장·배제하지 않는다.
- 정본: Protocol 2.1 (`studies/painter_feature_generation_v1/PROTOCOL_2.1.md`). 2.0의 장면 셀 규칙은 폐기 근거 기록용으로만 함께 계산한다.
- 입력: `data/manifests/painter_feature_generation_v1/broad_media_followup_publication_r2/candidates.jsonl` (3,722행), `data/manifests/painter_feature_generation_v1/aic_metadata_publication_r2/candidates.jsonl` (153행), 노출 denylist (122점), §7.4 content lexicon (`data/manifests/painter_feature_generation_v1/content_lexicon.json`).
- 생성 명령: `uv run --locked latent-art-bench scene-prescreen`

## 1. Protocol 2.1이 요구하는 화가당 최소 신규 적격작 수

| 항목 | 값 |
|---|---:|
| confirmation 필요 (균등 가중이므로 ESS = N) | 100 |
| development ≥10을 20% 배정으로 얻기 위한 적격작 | 50 |
| confirmation ≥100을 60% 배정으로 얻기 위한 적격작 | 167 |
| 화가당 primary 적격작 하한 | 167 |
| 보조 독립촬영 패널 | 12 |
| **화가당 합계** | **179** |

역사적 노출작(denylist)은 development 전용이므로 이 하한에 기여하지 않는다.

## 2. broad-media R2 manifest의 화가별 상한 (distinct Wikidata item, gate 통과분)

§7.4 lexicon을 discovery label/description에 적용한 결과다. R2 본 실행은 권위기관 필드를 쓰므로 수치가 달라진다.

| 화가 | gate 통과 item | eligible | ineligible | unresolved | 소장 QID 있음 | eligible & 소장 QID | registry 기관 | 비registry 주요 미술관 | QID 미해결 | denylist 겹침 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Monet | 699 | 590 | 56 | 53 | 631 | 529 | 171 | 106 | 354 | 0 |
| Sisley | 287 | 256 | 5 | 26 | 218 | 193 | 48 | 24 | 146 | 2 |
| Pissarro | 451 | 349 | 79 | 23 | 333 | 256 | 59 | 60 | 214 | 9 |
| Cézanne | 530 | 226 | 237 | 67 | 475 | 200 | 90 | 132 | 253 | 8 |

## 3. Protocol 2.1 하한 대비 상한

| 화가 | eligible & 소장 QID 상한 | 하한(보조 포함) | 여유 | 상한에서 통과 |
|---|---:|---:|---:|---|
| Monet | 529 | 179 | +350 | 예 |
| Sisley | 193 | 179 | +14 | 예 |
| Pissarro | 256 | 179 | +77 | 예 |
| Cézanne | 200 | 179 | +21 | 예 |

상한에서는 네 화가 모두 하한을 넘는다. 최약 화가는 Sisley이며, 권위검증·중복제거·완전화면·사적 소장 제외 후 실제 수치는 더 낮아지므로 R2 종료 시 NO-GO 가능성이 남아 있다.

## 4. 폐기된 Protocol 2.0 장면 셀 규칙의 기록

| 유지 장면 수 G | 셀당 적격작 하한 | 화가당 합계 |
|---|---:|---:|
| G=3 | 57 | 183 |
| G=4 | 50 | 212 |

| 장면 클래스 | Monet | Sisley | Pissarro | Cézanne | 최약 화가 | G=3 하한 통과 |
|---|---:|---:|---:|---:|---|---|
| `water_organized` | 343 | 93 | 63 | 66 | Pissarro | 예 |
| `route_organized` | 15 | 20 | 30 | 22 | Monet | 아니오 |
| `built_place_organized` | 107 | 53 | 129 | 52 | Cézanne | 아니오 |
| `open_or_wooded_land` | 64 | 27 | 34 | 60 | Sisley | 아니오 |

2.0 규칙으로는 G=3 하한을 통과하는 장면이 1개였고, 이것이 2.1이 장면 층화를 제거한 근거다.

## 5. AIC R2 screened 후보의 §7.4 판정

| 화가 | screened | eligible | ineligible | unresolved | denylist 겹침 | eligible·비노출 |
|---|---:|---:|---:|---:|---:|---:|
| Monet | 33 | 24 | 9 | 0 | 17 | 10 |
| Sisley | 6 | 2 | 4 | 0 | 6 | 0 |
| Pissarro | 9 | 0 | 9 | 0 | 6 | 0 |
| Cézanne | 9 | 2 | 7 | 0 | 5 | 0 |

## 6. 해석과 한계

- discovery label은 R2가 사용할 권위기관 필드보다 짧고 잡음이 많다. 실제 판정은 권위 reconciliation 후 같은 lexicon으로 한 번만 수행한다.
- 위 모든 수치는 exact attribution, oil-on-canvas, 권리, 완전화면, 물리작품 중복제거 이전의 상한이다. 실제 수치는 더 낮다.
- 소장 QID가 없거나 사적 소장인 item은 닫힌 registry 아래에서 권위기록에 도달할 수 없다.
- 이 문서는 어떤 작품도 입장시키지 않는다.

## 7. 미해결 소장 QID 상위 목록

| QID | gate 통과 item |
|---|---:|
| Q106857407 | 45 |
| Q23785329 | 36 |
| Q685038 | 28 |
| Q666331 | 20 |
| Q1465805 | 19 |
| Q1362629 | 18 |
| Q745866 | 16 |
| Q1574475 | 16 |
| Q3783572 | 16 |
| Q809600 | 16 |
| Q1267958 | 14 |
| Q176251 | 14 |
| Q1341595 | 14 |
| Q188740 | 14 |
| Q2603905 | 13 |
| Q46815 | 13 |
| Q1976985 | 13 |
| Q770918 | 12 |
| Q1752085 | 12 |
| Q1641836 | 12 |
