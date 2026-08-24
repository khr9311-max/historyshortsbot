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
│   ├── script.md              # 대본 + 씬 분해
│   ├── scenes.tsv             # 씬 매니페스트 (build.sh 입력)
│   ├── sources.md             # ★ 팩트 출처. 비어 있으면 발행 금지
│   ├── diagrams/S03.py        # Manim 씬 (도해 컷)
│   ├── assets/
│   │   ├── images/  S02.png
│   │   ├── clips/   S01.mp4   # i2v 결과 + Manim 렌더 결과
│   │   ├── vo/      vo.wav
│   │   └── bgm/     amb.wav bgm.mp3
│   └── sub.ass
├── scripts/
│   ├── new_episode.sh
│   ├── build.sh
│   └── qc.sh
├── assets_global/             # dust_overlay.mp4, 폰트, 픽토그램 SVG
└── render/                    # EP001_final.mp4
```

---

## scenes.tsv 포맷

탭 구분. `build.sh`가 이 파일만 보고 전체를 조립한다.

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

```bash
./scripts/new_episode.sh EP007     # 에피소드 스캐폴드 생성
./scripts/build.sh EP007           # 전체 조립 → render/EP007_final.mp4
./scripts/qc.sh EP007              # 발행 전 자동 검사
manim -qh episodes/EP007/diagrams/S03.py --format=mp4   # 도해 단독 렌더
```

---

## Claude Code가 지켜야 할 규칙

### 시각 스타일
- `docs/02_스타일_바이블.md`의 색상·폰트·타이밍 값은 **하드코딩된 상수**로 취급한다. Manim 씬을 쓸 때 임의의 색을 쓰지 말고 반드시 바이블 값을 참조한다.
- 새 Manim 씬은 `episodes/<EP>/diagrams/` 안의 기존 씬 스타일을 먼저 읽고 그대로 따른다.
- 애니메이션은 느리게. `run_time`은 최소 1.2초 이상. 빠른 모션은 싸구려로 보인다.

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
