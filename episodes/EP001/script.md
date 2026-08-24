# EP001 — 왜 산업혁명은 하필 영국에서 시작됐나

## 소재
소재 큐 #1 · 경제·기술의 인과 (역설형 / 인과 화살표)

## 인과 구조 한 줄
[고임금·저에너지 비용 구조] + [사유재산권·특허 제도] → [기계화 투자 수익 발생 (산업혁명)]

> 나레이션 원문과 컷 길이는 `generate_audio_and_subs.py` 의 `BEATS` 가 단일 권원이다.
> 이 문서를 고쳤으면 반드시 그쪽도 고치고 다시 생성해야 한다.
> `scenes.tsv` / `sub.ass` / `timing.json` 은 전부 거기서 자동 생성된다.

---

## 훅 3안
- **안 A (역설형 · 채택):** "18세기, 기술이 가장 앞섰던 나라는 영국이 아니었습니다."
- **안 B (반사실형):** "만약 당시 영국의 인건비가 쌌다면, 증기기관은 박물관의 장난감으로 끝났습니다."
- **안 C (수치충격형):** "당시 런던의 인건비는 파리의 2배, 석탄 가격은 대륙의 4분의 1이었습니다."

---

## 대본 (실측 54.2초)

### ① 도입 (0~5초)
18세기, 기술이 가장 앞섰던 나라는 영국이 아니었습니다.

### ② 난관 (5~19초)
정교한 기계는 프랑스에도 많았습니다. 그런데 왜 영국에서만 폭발했을까요?
천재가 나타나서도, 운이 좋아서도 아닙니다. 조건이 먼저였습니다.

### ③ 해결 (19~43초)
비용 구조와 제도, 두 조건이 같은 시기에 겹쳤습니다.
첫째, 영국은 사람 값이 가장 비쌌고 석탄이 가장 쌌습니다.
증기기관은 석탄을 쏟아부어야 겨우 돌았습니다. 그 낭비가 이득이 되는 곳은 영국뿐이었죠.
둘째, 명예혁명 뒤 자리 잡은 재산권과 특허가 그 투자를 지켰습니다.

### ④ 마무리 · 루프백 (43~54초)
기술 혁명은 천재가 아니라, 유인과 제도가 겹치는 자리에서 일어납니다.
그래서 기술이 가장 앞섰던 나라가, 주인공이 되지는 못했습니다.

> **루프 설계**: 마지막 문장이 곧 ①의 훅으로 이어진다.
> 쇼츠 자동 반복 시 "…주인공이 되지는 못했습니다" → "18세기, 기술이 가장 앞섰던
> 나라는 영국이 아니었습니다" 가 한 문단처럼 읽힌다.
> 화면도 S09 가 배경색으로 수렴하고 S01 이 같은 배경색에서 열려 이음매가 없다.
> 이 구조 때문에 '다음 편 예고' 카드는 넣지 않는다 (예고는 고정 댓글·설명란으로).

---

## 씬 분해표

컷 길이는 실제 나레이션에서 측정된 값이다 (`scenes.tsv` 와 동일).
컷 전환은 항상 문장과 문장 사이의 **정지 구간**에서 일어난다.

| 씬 | kind | move | dur | 나레이션 | 비주얼 |
|:---|:---|:---|---:|:---|:---|
| S01 | ai_hero | orbit | 5.20 | 18세기, 기술이 가장 앞섰던 나라는 영국이 아니었습니다. | 18세기 천문대 연구실 |
| S02 | ai_still | dolly_in | 7.14 | 정교한 기계는 프랑스에도 많았습니다. 그런데 왜 영국에서만 폭발했을까요? | 프랑스 기계공학 연구실 |
| S03 | diagram | - | 6.76 | 천재가 나타나서도, 운이 좋아서도 아닙니다. 조건이 먼저였습니다. | 픽토그램 대비 — 개인의 천재성 ✕ / 구조적 조건 ○ |
| S04 | diagram | - | 4.39 | 비용 구조와 제도, 두 조건이 같은 시기에 겹쳤습니다. | 인과 화살표 — 조건1 + 조건2 → 결과 |
| S05 | ai_hero | dolly_in | 5.29 | 첫째, 영국은 사람 값이 가장 비쌌고 석탄이 가장 쌌습니다. | 영국 석탄 탄광 |
| S06 | diagram | - | 7.90 | 증기기관은 석탄을 쏟아부어야 겨우 돌았습니다. 그 낭비가 이득이 되는 곳은 영국뿐이었죠. | 수치 그래프 — 채산성 손익 + 임금/석탄 수치 |
| S07 | ai_still | dolly_in | 5.88 | 둘째, 명예혁명 뒤 자리 잡은 재산권과 특허가 그 투자를 지켰습니다. | 영국 특허 아카이브 |
| S08 | ai_hero | crane_up | 5.56 | 기술 혁명은 천재가 아니라, 유인과 제도가 겹치는 자리에서 일어납니다. | 산업 도시 실루엣 |
| S09 | diagram | - | 6.05 | 그래서 기술이 가장 앞섰던 나라가, 주인공이 되지는 못했습니다. | 인과 요약 + 루프백 명제 + 보완설 각주 → BG 수렴 |

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
| S01 | 18th century European observatory workshop with brass telescope and clockwork mechanisms on desk, candle light |
| S02 | Interior of an 18th century French mechanical engineering laboratory with blueprints and gear models |
| S05 | Gloomy 18th century British coal mine landscape with wooden carts and coal piles in morning mist |
| S07 | 18th century British institutional archive hall, tall wooden shelves filled with rolled parchment patent documents and wax seals |
| S08 | Early British industrial city skyline with smoking chimneys in twilight haze, dramatic silhouettes of brick mills |

---

## 서술 점검 (바이블 §8)
- **다인과**: 비용 구조 + 제도, 두 조건의 결합으로만 결론을 낸다. 단일 원인 문장 없음.
- **학설 구분**: 지배학설은 앨런(고임금-저에너지) + 노스(제도). 보완설인 모키르
  '산업 계몽주의'는 S09 화면 각주로 명시. `sources.md` 참조.
- **결정론 프레임 없음**: 영국의 조건은 '우월'이 아니라 '당시의 가격 구조'로 서술.
- **수치**: 화면의 두 수치 모두 '약' + 출처 병기. `sources.md` 에 근거 기입.

---

## 발행 메타데이터
- **제목 1안:** 산업혁명은 왜 하필 영국이었을까? (기술 차이가 아닙니다)
- **제목 2안:** 영국 노동자들의 비싼 몸값이 세상을 바꾼 이유
- **제목 3안:** 프랑스도 기계가 많았는데 왜 영국만 성공했을까
- **설명문:** 산업혁명의 시작은 천재 발명가의 등장이 아니라, '비싼 인건비'와 '값싼 석탄'이라는 영국의 가격 구조와 재산권·특허 제도가 겹친 결과였습니다. 역사의 인과관계를 도해로 분석합니다.
- **해시태그:** `#역사 #산업혁명 #경제사 #세계사 #인과관계 #쇼츠 #영국역사 #지식`
- **썸네일 문구:** 기술 1위는 프랑스였다. 그런데 왜 영국인가?
- **고정 댓글(다음 편 예고):** 다음 편 — 명나라를 무너뜨린 은의 역설.
