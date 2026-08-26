#!/usr/bin/env bash
# 사용법: ./scripts/new_episode.sh EP007
set -euo pipefail

EP="${1:?사용법: ./scripts/new_episode.sh EP007}"
cd "$(dirname "$0")/.."
DIR="episodes/${EP}"

[ -d "$DIR" ] && { echo "이미 존재합니다: $DIR" >&2; exit 1; }

mkdir -p "$DIR"/{diagrams,prompts,assets/{images,clips,vo,bgm}}

# ------------------------------------------------------------
# scenes.json — 대본 · 씬 분해 · 프롬프트의 단일 권원
#
# 골격을 채워 둔다. 비워 두면 매번 다른 구조가 나오기 때문이다.
#   샷(shot)  = 돈이 나가는 생성 단위. veo 클립 1개가 씬 2개를 채운다.
#   씬(scene) = 나레이션 한 덩어리 = 컷 하나.
# scenes.tsv / timing.json / sub.ass 는 전부 여기서 파생된다.
# ------------------------------------------------------------
cat > "$DIR/scenes.json" <<JSON
{
  "episode": "${EP}",
  "title": "(제목)",
  "shots": [
    {
      "id": "V01",
      "kind": "veo",
      "scenes": ["S01", "S02"],
      "risk": "low",
      "golden_ref": "GP-01",
      "chars": 0,
      "prompt": "[0-5s] Beat A - wide situation, slow side tracking shot. [5-8s] Beat B - rapid push-in close-up on the decisive detail. Cinematic documentary footage, deep navy blue tone, low saturation, single directional light, heavy atmospheric haze, silhouette figures only, no visible faces, subtle film grain, 9:16 vertical, 8 seconds. No Korean text."
    },
    {
      "id": "I01",
      "kind": "still",
      "scenes": ["S05"],
      "risk": "low",
      "golden_ref": "GP-05",
      "chars": 0,
      "prompt": "Cinematic documentary still, wide composition of a subject, deep navy blue tone, low saturation, single directional light, heavy atmospheric haze, silhouette figure at the far edge, no visible faces, subtle film grain, 9:16 vertical, 2K. No Korean text."
    },
    {
      "id": "V02",
      "kind": "veo",
      "scenes": ["S07", "S08"],
      "risk": "low",
      "golden_ref": "GP-02",
      "chars": 0,
      "prompt": "[0-5s] Beat A - wide situation, slow side tracking shot. [5-8s] Beat B - rapid push-in close-up on the decisive detail. Cinematic documentary footage, deep navy blue tone, low saturation, single directional light, heavy atmospheric haze, silhouette figures only, no visible faces, subtle film grain, 9:16 vertical, 8 seconds. No Korean text."
    }
  ],
  "scenes": [
    {"id": "S01", "shot": "V01", "beat": "A", "move": "side_track", "pause": 0.42,
     "note": "도입 훅",
     "narration": "(훅 문장)",
     "subs": ["(자막 1줄)", "*(강조 구간)*"]},

    {"id": "S02", "shot": "V01", "beat": "B", "move": "push_in", "pause": 0.46,
     "note": "훅 결정타",
     "narration": "(질문으로 닫는 문장)",
     "subs": ["(자막)", "*(강조)*"]},

    {"id": "S03", "kind": "diagram", "pause": 0.34,
     "note": "도해 - 통념 부정",
     "narration": "(통념을 걷어내는 문장)",
     "subs": ["(자막)", "*(강조)*"]},

    {"id": "S04", "kind": "diagram", "pause": 0.40,
     "note": "도해 - 두 조건 수렴",
     "narration": "(두 조건이 겹쳤다는 문장)",
     "subs": ["(자막)", "*(강조)*"]},

    {"id": "S05", "shot": "I01", "move": "dolly_in", "pause": 0.34,
     "note": "조건 1 - 현장",
     "narration": "(첫째 조건)",
     "subs": ["(자막)", "*(강조)*"]},

    {"id": "S06", "kind": "diagram", "pause": 0.44,
     "note": "도해 - 조건 1 의 작동 방식",
     "narration": "(수치·비교로 조건 1 을 보이는 문장)",
     "subs": ["(자막)", "*(강조)*"]},

    {"id": "S07", "shot": "V02", "beat": "A", "move": "side_track", "pause": 0.40,
     "note": "조건 2 - 현장",
     "narration": "(둘째 조건)",
     "subs": ["(자막)", "*(강조)*"]},

    {"id": "S08", "shot": "V02", "beat": "B", "move": "push_in", "pause": 0.42,
     "note": "조건 2 결정타",
     "narration": "(둘이 겹친 결과)",
     "subs": ["(자막)", "*(강조)*"]},

    {"id": "S09", "kind": "diagram", "pause": 0.0,
     "note": "도해 - 인과 요약 + 루프백",
     "narration": "(S01 훅으로 물리는 마지막 문장)",
     "subs": ["(자막)", "*(강조)*"]}
  ]
}
JSON

# ------------------------------------------------------------
# 실행기 — 대본은 들고 있지 않다. scenes.json 만 읽는다.
# ------------------------------------------------------------
cat > "$DIR/generate_audio_and_subs.py" <<PY
"""
${EP} — 나레이션 · 자막 · 컷 길이 생성

대본은 이 파일이 아니라 **scenes.json** 에 있다 (단일 권원).
처리는 scripts/lib_narration.py 가 한다.

    python episodes/${EP}/generate_audio_and_subs.py
    → assets/vo/vo.wav · sub.ass · scenes.tsv · timing.json

보통은 이걸 직접 부르지 않고 파이프라인을 쓴다.

    python scripts/pipeline.py ${EP}
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))
from lib_narration import generate_from_scenes  # noqa: E402

if __name__ == "__main__":
    generate_from_scenes("${EP}")
PY

# ------------------------------------------------------------
# 도해 씬 골격
# ------------------------------------------------------------
cat > "$DIR/diagrams/S03.py" <<'PY'
"""
S03 — 도해

색·폰트·크기를 직접 쓰지 않는다. lib_style 의 상수만 쓴다.
모든 요소는 guard() 를 통과해야 하고, 같은 층위는 no_overlap() 으로 검사한다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403,E402


class S03Scene(DiagramScene):  # noqa: F405
    # scenes.tsv 의 dur 과 일치시킨다. 초과하면 렌더가 실패한다.
    DURATION = 4.0

    def build(self):
        pass
PY

# scenes.json 골격의 도해 씬 번호와 맞춘다 (S03 · S04 · S06 · S09)
for N in S04 S06; do
  sed -e "s/^S03 —.*/${N} — 도해/" -e "s/class S03Scene/class ${N}Scene/" \
      "$DIR/diagrams/S03.py" > "$DIR/diagrams/${N}.py"
done

# 마지막 컷: 루프백용 (LOOP_TAIL 로 배경색 수렴)
sed -e 's/^S03 —.*/S09 — 인과 요약 + 루프백 (마지막 컷)/' \
    -e 's/class S03Scene/class S09Scene/' \
    -e 's/    DURATION = 4.0/    DURATION = 4.0\n    LOOP_TAIL = 1.25  # 끝 프레임을 BG 로 수렴 → 반복 재생 이음매 제거/' \
    "$DIR/diagrams/S03.py" > "$DIR/diagrams/S09.py"

cat > "$DIR/script.md" <<MD
# ${EP}

## 소재
(소재 큐 번호 · 제목)

## 인과 구조 한 줄
조건 A + 조건 B → 결과 C

> 대본·씬 분해·프롬프트의 단일 권원은 \`scenes.json\` 이다.
> \`scenes.tsv\` / \`sub.ass\` / \`timing.json\` / \`prompts/\` 는 전부 거기서 파생된다.
> **scenes.tsv 의 dur 을 손으로 고치지 마라.** 대본을 고치고 다시 생성한다.
>
> 이 문서는 사람이 읽는 기획서다. 구조를 잡을 때 쓰고, 확정되면 scenes.json 에 옮긴다.

## 대본
### ① 도입 (S01~S02 · V01 한 클립)
### ② 난관 (S03~S04)
### ③ 해결 (S05~S08)
### ④ 마무리 · 루프백 (S09)
(마지막 문장이 ①의 훅으로 이어지게 쓴다 — 바이블 §11)

## 서술 점검 (바이블 §8)
- 다인과:
- 학설 구분:
- 결정론 프레임 없음:
- 수치 출처:
MD

cat > "$DIR/sources.md" <<MD
# ${EP} 출처

> 모든 수치·연도·인용에 근거를 기입한다.
> **빈칸이 하나라도 있으면 발행 금지.**

| 항목 | 대본 내 위치 | 출처 | 확인일 |
|---|---|---|---|
|  |  |  |  |

## 학설 구분
- 지배적 학설:
- 소수설/반론:
MD

cat <<EOF
생성 완료: $DIR

다음 순서:
  1. $DIR/script.md 로 구조를 잡고 $DIR/scenes.json 을 채운다
     (프롬프트는 docs/06_골든_프롬프트.md 의 예시를 붙여 만든다)
  2. $DIR/sources.md 의 빈칸을 채운다 — 비면 GATE1 에서 멈춘다
  3. python scripts/pipeline.py ${EP}
     → 구조 검증 → 나레이션 → prompts/ 생성까지 가고 생성물이 없어 멈춘다
  4. prompts/*.txt 를 생성 서비스에 붙여 결과를 assets/ 에 넣는다
       veo 클립  → assets/clips/<샷ID>.mp4
       still 이미지 → assets/images/<샷ID>.png
  5. scenes.tsv 의 dur 을 각 도해의 DURATION 에 옮기고 씬 코드를 작성한다
  6. python scripts/pipeline.py ${EP} --to assemble
  7. ./scripts/qc.sh ${EP}   (Windows: .\\scripts\\qc.ps1 ${EP})
EOF
