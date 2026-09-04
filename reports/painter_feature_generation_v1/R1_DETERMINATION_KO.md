# Painter Feature Generation v1 — R1 판정 (정식)

- 상태: **구속 판정.** 이 문서의 수치는 연구의 공식 입장 작품 수이며, 이후 모든 단계는 여기서 출발한다.
- 정본: Protocol 2.3 §2·§3 (`studies/painter_feature_generation_v1/PROTOCOL_2.3.md`), Protocol 2.1 §7.3·§7.4·§9.
- 판정기: `src/latent_art_bench/painter_feature_generation_v1/determine.py`
- 판정 결과: `data/manifests/painter_feature_generation_v1/pfg_v1_r1_20260904_determination.jsonl` (3,543행)
- 영수증: `data/manifests/painter_feature_generation_v1/pfg_v1_r1_20260904_determination_receipt.json`
- 생성 명령:
  `uv run --locked latent-art-bench determine --census data/manifests/painter_feature_generation_v1/broad_media_followup_publication_r2/candidates.jsonl --determination-id pfg_v1_r1_20260904`
- 감사 명령: `uv run --locked latent-art-bench verify-evidence`

이 판정은 이미지를 한 장도 내려받지 않았고 픽셀을 한 번도 읽지 않았다. 역할 배정(§8.1)도 하지 않았다.
메타데이터만으로 결정되는 입장 여부만 기록한다. Protocol 2.2 §4가 R1에 요구하는 freeze와 authorization
seal은 **첫 이미지 바이트를 받기 전**에 필요하며 아직 도래하지 않았다.

## 1. 판정 규칙

게이트 7개를 순서대로 통과시키고, 처음 걸리는 곳에서 멈춘다. 점수도, 신뢰도도, 재검토 상태도 없다.

| # | 게이트 | 규칙 | 근거 |
|---|---|---|---|
| 1 | creator | `P170`이 **정확히 하나**이고 대상 화가 QID와 같다 | 2.3 §2.1 |
| 2 | painting | `P31`에 `Q3305213` 포함 | 2.3 §2.2 |
| 3 | medium | `P186`에 `Q296955`(유화)와 `Q12321255`(캔버스) **둘 다** 포함 | 2.3 §2.3 |
| 4 | collection | `P195` 존재 | 2.3 §2.4 |
| 5 | rights | Commons 파일이 개방 라이선스이고, 사용제한 템플릿이 없으며, NC/ND 조건이 없다 | 2.3 §3 |
| 6 | geometry | 원본 단축변 ≥ 1,024 px | 2.1 §7.3 |
| 7 | content | Wikidata 레이블에 대한 §7.4 lexicon 판정이 `eligible_outdoor_place` | 2.1 §7.4 |

한 작품에 Commons 파일이 여러 개일 수 있다. rights와 geometry는 **하나라도 통과하면** 통과로 보고,
통과한 것 중 **가장 큰 파일**을 대리물(surrogate)로 기록한다. 내용 판정은 파일 문자열이 아니라
**레이블만** 본다. 어떤 파일이 선택되든 내용 판정이 흔들리지 않게 하기 위해서다.

## 2. 판정 결과 — 네 화가 모두 하한 통과

| 게이트 | Monet | Sisley | Pissarro | Cézanne |
|---|---:|---:|---:|---:|
| 발견 item | 1,257 | 812 | 766 | 708 |
| creator 통과 | 1,257 | 812 | 766 | 707 |
| painting 통과 | 1,257 | 812 | 766 | 707 |
| medium 통과 | 1,132 | 705 | 685 | 667 |
| collection 통과 | 1,012 | 378 | 533 | 581 |
| rights 통과 | 1,012 | 377 | 533 | 581 |
| geometry 통과 | 662 | 228 | 348 | 481 |
| **입장** | **538** | **196** | **259** | **200** |
| 하한 179 대비 | +359 | **+17** | +80 | +21 |

총 3,543점을 판정해 **1,193점을 입장**시켰다. 화가별 하한 179점(2.1 §9: confirmation 100점을 60%
배정에서 얻는 primary 167점 + 보조 독립촬영 패널 12점)을 네 화가 모두 넘는다.

## 3. 배제 사유

| 게이트 | Monet | Sisley | Pissarro | Cézanne | 계 |
|---|---:|---:|---:|---:|---:|
| creator | 0 | 0 | 0 | 1 | 1 |
| medium | 125 | 107 | 81 | 40 | 353 |
| collection | 120 | **327** | 152 | 86 | 685 |
| rights | 0 | 1 | 0 | 0 | 1 |
| geometry | **350** | 149 | 185 | 100 | 784 |
| content | 124 | 32 | 89 | **281** | 526 |

읽어야 할 세 가지가 있다.

**geometry가 가장 큰 손실이다(784점).** 권위나 내용이 아니라 Commons에 올라온 스캔 해상도가 코퍼스
크기를 결정한다. 1,024 px 문턱은 2.1 §7.3에서 정한 값이고, 낮추면 즉시 수백 점이 들어오지만
Family C 다중스케일 텍스처 좌표의 신뢰도가 함께 떨어진다. 지금 조정하지 않는다.

**Sisley는 collection에서 327점을 잃는다.** 유화·캔버스 진술이 있는 705점 중 46%다. Monet은 11%다.
Sisley 작품이 Wikidata에 소장기관 진술을 덜 갖고 있을 뿐이며, 이를 우리가 채워 넣는 것은 출처를
편집하는 일이라 허용되지 않는다(2.3 §6).

**Cézanne은 content에서 281점을 잃는다.** 야외 장소가 아닌 정물·인물이 그만큼 많다는 뜻이고,
화가에 대한 사실이지 데이터 결함이 아니다.

## 4. 입장 코퍼스의 구성

### 내용 분류

| 분류 | Monet | Sisley | Pissarro | Cézanne |
|---|---:|---:|---:|---:|
| water_organized | 344 | 91 | 56 | 61 |
| built_place_organized | 112 | 55 | 135 | 53 |
| open_or_wooded_land | 69 | 29 | 41 | 65 |
| route_organized | 13 | 21 | 27 | 21 |

**이 표는 §13.4 특이성 대조에 대한 경고다.** Monet 입장작의 64%가 물 중심 장면인데 Pissarro는 22%다.
Monet 프롬프트 출력이 Sisley보다 Monet 코퍼스에 가깝게 측정되더라도, 그 차이의 일부는 화풍이 아니라
**소재 구성 차이**다. Protocol 2.1이 장면 층화를 폐기하고 목표 분포를 작품 균등으로 정한 이상 이것은
게이트가 아니지만, 특이성 결과를 보고할 때 반드시 함께 적어야 한다.

### 대리 이미지 해상도

| 단축변 | Monet | Sisley | Pissarro | Cézanne |
|---|---:|---:|---:|---:|
| 1,024–2,047 | 195 | 76 | 75 | 74 |
| 2,048–4,095 | 252 | 106 | 134 | 95 |
| ≥ 4,096 | 91 | 14 | 50 | 31 |

2.1 §7.3이 선호하는 2,048 px 이상이 입장작의 65%다. Sisley만 ≥4,096이 14점으로 얇다.

### 라이선스

퍼블릭 도메인 1,045점, CC BY-SA 4.0 71점, CC0 37점, 나머지 CC BY 계열 40점. 사용제한 템플릿으로
배제된 파일은 1점이다.

## 5. 이 판정에서 바로잡은 것

**수집 시점의 rights 판정이 과했다.** census는 75건을 `rights_review`로 표시했는데, 원인은 Commons의
`Copyrighted: True` 플래그였다. 그 플래그가 붙은 297건은 전부 CC 라이선스다 — 퍼블릭 도메인 그림을
찍은 **사진**에 저작권이 있고 그것을 개방 라이선스로 공개한, 지극히 정상적인 상태다. 2.3 §3이 권리
근거로 지목한 것은 파일의 라이선스이므로 판정기는 라이선스만 본다. Protocol 2.2가 "수집 시점 판정은
findings가 아니다"라고 한 두 번째 사례다.

**판정기 자체에서 결함을 하나 찾았다.** 라이선스 허용목록을 접두어로만 검사하면 `"CC BY-NC 4.0"`이
`cc by`로 시작하므로 통과한다. 2.3 §3이 명시적으로 배제한 비상업 조건이 조용히 들어올 수 있었다.
라이선스를 토큰으로 쪼개 `nc`/`nd`를 배제하도록 고쳤다. 현재 census에는 해당 파일이 없어 수치는
바뀌지 않았지만, 다음 라우트에서 한 건만 들어와도 통과했을 것이다.

## 6. Protocol 2.3 §6 수치와의 차이

2.3 §6에 기록된 표(Monet 521, Sisley 187, Pissarro 252, Cézanne 197)는 프로토콜 발행 당시의 임시
스크립트 출력이었다. 정식 판정기는 세 가지를 다르게 처리한다.

1. 한 작품에 파일이 여럿일 때 **가장 큰 파일**로 geometry를 판정한다(임시 스크립트는 첫 행만 봤다).
2. 내용 판정에 **레이블만** 쓴다.
3. rights를 라이선스로만 판정한다(§5 참조).

**정식 수치는 이 문서의 것이다.** 결론은 바뀌지 않는다. 네 화가 모두 하한을 넘고, Sisley가 여전히
구속 조건이다(+17). 이후 어떤 규칙을 추가하든 Sisley 수치부터 확인해야 한다.

## 7. 이 판정이 증거인 이유

영수증은 답을 바꿀 수 있는 입력 전부를 SHA-256으로 묶는다: census, 규칙을 진술한 프로토콜 문서,
동결된 content lexicon, 그리고 판정기 소스 자체. `verify-evidence` 감사는 이 다섯 개를 커밋에 묶어
확인하고, 영수증이 보고한 깔때기가 산술적으로 가능한지도 검사한다 — 게이트 순서대로 단조 감소하는지,
마지막 게이트가 입장 수와 정확히 같은지, 배제 사유의 합과 입장 수를 더하면 판정한 작품 수가 되는지.

테스트 `test_the_recorded_determination_is_reproducible_from_its_bound_inputs`는 묶인 census로
판정기를 다시 돌려 기록된 3,543행과 완전히 일치하는지 확인한다. 코퍼스가 그것을 만든 규칙에서
말없이 떨어져 나가면 이 테스트가 깨진다.

## 8. 남은 한계

Protocol 2.3 §5가 진술한 비용은 이 판정으로 사라지지 않으며 모든 보고서에 다시 적어야 한다.

- Wikidata는 편집 심사가 없다. 귀속이 틀릴 수 있고 조정 절차가 없다.
- **오귀속이 무작위가 아니다.** Monet·Sisley·Pissarro는 같은 시기 같은 장소를 그렸고, 혼동이 서로에게
  쏠린다. §13.4 특이성 대조를 양성 쪽에 불리하게 만든다.
- `P186` 결측으로 353점이 유실됐다. 오분류가 아니라 유실이다.
- Commons 파일은 웹 이미지라 학습 데이터 중복이 미술관 IIIF 마스터보다 높다.

## 9. 다음으로 허가되는 행위

역할 배정(2.1 §8.1)이다. 입장한 1,193점에 `SHA256("pfg-v1/2.1-role" ‖ physical_work_id)`를 적용해
development / qualification / sealed_confirmation을 나누고, 노출 denylist 122점을 development 전용으로
고정한다. 여기까지도 이미지는 필요 없다.

그 다음이 이미지 취득이며, **그 전에** Protocol 2.2 §4가 요구하는 freeze와 authorization seal이
필요하다.
