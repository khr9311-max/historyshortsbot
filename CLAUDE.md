# CLAUDE.md — 역사 인과 쇼츠 제작 리포지토리

## 이 리포지토리는 무엇인가

역사적 사건의 **인과관계와 논리 구조**를 설명하는 유튜브 쇼츠(9:16, 45~55초)를 제작하는 파이프라인이다.
"무슨 일이 있었나"가 아니라 **"왜 그렇게 될 수밖에 없었나"**를 설명한다.

발행: 주 3편 (월/수/금) · 예산: 월 5만원 이내 · 언어: 한국어

---

## 컷 타입 — 이 프로젝트의 핵심 구조

모든 씬은 셋 중 하나다. **타입 배분이 비용과 퀄리티를 동시에 결정한다.**

| 타입 | 코드 | 내용 | 제작 방식 | 편당 | 비용 |
|---|---|---|---|---|---|
| 분위기 컷 | `ai_hero` | 현장·풍경·인물 실루엣, 실제 움직임 | AI 이미지 → i2v | 3컷 | 유료 |
| 정지 컷 | `ai_still` | 위와 같으나 슬로우 줌만 | AI 이미지 → FFmpeg zoompan | 2~3컷 | 이미지값만 |
| **도해 컷** | `diagram` | 인과 화살표·타임라인·지도·그래프·픽토그램 | **Manim 코드 렌더링** | 4~5컷 | **0원** |

**원칙: 글자·숫자·화살표가 들어가는 컷은 무조건 `diagram`이다.**
AI 영상 생성은 한글을 반드시 깨뜨린다. 예외 없음.

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
│   └── 04_소재_큐.md
├── episodes/EP001/
│   ├── generate_audio_and_subs.py  # ★ 타임라인 단일 권원 (대본 → 음성·자막·컷 길이)
│   ├── script.md              # 대본 + 씬 분해 (사람이 읽는 문서)
│   ├── scenes.tsv             # 씬 매니페스트 — 자동 생성. 손으로 고치지 말 것
│   ├── timing.json            # 실측 시각 — 자동 생성. build/qc 가 참조
│   ├── sources.md             # ★ 팩트 출처. 비어 있으면 발행 금지
│   ├── diagrams/S03.py        # Manim 씬 (lib_style 만 import)
│   ├── assets/
│   │   ├── images/  S02.png
│   │   ├── clips/   S01.mp4   # i2v 결과 + Manim 렌더 결과
│   │   ├── vo/      vo.wav
│   │   └── bgm/     amb.wav bgm.mp3
│   └── sub.ass                # 자동 생성
├── build.sh                   # 래퍼 → scripts/build.py
├── scripts/
│   ├── lib_style.py           # ★ 바이블의 코드판. 색·타이포·세이프에어리어·픽토그램
│   ├── build.py               # 조립 파이프라인 본체
│   ├── build.ps1              # 래퍼 (Windows)
│   ├── new_episode.sh
│   └── qc.ps1 / qc.sh
├── assets_global/             # dust_overlay.mp4, 폰트, 픽토그램 SVG
└── render/                    # EP001_final.mp4
```

---

## 타임라인은 나레이션이 결정한다

`episodes/<EP>/generate_audio_and_subs.py` 의 `BEATS` 가 **유일한 권원**이다.
문장 단위로 TTS 를 뽑고 정지 구간을 직접 넣어, 실측 시각으로 아래 넷을 함께 만든다.

```
vo.wav  ·  sub.ass  ·  scenes.tsv  ·  timing.json
```

- **`scenes.tsv` 의 dur 을 손으로 고치지 마라.** 대본을 고치고 다시 생성한다.
- 컷 전환은 항상 문장 사이의 정지 구간에서 일어난다. 말 도중에 컷하지 않는다.
- 마지막 컷은 루프백 문장으로 닫는다 (바이블 §11).

---

## scenes.tsv 포맷

탭 구분. 위 생성기가 만들고, `build.py` 는 `timing.json` 을 우선 참조한다.

```
scene	kind	move	dur	note
S01	ai_hero	orbit	5	훅 - 폐허 원경
S02	diagram	-	5	인과 화살표 3단
S03	ai_still	dolly_in	5	곡물 창고 내부
```

- `kind`: `ai_hero` | `ai_still` | `diagram`
- `move`: `dolly_in` | `orbit` | `crane_up` (diagram이면 `-`)
- `dur`: 초. 기본 5, 훅 컷만 2

---

## 자주 쓰는 명령

제작 순서는 **나레이션 → 도해 → 조립 → 검사** 다. 순서를 지켜야 타이밍이 맞는다.

```bash
./scripts/new_episode.sh EP007                    # 1. 스캐폴드 생성

python episodes/EP007/generate_audio_and_subs.py  # 2. 나레이션·자막·컷 길이 생성
                                                  #    → vo.wav / sub.ass / scenes.tsv / timing.json

manim -qh --resolution 1080,1920 \
  episodes/EP007/diagrams/S03.py --format=mp4     # 3. 도해 단독 렌더 (확인용)

./build.sh EP007                                  # 4. 전체 조립 → render/EP007_final.mp4
.\scripts\build.ps1 EP007                         #    (Windows)

.\scripts\qc.ps1 EP007                            # 5. 발행 전 자동 검사
```

`build.sh` / `build.ps1` 은 `scripts/build.py` 를 부르는 래퍼다. 로직은 한 곳에만 있다.

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
      DURATION = 6.76          # scenes.tsv 와 일치해야 한다. 초과하면 렌더 실패.
      def build(self):
          ...
  ```

- 모든 요소는 `guard(mob, "이름")` 을 통과시킨다. 화면 밖으로 나가면 렌더가 실패한다.
  같은 층위의 요소들은 `no_overlap()` 으로 포개짐을 검사한다.
- **이모지 금지.** 픽토그램은 `lib_style.py` 의 벡터 함수를 쓴다 (`pict_gear` 등).
  Pango 가 컬러 이모지를 빈 칸으로 떨어뜨린다.
- 글자에 `MUTE` 를 쓰지 않는다. 약화된 텍스트는 `DIM`.
- 애니메이션은 느리게. `run_time`은 최소 1.2초 이상. `reveal()` / `draw()` 가 강제한다.

### 역사 서술 (가장 중요)
- **단일 원인 설명을 만들지 마라.** 역사는 다인과다. "A 때문에 B가 됐다"가 아니라 "A가 B의 조건을 만들었고, C가 겹치며 D로 이어졌다"로 쓴다.
- 학계 논쟁이 있는 사안은 **지배적 학설과 소수설을 구분해 표기**한다. 단정문 금지.
- 지리결정론·문명우열론·민족주의 프레임 금지. 특정 집단의 우열을 함의하는 서술은 전부 거부한다.
- `sources.md`가 비어 있는 에피소드는 build를 진행하지 말고 경고한다.

### 코드
- 셸 스크립트는 `set -euo pipefail`을 유지한다.
- 에피소드 디렉토리 밖의 파일을 임의로 수정하지 않는다.
- `render/`와 `assets/`는 커밋하지 않는다 (.gitignore 유지).

---

## 하지 말 것

- AI 영상 생성 컷에 한글 텍스트를 넣으려 시도하기
- 스타일 바이블 값을 "더 나아 보인다"는 이유로 변경하기 (개정은 별도 세션에서만)
- 실존 인물의 얼굴을 특정해 생성하기
- 출처 없는 수치를 대본에 넣기
