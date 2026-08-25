"""
S06 — 수치 그래프 : 산지 대비 유럽 판매가 60배 폭등 및 베네치아 독점
나레이션: "유럽에 도착하면 산지 가격의 60배로 뛰었지만, 베네치아의 독점이었습니다."

수치 출처: Fernand Braudel, *The Wheels of Commerce* (1992); C. R. Boxer (1969)
바스코 다 가마 인도 직항로 개척 시 산지 대비 60배 순이익 기록.
다단계 거점 관세와 베네치아의 독점 마진으로 유럽 최종 판매가 60배 폭등.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403

BASE_Y = 2.45
BAR_W = 1.8
NORM_X, CRISIS_X = -1.95, 1.95


class S06Scene(DiagramScene):
    DURATION = 6.06

    def build(self):
        head = title_block("다단계 유통과 가격 폭등")

        # --- 기준선 ---
        base = Line(LEFT * 3.6, RIGHT * 3.6, color=MUTE, stroke_width=2)
        base.move_to(UP * BASE_Y)
        label_base = tag("단계별 가격 격차 배율", DIM)
        label_base.next_to(base.get_left(), UP, buff=0.14, aligned_edge=LEFT)
        axis = VGroup(base, label_base)
        guard(axis, "baseline")

        self.reveal(head, axis, run_time=1.2, shift=DOWN * 0.2)

        # --- 산지 원가: 1 ---
        norm_bar = Rectangle(
            width=BAR_W, height=1.10,
            color=MUTE, fill_color=MUTE, fill_opacity=0.35, stroke_width=2,
        )
        norm_bar.next_to([NORM_X, BASE_Y, 0], UP, buff=0, aligned_edge=DOWN)
        norm_val = txt("1 (기준가)", size=FS_LEAD, color=DIM)
        norm_val.next_to(norm_bar, UP, buff=0.20)
        norm_lbl = txt("인도·몰루카 산지\n현지 구매가", size=FS_CAPTION, color=DIM, bold=False)
        norm_lbl.next_to([NORM_X, BASE_Y, 0], DOWN, buff=0.3)
        norm = VGroup(norm_bar, norm_val, norm_lbl)

        # --- 유럽 소비지: 60배 이상 (폭등, 화면의 유일한 ACCENT) ---
        crisis_bar = Rectangle(
            width=BAR_W, height=2.85,
            color=ACCENT, fill_color=ACCENT, fill_opacity=0.55, stroke_width=STROKE,
        )
        crisis_bar.next_to([CRISIS_X, BASE_Y, 0], UP, buff=0, aligned_edge=DOWN)
        crisis_val = txt("60배+", size=FS_LEAD, color=ACCENT)
        crisis_val.next_to(crisis_bar, UP, buff=0.20)
        crisis_lbl = txt("베네치아·유럽\n소비지 독점가", size=FS_CAPTION, color=INK)
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
            figure("약 60배", "유럽 도착가 폭등", "산지 원가 대비"),
            figure("독점", "베네치아 마진", "레반트 중개 무역"),
        ).arrange(RIGHT, buff=1.2)
        note = footnote("※ 산지-유럽 가격차 및 포르투갈 원정 수익률 · Braudel(1992)")
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
