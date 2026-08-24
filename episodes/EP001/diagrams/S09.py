"""
S09 — 인과 요약 + 루프백 (마지막 컷)
나레이션: "그래서 기술이 가장 앞섰던 나라가, 주인공이 되지는 못했습니다."

쇼츠는 자동 반복된다. 그래서 이 컷은 '끝'이 아니라 '이음매'다.

  1) 마지막 문장이 곧 S01 의 훅("기술이 가장 앞섰던 나라는 영국이 아니었습니다")과
     이어지도록 써서, 반복 재생이 한 문단처럼 읽히게 한다.
  2) LOOP_TAIL 동안 모든 요소를 배경색으로 수렴시켜 끝 프레임을 순수 BG 로 만든다.
     build.sh 가 첫 컷을 같은 BG 에서 열어 주므로 이음매가 보이지 않는다.

'다음 편 예고' 카드는 뺐다. 루프를 끊는 가장 큰 요인이라
예고는 고정 댓글/설명란으로 옮기는 편이 낫다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S09Scene(DiagramScene):
    DURATION = 6.05
    LOOP_TAIL = 1.25  # 배경색 수렴 구간

    def build(self):
        head = title_block("오늘의 인과")
        self.reveal(head, run_time=1.2, shift=DOWN * 0.25)

        # --- 한 줄 공식 ---
        formula = card(
            txt("비용 구조   +   제도", size=FS_LEAD, color=INK),
            down_arrow(ACCENT, 0.7),
            txt("기계화 투자가 이득이 된다", size=FS_LEAD, color=ACCENT),
            width=7.8, accent=True, pad_y=0.5, gap=0.18,
        )
        formula.move_to(UP * 3.9)
        guard(formula, "formula")
        self.reveal(formula, run_time=1.5, shift=UP * 0.2)

        # --- 루프백 명제: 다음 재생의 훅으로 넘겨준다 ---
        div = rule(6.8).move_to(UP * 1.1)
        prop = txt(
            "기술이 앞선 것과\n그 기술이 돈이 되는 것은\n다른 문제다",
            size=FS_LEAD, color=INK, line_spacing=1.0,
        )
        prop.move_to(DOWN * 0.7)

        # 학설 구분 명시 — 바이블 §8
        note = footnote("※ 보완설 — 모키르 '산업 계몽주의':\n숙련 기술자 네트워크를 강조")
        note.move_to(DOWN * 2.9)

        guard(VGroup(div, prop), "proposition")
        guard(note, "note")
        no_overlap((formula, "formula"), (prop, "proposition"), (note, "note"))
        self.reveal(div, prop, note, run_time=1.5, shift=UP * 0.2)

        self.beat(0.52)
        # 이후 _settle 이 LOOP_TAIL(1.25s) 동안 BG 로 수렴시킨다
