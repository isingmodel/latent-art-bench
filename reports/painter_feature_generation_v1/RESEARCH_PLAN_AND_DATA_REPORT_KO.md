# 생성모델은 실제 화가의 측정 특징분포를 재현하는가?

연구 재설계, 자료준비, 수집계획 및 현재 결과 보고서

- 연구명: `Painter Feature Generation v1`
- 정본 protocol ID: `painter-feature-generation-v1/1.7`
- 자료준비 evidence schema: `painter-feature-generation-v1-data-readiness/1.8`
- 기준일: 2026-09-02
- 현재 판정: **NO-GO — active-study에 승인·다운로드·동결된 작품이 0점**
- 경험적 생성–실제 비교결론: **없음**

## 0. 먼저 읽어야 할 결론

이 프로젝트는 아직 그림을 수집해 분석한 연구가 아니다. 지금까지 실제로 완료한 것은
문헌·과거 pilot·기존 파일을 감사하고, 잘못된 연구질문과 실행 불가능한 표본설계를
폐기하고, 다음 연구를 시작할 수 있는 prospective protocol을 세운 일이다.

현재 연구질문은 반드시 두 부분으로 읽어야 한다.

> 고정 생성모델과 R0a에서 동결한 하나의 공통 24-template prompt frame에 대해,
> (1) 화가명 요청이 availability와 맹검 content-adherence 관문을 통과하는가?
> (2) 그 관문과 copy 감사를 거쳐 기술적으로 분석 가능하고 near-copy가 아닌 output들에서,
> 측정 특징분포가 해당 화가의 R0a 무작위화·봉인-confirmation 실작품 유한모집단을
> 공통 내용으로 표준화한 분포를 재현하는가?

첫째 질문을 통과하지 못한 상태에서 둘째 질문의 일부 성공만 보고할 수 없다. 예를 들어
거부된 요청을 빼고 남은 좋은 이미지만 분석하거나, prompt 내용과 다른 output을 유리한
내용군으로 옮기거나, 특정 실작품을 근접복사한 결과를 화가 분포 재현으로 세면 안 된다.

연구대상은 캔버스의 안료·바인더·물리적 붓질이 아니라, 권위 작품기록과 권리·전달·
capture ancestry가 확인된 **디지털 회화 재현본에서 측정한 세 영상통계 family**다. 따라서
향후 성공하더라도 허용되는 문장은 “이 취득·전처리·특징·모델·prompt frame에서 그
디지털 특징분포를 재현했다”까지다. 화가의 전체 style, 지각된 painterly manner,
unrestricted oeuvre, 진위, 저작권 침해, 훈련자료 포함 여부를 결론내리지 않는다.

### 0.1 이 보고서의 핵심 용어

- **물리작품(physical work)**: 한 점의 실제 회화. 같은 작품의 thumbnail, crop, resize,
  re-encode, 다른 delivery는 새 작품이 아니다.
- **digital surrogate / capture**: 물리작품을 촬영·스캔해 전달한 디지털 재현본과 그
  획득 workflow. 서로 독립인 capture만 reproduction disturbance를 말할 수 있다.
- **source group**: 같은 holding institution과 capture/delivery 계통을 공유하는 묶음.
  source 차이는 화가 차이로 오인될 수 있다.
- **유한모집단 전수(census)**: R0a가 구성원 전체를 먼저 동결하고, access stage가 열릴 때
  그 전부를 측정한다는 뜻이다. 일부를 추출해 전체를 추론하는 표본조사가 아니다.
- **24-template frame**: 가능한 모든 prompt의 표본이 아니라, 사전 동결한 24개 prompt의
  유한 목록이다. 이 목록에 대한 결론만 낸다.
- **active label**: 새 연구 후보에 대한 eligibility, broad scene, 다섯 content-variable
  판정값. 이를 읽기 전에 12개 candidate prompt frame과 선택 code가 hash되어야 한다.
- **\(q^*\)**: 한 24-template frame의 공통 8차원 content target에 맞추기 위해 각 완전
  real population의 모든 작품에 R0a에서 한 번 부여하는 bounded mass. 표본가중치나
  결과를 본 뒤의 보정값이 아니다.
- **availability**: 등록요청 전체 중 기술적으로 분석 가능한 반환이 나온 비율.
  **adherence**는 기술적으로 유효한 반환이 배정된 broad scene group을 시각적으로 따른 비율이다.
- **near-copy 제외**: 특정 실작품의 exact/crop/soft copy로 판정된 생성물을 fit 분석에서
  제외하는 것. 그 생성물은 availability 분모와 copy-rate 분자에서는 사라지지 않는다.
- **NO-GO**: 실패를 성공으로 바꾼다는 뜻이 아니라, 다음 봉인단계를 열 근거가 아직 없다는
  운영판정이다.

## 1. 현재 실행 상태: 수집 결과와 계획을 구분한다

### 1.1 Active-study 수치

| 항목 | 현재 수치 |
|---|---:|
| 승인된 `outdoor_place_landscape` 물리작품 | **0** |
| 자격판정용 ≤512px derivative | **0** |
| active-study 실작품 이미지 다운로드 | **0** |
| active-study 신규 이미지 취득 | **0** |
| R0a 동결 물리작품 | **0** |
| auxiliary independent-capture census 물리작품 | **0** |
| 검증된 독립 capture pair | **0** |
| 등록된 생성요청 | **0** |
| 생성 output | **0** |
| 생성–실제 비교결과 | **0** |

따라서 아래의 실작품 1,440점·external 포함 1,824점은 **현재 보유량이 아니라 미래 설계의
최소 frame 용량**이다. 생성요청 수도 현재 0이다. v1.5의 1,920요청은 v1.7에서 폐기되었고,
모든 repetition이 서로 다른 auditable independence unit이라는 절대 최선의 가정에서도
수학적 하한은 3,000요청이다. common-shock clustering은 이를 늘리거나 rate bound 자체를
무정보적으로 만들 수 있으며, 실제 등록 수는 아직 미정이다.

### 1.2 지금 확보된 것은 무엇인가

현재 확보된 것은 세 종류의 탐색·역사 자료다.

1. 과거 pilot의 candidate ledger와 로컬 JPEG inventory
2. 네 공식기관에서 다시 찾을 수 있는 43건의 live metadata 후보 목록
3. Wikidata/Commons에서 찾은 3,190개 painting-item **census 후보경로**와 실패한 40건의
   Commons file 점검 기록

어느 것도 active-study 실작품 corpus가 아니다. 물리작품 identity, 정확 attribution,
oil-on-canvas support, 작품·미디어 권리, 실제 file geometry와 decode, capture ancestry,
outdoor-place content, 중복, source balance를 prospective R0a에서 다시 닫아야 한다.

## 2. 왜 연구를 다시 설계했는가

### 2.1 과거 질문은 최종 질문이 아니었다

과거 `painter_features_v1`은 실제 그림에서 측정좌표가 안정적인지를 엄격하게 검증하는
real-only 방법연구였다. 이 단계는 필요하지만 생성분포를 한 장도 직접 비교하지 않으므로
“생성모델이 화가 특징을 재현하는가?”에 답하지 않는다. 화가분류 정확도, A-vector
centroid, 이름 조건이 control보다 목표 쪽으로 조금 움직였다는 결과도 분포 재현의
대체물이 아니다.

새 연구는 다음 실패양상을 분리한다.

1. 요청이 거부되거나 분석 가능한 output이 부족함
2. output이 지정한 내용군을 따르지 않음
3. 실제 목표분포와 절대적으로 멂
4. 중심은 가깝지만 spread·tail·mode를 덮지 못함
5. 목표 화가보다 이웃 화가에도 비슷하게 가까움
6. 특정 실작품을 근접복사해 겉보기 적합성이 생김
7. source·capture·서명·frame 또는 내용 shortcut에 의존함

### 2.2 좁은 6개 scene-cell 동일 quota가 왜 폐기되었는가

이전 설계는 화가마다 coast/sea/harbor, river/canal, lake/pond,
street/village/settlement, road/path, field/hillside/forest/orchard의 좁은 여섯 scene을
같은 수로 채우려 했다. 이것은 “내용을 통제한다”는 의도는 좋았지만, 권위·권리·품질을
통과한 작품이 모든 화가×좁은 scene에서 풍부하다는 검증되지 않은 가정을 quota로
바꾼 것이었다.

이를 반증하기 위한 filename stress test는 3,190개 discovery 후보에서 decoded Commons
filename이 대소문자 무시 whole token으로 다음 중 하나를 포함하는 creator-item row를 셌다.

`lake | pond | lac | étang | etang | bassin | pool`

그 결과는 **Pissarro 5, Sisley 1, Monet 46, Cézanne 6 item row**였다.

| 화가 | 일치 item row |
|---|---:|
| Camille Pissarro | **5** |
| Alfred Sisley | **1** |
| Claude Monet | **46** |
| Paul Cézanne | **6** |

이 결과는 content coding이나 물리작품 수가 아니다. filename은 다국어이고 누락·오표기·
중복이 있으며, 작품 자격이나 특정 scene의 진짜 부재를 증명하지 않는다. 그러나 최소한
“각 화가의 좁은 lake/pond cell에 합법적·적합한 작품 60점이 있을 것”이라는 전제는
근거가 없음을 보여준다. 이 stress test의 등록된 용도는 **좁은 scene 동일 quota를
폐기하는 것뿐**이다.

새 설계는 희소한 cell을 억지로 채우지 않는다. 화가별로 큰 유한 frame을 먼저 만들고,
네 개의 넓은 scene group과 다섯 visible-property contrast가 공통인 하나의 target을
bounded population weight로 맞춘다. 옛 여섯 범주는 가능할 때 진단값으로 기록하지만
sampling cell이나 quota가 아니다.

### 2.3 Pilot 0–3에서 실제로 배운 것

- **Pilot 0**: 108개 canonical work와 119개 reproduction을 만들었지만 chromatic JPEG
  안정성과 learned-formal source-faithful reproduction 관문이 실패했다. 정식 결정은
  `stop before scientific generation`이었다. 명시적 bypass로 성공한 API smoke 10건은
  transport 기록이지 과학적 생성 비교가 아니다.
- **Pilot 1**: 공학 pipeline은 완주했지만 두 feature card가 모두 실패했다. chromatic
  border-clear primary는 0/108이었고, learned-formal PCA 보존분산은 0.6152로 목표
  0.95에 미달했다. same-work interval 상한 1.1002는 margin 1.0을 넘었고 source coverage도
  불완전했다. 실패한 관문 뒤의 bypass 분석은 자격을 회복시키지 않는다.
- **Pilot 2**: 두 requested-label stratum, 8 matched content block, block마다 네 painter-name
  조건과 공유 artist-free control, 4회 반복으로 \(2\times8\times5\times4=320\) logical
  request를 등록했다. 315건은 성공했지만 refusal 5건(`gpt-image-1` 4,
  `gpt-image-2` 1)을 교체하지 않아 feature pair는 124/128과 127/128, 합계 251/256이었다.
  두 label grid가 모두 불완전해 target-improvement와 specificity-improvement의 네 primary
  test는 모두 실행하지 않았다. 가용 pair의 움직임은 기술통계일 뿐 fidelity 결과가 아니다.
  실작품 source probe도 pooled held-work balanced accuracy 0.500, AIC 0.625, NGA 0.375,
  반대 source 전이 AIC 0.250·NGA 0.375, source-label predictability 0.8125로 source shortcut
  위험을 보였다. 각 source held set이 8점뿐이므로 일반화하지 않되, paired name-control
  구조는 유지하고 prompt movement를 2차로 낮춘다.
- **Pilot 3**: 예정 52점 중 AIC development 20점만 취득·정규화했다. Met R2는 첫 metadata
  request의 terminal HTTP 403에서 닫혔고 Met image request는 0건이었다. 다른 endpoint로
  우회하거나 미완성 cohort에 feature를 추출하거나 외부·생성 단계를 여는 것은 금지된다.

공통 교훈은 간단하다. 실패한 목표를 더 쉬운 목표로 바꾸지 말고, 물리작품·capture·
source·content·request 결측의 단위를 먼저 동결해야 한다.

## 3. 문헌검토에서 확인한 근거와 한계

### 3.1 문헌 corpus의 범위

현재 `literature_reviews/EVIDENCE_MATRIX.csv`에는 고유 structured evidence record
**144개**, `literature_reviews/BIBLIOGRAPHY.md`에는 고유 included-source 항목 **205개**가
있다. 일부는 full text와 code까지, 일부는 methods/results 또는 abstract만 감사되어
깊이가 다르다. 과거 web search의 완전한 result export와 record-level exclusion ledger가
없으므로 PRISMA flow, 검색 포화, 완전성을 주장하지 않는다. “205개를 모두 같은 깊이로
review했다”는 문장도 쓰지 않는다.

### 3.2 Kim et al.을 어떻게 사용하고 어떻게 사용하지 않는가

Kim, J., Lee, B., You, T., & Yun, J. (2026), “Context-aware multimodal AI navigates hidden
pathways in five centuries of art evolution,” *Proceedings of the National Academy of Sciences,
123*(30), e2517969123, DOI `10.1073/pnas.2517969123`. 이 논문은 ART500K에서 정제한
72,447점, 2,354명, 1500–1990년 자료를 사용한다.

- A-vector는 Stable Diffusion 2.0 1단계 VAE의 `4×64×64` posterior latent를 펼친
  16,384차원 coordinate다.
- C-vector는 1,024차원 CLIP 계열 image representation이다.
- A 경로는 512×512 강제 변형, VAE·codec·content·source를 함께 담고 posterior sampling
  계약도 재현성에 영향을 준다.
- 논문의 질문은 시간·맥락을 포함한 미술사 구조이며, 생성이미지가 특정 화가의
  실작품 분포를 재현하는지를 검증하지 않았다.
- 공개 A script에는 return 뒤에 들여쓰기된 도달 불가능 model initialization,
  module-level undefined `model`, author-local path가 남아 있어 그대로 실행되는 완전한
  reproduction package가 아니다.
- paper와 공개 C code가 정확히 동일한 checkpoint contract를 제공한다고 확인할 수 없다.

따라서 Kim A는 `SD2-VAE appearance compatibility`, C는 semantic/context diagnostic으로만
명명한다. 수정해서 실행한 구현은 exact replication이 아니라 adaptation이며, A/C 하나를
“화가 특징의 참값”이나 primary fidelity score로 쓰지 않는다.

원문: <https://doi.org/10.1073/pnas.2517969123>

### 3.3 직접 관련된 생성·style 평가 문헌

- **[Somepalli et al., CSD](https://doi.org/10.1007/978-3-031-72848-8_9)**:
  511,921개 image와 3,840 style tag로 Contrastive Style
  Descriptors를 학습하고 WikiArt 80,096점·1,119명, 생성실험 400명에 적용했다. set/prototype,
  content-controlled prompt, hard neighbor라는 설계는 유용하다. 그러나 caption-derived
  tag supervision, CLIP initialization, random work split, checkpoint discrepancy 때문에 raw
  cosine threshold를 보편 화가-fidelity gate로 옮기지 않는다.
- **[ArtSavant](https://proceedings.iclr.cc/paper_files/paper/2025/file/63ef323523f3be8b58ed9277cc747485-Paper-Conference.pdf)**:
  약 91,000개 WikiArt 작품·372명에서 set-level DeepMatch와 TagMatch,
  비슷한 화가와 abstention을 다룬다. 이름 인식은 유용한 진단이지만 subject, period,
  source, encoder exposure로도 가능하므로 oeuvre coverage가 아니다.
- **[ArtFID](https://doi.org/10.1007/978-3-031-16788-1_34)**: content loss와
  art-domain Fréchet distance를 분리하고 31,200 crowd pairwise
  task로 neural style-transfer method rank를 비교했다. content와 style-related 결과를
  분리한다는 원리는 채택하지만, paired NST와 자유 text-to-image painter distribution은
  다른 과업이고 소표본 raw FID는 primary가 아니다.
- **[MMD](https://www.jmlr.org/papers/v13/gretton12a.html)·[energy
  statistics](https://doi.org/10.1016/j.jspi.2013.03.018)·precision/recall·density/coverage**:
  분포차이와 support failure를 표현하지만
  representation 자체의 construct validity를 보장하지 않는다. energy를 primary discrepancy로
  쓰되 나머지는 sensitivity 또는 표본수·(k) 진단으로 둔다.
- **[SSCD](https://openaccess.thecvf.com/content/CVPR2022/html/Pizzi_A_Self-Supervised_Descriptor_for_Image_Copy_Detection_CVPR_2022_paper.html)와
  memorization 문헌**: exact/crop/near-copy를 painter fit과 별도 감사해야 함을
  지지한다. 검색 hit가 없다는 것은 알려지지 않은 전체 training corpus에 없었다는 증거가
  아니다.
- **digitization/source 문헌**: ICC, resize, JPEG, border, independent capture를 닫지 않으면
  painter signal과 reproduction signal을 구분할 수 없다.

### 3.4 수학 원전이 지지하는 범위와 지지하지 않는 범위

**[Csiszár (1975)](https://doi.org/10.1214/aop/1176996454)**는 확률분포의 convex set에 대한
I-divergence geometry와 상대엔트로피 최소화, 즉 KL/I-projection 형태의 수학적 근거다. 이
원전이 지지하는 것은 uniform mass에서 사전지정 linear moment constraint로 투영하는
목적함수의 형태다. 본 연구가 고른 8개 content moment, 작품당 uniform의 4배 weight cap,
Kish ESS 60%, source-share cap, 또는 “화가 특징 재현” construct의 타당성은 지지하지 않는다.
그 선택들은 프로젝트 고유의 prospective gate이며 R0a feasibility와 R1a simulation에서
별도로 실패 가능해야 한다.

**[Hoeffding (1963)](https://doi.org/10.1080/01621459.1963.10500830)**은 서로 독립인 bounded
unit의 합에 대한 one-sided exponential tail inequality를 제공한다. 이 원전은 remote request의
독립성을 만들어 주지 않으며, 본 연구의 endpoint inventory, \(\alpha\) 분할, 네 directional
bound, ratio bound \(L_J/U_A\)·\(U_K/L_A\), 0.90·0.80·0.10 threshold도 선택하지 않는다.
따라서 independence-unit 정의와 모든 과학적 threshold는 프로젝트 고유이며, 실제 dependence
design에서 R1a coverage simulation을 통과해야 한다. 두 원전의 추가는 화가 재현에 대한 새
경험적 증거가 아니다.

### 3.5 HT와 Rao–Wu 문헌을 보존하지만 active estimator에서 쓰지 않는 이유

Horvitz & Thompson([1952](https://doi.org/10.1080/01621459.1952.10483446))과
Rao & Wu([1988](https://doi.org/10.1080/01621459.1988.10478591))는 비복원 확률표본과 complex survey
resampling의 중요한 원전이다. 이전 probability-sample 설계에서는 1·2차 포함확률과
design-consistent bootstrap을 검토할 이유가 있었다. 그러나 protocol 1.7은 R0a가 취득한
development·qualification·confirmation·external population을 각 access stage에서 **전수
측정**한다. 선언한 유한모집단에 조건부로 real-work sampling error가 없으므로 HT inverse
probability weight나 Rao–Wu real bootstrap을 적용하면 존재하지 않는 sampling noise를
만드는 셈이다.

따라서 문헌은 삭제하지 않되 active continuous inference는 real census를 고정하고 generator
repetition만 재표집한다. availability·adherence·copy rate는 empirical bootstrap이 아니라
별도 boundary-safe bound를 쓴다. source·digitization uncertainty는 independent-capture census,
held-source, leave-one-source, perturbation, uniform-real sensitivity로 다룬다.

## 4. 기존 자료를 다시 감사한 결과

### 4.1 역사적 candidate audit: 194행

`configs/pilot_0/candidate_work_audit.jsonl`의 hash-bound ledger는 194행이다.

| 기존 판정 | 행 수 |
|---|---:|
| include | 142 |
| exclude | 50 |
| review | 2 |
| 합계 | **194** |

include 142행의 화가·source 분포는 다음과 같다.

| 화가 | AIC | CMA | Met | NGA | 합계 |
|---|---:|---:|---:|---:|---:|
| Alfred Sisley | 6 | 1 | 7 | 7 | 21 |
| Camille Pissarro | 7 | 3 | 15 | 15 | 40 |
| Claude Monet | 32 | 3 | 0 | 19 | 54 |
| Paul Cézanne | 5 | 3 | 10 | 9 | 27 |
| 합계 | 50 | 10 | 32 | 50 | **142** |

medium 문자열이 문자 그대로 `oil on canvas`인 include만 남기면 133행이다.

| 화가 | AIC | CMA | Met | NGA | strict-canvas 합계 |
|---|---:|---:|---:|---:|---:|
| Alfred Sisley | 6 | 0 | 7 | 7 | 20 |
| Camille Pissarro | 6 | 1 | 15 | 14 | 36 |
| Claude Monet | 32 | 2 | 0 | 19 | 53 |
| Paul Cézanne | 5 | 0 | 10 | 9 | 24 |
| 합계 | 49 | 3 | 32 | 49 | **133** |

142나 133은 물리작품 수가 아니다. 같은 작품의 여러 asset/capture, 현재 attribution,
support ontology, 권리, geometry, content를 다시 판정해야 한다.

### 4.2 로컬 JPEG inventory

`data/pilot_0/source/`의 역사적 inventory는 다음과 같다.

| 화가 | primary-name file | alternate-name file | 전체 JPEG |
|---|---:|---:|---:|
| Alfred Sisley | 21 | 0 | 21 |
| Camille Pissarro | 32 | 7 | 39 |
| Claude Monet | 33 | 9 | 42 |
| Paul Cézanne | 27 | 3 | 30 |
| 합계 | **113** | **19** | **132** |

- 전체 byte: 69,549,332
- primary file 113개는 모두 서로 다른 SHA-256
- 같은 byte hash의 primary duplicate: 0
- 전체 filename+SHA-256 digest:
  `68173e1a117a9391adb1dc9b4f30b1338f09eb8838708495f48c5e92f7b42219`

byte hash가 다르다는 사실은 물리작품이 다르다는 뜻이 아니다. crop, resize, re-encode,
다른 capture의 같은 작품일 수 있으므로 accession과 perceptual comparison으로 묶어야 한다.

과거 pixel-exposure denylist에는 물리작품 ID 118행이 있다. strict-canvas 후보에서 이
denylist와 Freeze 3 네 점을 제외했을 때 기록상 미노출 후보는 25행뿐이다: Sisley 0,
Pissarro 6, Monet 19, Cézanne 0. 이것은 model training 미노출을 뜻하지 않고, 프로젝트
내부 exposure ledger에서 찾지 못했다는 좁은 뜻이다. 기존 자료만으로 네 화가의 새 external
population을 만들 수 없다.

### 4.3 공식기관 live-item audit: 43건

네 기관의 exact live record ID를 보존한 exploratory metadata audit은 다음 43건을 찾았다.

| 공식 source | 후보 수 |
|---|---:|
| Yale University Art Gallery | 16 |
| Paris Musées | 9 |
| J. Paul Getty Museum | 10 |
| Minneapolis Institute of Art | 8 |
| 합계 | **43** |

탐색 audit에서 사용한 권리 근거도 source마다 달랐다.

| source | record-level 탐색 근거 | R0a에서 다시 닫아야 할 점 |
|---|---|---|
| Yale | accepted IIIF manifest의 top-level CC0와 canvas의 `No Copyright - United States` | exact manifest·canvas·delivery response를 다시 snapshot |
| Paris Musées | 개별 work page의 CC0 marker와 image credit | manifest 자체에는 license field가 없으므로 work page와 API account/query context를 보존 |
| Getty | preferred media JSON의 exact CC0 `subject_to`, download clearance, native dimensions | collection dataset 전체의 CC0를 image 권리로 대체하지 말고 exact media record를 재확인 |
| MIA | item의 `Public Domain`, `public_access=1`, `Rights_Image_Display=Full` | CC0로 재명명하지 않으며, 정책문구가 엇갈리므로 raw 고해상도 재배포는 별도 확인 전 금지 |

화가별로는 Pissarro 11, Monet 13, Cézanne 12, Sisley 7건이다. 이들은 exact attribution,
oil-on-canvas, metadata rights/image/geometry screen을 탐색적으로 통과한 **모든 content의
live metadata 후보**다. mutable response byte와 시점 hash를 완전 봉인한 snapshot이 아니며,
Getty/MIA retrieval window도 근사적이다. 이미지 다운로드 0, outdoor-place 승인 0,
동결 물리작품 0이다. 43을 수집된 landscape나 실험표본 수로 쓰지 않는다.

### 4.4 Wikidata/Commons 규모경로

federated evidence schema는 `painter-feature-generation-v1-federated-census/1.3`이다.
2026-09-02 exploratory query는 creator가 네 화가이고 Commons image가 있으며 material에
oil paint와 canvas statement가 있는 Wikidata painting item을 셌다.

| 화가 | distinct creator-item 후보 |
|---|---:|
| Camille Pissarro | 685 |
| Alfred Sisley | 705 |
| Claude Monet | 1,132 |
| Paul Cézanne | 668 |
| 합계 | **3,190** |

- item-image row: **3,367**
- distinct Commons file link: **3,364**

raw discovery item을 모두 서로 다른 적합작품이라고 가정해도 필요한 산술 yield 하한은 높다.

| 화가 | internal 360/item 수 | external 포함 456/item 수 |
|---|---:|---:|
| Camille Pissarro | **52.55%** | **66.57%** |
| Alfred Sisley | **51.06%** | **64.68%** |
| Claude Monet | **31.80%** | **40.28%** |
| Paul Cézanne | **53.89%** | **68.26%** |

이는 noisy pre-dedup discovery item을 분모로 단순 나눈 **산술 하한**이지 pass-rate 추정치가
아니다. authority, rights, geometry, outdoor content, source diversity, capture ancestry,
deduplication은 usable yield를 더 낮출 수 있다.

이 수는 작품 3,190점을 수집했다는 뜻이 아니다. Wikidata statement 오류, 여러 image가
가리키는 한 물리작품, 잘못된 attribution/support, Commons file rights·geometry,
권위 holding record, capture ancestry, content가 아직 검증되지 않았다.

따라서 3,190은 **완전한 R0a census를 실행할 가치가 있는 candidate universe**만 뜻한다.
필요한 pass yield가 가능하거나 1,440점 frame을 만들 수 있다는 근거가 아니다. feasibility를
말하기 전에 화가별로 discovery item → authority reconciliation → exact attribution·painting·
oil-on-canvas → item/media rights → delivery·geometry·decode → physical-work dedup·capture ancestry
→ outdoor-place/broad-group coding → source-share·\(q^*\) feasibility → final admission의 각 gate에서
들어온 수, 제외 수, 사유를 보존한 exact attrition funnel을 공개해야 한다.

화가당 결정적 10건, 총 40건의 Commons file 요청은 모두 HTTP 429였다. resolved 0,
retry 0, fallback 0이다. 원인을 concurrency나 provider 정책으로 추정하지 않는다. 이 시도로
file-level license, geometry, image quality 수치를 말할 수 없으며, R0a는 동결된 ordered
intent와 provider rate limit을 지키는 새 ledger로 시작해야 한다.

## 5. v1.7의 실제 real-work 설계

### 5.1 표본이 아니라 동결 유한모집단 전수다

각 화가에서 최소 360개 적합 물리작품을 모두 취득·판정하고 한 번 무작위화한다.

| population | 화가당 | 네 화가 합계 | access와 역할 |
|---|---:|---:|---|
| development | 72 | 288 | R0a 뒤 전수 측정, 방법·margin 개발 |
| untouched qualification | 108 | 432 | R0b에서 전부 방출, R1b 일회 자격검증 |
| sealed confirmation | 최소 180 | 최소 720 | G1a seal 뒤 G1b에서 전부 일회 개봉 |
| internal 합계 | **최소 360** | **최소 1,440** | 취득 수와 분석 수가 같음 |
| optional unopened-source external | 최소 96 | 최소 384 | 같은 R0a에서 전부 취득·동결·별도 분석 |
| external 포함 합계 | **최소 456** | **최소 1,824** | internal과 pooled rescue 금지 |

R0a painter-level CSPRNG permutation은 rank 1–72를 development, 73–180을 qualification,
181 이상을 sealed confirmation으로 배정한다. rank는 exposure role을 나누는 장치이지,
뒤에서 일부 작품만 뽑는 sampling rank가 아니다. R0b는 qualification 108점을 모두 열고,
G1b는 confirmation을 모두 연다. real-work subsampling, inclusion probability, inverse weight,
real bootstrap은 없다.

각 화가 internal frame은 네 broad scene group마다 최소 24점을 가져야 한다. external을
등록하면 각 화가 external population도 group마다 최소 8점을 가져야 한다. 이 숫자는
support alarm이지 1/4 quota나 inferential sufficiency 보장이 아니다.

### 5.2 네 broad scene group

모든 적합 작품은 다음 중 정확히 하나를 받는다.

1. `water_organized`: sea, coast, harbor, river, canal, lake, pond, stream이 scene을 조직
2. `built_place_organized`: building, settlement, street, square, industrial place가 조직하고
   water가 주 조직자가 아님
3. `route_organized`: dominant settlement 밖의 road, path, lane, track이 조직
4. `open_or_wooded_land`: field, hillside, mountain, forest, orchard, garden 또는 나머지
   terrestrial landscape가 조직

코더는 화가명·제목·필요 count를 보지 않고 시각적 principal spatial organizer를 판정한다.
water surface/channel/coastline이 composition을 조직할 때만 water가 이긴다. incidental
stream은 충분하지 않다. 다음으로 built, route, residual land 순서다. frozen area/focal rule로도
주 조직자를 정할 수 없으면 `ambiguous_multiple`로 제외한다. 필요한 group을 채우려고
판정을 바꾸지 않는다.

과거 여섯 narrow scene category는 판정 가능할 때 진단용으로 남긴다. sampling cell,
prompt quota, primary estimand이 아니다. career date는 화가의 eligible-domain variation이므로
phase별 heterogeneity로 보고하되 화가들을 인위적으로 같은 시기로 맞추지 않는다.

### 5.3 다섯 content variable과 visible-property contrast

코더는 broad group과 함께 다음 full category를 기록한다.

1. season/foliage: `leafless_or_winter`, `spring_or_blossom`, `full_green_foliage`,
   `autumn_or_senescent`, `indeterminate`
2. illumination/weather: `clear_direct_light`, `diffuse_or_overcast`, `fog_rain_or_snow`,
   `dawn_dusk_or_night`, `indeterminate`
3. built-element prominence: `absent`, `incidental`, `organizing_or_dominant`
4. people/animal/boat/vehicle prominence: `absent`, `incidental`,
   `organizing_or_dominant`
5. view depth: `shallow`, `middle`, `deep`, `indeterminate`

생성 template은 이 다섯 변수에 `indeterminate`를 사용하지 않는다.

primary standardization은 full-category multi-contrast rake가 아니라 정확히 다섯 binary
contrast를 쓴다.

1. visible `leafless_or_winter`
2. visible diffuse/adverse/low light: `diffuse_or_overcast`, `fog_rain_or_snow`,
   `dawn_dusk_or_night` 중 하나
3. `organizing_or_dominant` built element
4. any visible person/animal/boat/vehicle: `incidental` 또는 `organizing_or_dominant`
5. visible `deep` view

`indeterminate`는 해당 visible-property contrast에서 0을 받지만 determinate 반대범주로
재명명하지 않는다. full categorical table과 indeterminate rate는 의무 진단이다.

### 5.4 열두 candidate prompt frame과 8차원 공통 target

active label을 읽기 **전에** R0a-intent는 정확히 12개의 완성된 candidate frame과 selection
code를 hash한다. 각 candidate는 24개의 의미론적으로 일관된 template를 가지며 네 broad
group마다 최소 2개 template를 포함한다. 각 template에서 hash할 대상은 byte-exact UTF-8
artist-free text, `<target_painter>` placeholder가 정확히 한 번 들어간 byte-exact named
rendering, exact painter-name substitution table, punctuation, language, negative-prompt string,
condition insertion point, broad-group
label, 다섯 content value, render function이다. painter name, title, museum, distinctive object,
평가작품 고유구도는 template attribute에 들어가지 않는다. 독립 wording/codebook review도
active label 전에 끝나며, R1a는 hash를 감사할 수만 있고 G0를 포함한 어느 후속단계도 문자열을
고쳐 쓸 수 없다. wording이나 syntax adaptation이 필요한 endpoint는 이 version에서 제외하거나
새 protocol/R0a를 시작한다.

한 번의 painter-level population assignment 뒤, R0a는 content label만 사용해 각 candidate의
공통 8차원 target (m)을 만든다.

- 네 broad-group proportion 중 비중복 3차원
- 다섯 visible-property mean

각 painter의 development, qualification, confirmation, 등록 external **각 전체 population**에서
다음 entropy projection을 푼다.

\[
q^*=\arg\min_{q_i\ge0}\sum_{i\in U}q_i\log\{q_i/(1/N)\},\qquad
\sum_iq_i=1,\qquad \sum_iq_i z_i=m.
\]

이는 [Csiszár (1975)](https://doi.org/10.1214/aop/1176996454)의 의미에서 uniform finite
distribution을 사전지정 linear moment constraint에 KL/I-project하는 형태다. 원전은 이
최적화 형식의 근거일 뿐, 여기서 선택한 8개 moment, 4× mass cap, 60% Kish ESS,
source-share cap 또는 painter-fidelity construct를 검증하지 않는다.

candidate가 살아남으려면 모든 intended population에서 동시에 다음을 만족해야 한다.

- 완전한 8차원 target이 joint convex hull 안에 있음
- unique solution과 frozen numeric tolerance
- 한 작품의 mass가 uniform (1/N)의 4배 이하
- Kish \(ESS=1/\sum_i(q_i^*)^2\)가 \(0.60N\) 이상

survivor 중 minimum Kish-ESS fraction을 최대화한다. tie이면 차례로 maximum relative weight를
최소화하고, broad-group proportion의 1/4로부터 squared deviation을 최소화하고,
lexicographic frame ID를 쓴다. 이 finite selection은 feature, generated image, painter-favorable
distance, source-quality outcome을 보지 않는다.

어느 한 공통 candidate도 모든 population을 통과하지 못하면 R0a는 NO-GO다. redraw,
regularization, 같은 version의 top-up, painter별로 다른 target 선택을 금지한다. 선택된
frame, (m), 모든 (q^*), solver receipt, convex-hull·weight·ESS 판정을 봉인한다.

(q^*)로 표준화한 census가 primary real target이다. uniform (1/N) census는 의무 sensitivity다.
둘 다 실제 observed source mixture를 포함하며 unrestricted oeuvre가 아니다. exact interaction이나
5-way joint profile을 맞췄다고 주장하지 않는다.

### 5.5 Source와 auxiliary independent-capture census

internal 전체 frame과 그 development·qualification·confirmation **각 population**은 화가당
holding/capture source group이 최소 네 개여야 한다. 아직 공통 content target이 정해지지 않아
\(q^*\)가 정의되지 않는 **전체 internal frame**에서는 source cap을 unweighted share로만
판정하며, 어느 source도 30%를 넘지 못한다. 반면 무작위 배정된 development·qualification·
confirmation 각 population에서는 어느 source도 unweighted share와 그 population의 최종
\(q^*\) mass 모두 30%를 넘지 못한다. 권위 federation이 허용하면 전체 frame의 broad scene
group마다 source group을 최소 두 개 둔다. source가 둘 이상인 broad group에서는 전체 frame은
unweighted share만, \(q^*\)가 정의된 development·qualification·confirmation population은
unweighted share와 scene-conditional \(q^*\) mass를 함께 보며 어느 source도 70%를 넘지
못한다. 구조적으로 한 source뿐인 group은 `source_domain_limited`이며 provider-general claim을
금지한다. assignment 뒤 각 population의 incidence·unweighted-share·weighted-share table을
그대로 봉인하고, 불리하다고 redraw하지 않는다.
source는 sampling stratum이나 채워야 할 museum quota가 아니라 binding balance·robustness
gate이며, 관찰된 source mixture 자체가 digital-surrogate estimand의 일부다.

Optional external은 “다른 URL”이라는 뜻이 아니다. 같은 R0a에서 candidate, 저해상도 label,
painter-level rank를 모두 동결하고, analysis team이 analysis-resolution pixel이나 feature를
보지 않은 holding/capture group과 physical-work family로 구성해야 한다. 화가당 unopened
source group이 최소 두 개여야 하고, 어느 하나도 external 전체의 unweighted share 또는
\(q^*\) mass 70%를 넘지 못한다. external의 source가 둘 이상인 broad scene에서도 어느
source도 그 scene의 unweighted share나 scene-conditional \(q^*\) mass 70%를 넘지 못하며,
이 \(q^*\)들은 external assigned population 안에서만 정의·계산한다. external 결과는
internal과 별도로 분석하며 internal 실패를 pooled 결과로 구제하지 않는다.

별도 auxiliary same-work-reproduction **census**는 randomized study frame 밖에 둔다.

- R0a source snapshot 안에서 조건을 만족하는 작품은 외관이나 feature로 선별하지 않고 전부 포함
- 화가당 최소 8점, 총 최소 32점
- 화가당 최소 3 broad scene group
- 화가당 최소 2 holding/capture-workflow pair type
- 작품마다 demonstrably independent capture workflow 최소 2개
- 같은 capture의 size, crop, re-encode, mirror, 반복 delivery는 독립으로 세지 않음
- auxiliary 작품과 capture는 1,440/1,824 totals에 포함하지 않음

한 번의 공통 pooled-development scaling 뒤 한 작품·family의 capture disturbance는 모든 independent capture pair의
RMS coordinate difference 중 최대다. 관찰 workflow bound (eta_F)는 census 작품 전체의
최대다. family는 (eta_F\le0.5) scaled-IQR이고 모든 coordinate의 maximum absolute paired
shift도 0.5 IQR 이하여야 한다. 이는 관찰 census의 exact bound이지 세상 모든 digitization
workflow에 대한 confidence bound가 아니다.

## 6. R0a 실제 수집 SOP

### 6.1 시작 전 동결

1. official bulk/API version, 조회시각, exact query, rights 문구, response snapshot hash를 동결한다.
2. 12개 complete prompt-frame candidate의 byte-exact dual rendering, exact painter-name
   substitution table, punctuation, language, negative prompt, insertion contract, content label,
   render function과 selection code를 active label 열람 전에 hash한다.
3. provider별 ordered acquisition intent를 network access 전에 append-only ledger에 쓴다.
4. provider 문서의 rate limit, single-thread rule, 허용 MIME·redirect·delivery contract를 동결한다.
5. 역할을 acquisition/coding, feature/method/generation, independent review로 분리한다.

Primary source hierarchy는 traceable work identity와 image delivery가 있는 AIC, NGA, CMA,
Smithsonian, Yale, Paris Musées, Getty, MIA 같은 공식 open-collection record다. 다른 공식기관은
R0a에서 exact data version, query, rights statement, delivery contract, provider code를 먼저
동결한 경우에만 추가한다. WikiArt·ART500K는 literature-comparable development/benchmark
view일 뿐 confirmation source가 아니며, search-result scrape, Pinterest, auction preview,
attribution 없는 mirror는 쓰지 않는다.

### 6.2 Item-level admission

각 후보는 다음을 모두 통과해야 한다.

- exact painter attribution; `attributed to`, `after`, `workshop of`는 primary 제외
- object classification이 painting
- raw medium을 보존하고 ontology로 `oil_on_canvas` 확인
- board, panel, paper, mixed support, unresolved `fabric` 제외
- public-domain 또는 institutionally open image 상태를 item/media 수준에서 기록
- 권위 work page와 실제 image endpoint 연결
- delivered short side ≥1,024px, upsampling 없음
- complete decode, credible geometry, ICC/profile 상태 보존
- 네 broad outdoor-place group 중 정확히 하나와 다섯 변수 coding

Wikidata/Commons는 discovery/delivery layer다. Commons asset은 authority holding/catalogue
record, exact attribution/support, file-page reuse statement, geometry, capture ancestry가 연결된
경우에만 primary 후보가 된다. aggregator 전체 문구는 item/media rights를 대신하지 않는다.
Met R2는 닫혔으므로 새 endpoint나 fallback으로 재시도하지 않는다.

### 6.3 전달과 보존 ledger

provider당 qualification object 두 개를 먼저 받아 delivery·decode contract를 검증한다.
main queue는 이 관문 뒤 single-thread, provider-throttled로 실행한다. 각 attempt에 다음을 남긴다.

- timestamp, exact URL, object/asset ID
- HTTP status, redirect chain, content type
- byte count, pixel width/height, ICC/profile
- immutable source-file SHA-256
- rights basis와 source snapshot reference
- 실패·retry eligibility·최종 terminal status

별도 attrition ledger는 화가별 discovery item을 고정된 gate 순서로 추적한다. 각 gate마다
입력 ID, 통과 ID, 제외 ID, 하나의 primary exclusion reason, 누적 잔여 수를 남겨야 하며,
최종 보고서는 화가×gate funnel을 모두 공개한다. 3,190개 시작행과 최종 admission만 비교하는
요약은 어느 gate가 frame을 무너뜨렸는지 알 수 없으므로 충분하지 않다.

frozen intent에 cross-provider fallback을 하지 않는다. source file은 overwrite하지 않고 ignored
research workspace에 보존하며 Git에는 compact manifest, hash, rights evidence, report만 둔다.

### 6.4 Identity graph와 중복

physical work, capture event/family, museum-published asset, derivative service, delivered file ID를
분리한다. accession/catalogue/Wikidata ID, title/year/dimensions, exact hash, pHash/SSCD와 시각
검토로 collision을 reconcile한다.

- 다른 IIIF size, thumbnail, re-encode, crop, mirror는 새 작품이 아님
- 독립 capture도 physical-work sample size를 늘리지 않음
- related capture/derivative는 서로 다른 development·qualification·confirmation role에 갈 수 없음
- ambiguous physical-work collision은 randomization 전에 quarantine

### 6.5 Firewalled content coding

1. 최대 long side 512px의 eligibility derivative를 만들고 hash한다.
2. painter, title, institution, accession, source를 가린다.
3. metadata·rights·geometry·decode를 통과한 **모든** derivative를 visual-screening denominator에
   넣는다. 두 코더는 서로 독립적으로
   `eligible_outdoor_place_landscape`, `ineligible`, `ambiguous_multiple` 중 하나를 판정한다.
   blank/missing label도 명시적 disagreement이며, 어느 코더의 제외판정도 행을 분모에서
   지우지 못한다.
4. 두 코더 중 한 명이라도 eligible로 부른 derivative 전체를 **union-eligible denominator**로
   정한다. 이 집합에서 각 코더가 four-way broad group, narrow diagnostic, 다섯 full variable과
   사전지정한 다섯 3-state contrast(`visible`, `not_visible`, `indeterminate`)를 판정한다. 다른
   코더의 ineligible·ambiguous·missing 응답도 confusion table의 별도 값으로 남기며 삭제하지
   않는다.
5. metadata를 열기 전에 image/painter recognition 여부를 기록한다.
6. disagreement, raw-table hash, adjudication, recognition flag를 모두 ledger에 남긴다.
7. 코드북 예시는 역사적 또는 전용 calibration 작품만 쓰고 Q/C에 넣지 않는다.

Adjudication **전** raw receipt가 coding-quality gate다.

- 각 화가의 complete visual-screening denominator에서 exact three-way eligibility agreement가
  ≥0.90이어야 하고, 각 코더별 `ambiguous_multiple` 비율이 각각 ≤0.10이어야 한다.
- 각 화가의 union-eligible denominator에서 four-way broad-scene 판정과 다섯 3-state
  visible-property contrast 각각의 raw agreement가 모두 ≥0.85여야 한다.
- 같은 원 raw label로 randomization 뒤 각 화가의 development·qualification·confirmation,
  그리고 등록했다면 optional external population에서도 위 broad-scene·다섯 contrast 0.85
  gate를 다시 계산한다.
- season·illumination·view-depth의 `indeterminate` 비율은 pooled/adjudicated label이 아니라
  **각 코더별로 따로**, 각 해당 painter-population denominator에서 각각 ≤0.20이어야 한다.

모든 분모, missing-label 수, full confusion matrix, raw agreement, Cohen's kappa,
category-specific agreement, coder별 indeterminate rate를 보고한다. prevalence 영향을 받는
kappa만으로 관문을 대신하지 않는다. 하나라도 실패하면 같은 R0a는 NO-GO다. raw table과 hash를
먼저 봉인한 뒤 adjudication할 수 있지만, adjudication은 실패 receipt를 지우거나 관문을
회복시키거나 같은 version에서 codebook을 고쳐 쓰게 하지 못한다.

≤512px derivative를 보는 것은 실제 pixel exposure다. 이를 metadata-only 또는 완전 sealed
pixel이라고 부르지 않는다. derivative, coder note, adjudication imagery는 G1b 전까지
feature/method/generation analyst에게 공개하지 않는다. analyst는 frozen label, count,
agreement, population-standardization receipt만 받는다. qualification·confirmation의
analysis-resolution file과 feature는 해당 access stage까지 봉인한다.

### 6.6 R0a partition, target selection, seal

1. 화가당 적합 internal 360점과 broad group당 24점 support alarm을 확인한다.
2. optional external을 등록했다면 **target 선택 전에** 화가당 96점과 group당 8점을 모두
   취득·double-code하고 unopened-source population으로 동결한다.
3. painter×gate attrition funnel, identity graph, full-frame unweighted source-diversity gate와
   화가별 visual-screening 3-way/union-eligible pre-adjudication coding receipt를 확인한다.
4. painter-level domain-separated CSPRNG로 internal의 72/108/≥180 population role을 한 번
   배정하고, external의 population membership와 audit rank도 고정한다.
5. 이 frozen assignment에서 각 development/Q/C와 등록 external population의 raw content
   agreement·각 코더별 indeterminate gate를 확인한다. 실패 receipt는 adjudication으로 지우지
   않는다.
6. 12 candidate frame을 모든 development/Q/C/등록 external **완전모집단**에서 여덟 제약으로
   평가하고 하나의 common target을 선택한다.
7. 선택된 모든 population의 \(q^*\), solver receipt, ESS·weight·target residual을 봉인하고
   assigned internal/external population의 final \(q^*\) source-share cap을 확인한다. 전체
   internal frame에는 \(q^*\)를 정의하지 않는다. 실패해도 다른 frame을 고르거나 redraw하지
   않고 NO-GO다.
8. auxiliary independent-capture census를 완성·봉인한다.
9. development 288점과 auxiliary census만 analyst에게 방출한다.

### 6.7 즉시 중단하는 조건

- item authority, rights, geometry, decode, content, identity가 닫히지 않음
- internal 360점/화가 또는 broad group 24점/화가가 부족함
- source-diversity, 전체 frame unweighted cap, assigned-population unweighted/\(q^*\) cap 또는
  auxiliary-census 최소조건 실패
- three-way eligibility agreement 0.90, coder별 ambiguous 0.10, content agreement 0.85 또는
  coder별 indeterminate 0.20 coding-quality gate 실패
- 하나의 common candidate frame이 모든 population의 joint convex-hull·4×weight·60% ESS를 통과하지 못함
- randomization 이후 missing/corrupt file로 complete census가 무너짐
- frozen ledger/hash를 network re-request 없이 독립 검증할 수 없음

중단 뒤 같은 version에서 작품 추가, 판정 이동, frame 재검색, redraw, 낮은 provenance source
대체를 하지 않는다. 새 protocol/R0a가 필요하다.

## 7. Feature measurement plan

### 7.1 Primary family 세 개

1. **Color organization**
   - sRGB→CIELAB D65
   - (L^*), chroma의 10·25·50·75·90% quantile
   - chroma <5 pixel mass
   - 나머지 hue의 1–3차 circular sine/cosine coefficient
2. **Spatial/orientation organization**
   - relative luminance, Gaussian (sigma=1,2,4), Sobel gradient
   - development-frozen normalized threshold의 edge density
   - gradient-weighted axial-orientation entropy와 1–3차 axial sine/cosine coefficient
   - Hann-windowed radial Fourier slope와 angular anisotropy
3. **Texture organization**
   - 4-level undecimated `db2` wavelet
   - total log detail energy
   - level별 H/V/D normalized log energy
   - coarse/fine ratio, H/V asymmetry, scale entropy

raw ordered hue/orientation bin은 circular boundary를 깨므로 Euclidean energy vector에 넣지 않는다.
ordinal pattern, local color transition, spatial pyramid, 다른 scale은 사전등록 sensitivity일 뿐
결과가 좋은 primary family를 교체하는 후보가 아니다.

### 7.2 전처리

- source byte overwrite 금지
- valid ICC는 frozen transform으로 sRGB 변환하고 transform 기록
- untagged는 provider contract가 sRGB를 명시할 때만 primary color에 사용
- untagged assumed-sRGB 처리는 별도 sensitivity로만 허용
- aspect ratio 보존, forced-square warp 금지
- frame, mat, border, signature, watermark, text를 frozen procedure로 mask
- 1,024px long-side derivative는 downsampling일 때만 생성
- composition crop 없이 normalized canvas coordinate 사용
- real과 generated에 같은 resize·mask·color·feature code 적용
- generated fake signature나 painter-name text도 같은 mask로 제거하고 발생률을 별도 보고

### 7.3 Coverage coordinate와 qualification

family별 coverage coordinate는 네 개씩, 총 12개다.

- color: median (L^*), median chroma, low-chroma mass, hue first-harmonic resultant
- spatial: (sigma=2) edge density, orientation entropy, Fourier slope, anisotropy
- texture: total detail energy, coarse/fine ratio, H/V asymmetry, scale entropy

모든 좌표에는 단 하나의 공통 transform을 쓴다. 네 화가의 완전 development population을
각각 \(q^*\)로 가중한 뒤 화가마다 정확히 1/4 질량을 주어

\[
P^{D,\mathrm{pool}}_F=\frac14\sum_{a=1}^{4}\sum_{i\in U_a^D}q^*_{ai}\delta_{x_{ai,F}}
\]

를 만들고, coordinate별 weighted median을 center, weighted IQR을 scale로 동결한다. 이 한
transform을 모든 화가의 development/Q/C/external real vector, artist-free control, named
generated vector에 그대로 적용한다. painter별 scaling은 pairwise specificity를 무효화하므로
금지한다. pooled development IQR가 등록 reproduction-perturbation 최대이동의 두 배를 넘지
못하는 coordinate는 nonidentifying으로 실패한다. outcome-selected PCA나 차원축소를
primary에 쓰지 않는다.

family가 G0로 가려면 development와 untouched qualification에서 다음을 통과해야 한다.

- deterministic repeatability
- resize/JPEG/border/ICC perturbation stability
- held-work painter separation
- held-source와 leave-one-source-group-out robustness
- 전체 close-neighbor panel specificity
- signature/label/frame/한 broad group dependence 부재
- auxiliary census의 (eta_F\le0.5)와 coordinate shift ≤0.5 IQR
- disjoint-population·generator simulation에서 구간폭과 power 충족

R1a는 development와 auxiliary census로 family별 source-shift bound \(\eta_F\), 양쪽의 최소
positive-weight count와 ESS, leave-one-group alarm을 먼저 동결한다. R1b에서 화가 \(a\), broad
scene \(s\), source group \(c\), \(d_F\)차원 family에 대해 \(q^*\)를 \(c\)와 같은
화가·같은 scene의 complement 안에서 각각 다시 합이 1이 되게 정규화하고, 공통 pooled scaling
후 coordinate별 exact weighted median 차이의 RMS를 계산한다.

\[
R_{a,s,c,F}=\left\{\frac1{d_F}\sum_{\ell=1}^{d_F}
\left[Q^{q^*}_{a,s,c,\ell}(.5)-Q^{q^*}_{a,s,\neg c,\ell}(.5)\right]^2\right\}^{1/2}.
\]

uniform conditional weight로도 같은 값을 계산한다. 지원되는 모든 exact finite-population
\(R_{a,s,c,F}\)가 \(\eta_F\) 이하여야 하고, uniform-real source alarm이 없어야 하며, source
하나씩 제외한 target–neighbor separation 방향이 뒤집히거나 alarm을 넘지 않아야 한다.
support가 얇아 계산할 수 없는 비교는 impute하지 않고 해당 source-general claim을 실패 또는
`domain_limited`로 남긴다. 이 값은 confidence interval이 아니라 봉인 population의 exact
functional이다.

provider classifier accuracy는 shortcut diagnostic이다. 한 family의 실패를 다른 learned
representation 성공으로 대체하지 않는다. 하나 이상 통과해야 G0로 갈 수 있고, 세 family
전체 claim은 셋 모두 자격검증과 최종 관문을 통과할 때만 허용한다.

Kim A/C, CLIP, CSD, attribution classifier, FID/KID, UMAP/t-SNE, raw cosine은 secondary
diagnostic이다. primary conclusion을 결정하거나 구제하지 않는다.

## 8. Generation plan

### 8.1 모델 선택

연구 prompt 전에 화가·미술과 무관한 frozen conformance prompt로 identity, seed behavior,
receipt, error rate, cost만 검사한다. 그 output은 격리하고 painter resemblance로 모델을
선택하지 않는다. G0는 provider/endpoint 또는 local checkpoint, marketed name, requested
label, revision/weight hash, runtime, sampler, steps, guidance, size, quality, negative prompt,
safety, seed, execution window, account/region, retry/refusal rule을 동결한다. backend가 opaque면
claim은 exact endpoint·label·parameter·date에 한정한다.

두 번째 모델은 같은 sealed design의 독립 replication이며 결과를 pooled하지 않는다.

### 8.2 선택된 24-template frame

R0a가 12 candidate 중 고른 하나의 byte-exact 24-template semantic frame 전부를 쓴다. broad group마다
최소 두 template가 있고, 각 template의 group과 다섯 content value가 8차원 real target을
정의한다. R1a는 research-model output 없이 이미 동결된 wording·render hash의 일치와 content
interpretability만 감사하고 문자를 고치지 않는다. G0는 선택된 artist-free/named UTF-8 byte,
exact painter-name substitution table, punctuation, language, negative prompt, condition insertion
point, render function hash를 다시 검증한 뒤 frozen table에 따라 placeholder를 대입한다.
G0는 template attribute나
문자열을 다시 쓰지 않는다. 24개 template은 가능한 prompt에서 뽑은 표본이 아니라
고정 전수 frame이며 각각 primary에서 \(1/24\)의 질량을 갖는다. broad group 질량은 선택된
frame 안의 해당 group template 수를 24로 나눈 값이지, 사후에 1/4로 재가중한 값이 아니다.

한 template 안에서 named와 control은 조건 phrase만 다르다.

- named: `... in the style of <target painter>`
- artist-free: 같은 content, artist·movement·period·style phrase 없음

### 8.3 요청 수와 seed dependence

모든 template에서 네 named condition과 shared artist-free control은 같은 반복 수 \(R\)을
가져야 한다. 화가 수 \(A\), template 수 \(B\)이면

\[
N_{requests}=BR(A+1).
\]

네 화가와 24개 template에서는 \(N_{requests}=120R\)이다. v1.5의 \(R=16\), 즉
1,920 requests/model 계획은 **폐기**되었다. boundary-safe availability gate는 return이 모두
성공해도 유한한 불확실성을 남기므로 이 수로는 관문을 수학적으로 넘을 수 없다. 다음 식은
각 등록 repetition이 서로 다른 auditable independence unit이라는 **수학적으로 가장 유리한
경우에만** 성립한다. scene group \(s\)의 template 수를 \(B_s\), availability gate를 \(\tau\)라
하면 all-success lower bound는

\[
1-\left\{\frac{\log(1/\alpha_e)}{2B_sR}\right\}^{1/2},
\]

따라서 먼저

\[
R\ge \max_s\left\lceil
\frac{\log(1/\alpha_e)}{2B_s(1-\tau)^2}
\right\rceil
\]

을 만족해야 한다. 불가능하게 낙관적인 \(\alpha_e=.05\), 모든 group \(B_s=6\),
\(\tau=.90\)만 넣어도 \(R\ge25\), 즉 model당 **최소 3,000요청**이다. 실제로는 rate endpoint
전체에 대한 Bonferroni 배분, adherence·copy·distance·coverage·missingness, whole-decision
power뿐 아니라 common-shock clustering 때문에 더 커지며, 보수적 unit이 너무 크면 bound가
무정보적이 되어 rate endpoint 자체가 ineligible/inconclusive가 될 수 있다. 선택 frame,
directional endpoint inventory, independence-unit 설계가 봉인된 뒤 R1a가 analytic floor와
simulation을 모두 적용해 \(R\)을 정한다. 현재 final \(R\)과 request count는 등록되지 않았다.
named/control 간 서로 다른 \(R\)이나 supplementary unpaired primary block은 허용하지 않는다.

**고정된 deterministic local model/runtime map**에서 결정적 seed 계약이 검증된 경우에만,
선언한 유한 integer seed space에서 template마다 독립된 domain-separated randomization으로
ordered seed list를 **IID uniform, 복원추출**한다. 중복 seed를 일부러 넣거나 제거하지 않고,
우연히 나온 중복과 seed-space 크기를 기록한다. 한 template의 list를 다른 template에 재사용하지
않는다. 한 template 안에서 한 seed draw는 네 painter-named 조건과 shared control을 묶는 full
condition vector이며, 추론은 이 vector 전체를 움직이고 painter component를 따로 재표집하지
않는다.

반면 **opaque 또는 remote endpoint**는 seed field가 있어도 fixed-map 독립성을 주장하지 않는다.
G0는 \(C\)개의 같은 크기 prospective common-shock unit을 만들고, 각 unit에 \(L\)개의 complete
balanced execution wave를 둔다. 한 wave는 선택된 모든 template과 다섯 condition(화가별 named
네 개와 shared control 한 개)의 모든 조합에 정확히 한 요청을 포함하며, wave 안 순서는
무작위화하고 \(R=CL\)로 한다. unit 사이는
backend·account·region·batch·moderation receipt와 사전 독립성 논거로 구분한다. provider episode,
backend revision, moderation state, outage, retry cascade 또는 다른 plausible common shock를
공유하는 요청은 같은 unit에 둔다. 공통 shock가 frozen boundary를 가로지르거나, 실패를 그대로
남긴 complete balanced unit을 실행·보존할 수 없거나, 독립성 논거가 성립하지 않으면 rate와
continuous endpoint 모두 ineligible/inconclusive다. request ID·timestamp·random order·null
autocorrelation만으로 독립이라 하지 않는다. frozen random draw 밖의 seed 고의반복이나 파일
복제도 표본수를 늘리지 않는다. remote unit이 equal-weight이면 rate bound에서
\(W_c=1/C\), \(\sum_cW_c^2=1/C\)이므로 같은 unit 안의 \(L\)만 늘려서는 Hoeffding 폭이 줄지
않는다. auditable independent unit 수 \(C\) 자체가 충분해야 한다.

### 8.4 Request ledger와 결측

모든 request를 전송 전에 기록한다. best-of-N, curator selection, 마음에 들지 않는 output
교체를 금지한다. transient retry는 frozen 조건에만 허용하고 모든 attempt를 남긴다.
moderation refusal, empty/corrupt return, policy error는 원래 분모에 남는다.

primary result는 두 부분이다.

1. 모든 등록요청에 대한 intention-to-generate availability
2. 분석가능 return에 조건부인 feature distribution

off-topic output은 assigned template·broad group에 남긴다. primary는 intention-to-prompt이고,
맹검 realized group/variable coding은 adherence endpoint와 sensitivity다. feature가 없는
refusal에 값을 impute하지 않는다. realized-scene grouping과 generated output을 다섯
visible-property contrast에 맞춰 다시 가중한 결과는 의무 sensitivity이지만, assigned-template
primary를 바꾸거나 구제하지 못한다.

## 9. Copy와 leakage audit

G1a request/attempt/output ledger와 hash를 봉인한 뒤, G1b에서 fit 결과를 unblind하기 전에:

1. byte와 decoded-pixel exact hash
2. transform-tolerant perceptual hash
3. locally calibrated SSCD 또는 frozen copy descriptor
4. whole-image·crop nearest-neighbor
5. 가능하면 primary distance·condition·painter를 가린 flagged-pair adjudication

threshold는 known same-work transform, 같은 화가의 다른 작품, same-content 작품,
close neighbor, unrelated pair로 생성 전에 보정한다. 검색은 등록 실작품 corpus와 합법적으로
접근 가능한 same-work derivative로 한정한다. no hit는 unknown training set 부재의 증명이 아니다.

flagged output은 availability 분모와 immutable ledger에 남는다. confirmatory fit·specificity·
coverage는 near-copy-excluded set으로 계산하고 all-output은 descriptive다. copy 제외 뒤 어느
template라도 frozen minimum이 무너지면 inconclusive다.

soft near-copy는 화가 전체 named output 단위가 binding이다. point estimate ≤5%, 아래
10.2절의 boundary-safe conditional upper bound \(U_K/L_A\) ≤10%를 모두 요구한다. broad-group rate와 exact/crop 사례는 의무
진단이다. exact/crop event가 하나라도 있으면 무제한 `without observed reconstruction` 문장을
금지하고, broad-group heterogeneity가 R1a-frozen alarm을 넘으면 painter 결과는 inconclusive다.
두 soft-copy threshold는 detector operating characteristic와 R1a power로 생성 전에 최종
동결한다. upper bound가 5% 아래일 때만 `copy rate below 5%`라고 말한다.

## 10. Primary estimand과 exact statistic

### 10.1 Real target

화가 (a), qualified family (F)에서 (U_a^C)는 R0a가 무작위화하고 G1b까지 봉인한
confirmation population의 **모든 물리작품**이다. (q^*_{ai})는 선택된 공통 8차원 target의
R0a-frozen population mass다.

\[
P^{C,*}_{a,F}=\sum_{i\in U_a^C}q^*_{ai}\delta_{x_{ai,F}},\qquad
\sum_iq^*_{ai}=1.
\]

이것이 primary real standard다. uniform census

\[
P^{C,u}_{a,F}=N_a^{-1}\sum_i\delta_{x_{ai,F}}
\]

는 의무 sensitivity다. development와 qualification은 final reference를 정의하지 않는다.
external (P^{E,*})는 같은 R0a에서 등록한 경우 별도 분석하고 internal 실패를 rescue하도록
pooling하지 않는다.

### 10.2 먼저 판정하는 availability와 adherence

All-success 또는 zero-copy 관측에 empirical bootstrap을 쓰면 부당한 zero-width 확신이 생길
수 있다. 따라서 rate endpoint는 continuous max-stat과 별도의 alpha를 받고, boundary-safe
Bonferroni weighted-Hoeffding bound를 쓴다.

각 고정 rate endpoint의 모든 등록 request를 \(i\)로 두고, 각 template 총질량이 같고 그 안의
등록 repetition 질량이 같은 \(w_i\)를 부여해 \(\sum_iw_i=1\)로 한다. \(A_i=1\)은 analyzable
return, \(J_i=1\)은 그 return이 assigned broad group에도 adherence, \(K_i=1\)은 그 return이
soft near-copy인 경우다. request-level point rate 자체는

\[
\widehat A=\sum_iw_iA_i,\qquad
\widehat J=\sum_iw_iJ_i,\qquad
\widehat K=\sum_iw_iK_i,
\]

\[
\widehat V=\widehat A,\qquad
\widehat H=\frac{\widehat J}{\widehat A},\qquad
\widehat C=\frac{\widehat K}{\widehat A}
\]

다. 그러나 request 하나를 곧 독립 관측 하나로 세지 않는다. G0는 return을 보기 전에 같은
endpoint의 request를 auditable independence unit \(c\)로 분할하고

\[
W_c=\sum_{i\in c}w_i,\qquad
\bar X_c=W_c^{-1}\sum_{i\in c}w_iX_i\in[0,1],
\quad X\in\{A,J,K\}
\]

를 봉인한다. 따라서 \(\widehat X=\sum_cW_c\bar X_c\)이고, uncertainty의 유효 단위는
request가 아니라 서로 독립이라고 방어할 수 있는 \(c\)다. fixed deterministic local map에서는
한 IID seed draw가 한 unit이 될 수 있지만 condition을 가로지르는 endpoint라면 그 seed의 전체
painter/control vector가 함께 있어야 한다. opaque/remote에서는 8.3절의 \(C\)개 equal-size
balanced common-shock unit을 그대로 쓴다. 같은 episode·batch·backend revision·moderation
state·outage·retry cascade·기타 plausible common shock를 공유하는 요청을 서로 다른 unit으로
쪼개지 않는다.

R1a는 G0 전에 binding·보고 rate endpoint에 필요한 **모든 one-sided directional bound**를
따로 세어 전체 \(M_{rate}\)를 열거하고 \(\alpha_{rate}\)를 고정한다. 하나의 logical rate
endpoint가 availability·conditional adherence·conditional copy를 모두 판정하려면 필요한
방향은 \(L_A,U_A,L_J,U_K\) 네 개다. 즉 \(A\)의 lower와 upper는 하나의 two-sided interval로
묶어 세지 않고 서로 다른 두 directional bound로 센다. 완전히 같은 endpoint의 같은 방향을
여러 식에서 재사용할 때만 한 번 세며, 반대 tail은 반드시 별개다. 추가로 보고하는 template·group·
visible-property rate의 각 필요한 방향도 \(M_{rate}\)에 하나씩 더한다. 열거된 각 방향
\(e\)마다

\[
\alpha_e=\frac{\alpha_{rate}}{M_{rate}},\qquad
h_e=\left\{\tfrac12\log(1/\alpha_e)\sum_cW_c^2\right\}^{1/2}.
\]

해당 endpoint의 방향별 half-width를 명시하면

\[
L_A=\max(0,\widehat A-h_{A,L}),\quad
U_A=\min(1,\widehat A+h_{A,U}),\quad
L_J=\max(0,\widehat J-h_{J,L}),\quad
U_K=\min(1,\widehat K+h_{K,U}),
\]

이며 각 \(h_{X,d}\)는 그 directional bound의 \(\alpha_e\)와 frozen cluster-mass vector
\((W_c)\)로 계산한다. 보고 목적으로 \(U_J\)나 \(L_K\)가 필요하면 그것들도 별도 방향으로
열거·보정한다. 이 반지름은 [Hoeffding
(1963)](https://doi.org/10.1080/01621459.1963.10500830)의 independent bounded-unit inequality를
등록된 cluster contribution에 적용한 것이다. 원전은 cluster 독립성, endpoint inventory,
alpha split, ratio construction 또는 과학적 threshold를 보장하지 않으므로 이 모두를 G0/R1a가
별도로 동결·검증해야 한다.

binding availability lower bound는 \(L_A\), conditional adherence lower bound는
\(L_J/U_A\), conditional soft-copy upper bound는 \(U_K/L_A\)다. denominator bound가 0이면
endpoint는 inconclusive다. 모든 return이 성공하거나 copy가 0건이어도 interval width가 0이
되지 않는다. union bound는 painter/control condition 사이 독립을 요구하지 않지만 Hoeffding
단계는 frozen unit \(c\) 사이 독립을 요구한다. request ID, timestamp, random order 또는 null
autocorrelation diagnostic은 보조점검일 뿐 독립성 증명이 아니다. unit partition을 감사 가능하게
방어할 수 없거나, 하나의 보수적 common-shock unit 때문에 bound가 무정보적이면 해당 rate
endpoint는 ineligible/inconclusive이며 request-level pseudoreplication을 금지한다. R1a는
heterogeneous template probability, shared full-vector dependence, 실제 cluster size,
batch·outage·moderation·backend common shock에서 coverage를 검증해야 한다.

- named painter×broad-group와 shared-control×broad-group마다 \(L_A\ge0.90\)
- 같은 endpoint마다 \(L_J/U_A\ge0.80\)
- template마다 R1a-frozen minimum analyzable repetition
- sealed real reference의 frozen eligibility group과 G1b blind recode 사이 **exact
  finite-population agreement fraction ≥0.90 per painter**; real census에는 confidence lower
  bound를 붙이지 않음
- template/group별 denominator, 다섯 realized-variable marginal, full confusion table 공개
- differential-failure MNAR bound가 결론을 뒤집으면 inconclusive

이 관문을 통과하지 않은 condition에서는 남은 output의 좋은 feature distance만으로 성공을
말하지 않는다.

### 10.3 Exact finite-census energy estimator

confirmation의 모든 real work를 측정하므로 real 쪽 sampling estimator가 없다. real mass는
primary에서 (p_i=q_i^*), uniform sensitivity에서 (p_i=1/N)다. template (t)의 분석가능
반복 수를 (m_t\ge2), generated vector를 (g_{tj}), real vector를 (x_i), Euclidean distance를
(d)라 한다.

\[
\widehat D_{GP}=\frac1{24}\sum_{t=1}^{24}\frac1{m_t}
\sum_{j=1}^{m_t}\sum_{i\in U}p_i d(g_{tj},x_i).
\]

\[
\widehat D_{PP}=\sum_{i\in U}\sum_{k\in U}p_ip_kd(x_i,x_k).
\]

real self term은 frozen finite population에서 exact다. diagonal은 distance 0이다.
generated self term은 equal-template mixture U-statistic이다.

\[
\widehat D_{GG}=\frac1{24^2}\left[
\sum_t\frac{\sum_{j\ne k}d(g_{tj},g_{tk})}{m_t(m_t-1)}+
\sum_{t\ne u}\frac{\sum_j\sum_k d(g_{tj},g_{uk})}{m_tm_u}
\right].
\]

\[
\widehat E=2\widehat D_{GP}-\widehat D_{GG}-\widehat D_{PP}.
\]

generated term의 finite-sample estimation 때문에 \(\widehat E\)가 조금 음수일 수 있으며 0으로
truncate하지 않는다. unequal real/generated size의 모든 적합 관측을 쓴다. MMD는 sensitivity이며
failed energy 결과를 대체하지 않는다.

real scalar quantile은 exact weighted finite CDF를 쓴다.

\[
F_P(v)=\sum_i p_i\mathbf1(v_i\le v),\qquad
Q_P(\alpha)=\inf\{v:F_P(v)\ge\alpha\}.
\]

interpolation 없는 left quantile이며 IQR은 \(Q(.75)-Q(.25)\)다. positive-weight 작품 세 개
미만이 tail quantile을 결정하면 해당 endpoint는 inconclusive다.

generated coverage도 같은 left-quantile을 쓰되 template마다 총질량 \(1/24\)을 보존한다.

\[
F_G(v)=\frac1{24}\sum_{t=1}^{24}\frac1{m_t}
\sum_{j=1}^{m_t}\mathbf1(v_{tj}\le v),\qquad
Q_G(\alpha)=\inf\{v:F_G(v)\ge\alpha\}.
\]

따라서 한 analyzable output의 질량은 \(1/(24m_t)\)다. template별 return 수가 다를 때
모든 image에 같은 weight를 주어 pooled quantile을 계산하면 고정 prompt-frame estimand가
바뀌므로 금지한다. replicate마다 이 weight를 다시 계산한다.

### 10.4 Realized-content sensitivity와 continuous 9,999 resampling

Primary는 assigned-template intention-to-prompt다. 그러나 blind realized content가 target과
크게 어긋나는지 판정하기 위해 별도의 binding entropy sensitivity를 사전 동결한다.
near-copy-excluded analyzable output의 base mass를 \(b_{tj}=1/(24m_t)\), blind content
8-vector를 \(z_{tj}\), 공통 target을 \(m\)이라 하면

\[
r^*=\arg\min_{r\ge0}\sum_{t,j}r_{tj}\log(r_{tj}/b_{tj}),\qquad
\sum_{t,j}r_{tj}=1,\qquad \sum_{t,j}r_{tj}z_{tj}=m.
\]

\(r^*\)는 같은 joint-convex-hull tolerance, unit mass ≤\(4b_{tj}\), Kish ESS ≥ base-weight
ESS의 60%를 모두 통과해야 한다. output index를 \(u,v\)라 할 때 generated self term은

\[
\widehat D^{r}_{GG}=
\frac{\sum_{u\ne v}r_u^*r_v^*d(g_u,g_v)}{1-\sum_u(r_u^*)^2}
\]

인 weighted distinct-pair U-statistic이며, generated–real term과 exact weighted coverage
quantile에도 \(r^*\)를 직접 쓴다. 각 generator replicate 안에서 \(r^*\)를 다시 계산한다.
infeasible·unstable weight, target residual 실패, 또는 이미 통과한 target-fit·coverage·specificity
margin의 reversal은 `content_sensitive` 또는 inconclusive다. 이 sensitivity는 실패한
intention-to-prompt primary를 구제하지 못한다. base/realized weight, maximum weight, Kish ESS,
target residual을 모두 공개한다.

Continuous feature·distance uncertainty도 rate와 **같은 G0-frozen auditable independence
partition**에 따라 9,999 generator replicate를 만든다. real census와 \(q^*\)는 고정하며
real-work bootstrap, IID image bootstrap, HT, Rao–Wu를 쓰지 않는다.

- fixed deterministic local map에서는 template 안의 complete seed condition vector를
  복원추출한다. 한 vector의 모든 painter condition, shared control, availability, content,
  copy, feature가 함께 이동하고 independently seeded template list는 서로 따로 재표집한다.
- opaque/remote endpoint에서는 8.3절의 complete balanced common-shock unit vector만
  복원추출한다. 한 unit의 모든 \(L\) wave와 모든 template×condition outcome, failure, label,
  copy, pixel/feature를 함께 움직이며 그 안의 request·wave·template·condition을 따로
  재표집하지 않는다.
- 두 방식 모두 모든 fixed template의 count를 보존한다. 24 template은 prompt superpopulation
  표본이 아니라 fixed census이므로 template 자체를 재표집하지 않는다.
- 매 replicate마다 rate point value, \(r^*\), \(D_{GG}\), \(D_{GP}\), coverage, specificity,
  copy outcome과 전체 decision을 재계산한다. 다만 rate의 binding interval은 bootstrap
  quantile이 아니라 10.2절 bound다.

independence unit이 이 fixed-template resampler와 정렬되지 않거나, 공통 shock가 frozen unit
boundary를 가로지르거나, unit 사이 독립성을 방어할 수 없으면 영향받은 rate와 continuous
endpoint를 모두 ineligible/inconclusive로 판정한다. request-level pseudoreplication으로
구제하지 않는다.

endpoint \(e\)에서 replicate \(T_e^{(r)}\), mean \(\bar T_e^*\), standard deviation \(s_e^*\)를
사용해 frozen direction의 studentized max statistic

\[
\{T_e^{(r)}-\bar T_e^*\}/s_e^*
\]

을 만든다. simultaneous bound는 observed \(T_e\)를 중심으로 max-stat critical value와
\(s_e^*\)를 쓴다. bootstrap variance 0이 exact인 경우는 algebra로 endpoint가 설계상
structurally fixed임을 증명했을 때뿐이다. 그 밖의 zero 또는 numerically degenerate variance는
zero-width interval을 주지 않고 inconclusive로 판정해 prospective repetition을 늘리거나
중단한다. R1a는 studentization, centering, degeneracy tolerance, quantile convention, seed,
direction, Monte Carlo error를 R1b 전에 동결한다.

R1a는 U-stat/dependence fixture, point bias, simultaneous coverage, equivalence power,
copy·availability error control, unequal template return, MNAR scenario뿐 아니라 등록 cluster
size와 batch·outage·moderation의 refusal common shock, backend가 만드는 pixel/feature common
shock를 함께 검증한다. 실패하면 resource ceiling 안에서 generator repetition을 prospective하게
늘리거나 stop/new protocol을 선택한다. 다른 resampling analogue로 바꾸지 않는다.

### 10.5 Binding decision conjunction

먼저 absolute target-fit statistic은

\[
A_{a,F}=E_F(G^N_{a,F},P^{C,*}_{a,F})
\]

이다. R1a는 development에서 각 coverage coordinate의 \(\pm0.25\) IQR 이동, coherent
family-location 이동, spread의 0.80 수축·1.25 팽창, 20% tail contamination, 가장 가까운
비교화가와의 20% mixture, 등록된 correlation/dependence 변화 각각의 population energy를
계산한다. 그중 가장 작은 adverse distance를 painter–family별 잠정 practical-equivalence
margin \(\epsilon_{a,F}\)으로 정한다. disjoint development/qualification 안정성과 controlled
reproduction perturbation은 별도 identification check이며 margin에 더하지 않는다. 안정성
envelope가 \(\epsilon/2\)와 \(\epsilon\)을 구분하지 못하거나 margin이 target–neighbor
separation과 겹치면 그 family는 nonidentifying이다.

Absolute fit은 \(A_{a,F}\)의 one-sided simultaneous upper bound가 frozen
\(\epsilon_{a,F}\) 이하일 때만 통과한다. 단순히 차이검정이 유의하지 않거나 point estimate가
작다는 이유로 equivalence라 부르지 않는다.

화가–모델–qualified family별 성공은 다음을 모두 요구한다.

1. real-only family qualification 통과
2. \(P^{C,*}\)와 fixed equal-24-template \(G^N\)의 absolute target-fit equivalence 통과
3. 12 coverage coordinate의 median shift interval이 \([-0.25,0.25]\) 안, IQR ratio가
   \([0.80,1.25]\) 안
4. 10·90% tail diagnostic 공개와 registered tail/dependence alternative 검출력 충족
5. 모든 competitor에 대해
   \[
   S_{a,h,F}=E(G^N_a,P^{C,*}_h)-E(G^N_a,P^{C,*}_a)
   \]
   의 simultaneous lower bound가 \(\delta_{a,h,F}=0.10L_{a,h,F}\)보다 큼
6. source/reproduction gate와 uniform-real·realized-content \(r^*\) sensitivity가 실패·
   infeasible·불안정하거나 결론을 뒤집지 않음
7. availability \(L_A\ge0.90\), adherence \(L_J/U_A\ge0.80\), template minimum 통과
8. copy point ≤5%, \(U_K/L_A\le0.10\), near-copy-excluded analysis 통과
9. continuous max-stat, Bonferroni-Hoeffding rate family, total alpha, MNAR sensitivity 통과

여기서 \(L_{a,h,F}\)는 common-content development target에서 frozen source leave-out과
등록 reproduction perturbation을 모두 거친 cross-fitted target–neighbor energy separation의
최솟값이다. 관찰 development population의 보수적 robustness bound이지 oeuvre에 대한
confidence bound가 아니다. 10%는 이 프로젝트의 SESOI이지 문헌의 보편상수가 아니다. \(L\le0\)인
painter-family pair는 real-only specificity qualification 실패다. 쉬운 competitor
하나만 이기거나 generic Impressionist distribution에 머무는 것은 성공이 아니다. 공통
holding/capture-source×broad-group 비교는 양쪽 support가 있을 때 의무 진단이며 missing cell은
impute하지 않는다. 유리한 matched-source subset이 실패한 primary specificity를 구제하지 않는다.

secondary prompt effect

\[
\Delta^0_{a,F}=E(G_F^0,P^{C,*}_{a,F})-E(G^N_{a,F},P^{C,*}_{a,F})
\]

이 양수여도 absolute fit·coverage·specificity 실패를 구제하지 못한다.

### 10.6 Simulation operating criteria

R1a whole-decision simulation은 location, scale, tail, multimodality, prototype collapse,
neighbor mixture, source shift, reproduction noise, 5·10·15% nonrandom refusal, near-copy를
포함한다. 특히 등록된 common-shock unit 크기에서 batch·outage·moderation refusal뿐 아니라
backend episode가 output pixel과 feature를 함께 이동시키는 common shock까지 주입해 rate와
continuous coverage를 동시에 stress-test한다.

- 모든 target-fit distance ≤\(\epsilon/2\), median shift ≤0.125 IQR, spread ratio
  \([0.90,1.11]\), availability·adherence·copy 조건 충족인 유리한 scenario에서
  painter-family 전체 conjunction 통과확률 **≥80%**
- 모든 margin-defining adverse alternative를 각각 reject할 확률 **≥90%**
- registered family에서 unsupported painter-family reproduction claim을 하나라도 낼 확률 **≤5%**
- target-fit simultaneous interval width ≤\(\epsilon/2\), coverage는 해당 half-margin 이하

평균 power 90%나 일부 alternative만의 90%로 바꾸지 않는다. 별도 four-painter/all-family
omnibus claim은 따로 등록한다. primary multiplicity는
\(\alpha_{cont}+\alpha_{rate}\le0.05\)로 사전분할한다. \(\alpha_{cont}\)의 continuous
max-stat family에는 painter, qualified family, scene-group/template, competitor, distance,
coverage endpoint가 들어간다. availability·adherence·copy rate 전체는 \(\alpha_{rate}\)의
Bonferroni-Hoeffding family가 따로 통제하며, union bound가 두 family의 conjunction을 묶는다.
endpoint inventory, alpha allocation, studentization, direction을 R1a에서 동결한다.
closed/Holm 결과는 sensitivity로만 허용하며 실패한 primary construction을 구제하지 않는다.

## 11. Sealed stage별 실행

### R0a — census, corpus, randomization, common-target freeze

- complete source snapshot·rights·intent·attempt ledger
- 모든 file 취득·item admission·identity graph·화가×gate attrition funnel·firewalled coding
- visual-screening 3-way/union-eligible content/assigned-population pre-adjudication reliability
  receipt와 adjudication을 분리 봉인; registered external도 같은 범위에 포함
- painter당 internal ≥360, broad group당 ≥24, 전체 frame의 unweighted-only source cap과
  assigned population별 unweighted/\(q^*\) source-count/share gate
- 한 번의 painter-level 72/108/≥180 exposure-role assignment
- 12 byte-exact prelabel-hashed frame 중 하나 선택, 공통 8차원 \(m\), 모든 population \(q^*\) 동결
- optional external과 auxiliary census를 등록한 경우 같은 R0a에서 완성
- development 288점과 auxiliary census만 방출

### R1a — development와 simulation

- development population 전수 feature 측정
- equal-painter \(q^*\)-weighted pooled-development median/IQR transform과 세 feature card 동결
- deterministic fixture, perturbation·exact source-RMS·auxiliary bound 동결
- energy·equal-template quantile·realized \(r^*\)·clustered boundary-safe rate 구현 fixture
- rate와 같은 independence partition을 쓰는 continuous 9,999 whole-vector resampling;
  refusal뿐 아니라 pixel/feature common-shock whole-decision simulation
- margin, \(\alpha_{cont}/\alpha_{rate}\), max-stat, Bonferroni-Hoeffding endpoint inventory,
  independence-unit rationale, analytic floor와 generator repetition count 동결

### R0b/R1b — complete qualification access와 일회 자격검증

- qualification 432점을 모두 방출·측정
- confirmation은 계속 봉인
- frozen method를 한 번 실행
- failed family를 유지하고 다른 diagnostic으로 교체하지 않음
- population census가 불완전하면 stop/new R0a

### G0 — exact generator·prompt·request freeze

- exact model/runtime/parameter identity
- selected 24-template의 byte-exact artist-free/named rendering·render-function hash 검증; rewrite 금지
- fixed deterministic local map이면 template별 IID-uniform-with-replacement seed list, chance
  duplicate receipt, within-template full condition matrix
- opaque/remote이면 \(C\) equal-size common-shock unit×각 \(L\) complete balanced wave,
  매 wave의 모든 template×condition request, \(R=CL\), randomized order와 backend/batch/moderation receipt
- rate·continuous 공통 independence-unit mapping과 boundary-crossing stop rule
- request order, retries, refusal, content, copy, estimand, report template
- rate-endpoint inventory와 analytic perfect-return floor를 통과한 simulation-selected \(R\);
  네 화가에서는 \(120R\), retired 1,920/model은 실행 금지

### G1a/G1b — generation seal과 final confirmation

G1a는 final real file을 봉인한 채 모든 request를 선별 없이 실행하고 attempt·failure·output·
hash를 seal한다. G1b는 seal 검증 뒤 confirmation population 전부를 한 번 연다. 두 독립 맹검
코더가 모든 sealed-confirmation image와 **모든 technically analyzable generated image**를 같은
codebook으로 판정한다. 가능한 범위에서 painter identity, real/generated status, source,
prompt assignment, condition을 가리고, complete raw label을 adjudication 전에 봉인한다.

그 receipt에서 broad scene과 다섯 3-state contrast agreement ≥0.85, 그리고 각 코더별
season·illumination·depth `indeterminate` ≤0.20을 real painter별 confirmation population과,
model별 generated named-painter condition 및 shared-control condition마다 따로 판정한다. 실패하면
영향받은 adherence·realized-content·feature-reproduction endpoint는 **inconclusive**이며 뒤의
합의가 receipt를 복구하지 못한다. 통과한 경우에만 제3의 맹검 adjudicator가 frozen codebook으로
불일치를 해결하고, 그 deterministic consensus 하나를 \(J_r,z_{tj},r^*\)에 사용한다. 원래
scene-group·prompt assignment는 바꾸지 않는다. 그 뒤 copy audit, availability/adherence,
near-copy-excluded feature analysis, negative·missing result, claim audit을 모두 낸다.

## 12. 이번 작업에서 완료한 것과 완료하지 않은 것

### 12.1 완료

- 연구질문을 two-part availability/adherence + conditional distribution reproduction으로 정정
- Pilot 0–3의 실패·결측·중단 근거 재감사
- Kim, CSD, ArtSavant, ArtFID, distribution, copy, source, missingness 문헌의 적용경계 확인
- 문헌 corpus 144 evidence record/205 bibliography item과 완전성 한계 명시
- historical ledger 194행(142/50/2), strict-canvas 133행 재집계
- 로컬 132 JPEG, primary 113 distinct byte hash, 69,549,332 byte inventory 확인
- 43 official live metadata 후보의 traceability와 snapshot 한계 확인
- Wikidata 3,190 item, 3,367 item-image row, 3,364 file link의 census 후보경로와 높은
  산술 yield burden 확인; feasibility 근거로 쓰지 않음
- Commons 40요청 모두 HTTP 429, no retry/fallback, file-level 결론 없음 확인
- filename stress test 5/1/46/6으로 narrow-scene equal quota 가정 폐기
- 네 broad group, **향후 12개 frame을 active label 전에 hash하도록 한 절차**, 8차원 공통
  target, primary \(q^*\), census 설계 수립
- all-real-census에 맞춰 HT/Rao–Wu를 active method에서 제거하고 generator-only inference로 단순화
- 공통 pooled scaling, exact source-median RMS, generated equal-template quantile, realized \(r^*\),
  common-shock-clustered rate/continuous inference와 alpha-split 계약 수립
- Csiszár I-projection과 Hoeffding bounded-unit inequality의 근거·비근거 경계 명시
- v1.5의 1,920요청을 폐기하고, repetition별 독립이라는 최선의 경우에만 v1.7 analytic
  floor가 최소 3,000임을 확인
- protocol 1.7와 data-readiness schema 1.8에 맞춘 연구·자료준비 계약 작성

### 12.2 아직 완료하지 않음

- reproducible R0a source snapshot과 ordered acquisition ledger 실행
- exact painter×gate attrition funnel 생성
- item-level authority/right/quality/content/identity 판정
- active-study 실작품 이미지 한 장이라도 다운로드·승인
- internal 1,440점, optional external 384점, auxiliary ≥32점 취득
- ≤512px derivative 생성과 double coding
- 12 candidate의 byte-exact dual-rendering hash freeze와 common target 실제 선택
- (q^*) feasibility, convex hull, 4× cap, 60% ESS 실제 판정
- development 288점 feature 측정과 auxiliary reproduction bound 계산
- qualification 432점 일회 자격검증
- generator selection, G0 request registration, image generation
- rate endpoint inventory, alpha split, auditable independence partition, remote \(C,L\), final
  \(R\) 및 \(120R\) request count 동결
- 생성–실제 energy·coverage·specificity·copy·availability 결과

따라서 “생성모델이 Monet/Sisley/Pissarro/Cézanne의 특징을 재현한다” 또는 “재현하지
않는다”는 어느 쪽 결론도 현재 근거가 없다.

## 13. Immediate actions와 unresolved issues

### 13.1 가장 가까운 실행순서

1. R0a metadata census query·response·rights·delivery snapshot을 재현 가능하게 동결하고
   exact painter×gate attrition funnel을 연다.
2. active label 전 12 complete 24-template candidate의 byte-exact UTF-8 artist-free/named
   rendering, placeholder/insertion point, punctuation, language, negative prompt, scene/variable,
   render function과 selection code를 hash한다.
3. provider별 qualification object 두 개와 frozen throttling으로 delivery contract를 닫는다.
4. authority/support/rights/geometry/capture ancestry를 item별 검증하고 complete file을 취득한다.
5. physical-work/capture/asset/derivative identity graph를 닫는다.
6. ≤512px firewalled derivative를 두 코더가 먼저 3-way visual eligibility로 판정한다. 화가별
   complete screening denominator의 exact agreement 0.90·각 코더 ambiguous 0.10과,
   union-eligible 및 assigned D/Q/C/registered external에서 broad 4·다섯 3-state contrast
   agreement 0.85·각 코더 indeterminate 0.20 gate를 adjudication 전에 판정한다.
7. internal 360/화가·24/group과, 등록했다면 external 96/화가·8/group을 모두 닫은 뒤
   source gate와 auxiliary census를 확인한다.
8. painter-level population assignment와 external audit rank를 고정한 뒤 12 frame을 모든
   intended population에서 평가하고 하나의 \((m,q^*)\)를 봉인한다.
9. development 288점과 auxiliary census만 열어 common pooled transform, exact source functional,
   \(r^*\), rate-bound, alpha-split, local/remote independence-unit 후보, analytic \(R\) floor와
   refusal·pixel·feature common-shock whole-decision simulation을 실행한다.
10. R0b/R1b qualification 432점이 모두 통과한 뒤에만 G0와 생성 실행을 고려한다.

### 13.2 아직 풀리지 않은 핵심 위험

- **Feasibility**: 3,190 discovery item은 census를 정당화할 뿐 pass yield를 보여주지 않는다.
  internal만으로도 raw-item 산술 yield가 Pissarro 52.55%, Sisley 51.06%, Monet 31.80%,
  Cézanne 53.89% 이상이어야 하고, optional external 포함 시 66.57%, 64.68%, 40.28%,
  68.26%다. 이는 loss 전 하한이며 exact painter×gate attrition funnel 전에는 feasibility가
  알려지지 않는다.
- **Content support**: broad group당 24점과 하나의 8차원 common target이 네 화가의 모든
  population joint convex hull에 들어갈지, 생성 뒤 realized \(r^*\)도 support·cap·ESS를
  통과할지 모른다.
- **Coding reliability**: complete screening frame의 3-way agreement 0.90·각 코더 ambiguous
  0.10, union-eligible와 assigned D/Q/C/registered external의 content agreement 0.85·각 코더
  indeterminate 0.20을 통과할지 모른다. G1b의 real/generation 독립 이중코딩도 별도 실패할 수
  있으며 그 경우 해당 endpoint는 inconclusive다.
- **Source support**: 각 internal population의 four-source/30% cap, scene 70% cap, external
  two-source/70% cap, exact weighted-median RMS와 leave-one-source qualification이 가능한지 모른다.
- **Independent capture**: 작품당 진정한 독립 capture 두 개를 가진 census ≥32점을 합법적으로
  만들 수 있을지 모른다.
- **Feature validity**: 세 family가 reproduction/source/neighbor 관문을 통과할지 모른다.
- **Generator identity**: exact backend와 seed behavior를 충분히 기록할 모델이 무엇인지
  아직 동결하지 않았다.
- **Generator repetitions**: 폐기된 1,920요청은 perfect-return availability 관문조차 넘지
  못한다. 3,000은 모든 repetition이 독립 unit이라는 불가능하게 낙관적인 절대 하한일 뿐이고,
  실제 \(R\)과 \(120R\) 요청 수는 endpoint inventory·Bonferroni allocation·clustered
  whole-decision simulation 전에는 모른다.
- **Dependence feasibility**: local fixed map의 IID seed 계약 또는 remote의 \(C\) equal-size
  unit×\(L\) complete balanced wave를 실제로 방어할 수 있을지 모른다. batch·backend·moderation·
  outage·retry·pixel/feature shock가 unit 경계를 넘거나 보수적 bound가 무정보적이면 rate와
  continuous endpoint가 함께 ineligible/inconclusive다.
- **Human construct**: 본 연구는 digital-statistic convergence만 다룬다. 지각적 painterly
  resemblance를 주장하려면 별도 맹검 human study가 필요하다.

어느 위험도 좋은 결과를 본 뒤 기준을 완화하는 방식으로 해결하지 않는다. 실패하면 실패
component를 보고하고, 필요한 경우 새 protocol version과 새 untouched confirmation을 만든다.

## 14. 최종 한 문장

> 이 프로젝트는 아직 자료수집 결과가 아니라 검증 가능한 연구계획 단계이며, active-study
> 실작품과 생성 output은 모두 0이다. 향후에도 availability·content adherence를 먼저 통과하고,
> near-copy를 제외한 분석가능 output의 분포가 하나의 공통 8차원 content target으로
> 표준화된 R0a 봉인-confirmation **전수 유한모집단**과 절대 적합성·coverage·모든 이웃화가
> specificity를 동시에 통과할 때만, 특정 digital feature family에 한정해 재현을 주장한다.
