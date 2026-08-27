"""
S10 픽토그램 컷: 요약 및 루프백
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "scripts"))
from lib_style import *  # noqa: F403


class S10Scene(DiagramScene):
    DURATION = 7.65
    DRIFT = 0.004
    LOOP_TAIL = 0.35

    def build(self):
        head = title_block("비대칭전의 최종 승자")

        # --- 상단: 오답 (화력/무기) ---
        t_wrong = tag("전투의 요소", color=MUTE)
        row_wrong = VGroup(
            pict_gear(DIM, height=0.85),
            txt("압도적인 무기와 화력 우위", size=FS_BODY, color=DIM),
        ).arrange(RIGHT, buff=0.35)
        wrong = card(
            VGroup(t_wrong, row_wrong).arrange(DOWN, buff=0.16),
            width=7.8,
            color=MUTE,
            pad_y=0.38,
        )
        wrong.move_to(UP * 4.4)
        guard(wrong, "wrong-card")

        # --- 하단: 정답 (인내심/시간) ---
        t_right = tag("전쟁의 최종 승패", color=ACCENT)
        num_block = VGroup(
            txt("버티는 시간과 인내심", size=FS_NUM, color=ACCENT),
            txt("약소국: 시간 끌기 → 강대국: 정치적 인내심 고갈", size=FS_BODY, color=INK),
        ).arrange(DOWN, buff=0.15)
        right = card(
            VGroup(t_right, num_block).arrange(DOWN, buff=0.16),
            width=7.8,
            accent=True,
            pad_y=0.42,
        )
        right.move_to(DOWN * 2.1)
        guard(right, "right-card")

        link = down_arrow(color=MUTE, length=0.8)
        link.move_to(VGroup(wrong, right).get_center())

        self.play(
            AnimationGroup(
                FadeIn(head, shift=DOWN * 0.25),
                FadeIn(wrong, shift=RIGHT * 0.25),
                lag_ratio=0.20,
            ),
            run_time=1.1,
        )

        x_mark = cross_out(wrong, DIM, pad=-0.14)
        self.draw(x_mark, run_time=0.7)

        self.reveal(link, right, run_time=1.1, shift=UP * 0.20)
        self.pulse(right, times=1, scale=1.03, run_time=0.35)
