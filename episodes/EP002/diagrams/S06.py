"""
S06 — 수치 그래프 : 은값 폭등과 농민 실질 세부담 3배
나레이션: "둘째, 은 유입이 줄자 은값이 폭등해 농민의 실질 세금이 세 배로 치솟았습니다."

수치 출처: Richard von Glahn, *Fountain of Fortune* (1996); William S. Atwell (1982)
은 1냥 당 동전 환율: 1,000문 → 2,000~2,500문 폭등.
농민은 곡물을 동전으로 팔아 은을 사야 했으므로 실질 세부담이 2~3배 폭증함.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403

BASE_Y = 2.45
BAR_W = 1.8
NORM_X, CRISIS_X = -1.95, 1.95


class S06Scene(DiagramScene):
    DURATION = 6.12

    def build(self):
        head = title_block("은값 폭등과 세금 폭탄")

        # --- 기준선 ---
        base = Line(LEFT * 3.6, RIGHT * 3.6, color=MUTE, stroke_width=2)
        base.move_to(UP * BASE_Y)
        label_base = tag("은 1냥당 동전 환율", DIM)
        label_base.next_to(base.get_left(), UP, buff=0.14, aligned_edge=LEFT)
        axis = VGroup(base, label_base)
        guard(axis, "baseline")

        self.reveal(head, axis, run_time=1.2, shift=DOWN * 0.2)

        # --- 16세기 평상시: 1,000문 ---
        norm_bar = Rectangle(
            width=BAR_W, height=1.35,
            color=MUTE, fill_color=MUTE, fill_opacity=0.35, stroke_width=2,
        )
        norm_bar.next_to([NORM_X, BASE_Y, 0], UP, buff=0, aligned_edge=DOWN)
        norm_val = txt("1,000문", size=FS_LEAD, color=DIM)
        norm_val.next_to(norm_bar, UP, buff=0.20)
        norm_lbl = txt("16세기 평상시\n안정적 유입", size=FS_CAPTION, color=DIM, bold=False)
        norm_lbl.next_to([NORM_X, BASE_Y, 0], DOWN, buff=0.3)
        norm = VGroup(norm_bar, norm_val, norm_lbl)

        # --- 17세기 위기기: 2,000문 이상 (폭등, 화면의 유일한 ACCENT) ---
        crisis_bar = Rectangle(
            width=BAR_W, height=2.70,
            color=ACCENT, fill_color=ACCENT, fill_opacity=0.55, stroke_width=STROKE,
        )
        crisis_bar.next_to([CRISIS_X, BASE_Y, 0], UP, buff=0, aligned_edge=DOWN)
        crisis_val = txt("2,000문+", size=FS_LEAD, color=ACCENT)
        crisis_val.next_to(crisis_bar, UP, buff=0.20)
        crisis_lbl = txt("17세기 위기\n은 공급 급감", size=FS_CAPTION, color=INK)
        crisis_lbl.next_to([CRISIS_X, BASE_Y, 0], DOWN, buff=0.3)
        crisis = VGroup(crisis_bar, crisis_val, crisis_lbl)

        # --- 수치 강조 블록 (바이블 §2) ---
        def figure(value: str, what: str, versus: str):
            return VGroup(
                num(value, color=SUB, size=fs(6.4)),
                txt(what, size=FS_CAPTION, color=INK),
                txt(versus, size=FS_TAG, color=DIM, bold=False),
            ).arrange(DOWN, buff=0.12)

        figures = VGroup(
            figure("약 2배+", "은화 가치 폭등", "동전 대비"),
            figure("약 3배", "농민 실질 세부담", "곡물 환전 손실"),
        ).arrange(RIGHT, buff=1.2)
        note = footnote("※ 은-동전 환율 및 실질 세부담 · von Glahn(1996)")
        block = VGroup(figures, note).arrange(DOWN, buff=0.25)
        block.move_to(DOWN * 2.15)

        for m, n in ((norm, "normal"), (crisis, "crisis"), (block, "figures")):
            guard(m, n)
        no_overlap(
            (head, "title"), (axis, "baseline"),
            (norm_val, "norm-val"), (norm_lbl, "norm-lbl"),
            (crisis_val, "crisis-val"), (crisis_lbl, "crisis-lbl"),
            (block, "figures"),
        )

        self.play(GrowFromEdge(norm_bar, DOWN), FadeIn(norm_val), FadeIn(norm_lbl), run_time=1.2)
        self.play(
            GrowFromEdge(crisis_bar, DOWN), FadeIn(crisis_val), FadeIn(crisis_lbl), run_time=1.4
        )
        self.reveal(block, run_time=1.2, shift=UP * 0.2)
