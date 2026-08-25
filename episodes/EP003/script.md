# EP003 — 향신료가 비쌌던 진짜 이유는 맛이 아니었다

## 소재
소재 큐 #3 · 경제·기술의 인과 (반전형 / 지도 이동)

## 인과 구조 한 줄
[지정학적 다단계 공급망 & 독점 유통 마진] + [사체액설 의학 & 과시적 신분재의 비탄력적 수요] → [천문학적 유통 마진 누적 및 화폐 대체물화 (금/은 가치의 향신료)]

> 나레이션 원문과 컷 길이는 `generate_audio_and_subs.py` 의 `BEATS` 가 단일 권원이다.
> 이 문서를 고쳤으면 반드시 그쪽도 고치고 다시 생성해야 한다.
> `scenes.tsv` / `sub.ass` / `timing.json` 은 전부 거기서 자동 생성된다.

---

## 훅 3안
- **안 A (반전형 · 채택):** "중세 유럽에서 후추가 금값이었던 건, 고기 맛 때문이 아니었습니다."
  - *코멘트:* '맛있는 음식'이라는 직관적 상식을 정면으로 뒤집어 호기심을 극대화함.
- **안 B (수치충격형):** "인도에서 은 한 닢이던 후추 한 자루가, 유럽에선 소 스무 마리 값이 되었습니다."
  - *코멘트:* 산지와 소비지 간 60배 이상의 극단적인 가격 격차를 가축 가치로 환산해 지적 충격을 줌.
- **안 C (역설형):** "고기 썩은 내를 가리려 후추를 썼다는 말은, 역사상 가장 비싼 가짜 뉴스입니다."
  - *코멘트:* 대중적 통념(썩은 고기 방부설)을 직접 저격하여 반박 욕구와 시청 몰입을 유도.

---

## 대본 (실측 50.75초)

### ① 도입 (0~5.66초)
중세 유럽에서 후추가 금값이었던 건, 고기 맛 때문이 아니었습니다.

### ② 난관 (5.66~15.86초)
고기 썩은 내를 가리려 썼다는 말은, 완전히 틀렸습니다.
신선한 고기를 먹던 귀족만 샀고, 가난한 사람은 구경도 못 했습니다.

### ③ 해결 (15.86~38.69초)
다단계 무역로와 중세 의학, 두 조건이 가격을 밀어 올렸습니다.
첫째, 인도에서 출발해 수십 개 거점을 거치며 관세가 쌓였습니다.
유럽에 도착하면 산지 가격의 60배로 뛰었지만, 베네치아의 독점이었습니다.
둘째, 소화를 돕는 필수 약재이자, 부를 과시하는 신분재였습니다.

### ④ 마무리 · 루프백 (38.69~50.75초)
독점 공급망과 대체 없는 수요가 만나면, 음식은 화폐가 됩니다.
그래서 향신료가 비쌌던 진짜 이유는, 맛이 아니라 독점과 신분이었습니다.

> **루프 설계**: 마지막 문장이 곧 ①의 훅으로 이어진다.
> 쇼츠 자동 반복 시 "…맛이 아니라 독점과 신분이었습니다" → "중세 유럽에서 후추가
> 금값이었던 건, 고기 맛 때문이 아니었습니다" 가 완벽한 하나의 문맥으로 연결된다.
> 화면도 S09 가 배경색으로 수렴하고 S01 이 같은 배경색에서 열려 이음매가 없다.

---

## 씬 분해표

컷 길이는 실제 나레이션에서 측정된 실측값이다 (`scenes.tsv` 와 동일).
컷 전환은 항상 문장과 문장 사이의 **정지 구간**에서 일어난다.

| 씬 | kind | move | dur | 나레이션 | 비주얼 |
|:---|:---|:---|---:|:---|:---|
| S01 | ai_hero | orbit | 5.66 | 중세 유럽에서 후추가 금값이었던 건, 고기 맛 때문이 아니었습니다. | 15세기 유럽 귀족 대연회장, 은쟁반과 향신료 잔 |
| S02 | ai_still | dolly_in | 4.54 | 고기 썩은 내를 가리려 썼다는 말은, 완전히 틀렸습니다. | 중세 정육소, 염장된 고기통과 신선육 가공대 |
| S03 | diagram | - | 5.66 | 신선한 고기를 먹던 귀족만 샀고, 가난한 사람은 구경도 못 했습니다. | 픽토그램 대비 — 대중 통념(썩은 고기 방부 ✕) vs 실체(귀족 신선육 소비 ○) |
| S04 | diagram | - | 5.42 | 다단계 무역로와 중세 의학, 두 조건이 가격을 밀어 올렸습니다. | 인과 화살표 — 조건1(다단계 공급망) + 조건2(신분재·의학 수요) → 가격 폭등 |
| S05 | ai_hero | dolly_in | 5.42 | 첫째, 인도에서 출발해 수십 개 거점을 거치며 관세가 쌓였습니다. | 15세기 인도양 말라바르(칼리컷) 항구와 무역선 선적 |
| S06 | diagram | - | 6.06 | 유럽에 도착하면 산지 가격의 60배로 뛰었지만, 베네치아의 독점이었습니다. | 지도 이동 + 수치 그래프 — 산지(1x) → 관세·운송 → 베네치아 독점(60x 폭등) |
| S07 | ai_still | dolly_in | 5.93 | 둘째, 소화를 돕는 필수 약재이자, 부를 과시하는 신분재였습니다. | 15세기 유럽 약제상 연구실, 갈레노스 사체액설 서적과 정밀 저울 |
| S08 | ai_hero | crane_up | 5.19 | 독점 공급망과 대체 없는 수요가 만나면, 음식은 화폐가 됩니다. | 황혼녘 베네치아 대운하와 산마르코 광장 무역 상인 실루엣 |
| S09 | diagram | - | 6.86 | 그래서 향신료가 비쌌던 진짜 이유는, 맛이 아니라 독점과 신분이었습니다. | 인과 요약 + 루프백 명제 + 학설 각주 → BG 수렴 |

### AI 이미지 프롬프트 고정 블록
바이블 §4 그대로. 씬별 주제어 뒤에 붙인다.

```
, cinematic documentary still, deep navy blue tone, low saturation,
single directional light, heavy atmospheric haze, wide establishing shot,
silhouette figures only, no visible faces,
subtle film grain, 9:16 vertical composition, 2K
--neg text, letters, numbers, signage, logo, watermark,
close-up faces, hands, modern objects, oversaturated, cartoon, illustration, cluttered
```

| 씬 | 주제어 |
|:---|:---|
| S01 | 15th century European grand castle banquet hall at night, candlelit wooden banquet table with silver platters and dark exotic spices in small golden chalice, noble silhouettes |
| S02 | 15th century medieval butchery cellar, salted meat hanging on hooks, large wooden barrels filled with coarse salt, dim cellar lantern light |
| S05 | 15th century Malabar coast Calicut harbor in India at twilight, silhouettes of Arab dhows and wooden merchant ships loading spice sacks, misty tropical bay |
| S07 | 15th century medieval apothecary workshop, glass vials, copper balance scales weighing precious black peppercorns, ancient Latin medical manuscripts, candle light |
| S08 | Ominous twilight skyline of Venice Grand Canal, silhouette of Venetian merchant galleys and St. Mark's Basilica against misty dark navy sky |

---

## 서술 점검 (바이블 §8)
- **다인과**: 다단계 독점 공급망(공급 조건) + 사체액설 의학 및 신분재(수요 조건), 두 조건의 결합으로만 결과를 도출.
- **학설 구분**: 지배학설(잭 터너, 폴 프리드먼의 중세 지위재 및 사체액설 소비론 + 페르낭 브로델의 유통 마진 누적론)을 뼈대로 하고, 보완설(오스만 제국의 관세 인상 영향 및 대항해시대 항로 개척 유인)은 S09 화면 각주로 명시. `sources.md` 참조.
- **결정론 프레임 없음**: 향신료의 고가를 지리적 거리의 필연성으로만 환원하지 않고, 중세 유럽의 계급 구조와 독점 무역 체제의 제도적 산물로 서술.
- **수치 출처**: 화면의 모든 수치(산지 대비 유럽 도착 가격 60배 폭등, 바스코 다 가마 원정 60배 이윤, 귀족 중심 소비)에 학술 문헌 근거 기입 완료.

---

## 발행 메타데이터
- **제목 1안:** 향신료가 금값이었던 진짜 이유 (고기 맛 때문이 아닙니다)
- **제목 2안:** 썩은 고기 냄새를 가리려 후추를 썼다는 거짓말의 진실
- **제목 3안:** 중세 귀족들은 왜 후추에 전 재산을 걸었을까?
- **설명문:** "중세 유럽인들은 썩은 고기 냄새를 없애려고 후추를 썼다?" 역사상 가장 널리 퍼진 이 가짜 뉴스의 실체를 파헤칩니다. 산지 가격의 60배가 넘는 극단적인 다단계 유통 독점과, 갈레노스 사체액설 및 부의 과시가 결합된 향신료 경제의 인과관계를 도해로 분석합니다.
- **해시태그:** `#역사 #세계사 #향신료 #경제사 #중세유럽 #인과관계 #쇼츠 #지식`
- **썸네일 문구:** 썩은 고기 가리려고? 후추가 비쌌던 진짜 이유
- **고정 댓글(다음 편 예고):** 다음 편 — 철도가 표준시간대를 만들어낸 과정.
