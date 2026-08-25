# EP002 — 은의 대량 유입이 명나라 재정을 무너뜨린 경로

## 소재
소재 큐 #2 · 경제·기술의 인과 (수치형 / 지도 이동 + 그래프)

## 인과 구조 한 줄
[조세 제도의 은납화(일조편법)] + [17세기 글로벌 은 공급망 충격] → [은값 폭등 및 디플레이션 → 농민 파산과 재정 고갈 (명 멸망)]

> 나레이션 원문과 컷 길이는 `generate_audio_and_subs.py` 의 `BEATS` 가 단일 권원이다.
> 이 문서를 고쳤으면 반드시 그쪽도 고치고 다시 생성해야 한다.
> `scenes.tsv` / `sub.ass` / `timing.json` 은 전부 거기서 자동 생성된다.

---

## 훅 3안
- **안 A (수치충격형 · 채택):** "전 세계 은의 3분의 1을 빨아들였던 제국이, 은 때문에 파산했습니다."
  - *코멘트:* 글로벌 은 유입량(1/3)과 제국 파산의 극단적 대조로 강한 지적 충격을 줌.
- **안 B (역설형):** "은이 쏟아져 들어올수록, 농민들의 세금은 세 배로 폭등했습니다."
  - *코멘트:* 부의 유입이 백성의 세금 폭탄으로 변한 경제적 역설을 집중 조명.
- **안 C (반사실형):** "만약 명나라가 세금을 곡물 대신 은으로만 걷지 않았다면, 제국의 수명은 훨씬 길었습니다."
  - *코멘트:* 일조편법이라는 제도적 결정타를 전면에 내세워 호기심 유발.

---

## 대본 (실측 50.95초)

### ① 도입 (0~5.85초)
전 세계 은의 3분의 1을 빨아들였던 제국이, 은 때문에 파산했습니다.

### ② 난관 (5.85~17.61초)
16세기 명나라에는 아메리카와 일본의 은이 끝없이 쏟아졌습니다.
돈이 넘치는데 국고는 비었고, 반란이 터졌습니다. 왜였을까요?

### ③ 해결 (17.61~39.26초)
조세의 은납화와 공급망 충격, 두 조건이 겹쳤습니다.
첫째, 모든 세금을 은으로만 걷는 일조편법이 농민을 묶었습니다.
둘째, 은 유입이 줄자 은값이 폭등해 농민의 실질 세금이 세 배로 치솟았습니다.
은을 못 구한 농민이 무너지자, 제국은 군대 급여조차 주지 못했죠.

### ④ 마무리 · 루프백 (39.26~50.95초)
통화 통제력을 잃은 제국은, 공급망이 흔들리면 디플레이션에 빠집니다.
그래서 전 세계 은을 가졌던 제국이, 가장 처참하게 무너졌습니다.

> **루프 설계**: 마지막 문장이 곧 ①의 훅으로 이어진다.
> 쇼츠 자동 반복 시 "…가장 처참하게 무너졌습니다" → "전 세계 은의 3분의 1을
> 빨아들였던 제국이, 은 때문에 파산했습니다" 가 자연스럽게 한 문맥으로 연결된다.
> 화면도 S09 가 배경색으로 수렴하고 S01 이 같은 배경색에서 열려 이음매가 없다.

---

## 씬 분해표

컷 길이는 실제 나레이션에서 측정된 실측값이다 (`scenes.tsv` 와 동일).
컷 전환은 항상 문장과 문장 사이의 **정지 구간**에서 일어난다.

| 씬 | kind | move | dur | 나레이션 | 비주얼 |
|:---|:---|:---|---:|:---|:---|
| S01 | ai_hero | orbit | 5.85 | 전 세계 은의 3분의 1을 빨아들였던 제국이, 은 때문에 파산했습니다. | 16세기 명나라 황실 은 보관 창고 |
| S02 | ai_still | dolly_in | 5.03 | 16세기 명나라에는 아메리카와 일본의 은이 끝없이 쏟아졌습니다. | 16세기 명나라 교역 항구와 서양 갤리온선 |
| S03 | diagram | - | 6.73 | 돈이 넘치는데 국고는 비었고, 반란이 터졌습니다. 왜였을까요? | 픽토그램 대비 — 은 풍요 상식 ✕ / 국고 파산·반란 현상 ○ |
| S04 | diagram | - | 4.73 | 조세의 은납화와 공급망 충격, 두 조건이 겹쳤습니다. | 인과 화살표 — 조건1(은납화) + 조건2(공급 충격) → 디플레이션 |
| S05 | ai_hero | dolly_in | 5.55 | 첫째, 모든 세금을 은으로만 걷는 일조편법이 농민을 묶었습니다. | 명나라 지방 관아 앞 은 세금 납부 행렬 |
| S06 | diagram | - | 6.12 | 둘째, 은 유입이 줄자 은값이 폭등해 농민의 실질 세금이 세 배로 치솟았습니다. | 수치 그래프 — 환율 폭등(1,000문→2,000문↑) & 세부담 3배 |
| S07 | ai_still | dolly_in | 5.25 | 은을 못 구한 농민이 무너지자, 제국은 군대 급여조차 주지 못했죠. | 만리장성 북방 국경 초소와 탈영한 수비군 흔적 |
| S08 | ai_hero | crane_up | 5.55 | 통화 통제력을 잃은 제국은, 공급망이 흔들리면 디플레이션에 빠집니다. | 황혼녘 먹구름 낀 자금성 궁궐 지붕 실루엣 |
| S09 | diagram | - | 6.14 | 그래서 전 세계 은을 가졌던 제국이, 가장 처참하게 무너졌습니다. | 인과 요약 + 루프백 명제 + 학설 각주 → BG 수렴 |

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
| S01 | 16th century Ming dynasty imperial treasury vault filled with wooden chests of glowing silver ingots (sycee), dramatic low candlelight, dark misty atmospheric perspective |
| S02 | 16th century Southern China maritime trade port at twilight, silhouettes of European galleons and Chinese junks unloading cargo crates in foggy bay |
| S05 | Ming dynasty local magistrate taxation courtyard at dusk, silhouette queue of peasant farmers holding small cloth pouches before wooden desk, paper lanterns |
| S07 | Cold desolate Ming dynasty military watchtower along the northern Great Wall in heavy blizzard fog, abandoned weapons and solitary guard silhouette |
| S08 | Ominous twilight skyline of Beijing Forbidden City palace roofs with flying eaves, dark storm clouds gathering, deep navy haze |

---

## 서술 점검 (바이블 §8)
- **다인과**: 조세 은납화(제도) + 글로벌 은 공급 쇼크(외부 조건), 두 조건의 결합으로만 결과를 도출.
- **학설 구분**: 지배학설(앳웰·폰 글란의 17세기 은 공급 위기설)을 뼈대로 하고, 보완설(보겔 등의 국내 통화 유통 불균형 및 군비 급증설)은 S09 화면 각주로 명시. `sources.md` 참조.
- **결정론 프레임 없음**: 명나라의 멸망을 단순한 은의 부재가 아닌, '통화 정책의 경직성과 외부 의존성'이라는 제도적 실패로 분석.
- **수치 출처**: 화면의 모든 수치(은 유입 1/3, 은-동전 환율 1,000→2,000문, 실질 세부담 3배)에 학술 문헌 근거 기입 완료.

---

## 발행 메타데이터
- **제목 1안:** 전 세계 은의 3분의 1을 가졌던 제국이 망한 이유 (명나라의 역설)
- **제목 2안:** 은이 넘쳐나던 제국은 왜 은 때문에 파산했을까?
- **제목 3안:** 세금을 은으로 걷자 백성들이 폭동을 일으킨 진짜 이유
- **설명문:** 16세기 전 세계 은의 3분의 1을 흡수하며 초강대국을 유지했던 명나라. 하지만 '일조편법'으로 세금을 은으로 고정한 상태에서 17세기 글로벌 은 공급망이 흔들리자, 치명적인 디플레이션과 세금 폭탄이 터졌습니다. 명나라 멸망의 경제적 인과관계를 도해로 분석합니다.
- **해시태그:** `#역사 #세계사 #명나라 #경제사 #인과관계 #쇼츠 #일조편법 #지식`
- **썸네일 문구:** 세계 은의 3분의 1을 가졌는데 왜 파산했을까?
- **고정 댓글(다음 편 예고):** 다음 편 — 향신료가 비쌌던 진짜 이유는 맛이 아니었다.
