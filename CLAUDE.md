# CLAUDE.md — 역사 인과 쇼츠 제작 리포지토리

## 이 리포지토리는 무엇인가

역사적 사건의 **인과관계와 논리 구조**를 설명하는 유튜브 쇼츠(9:16, 45~55초)를 제작하는 파이프라인이다.
"무슨 일이 있었나"가 아니라 **"왜 그렇게 될 수밖에 없었나"**를 설명한다.

발행: 주 3편 (월/수/금) · 예산: 월 10만원 이내 · 언어: 한국어
영상 생성: **Veo 3.1 Lite** (1080p, $0.08/s → 8초 클립 ≈ 900원)

---

## 컷 타입 — 이 프로젝트의 핵심 구조

모든 씬은 셋 중 하나다. **타입 배분이 비용과 퀄리티를 동시에 결정한다.**

| 타입 | `kind` | 내용 | 제작 방식 | 편당 | 비용 |
|---|---|---|---|---|---|
| 영상 컷 | `veo` | 현장·풍경·인물 실루엣, 실제 움직임 | Veo 3.1 Lite t2v 8초 2비트 | **6컷** | 900원/클립 |
| 정지 컷 | `still` | 위와 같으나 슬로우 줌만 | AI 이미지 → FFmpeg zoompan | 1컷 | 이미지값만 |
| **도해 컷** | `diagram` | 인과 화살표·타임라인·지도·그래프·픽토그램 | **Manim 투명 렌더 → 배경 플레이트 위 합성** | **3컷** | **0원** |

편당 10컷. 유료 생성은 **서사 클립 3개**뿐이다 (2,700원/편 · 월 12편 32,400원).

**원칙: 글자·숫자·화살표가 들어가는 컷은 무조건 `diagram`이다.**
AI 영상 생성은 한글을 반드시 깨뜨린다. 예외 없음.

**원칙: 도해 컷은 단색 배경 위에 놓지 않는다.** 알파 채널로 렌더해
배경 플레이트 위에 얹는다. 이래야 10컷 중 정지 톤인 컷이 하나도 남지 않는다.

### 샷과 씬은 다르다 ★

**veo 클립 하나(8초)가 씬 두 개를 채운다.**

```
V01 (8초 t2v 클립 = 유료 생성 1회)
  ├── S01  beat A  side_track   나레이션 3.84초 → 클립 [0, 3.84] 구간
  └── S02  beat B  push_in      나레이션 2.99초 → 클립 [3.84, 6.83] 구간
```

- 씬(scene) = 나레이션 한 덩어리 = 컷 하나
- 샷(shot) = API 호출 한 번 = **돈이 나가는 단위**
- veo 컷 6개라도 청구되는 건 클립 3개다

비트 경계는 대본이 정한다. 프롬프트의 `[0-5s]`/`[5-8s]`는 임시값이고,
TTS 실측이 나오면 `pipeline.py`가 `[0-3.8s]`/`[3.8-8s]`로 갈아끼운다.
자세한 건 `docs/05_영상프롬프트_규칙.md` §2.

**두 씬의 길이 합이 8초를 넘으면 파이프라인이 멈춘다.**
정지 구간을 빼면 발화 7초, 한국어로 두 문장 합쳐 45자 안팎이다.

### 배경 플레이트 ★

도해 컷의 배경은 **에피소드마다 새로 생성하지 않는다.**
`assets_global/plates/` 에 둔 8초 추상 루프를 재사용한다. 추가 비용 0원이다.

```
P_fog.mp4    느린 안개 흐름          — 인과 다이어그램·통념 부정
P_dust.mp4   빛줄기 속 먼지 입자     — 타임라인·연표
P_grid.mp4   아주 느린 격자 드리프트 — 그래프·수치 컷
```

- 플레이트는 **초점이 맞은 대상이 없어야 한다.** 도해가 주인공이고 배경은 질감이다.
- 밝기는 바이블 배경색 근처로 눌러 둔다. 도해 텍스트 대비를 잡아먹으면 안 된다.
- 씬마다 시작 오프셋을 달리 줘서 같은 플레이트가 반복돼 보이지 않게 한다.
- 플레이트가 낡으면 **한 번 새로 뽑아 전 에피소드가 같이 갈아탄다.**
  에피소드별로 다른 플레이트를 쓰면 채널 톤이 흩어진다.

플레이트는 `scenes.json` 의 `shots` 에 넣지 않는다. 에피소드 자산이 아니라 전역 자산이다.

---

## 디렉토리 구조

```
.
├── CLAUDE.md
├── .claude/commands/          # 슬래시 커맨드 (/new-episode, /qc)
├── docs/
│   ├── 01_프로젝트_지침.md      # claude.ai 프로젝트 지침 원본
│   ├── 02_스타일_바이블.md      # ★ 모든 시각 결정의 단일 기준
│   ├── 03_제작_SOP.md
│   ├── 04_소재_큐.md
│   ├── 05_영상프롬프트_규칙.md  # ★ 컷 타입·2비트·리스크·scenes.json 스키마
│   ├── 06_골든_프롬프트.md      # ★ 프롬프트 라이브러리. A/B 계열 앵커
│   └── 07_대본_문체_규칙.md     # ★ 어미 리듬·셀프 문답·반전의 한계
├── episodes/EP001/
│   ├── scenes.json            # ★ 단일 권원 (대본·씬 분해·프롬프트)
│   ├── generate_audio_and_subs.py  # scenes.json 을 읽는 얇은 실행기
│   ├── script.md              # 사람이 읽는 기획서
│   ├── scenes.tsv             # 씬 매니페스트 — 자동 생성. 손으로 고치지 말 것
│   ├── timing.json            # 실측 시각 — 자동 생성. build/qc 가 참조
│   ├── sources.md             # ★ 팩트 출처. 비어 있으면 발행 금지
│   ├── prompts/V01.txt        # 비트 경계가 확정된 최종 프롬프트 — 자동 생성
│   ├── diagrams/S03.py        # Manim 씬 (lib_style 만 import)
│   ├── assets/
│   │   ├── images/  I01.png   # ← 샷 이름
│   │   ├── clips/   V01.mp4   # ← 샷 이름 (도해 결과는 씬 이름 S03.mp4)
│   │   ├── vo/      vo.wav
│   │   └── bgm/     amb.wav bgm.mp3
│   ├── sub.ass                # 자동 생성
│   └── .state.json            # 파이프라인 진행 상태 — 자동 생성
├── build.sh                   # 래퍼 → scripts/build.py
├── scripts/
│   ├── pipeline.py            # ★ 단일 진입점. 순서·상태·게이트·검증
│   ├── lib_scenes.py          # ★ scenes.json 로더·검증기
│   ├── lib_narration.py       # 대본 → 음성·자막·컷 길이 (타임라인 권원)
│   ├── lib_style.py           # ★ 바이블의 코드판. 색·타이포·세이프에어리어·픽토그램
│   ├── build.py               # 조립 파이프라인 본체
│   ├── build.ps1              # 래퍼 (Windows)
│   ├── new_episode.sh
│   └── qc.ps1 / qc.sh
├── assets_global/             # dust_overlay.mp4, 폰트, 픽토그램 SVG
│   └── plates/                # ★ 도해 배경 루프 (P_fog/P_dust/P_grid.mp4)
└── render/                    # EP001_final.mp4
```

---

## 권원은 scenes.json, 타임라인은 나레이션이 결정한다

`episodes/<EP>/scenes.json` 이 대본·씬 분해·프롬프트의 **유일한 권원**이다.
claude.ai 프로젝트가 이 파일 하나를 뱉고, 나머지는 전부 파생물이다.

```
scenes.json ──> vo.wav · sub.ass · scenes.tsv · timing.json · prompts/*.txt
```

`lib_narration.py` 가 문장 단위로 TTS 를 뽑고 정지 구간을 직접 넣어
실측 시각으로 위 넷을 함께 만든다.

- **`scenes.tsv` 의 dur 을 손으로 고치지 마라.** `scenes.json` 을 고치고 다시 생성한다.
- **`scenes.json` 에 `dur` 을 쓰지 마라.** TTS 실측이 정한다.
- 컷 전환은 항상 문장 사이의 정지 구간에서 일어난다. 말 도중에 컷하지 않는다.
- 마지막 컷은 루프백 문장으로 닫는다 (바이블 §11).
- `scenes.json` 이 바뀌면 `.state.json` 의 진행 기록이 자동으로 무효화된다.

### 파생 파일 포맷

`scenes.tsv` — 탭 구분. 생성기가 만들고 `build.py` 는 `timing.json` 을 우선 참조한다.

```
scene	kind	move	dur	note
S01	ai_hero	side_track	3.84	도입 훅
S03	diagram	-	3.73	도해 - 통념 부정
```

`kind` 는 내부 이름으로 변환된다: `veo`→`ai_hero`, `still`→`ai_still`, `diagram` 그대로.
`scenes.json` 에는 항상 `veo`/`still`/`diagram` 을 쓴다.

---

## 자주 쓰는 명령

`pipeline.py` 가 단일 진입점이다. 순서를 기억할 필요 없이 되는 데까지 가고,
사람이 해야 할 일이 나오면 무엇을 어디에 놓아야 하는지 알려주고 멈춘다.

```bash
./scripts/new_episode.sh EP007            # 1. 스캐폴드 생성 (scenes.json 골격 포함)

python scripts/pipeline.py EP007          # 2. 되는 데까지 진행
                                          #    script → sources(GATE1) → narration
                                          #    → prompt → video → diagram → assemble
                                          #    → package → review(GATE2) → publish

python scripts/pipeline.py EP007 --status # 어디까지 됐나
python scripts/pipeline.py EP007 --from prompt --only V02   # 특정 샷만 다시
python scripts/pipeline.py EP007 --to review                # 최종 검수까지

.\scripts\qc.ps1 EP007                    # 3. 발행 전 자동 검사
```

개별 도구를 직접 부를 수도 있다.

```bash
python episodes/EP007/generate_audio_and_subs.py   # 나레이션만 다시
manim -qh --resolution 1080,1920 \
  episodes/EP007/diagrams/S03.py --format=mp4      # 도해 단독 렌더 (확인용)
./build.sh EP007                                   # 조립만
```

### 파이프라인이 멈추는 지점

| 단계 | 멈추는 이유 | 사람이 할 일 |
|---|---|---|
| `script` | 구조 위반 · `risk: high` | `scenes.json` 수정 |
| `sources` | 출처 빈칸 (GATE1) | `sources.md` 작성 |
| `prompt` | 2비트 합이 8초 초과 | 대본 축약 또는 `diagram` 전환 |
| `video` | 생성물 없음 | `prompts/*.txt` 로 생성해 `assets/` 에 배치 |
| `diagram` | 씬 코드 없음 | Manim 씬 작성 |
| `package` | `package` 필드 누락(제목/설명/썸네일 씬) | `scenes.json` 의 `package`·`hook_text` 채우기 |
| `review` | 최종 검수 (GATE2) | 결과물 확인 후 승인 |

---

## Claude Code가 지켜야 할 규칙

### 시각 스타일
- `docs/02_스타일_바이블.md`의 색상·폰트·타이밍 값은 **하드코딩된 상수**로 취급한다.
- **Manim 씬은 색·폰트·크기를 직접 쓰지 않는다.** `scripts/lib_style.py` 만 import 한다.
  바이블 값이 전부 거기 상수로 들어 있고, 세이프 에어리어·픽토그램·타이밍 검사도 같이 딸려 온다.

  ```python
  import sys, pathlib
  sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
  from lib_style import *

  class S03Scene(DiagramScene):
      DURATION = 3.73          # scenes.tsv 와 일치해야 한다. 초과하면 렌더 실패.
      def build(self):
          ...
  ```

- 모든 요소는 `guard(mob, "이름")` 을 통과시킨다. 화면 밖으로 나가면 렌더가 실패한다.
  같은 층위의 요소들은 `no_overlap()` 으로 포개짐을 검사한다.
- **이모지 금지.** 픽토그램은 `lib_style.py` 의 벡터 함수를 쓴다 (`pict_gear` 등).
  Pango 가 컬러 이모지를 빈 칸으로 떨어뜨린다.
- **도해는 투명 배경으로 렌더한다.** 씬이 배경 사각형을 직접 깔지 않는다.
  합성은 `build.py` 가 배경 플레이트와 함께 처리한다.
  플레이트 위에 얹히므로 **텍스트 대비를 스스로 확보해야 한다** — 글자 뒤 어둠은
  `lib_style.py` 의 헬퍼가 넣는다. 씬에서 직접 반투명 박스를 만들지 말 것.
- 글자에 `MUTE` 를 쓰지 않는다. 약화된 텍스트는 `DIM`.
- 애니메이션은 느리게. `run_time`은 최소 1.2초 이상. `reveal()` / `draw()` 가 강제한다.
- 모션 헬퍼를 쓴다. 정적인 도해는 이 포맷에서 이탈을 만든다.

  | 헬퍼 | 쓰는 자리 |
  |---|---|
  | `self.dolly(target, zoom=0.7)` | 결정타 요소로 달리 인. `zoom=1.0` 이면 원위치 |
  | `self.count_up("1,750", unit="km")` | 수치 컷. 숫자가 굴러 올라간다 |
  | `self.pulse(mob)` | 한 요소를 맥동. 컷당 한 번만 |
  | `self.sweep(mob)` | 계측선이 요소를 훑고 지나간다 |
  | `DRIFT = 0.006` | 씬 내내 아주 느린 줌인 (클래스 속성) |

  `DiagramScene` 은 `MovingCameraScene` 을 상속한다. 프레임을 직접 만지지 말고
  `dolly()` 를 쓴다. 세이프 에어리어 검사는 프레임이 아니라 요소 좌표 기준이다.

### 영상 프롬프트
- **규칙을 설명하지 말고 골든 프롬프트를 예시로 붙여라** (`docs/06`). 이게 일관성의 전부다.
- 프롬프트에 한글을 넣지 않는다. `lib_scenes` 가 검사해서 막는다.
  화면 위 정보는 **영어 전문용어**로 넣는다. 모델은 영어는 잘 그린다.
- 계열을 먼저 고른다. 보이는 대상이면 **B(아이소메트릭 디오라마)**, 관념이면 **A(다큐멘터리)**.
  A: `side_track` → `push_in` · B: `dolly_out` → `zoom_in`. 한 클립에서 계열을 섞지 않는다.
- 프롬프트에 실제 초를 손으로 적지 않는다. `[0-5s]`/`[5-8s]` 형식만 지킨다.
- veo 는 `pipeline.py`의 `video` 단계가 Gemini API로 직접 생성한다 (`prompts/*.txt`는
  확인용 기록이자 폴백이다). still 이미지는 여전히 사람이 생성 서비스에
  `prompts/*.txt`를 붙여 넣는다.
- 장소가 다른 두 비트를 한 클립에 묶지 않는다 (`risk: high`).

### 대본 문체
- 첫 문장은 상식을 비트는 모순문. 정보 제시가 아니라 균열이다.
- 같은 어미를 세 번 이어 쓰지 않는다 (다체/요체/질문 교차). 파이프라인이 검사한다.
- 중반 이후 시청자가 떠올릴 반박을 대신 묻고 즉시 답한다.
- **반전은 주체·순서·비용에 건다. 원인의 단일화로 만들지 않는다.** 자세한 건 `docs/07`.

### 역사 서술 (가장 중요)
- **단일 원인 설명을 만들지 마라.** 역사는 다인과다. "A 때문에 B가 됐다"가 아니라 "A가 B의 조건을 만들었고, C가 겹치며 D로 이어졌다"로 쓴다.
- 학계 논쟁이 있는 사안은 **지배적 학설과 소수설을 구분해 표기**한다. 단정문 금지.
- 지리결정론·문명우열론·민족주의 프레임 금지. 특정 집단의 우열을 함의하는 서술은 전부 거부한다.
- `sources.md`가 비어 있는 에피소드는 build를 진행하지 말고 경고한다.

### 코드
- 셸 스크립트는 `set -euo pipefail`을 유지한다.
- 에피소드 디렉토리 밖의 파일을 임의로 수정하지 않는다.
- `render/`와 `assets/`는 커밋하지 않는다 (.gitignore 유지).
- **`pipeline.py`는 veo 클립을 Gemini API(Veo 3.1 Lite)로 직접 생성한다**
  (`video` 단계, 레포 루트 `.env`에 `GEMINI_API_KEY=...` 필요 — `.gitignore`
  대상). 이미 파일이 있는 샷은 절대 다시
  부르지 않는다 — 재실행 과금 사고를 막는 유일한 장치다. 다시 뽑고 싶으면
  `assets/clips/<샷ID>.mp4`를 직접 지우고 재실행한다.
  still 이미지 생성은 여전히 사람이 한다.

### 옛 에피소드
EP001~EP003 은 `scenes.json` 이전 방식(`generate_audio_and_subs.py` 안의 `BEATS`)으로
만들어졌고 이미 렌더가 끝났다. `lib_narration.generate()` 가 계속 동작하므로 그대로 둔다.
**소급해서 옮기지 마라.** 없는 프롬프트를 지어내야 하고 얻는 게 없다.
EP004 부터 새 방식을 쓴다.

---

## 하지 말 것

- AI 영상 생성 컷에 한글 텍스트를 넣으려 시도하기
- `scenes.json` 에 `dur` 을 적어 넣기 (TTS 실측이 정한다)
- 스타일 바이블 값을 "더 나아 보인다"는 이유로 변경하기 (개정은 별도 세션에서만)
- 실존 인물의 얼굴을 특정해 생성하기
- 출처 없는 수치를 대본에 넣기
- 도해 씬 안에서 배경을 직접 칠하기 (합성은 `build.py` 몫이다)
- 에피소드마다 배경 플레이트를 새로 생성하기 (전역 자산을 재사용한다)
- 예산이 남는다고 서사 클립을 4개 이상 잡기
  (Lite 기준 3개 = 32,400원/월. 재시도분 1.5배를 남겨 둬야 한다)
