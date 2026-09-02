# Painter Feature Generation v1 공식 자료원 경로 감사

- 기준일: 2026-09-02
- protocol: `painter-feature-generation-v1/2.0`
- 목적: Protocol 2.0의 고정 source registry를 실제 수집 가능한 권위·매체 경로로 구체화
- 상태: 공식 문서 기반 사전 경로 감사; source census나 작품 입장을 뜻하지 않음

## 1. 판정 원칙

각 자료원은 `authority`, `discovery`, `media/capture` 역할을 분리해 평가한다. 기관의 metadata가
CC0여도 연결된 image가 자동으로 CC0인 것은 아니다. 반대로 공개 image가 있어도 exact
attribution, oil-on-canvas, accession, 물리 작품 동일성이 확인되지 않으면 실험 작품이 아니다.

모든 실제 수집은 사전에 다음을 동결해야 한다.

1. endpoint 또는 export commit, exact creator identifier, query/body, requested fields
2. pagination, 정렬, cutoff, retry 및 terminal condition
3. authority/rights/geometry의 source field와 fail-closed 결측 처리
4. raw response 또는 source snapshot의 byte hash
5. source row → authority object/accession → physical work → capture/master → asset의 연결

## 2. 공식 자료원별 실행 가능성

| 자료원 | 권위 경로 | image/rights 경로 | 현재 판정 |
|---|---|---|---|
| AIC | 공개 artworks/search 및 item API; `artist_id`, `medium_display`, `main_reference_number` | `is_public_domain`, `image_id`, IIIF config를 item별 확인 | 인증 불필요, 전수 pagination 가능 |
| Cleveland | 공개 Open Access API 또는 versioned JSON/CSV export; accession, creator, type, support/material | `share_license_status`, `images`의 web/print/original별 URL·크기 | 인증 불필요, item-level CC0만 허용 |
| NGA | 공식 GitHub Open Data의 commit-pinned CSV; objects/constituents/relationships | `published_images.openaccess=1`, primary view, width/height, IIIF URL | live search보다 commit-pinned export 우선 |
| Yale YUAG | LUX exact person authority ID와 item search; YUAG owner, Painting, oil+canvas, Artist role | 공식 YUAG IIIF manifest의 work/image rights와 canvas service | 공개 API 가능; manifest별 rights 필요 |
| Getty | exact person ID를 사용한 Museum Collection SPARQL/Linked Art object | preferred media record의 `subject_to`, download clearance, native size | 공개 API 가능; dataset CC0를 image 권리로 대체 금지 |
| Minneapolis | 공식 collection/search metadata; exact artist, Painting, Oil on canvas | item의 `rights_type`, `public_access`, display 권한과 공식 media asset | 공개 경로 가능; metadata CC0와 image policy 분리 |
| Paris Musées | exact author의 collection API/search와 official work record | work별 CC0 credit와 official IIIF/HD asset | API는 계정/token 필요; 계정 없는 대체 수집 금지 |
| Europeana | exact creator authority/query와 EDM provider record | `edm:rights` 및 provider 원기록·media 링크 | API key와 provider별 authority 재검증 필요 |
| POP/Joconde | 문화부 POP/Joconde open-data export/API | image reuse statement와 원 소장기관 record | 공개 export를 snapshot하고 institution crosswalk 필요 |

## 3. 공식 문서에서 확인한 핵심 제약

### 3.1 AIC

[AIC API 공식 문서](https://api.artic.edu/docs/)는 인증 없는 HTTPS 접근, page/limit pagination,
최대 100 records/page, item/search endpoint를 문서화한다. API metadata의 대부분은 CC0지만
`is_public_domain`은 작품의 저작권 상태이고 `copyright_notice`도 작품에 관한 필드다.
따라서 image admission은 `image_id`와 IIIF 응답, native geometry, item별 공개 상태를 함께
보존해야 한다.

### 3.2 Cleveland Museum of Art

[CMA Open Access API](https://openaccess-api.clevelandart.org/)는 versioned API/export와
`share_license_status`, `support_materials`, `type`, accession, image rendition별 URL·크기를
제공한다. dataset에는 저작권 작품도 들어 있으므로 `share_license_status=CC0`와 usable
image rendition을 각 record에서 요구한다.

### 3.3 National Gallery of Art

[NGA Open Data](https://github.com/NationalGalleryOfArt/opendata)는 자주 갱신되는 CC0 CSV
snapshot과 data dictionary를 제공한다. metadata CC0는 연결 image의 권리를 보장하지 않는다.
공식 `published_images`의 `openaccess=1`, primary view, native width/height, IIIF URL을
object/accession과 join해야 한다. branch tip이 아니라 exact commit을 evidence identity로 쓴다.

### 3.4 Yale

[Yale CDS2 공식 개발문서](https://yaleits.atlassian.net/wiki/spaces/CHI/pages/1041334298)는
`manifests.collections.yale.edu/{unit}/{object_type}/{object_id}`와 IIIF image service 규칙을
문서화한다. manifest의 일반 metadata CC0 문구와 문화재/image 권리는 동일하지 않으므로
top-level rights, `Image Use Rights`, YUAG owner, exact Artist production role를 각각 보존한다.

### 3.5 Getty

[Getty Museum Collection API 문서](https://data.getty.edu/museum/collection/docs/)는 collection
data와 media reference를 분리하며, Open Content가 아닌 image는 별도 권리가 필요하다고
명시한다. 그러므로 object dataset의 CC0만으로 image를 허용하지 않고 preferred media
record의 권리 분류와 download clearance를 요구한다.

### 3.6 Minneapolis Institute of Art

[Mia collection metadata](https://github.com/artsmia/collection)는 metadata가 CC0이지만 image는
별도 policy 대상이라고 명시한다. [Mia Open Access 설명](https://github.com/artsmia/collection-info/blob/gh-pages/open-access.md)은
Public Domain으로 표시된 image의 자유로운 재사용을 설명한다. frozen census는 item별
`rights_type`, public access/display 상태, 정확한 media URL과 크기를 함께 기록해야 한다.

### 3.7 Paris Musées

[Paris Musées API](https://apicollections.parismusees.paris.fr/)는 계정과 token을 요구한다.
[공식 이용조건](https://apicollections.parismusees.paris.fr/en/documentation/20)은 CC0 credit으로
표시된 image와 all-rights-reserved image를 구분한다. 따라서 계정/token 없이 collection
page를 API census의 조용한 대체물로 사용하지 않는다. token이 준비되기 전에는 route를
`not_executed_missing_authorized_credential`로 남긴다.

### 3.8 Europeana와 POP/Joconde

[Europeana rights 문서](https://pro.europeana.eu/page/available-rights-statements)의 rights
statement는 reuse screening에 필요하지만 provider museum의 attribution·medium·accession을
대체하지 않는다. [POP 도움말](https://pop.culture.gouv.fr/aide)은 Joconde가 프랑스
문화부/Service des Musées de France에서 관리되고 open-data platform에서도 제공됨을
명시한다. 두 aggregator 모두 원 소장기관 crosswalk가 없는 row는 authority-complete가 아니다.

## 4. 실행 순서

1. broad Wikidata 3,722행의 현재 entity/Commons metadata follow-up을 별도 freeze로 수행한다.
2. 인증 없는 공식 source(AIC, CMA, NGA snapshot, Yale, Getty, Mia, POP)를 각각 terminal
   condition까지 실행한다.
3. API key가 필요한 Europeana와 Paris Musées는 credential 존재 여부를 freeze 전에 확인하고,
   없으면 그 route 자체를 미실행 상태로 보고한다. 다른 source로 top-up하지 않는다.
4. 모든 source row를 accession 및 authority cross-reference로 physical-work graph에 합친다.
5. item-level reuse와 native short side ≥1,024를 통과한 asset만 R1 image-acquisition freeze의
   후보가 된다. 이 문서 자체는 image request를 승인하지 않는다.

## 5. 현재 결론

공개·고해상도 경로가 여러 기관에 존재하므로 “자료가 전혀 없다”는 결론은 근거가 없다.
그러나 현재 3,722 discovery rows를 작품 수로 간주하거나 Commons 권리표지를 museum authority로
간주하는 것도 근거가 없다. 충분성은 전수 source closure, 물리 작품 통합, 장면 이중코딩 후의
실제 painter×scene×workflow count로만 판단한다.
