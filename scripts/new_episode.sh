#!/usr/bin/env bash
# 사용법: ./scripts/new_episode.sh EP007
set -euo pipefail

EP="${1:?사용법: ./scripts/new_episode.sh EP007}"
cd "$(dirname "$0")/.."
DIR="episodes/${EP}"

[ -d "$DIR" ] && { echo "이미 존재합니다: $DIR" >&2; exit 1; }

mkdir -p "$DIR"/{diagrams,assets/{images,clips,vo,bgm}}

# ------------------------------------------------------------
# 대본 → 음성·자막·컷 길이 생성기
# scenes.tsv 는 여기서 자동 생성되므로 스캐폴드에 만들지 않는다.
# ------------------------------------------------------------
cat > "$DIR/generate_audio_and_subs.py" <<PY
"""
${EP} — 나레이션 · 자막 · 컷 길이 생성

이 파일은 대본만 들고 있다. 처리는 scripts/lib_narration.py 가 한다.

    python episodes/${EP}/generate_audio_and_subs.py
    → assets/vo/vo.wav · sub.ass · scenes.tsv · timing.json

pause : 이 문장 뒤의 정지 길이(초). 컷 전환이 여기서 일어난다.
subs  : 화면 자막. *별표* 로 감싼 구간이 ACCENT. 한 컷 최대 2줄, 강조는 한 곳만.

바이블 §8  단일 원인 금지 · 학설 구분 명시 · 출처 없는 수치 금지
바이블 §11 마지막 문장은 S01 의 훅으로 이어지게 쓴다 (루프백)
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))
from lib_narration import Beat, generate  # noqa: E402

BEATS = [
    Beat(
        scene="S01", kind="ai_hero", move="orbit", pause=0.42,
        note="도입 훅",
        vo="여기에 훅 문장.",
        subs=["여기에 훅 문장."],
    ),
    Beat(
        scene="S02", kind="ai_still", move="dolly_in", pause=0.44,
        note="난관",
        vo="왜 그렇게 됐을까요?",
        subs=["왜 *그렇게* 됐을까요?"],
    ),
    Beat(
        scene="S03", kind="diagram", pause=0.40,
        note="도해 - 인과 화살표",
        vo="두 조건이 겹쳤습니다.",
        subs=["*두 조건*이 겹쳤습니다."],
    ),
    Beat(
        # 마지막 컷은 diagram 요약 + 루프백 (바이블 §7, §11)
        scene="S04", kind="diagram", pause=0.0,
        note="도해 - 요약 + 루프백 (끝 프레임 BG 수렴)",
        vo="그래서 첫 문장으로 되돌아가는 마무리.",
        subs=["그래서 첫 문장으로", "*되돌아가는 마무리.*"],
    ),
]

if __name__ == "__main__":
    generate("${EP}", BEATS)
PY

# ------------------------------------------------------------
# 도해 씬 견본
# ------------------------------------------------------------
cat > "$DIR/diagrams/S03.py" <<'PY'
"""
S03 — 인과 화살표

색·폰트·크기·세이프에어리어는 scripts/lib_style.py 에서만 가져온다.
직접 색을 쓰거나 이모지를 넣지 않는다 (바이블 §10).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S03Scene(DiagramScene):
    # scenes.tsv 의 dur 과 일치시킨다. 초과하면 렌더가 실패한다.
    DURATION = 4.0

    def build(self):
        head = title_block("제목")
        self.reveal(head, run_time=1.2, shift=DOWN * 0.25)

        c1 = card(txt("조건 1", size=FS_LEAD), width=7.8)
        c1.move_to(UP * 4.6)
        c2 = card(txt("조건 2", size=FS_LEAD), width=7.8)
        c2.move_to(UP * 2.2)
        plus = txt("+", size=FS_TITLE, color=DIM).move_to(UP * 3.4)

        result = card(txt("결과", size=FS_LEAD, color=ACCENT), width=7.4, accent=True)
        result.move_to(DOWN * 1.0)

        for m, n in ((c1, "c1"), (c2, "c2"), (plus, "+"), (result, "result")):
            guard(m, n)
        no_overlap((c1, "c1"), (c2, "c2"), (result, "result"))

        self.play(
            AnimationGroup(FadeIn(c1), FadeIn(plus), FadeIn(c2), lag_ratio=0.3),
            run_time=1.4,
        )
        arrow = Arrow(c2.get_bottom(), result.get_top(), color=ACCENT,
                      stroke_width=6, buff=0.08)
        self.play(GrowArrow(arrow), FadeIn(result, shift=UP * 0.25), run_time=1.4)
PY

# 마지막 컷: 루프백용 (LOOP_TAIL 로 배경색 수렴)
sed -e 's/^S03 —.*/S04 — 요약 + 루프백 (마지막 컷)/' \
    -e 's/class S03Scene/class S04Scene/' \
    -e 's/    DURATION = 4.0/    DURATION = 4.0\n    LOOP_TAIL = 1.25  # 끝 프레임을 BG 로 수렴 → 반복 재생 이음매 제거/' \
    "$DIR/diagrams/S03.py" > "$DIR/diagrams/S04.py"

cat > "$DIR/script.md" <<MD
# ${EP}

## 소재
(소재 큐 번호 · 제목)

## 인과 구조 한 줄
조건 A + 조건 B → 결과 C

> 나레이션 원문과 컷 길이는 \`generate_audio_and_subs.py\` 의 \`BEATS\` 가 단일 권원이다.
> \`scenes.tsv\` / \`sub.ass\` / \`timing.json\` 은 전부 거기서 자동 생성된다.
> **scenes.tsv 의 dur 을 손으로 고치지 마라.**

## 대본
### ① 도입
### ② 난관
### ③ 해결
### ④ 마무리 · 루프백
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
  1. $DIR/script.md 에 대본을 쓰고
     $DIR/generate_audio_and_subs.py 의 BEATS 에 옮긴다
  2. python $DIR/generate_audio_and_subs.py
     → scenes.tsv 가 생성된다. 거기 적힌 dur 을 각 도해의 DURATION 에 옮긴다
  3. AI 이미지/영상을 assets/images · assets/clips 에 넣는다
  4. ./build.sh ${EP}
  5. ./scripts/qc.sh ${EP}   (Windows: .\\scripts\\qc.ps1 ${EP})
EOF
